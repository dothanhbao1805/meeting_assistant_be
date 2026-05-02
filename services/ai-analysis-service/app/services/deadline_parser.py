import re
from datetime import date, datetime, timedelta


def parse_deadline(raw: str | None, reference_date: date | None = None) -> date | None:
    if not raw:
        return None

    ref = reference_date or date.today()
    raw = raw.lower().strip()

    # dd/mm/yyyy hoặc yyyy-mm-dd hoặc dd-mm-yyyy
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    # X ngày nữa / trong X ngày
    match = re.search(r"(\d+)\s*ngày", raw)
    if match:
        return ref + timedelta(days=int(match.group(1)))

    # Cuối tuần / cuối tuần sau
    if "cuối tuần" in raw:
        days_to_friday = (4 - ref.weekday()) % 7 or 7
        if "sau" in raw:
            days_to_friday += 7
        return ref + timedelta(days=days_to_friday)

    # Thứ X tuần này / tuần sau
    weekday_map = {
        "thứ hai": 0, "thứ 2": 0,
        "thứ ba": 1,  "thứ 3": 1,
        "thứ tư": 2,  "thứ 4": 2,
        "thứ năm": 3, "thứ 5": 3,
        "thứ sáu": 4, "thứ 6": 4,
        "thứ bảy": 5, "thứ 7": 5,
        "chủ nhật": 6,
    }
    for key, weekday in weekday_map.items():
        if key in raw:
            days_ahead = (weekday - ref.weekday()) % 7 or 7
            if "sau" in raw:
                days_ahead += 7
            return ref + timedelta(days=days_ahead)

    # Cuối tháng
    if "cuối tháng" in raw:
        next_month = ref.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)

    return None  # không parse được → user điền tay