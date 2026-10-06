import sys
from datetime import datetime, timedelta
from database import get_session
from models import ScheduledTask, Assignment, Group
from services.helpers import is_logist, find_user_by_username
from parsers import parse_broadcast_command, parse_route_command, normalize, match_group_in_text
from constants import HELP_TEXT, ROUTE_HELP, BROADCAST

def register(bot):
    def check(message):
        if not is_logist(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ Команда доступна только логистам.")
            return False
        return True

    @bot.message_handler(commands=["help"])
    def cmd_help(message):
        if not check(message):
            return
        bot.send_message(message.chat.id, HELP_TEXT, parse_mode="HTML")

    @bot.message_handler(commands=["driver"])
    def cmd_driver(message):
        if not check(message):
            return
        parts = message.text.split(maxsplit=2)
        if message.reply_to_message:
            driver_id = message.reply_to_message.from_user.id
            plate = (parts[1].upper() if len(parts) > 1 else "").strip()
        else:
            if len(parts) < 3:
                bot.send_message(message.chat.id, "Формат: /driver M772OP21 @username\nили ответом на сообщение водителя: /driver M772OP21", parse_mode="HTML")
                return
            plate = parts[1].upper()
            who = parts[2].strip()
            if who.lstrip("@").isdigit():
                driver_id = int(who.lstrip("@"))
            else:
                driver_id = find_user_by_username(who)
                if not driver_id:
                    bot.send_message(message.chat.id, "⚠️ Не нашёл по username. Водитель должен сначала нажать кнопку бота.",parse_mode="HTML")
                    return
        session = get_session()
        try:
            group = None
            for g in session.query(Group).all():
                if g.group_name and normalize(plate) in normalize(g.group_name):
                    group = g
                    break
            if not group:
                bot.send_message(message.chat.id, f"⚠️ Группа с машиной {plate} не найдена.")
                return
            group.driver_id = driver_id
            session.commit()
            bot.send_message(message.chat.id, f"✅ Водитель {driver_id} назначен в «{group.group_name}». Бот будет тегать его.",parse_mode="HTML")
        except Exception as e:
            print(f"[ADMIN] Ошибка driver: {e}", file=sys.stderr, flush=True)
            session.rollback()
        finally:
            session.close()

    @bot.message_handler(commands=["route"])
    def cmd_route(message):
        if not check(message):
            return
        parts = message.text.split(maxsplit=1)
        text = parts[1].strip() if len(parts) > 1 else ""
        if not text:
            bot.send_message(message.chat.id, ROUTE_HELP, parse_mode="HTML")
            return
        data = parse_route_command(text)
        if not data:
            bot.send_message(message.chat.id, "⚠️ Не понял формат.\n\n" + ROUTE_HELP, parse_mode="HTML")
            return
        if not data["daily"] and data["send_at"] <= datetime.utcnow():
            bot.send_message(message.chat.id, "⚠️ Время выгрузки уже прошло. Укажите будущую дату/время.",parse_mode="HTML")
            return
        session = get_session()
        try:
            session.add(Assignment(
                route_date=data["route_date"],
                local_time=data["local_time"],
                vehicle_plate=data["vehicle_plate"],
                route_name=data["route_name"],
                utc_offset=data["utc_offset"],
                daily=data["daily"],
                send_at=data["send_at"],
            ))
            session.commit()
        except Exception as e:
            print(f"[ADMIN] Ошибка route: {e}", file=sys.stderr, flush=True)
            session.rollback()
            return
        finally:
            session.close()
        daily_txt = "🔁 Ежедневно, " if data["daily"] else ""
        bot.send_message(
            message.chat.id,
            f"✅ Рейс запланирован:\n"
            f"{daily_txt}🚛 {data['vehicle_plate']} - {data['route_name']}\n"
            f"   Отправка: {data['route_date']} в {data['local_time']} (МСК+{data['utc_offset']})\n"
            f"🕘 Это {data['msk_dt'].strftime('%d.%m %H:%M')} по МСК", parse_mode="HTML"
        )

    @bot.message_handler(commands=["routes"])
    def cmd_routes(message):
        if not check(message):
            return
        session = get_session()
        try:
            rows = session.query(Assignment).filter_by(is_sent=False).all()
            if not rows:
                bot.send_message(message.chat.id, "Нет запланированных рейсов.", parse_mode="HTML")
                return
            text = "🚛 Запланированные рейсы:\n\n"
            for i, r in enumerate(rows, 1):
                daily = "🔁 " if r.daily else ""
                text += (
                    f"#{i} {daily}{r.route_date} {r.local_time} (МСК+{r.utc_offset})\n"
                    f"    {r.vehicle_plate} - {r.route_name}\n"
                )
            text += "\nУдалить: /delroute НОМЕР"
            bot.send_message(message.chat.id, text, parse_mode="HTML")
        finally:
            session.close()

    @bot.message_handler(commands=["delroute"])
    def cmd_delroute(message):
        if not check(message):
            return
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            bot.send_message(message.chat.id, "Формат: /delroute НОМЕР", parse_mode="HTML")
            return
        idx = int(parts[1])
        session = get_session()
        try:
            rows = session.query(Assignment).filter_by(is_sent=False).order_by(Assignment.id).all()
            if 1 <= idx <= len(rows):
                session.delete(rows[idx - 1])
                session.commit()
                bot.send_message(message.chat.id, f"🗑 Рейс #{idx} удалён.",parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, f"Нет рейса с номером {idx}.", parse_mode="HTML")
        except Exception as e:
            print(f"[ADMIN] Ошибка delroute: {e}", file=sys.stderr, flush=True)
            session.rollback()
        finally:
            session.close()

    @bot.message_handler(commands=["broadcast"])
    def cmd_broadcast(message):
        if not check(message):
            return
        parts = message.text.split(maxsplit=1)
        text = parts[1].strip() if len(parts) > 1 else ""
        if not text:
            bot.send_message(message.chat.id, BROADCAST, parse_mode="HTML")
            return
        result = parse_broadcast_command(text)
        if not result:
            bot.send_message(message.chat.id, "⚠️ Не понял время. Формат: ЧЧ:ММ или «ежедневно ЧЧ:ММ»\n\n" + BROADCAST, parse_mode="HTML")
            return
        send_at, daily, message_text = result

        session = get_session()
        try:
            target_chat_id = None
            target_name = None
            if daily:
                pairs = [(g.chat_id, g.group_name) for g in session.query(Group).all()]
                target_chat_id, target_name, message_text = match_group_in_text(message_text, pairs)

            if target_chat_id is not None:
                session.add(ScheduledTask(task_type="broadcast_to_group", target_id=target_chat_id,
                                          send_at=send_at, text=message_text, daily=True))
                group_info = f"ежедневно в «{target_name}»"
            elif daily:
                session.add(ScheduledTask(task_type="broadcast_to_groups", target_id=None,
                                          send_at=send_at, text=message_text, daily=True))
                group_info = "ежедневно во все группы"
            else:
                session.add(ScheduledTask(task_type="broadcast_to_groups", target_id=None,
                                          send_at=send_at, text=message_text, daily=False))
                group_info = "единоразово во все группы"
            session.commit()
        except Exception as e:
            print(f"[ADMIN] Ошибка broadcast: {e}", file=sys.stderr, flush=True)
            session.rollback()
            return
        finally:
            session.close()
        msk = send_at + timedelta(hours=3)
        bot.send_message(
            message.chat.id,
            f"✅ Рассылка запланирована:\n{group_info}, {msk.strftime('%d.%m %H:%M')} по МСК\nТекст: {message_text[:100]}", parse_mode="HTML"
        )

    @bot.message_handler(commands=["deltask"])
    def cmd_deltask(message):
        if not check(message):
            return
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            bot.send_message(message.chat.id, "Формат: /deltask НОМЕР (см. /tasks)")
            return
        idx = int(parts[1])
        session = get_session()
        try:
            task = session.query(ScheduledTask).filter_by(id=idx).first()
            if task:
                session.delete(task)
                session.commit()
                bot.send_message(message.chat.id, f"🗑 Задача #{idx} удалена.",parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, f"Задача с номером {idx} не найдена.", parse_mode="HTML")
        except Exception as e:
            print(f"[ADMIN] Ошибка deltask: {e}", file=sys.stderr, flush=True)
            session.rollback()
        finally:
            session.close()

    @bot.message_handler(commands=["groups"])
    def cmd_groups(message):
        if not check(message):
            return
        session = get_session()
        try:
            groups = session.query(Group).all()
            if not groups:
                bot.send_message(message.chat.id, "Пока нет групп. Добавьте бота в чаты.",parse_mode="HTML")
                return
            text = "📋 Подключённые группы:\n\n"
            for i, g in enumerate(groups, 1):
                drv = f"\n    👤 Водитель: {g.driver_id}" if g.driver_id else ""
                text += f"{i}. {g.group_name}{drv}\n   ID: {g.chat_id}\n\n"
            bot.send_message(message.chat.id, text, parse_mode="HTML")
        finally:
            session.close()