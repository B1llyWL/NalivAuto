import sys
from datetime import datetime, timedelta
from database import get_session
from models import ScheduledTask, Group, Assignment
from keyboards import yes_no_keyboard
from services.notifications import notify_logists
from parsers import normalize
from constants import MSG_LOAD_QUESTION, MSG_REMINDER

GRACE = timedelta(minutes=30)
EXPIRE_OVERDUE = timedelta(minutes=60)   # просрочка единоразовой задачи, после которой она удаляется
RETENTION_DONE = timedelta(days=7)       # сколько храним отправленные задачи

def log(msg):
    print(f"[SCHED] {msg}", file=sys.stderr, flush=True)


def find_group_by_plate(session, plate):
    plate_n = normalize(plate)
    for g in session.query(Group).all():
        if g.group_name and plate_n in normalize(g.group_name):
            return g
    return None

def driver_mention(group):
    if getattr(group, "driver_id", None):
        return f'<a href="tg://user?id={group.driver_id}">Водитель</a>, '
    return ""

def cleanup_old_tasks(session, now):
    """Автоочистка старых задач."""
    stale = (
        session.query(ScheduledTask)
        .filter(ScheduledTask.is_sent == False,
                ScheduledTask.daily == False,
                ScheduledTask.send_at < now - EXPIRE_OVERDUE)
        .all()
    )
    for t in stale:
        log(f"Задача #{t.id} протухла и удалена (просрочка > 60 мин): {str(t.text)[:40]}")
        session.delete(t)
    done = (
        session.query(ScheduledTask)
        .filter(ScheduledTask.is_sent == True,
                ScheduledTask.send_at < now - RETENTION_DONE)
        .all()
    )
    for t in done:
        session.delete(t)
    if stale or done:
        session.commit()
        log(f"Автоочистка: протухших={len(stale)}, из истории={len(done)}")


def process_scheduled_tasks(bot):
    session = get_session()
    try:
        now = datetime.utcnow()
        cleanup_old_tasks(session, now)
        tasks = (
            session.query(ScheduledTask)
            .filter(ScheduledTask.is_sent == False, ScheduledTask.send_at <= now)
            .all()
        )
        log(f"Задач к отправке: {len(tasks)}")
        for task in tasks:
            try:
                delivered = 0
                if task.task_type == "broadcast_to_groups":
                    groups = session.query(Group).filter_by(is_active=True).all()
                    log(f"Рассылка во все группы ({len(groups)}): {task.text[:30]}")
                    for g in groups:
                        try:
                            bot.send_message(g.chat_id, task.text)
                            delivered += 1
                        except Exception as e:
                            log(f"Ошибка отправки в {g.group_name}: {e}")
                elif task.task_type == "broadcast_to_group":
                    log(f"Рассылка в группу {task.target_id}: {task.text[:30]}")
                    try:
                        bot.send_message(task.target_id, task.text)
                        delivered += 1
                    except Exception as e:
                        log(f"Ошибка отправки в {task.target_id}: {e}")
                elif task.task_type == "remind_driver":
                    group_id = int(task.text) if task.text else None
                    if group_id:
                        try:
                            bot.send_message(group_id, MSG_REMINDER)
                            delivered += 1
                        except Exception as e:
                            log(f"Ошибка напоминания в {group_id}: {e}")

                if delivered > 0:
                    if task.daily:
                        task.send_at += timedelta(days=1)
                        while task.send_at <= now:
                            task.send_at += timedelta(days=1)
                        task.is_sent = False
                    else:
                        task.is_sent = True
                else:
                    log(f"Задача #{task.id}: доставка не удалась, повтор на следующем чеке")
                session.commit()
            except Exception as e:
                log(f"Ошибка задачи {task.id}: {e}")
                session.rollback()
    except Exception as e:
        log(f"Общая ошибка tasks: {e}")
    finally:
        session.close()


def process_assignments(bot):
    session = get_session()
    try:
        now = datetime.utcnow()
        rows = (
            session.query(Assignment)
            .filter(Assignment.is_sent == False, Assignment.send_at <= now)
            .all()
        )
        log(f"Рейсов к отправке: {len(rows)}")
        for row in rows:
            try:
                group = find_group_by_plate(session, row.vehicle_plate)
                if group:
                    text = driver_mention(group) + MSG_LOAD_QUESTION
                    bot.send_message(group.chat_id, text,
                                     reply_markup=yes_no_keyboard(), parse_mode="HTML")
                    notify_logists(bot, f"📨 Вопрос отправлен в «{group.group_name}»\nРейс: {row.route_name}")
                    if row.daily:
                        row.send_at += timedelta(days=1)
                        while row.send_at <= now:
                            row.send_at += timedelta(days=1)
                    else:
                        session.delete(row)
                else:
                    log(f"Рейс {row.id}: группа не найдена, ждём")
                    if (now - row.send_at) > GRACE:
                        notify_logists(bot, f"⚠️ Группа для {row.vehicle_plate} не найдена за 30 минут - рейс удалён")
                        session.delete(row)
                session.commit()
            except Exception as e:
                log(f"Ошибка рейса {row.id}: {e}")
                session.rollback()
    except Exception as e:
        log(f"Общая ошибка assignments: {e}")
    finally:
        session.close()