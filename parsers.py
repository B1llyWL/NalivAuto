import re
from datetime import datetime, timedelta

MSK = 3

CYR_TO_LAT = {
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H',
    'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X', 'У': 'Y',
}

def normalize(s):
    s = " ".join(CYR_TO_LAT.get(ch, ch) for ch in s.upper())
    return " ".join(s.split())


def _make_dt(year_s, month_s, day_s, hh, mm, now_msk):
    try:
        year = int(year_s) if year_s else now_msk.year
        if year < 100:
            year += 2000
        return datetime(year, int(month_s), int(day_s), int(hh), int(mm))
    except (ValueError, TypeError):
        return None

def parse_delay_minutes(text):
    t = text.lower().strip()
    now_utc = datetime.utcnow()
    now_msk = now_utc + timedelta(hours=MSK)
    m = re.search(r"(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\s+(\d{1,2}):(\d{2})", t)
    if m:
        dt = _make_dt(m.group(3), m.group(2), m.group(1), m.group(4), m.group(5), now_msk)
        if dt:
            return ("datetime", dt - timedelta(hours=MSK))
    m = re.fullmatch(r"(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?", t)
    if m:
        dt = _make_dt(m.group(3), m.group(2), m.group(1), "9", "0", now_msk)
        if dt:
            return ("datetime", dt - timedelta(hours=MSK))
    day_word = re.search(r"(сегодня|завтра|послезавтра)", t)
    time_m = re.search(r"(\d{1,2}):(\d{2})", t)
    if day_word:
        shift = {"сегодня": 0, "завтра": 1, "послезавтра": 2}[day_word.group(1)]
        base = now_msk + timedelta(days=shift)
        if time_m:
            dt = base.replace(hour=int(time_m.group(1)), minute=int(time_m.group(2)), second=0, microsecond=0)
        else:
            dt = base.replace(hour=9, minute=0, second=0, microsecond=0)
        if dt <= now_msk and shift == 0:
            dt += timedelta(days=1)
        return ("datetime", dt - timedelta(hours=MSK))
    if "вечер" in t:
        dt = now_msk.replace(hour=18, minute=0, second=0, microsecond=0)
        if dt <= now_msk:
            dt += timedelta(days=1)
        return ("datetime", dt - timedelta(hours=MSK))
    if "обед" in t:
        dt = now_msk.replace(hour=15, minute=0, second=0, microsecond=0)
        if dt <= now_msk:
            dt += timedelta(days=1)
        return ("datetime", dt - timedelta(hours=MSK))
    if t.isdigit():
        return ("minutes", int(t))
    m_min = re.search(r"(\d+)\s*(мин|минут|минуты|м\b|m\b|min|minutes)", t)
    m_hour = re.search(r"(\d+)\s*(час|часа|часов|ч\b|h\b|hour|hours)", t)
    m_day = re.search(r"(\d+)\s*(день|дня|дней|д\b|d\b|day|days)", t)
    total = 0
    if m_min:
        total += int(m_min.group(1))
    if m_hour:
        total += int(m_hour.group(1)) * 60
    if m_day:
        total += int(m_day.group(1)) * 60 * 24
    if total > 0:
        return ("minutes", total)
    cherez = re.search(r"через\s+(\d+)", t)
    if cherez:
        return ("minutes", int(cherez.group(1)))
    if "недел" in t:
        return ("minutes", 7 * 24 * 60)
    return None


def parse_broadcast_command(text):
    """Возвращает (send_at_utc, daily, message_text) или None."""
    t = text.strip()
    daily = False
    m_daily = re.match(r"(ежедневно|daily|каждый день)\s+(.+)$", t, re.I)
    if m_daily:
        daily = True
        t = m_daily.group(2)
    m = re.match(r"(\d{1,2}):(\d{2})\s+(.*)$", t, re.S)
    if not m:
        return None
    hh, mm, rest = m.groups()
    rest = rest.strip()
    if not rest:
        return None
    now_msk = datetime.utcnow() + timedelta(hours=MSK)
    try:
        send_msk = now_msk.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    except ValueError:
        return None
    if send_msk <= now_msk:
        send_msk += timedelta(days=1)
    send_at = send_msk - timedelta(hours=MSK)
    return (send_at, daily, rest)


def match_group_in_text(rest, groups):
    """Умный поиск группы в начале сообщения.
    groups - список кортежей (chat_id, group_name).
    Возвращает (chat_id, group_name, message_text) или (None, None, rest)."""
    words = rest.split()
    for n in range(len(words) - 1, 0, -1):
        prefix_n = normalize(" ".join(words[:n]))
        for chat_id, name in groups:
            if name and prefix_n in normalize(name):
                return chat_id, name, " ".join(words[n:])
    return None, None, rest

def parse_route_command(text):
    t = text.strip()
    daily = False
    m_daily = re.match(r"(ежедневно|daily|каждый день)\s+(.+)$", t, re.I)
    if m_daily:
        daily = True
        t = m_daily.group(2)
    m = re.match(
        r"(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?"
        r"(?:\s*-\s*(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?)?"
        r"[:\s]+"
        r"(\d{1,2}):(\d{2})"
        r"[:\s]+"
        r"([A-Za-zА-Яа-я0-9]+)"
        r"[:\s]+"
        r"(.+?)"
        r"(?:[:\s]([+-]\d{1,2}))?$",
        t
    )
    if not m:
        return None
    dep_d, dep_m, dep_y, unl_d, unl_m, unl_y, hh, mm, plate, route, off_s = m.groups()
    offset = int(off_s) if off_s else 0
    now_msk = datetime.utcnow() + timedelta(hours=MSK)
    if unl_d:
        msk_dt = _make_dt(unl_y, unl_m, unl_d, hh, mm, now_msk)
        depart_str = f"{dep_d}.{dep_m}"
        unload_str = f"{unl_d}.{unl_m}"
        date_str = f"{dep_d}.{dep_m}–{unl_d}.{unl_m}"
    else:
        msk_dt = _make_dt(dep_y, dep_m, dep_d, hh, mm, now_msk)
        depart_str = None
        unload_str = f"{dep_d}.{dep_m}"
        date_str = f"{dep_d}.{dep_m}"
    if not msk_dt:
        return None
    send_at = msk_dt - timedelta(hours=MSK)
    local_dt = msk_dt + timedelta(hours=offset)
    return {
        "route_date": date_str,
        "depart_date": depart_str,
        "unload_date": unload_str,
        "local_time": f"{int(hh):02d}:{int(mm):02d}",
        "vehicle_plate": plate.upper(),
        "route_name": route.strip(),
        "utc_offset": offset,
        "daily": daily,
        "send_at": send_at,
        "msk_dt": msk_dt,
        "local_dt": local_dt,
    }