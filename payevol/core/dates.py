from datetime import date

def add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    return date(y, m, 1)

def first_day_current_month() -> date:
    t = date.today()
    return date(t.year, t.month, 1)
