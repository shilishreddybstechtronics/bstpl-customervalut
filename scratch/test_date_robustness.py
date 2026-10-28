from datetime import datetime, date, timedelta
import re

_DATE_FORMATS = (
    "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y/%m/%d", "%Y.%m.%d",
    "%d-%m-%y", "%d/%m/%y", "%d.%m.%y",
    "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y", "%m/%d/%y", "%m-%d-%y", "%m.%d.%y",
    "%d-%b-%Y", "%d %b %Y", "%d-%b-%y", "%d %b %y", "%d/%b/%y", "%d.%b.%y", "%d/%b/%Y", "%d.%b.%Y",
    "%b %d, %Y", "%b %d %Y", "%b %d, %y", "%b %d %y",
    "%d-%B-%Y", "%d-%B-%y", "%d %B %Y", "%d %B %y", "%B %d, %Y", "%B %d, %y",
    "%Y%m%d", "%d%m%Y", "%d%m%y"
)

def _to_date(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    if not s or s.lower() in ("nan", "nat", "none", "null", "-", "--", "---", "—", "–", "#n/a", "n/a", "na", "nil", "undefined", "blank", "0", "0000-00-00", "00/00/0000"):
        return None
    try:
        n = float(s)
    except ValueError:
        n = None
    if n is not None:
        if n == 0:
            return None
        if 20000 < n < 80000:
            return date(1899, 12, 30) + timedelta(days=int(n))
        if 19900101 <= n <= 20991231:
            s = str(int(n))
        elif 1011990 <= n <= 31122099:
            s = str(int(n)).zfill(8)

    # Drop time part including AM/PM
    s = re.sub(r"[T\s]\d{1,2}:\d{2}(:\d{2})?(\.\d+)?(\s*[APap][Mm])?.*$", "", s).strip()
    s = re.sub(r"^[\"\'\s\-_/.]+|[\"\'\s\-_/.]+$", "", s)
    if not s:
        return None

    # Delimited format check
    for fmt in _DATE_FORMATS:
        try:
            d = datetime.strptime(s, fmt).date()
            if 1950 <= d.year <= 2099:
                return d
        except ValueError:
            pass

    # Delimited numbers fallback: e.g. 24-05-18 or 18/05/24
    parts = [p for p in re.split(r"[-/. ,\\]+", s) if p and p.isdigit()]
    if len(parts) == 3:
        p0, p1, p2 = int(parts[0]), int(parts[1]), int(parts[2])
        # Case A: Year first e.g. 24-05-18 or 2024-05-18
        if 1990 <= p0 <= 2099 and 1 <= p1 <= 12 and 1 <= p2 <= 31:
            return date(p0, p1, p2)
        if len(parts[0]) == 2 and 20 <= p0 <= 50 and 1 <= p1 <= 12 and 1 <= p2 <= 31:
            return date(2000 + p0, p1, p2)
        # Case B: Year last e.g. 18-05-24 or 18/05/2024
        yr = p2
        if len(parts[2]) == 2:
            yr = 2000 + p2 if p2 < 70 else 1900 + p2
        if 1990 <= yr <= 2099:
            if p1 > 12 and 1 <= p0 <= 12 and 1 <= p1 <= 31:
                return date(yr, p0, p1)
            elif 1 <= p0 <= 31 and 1 <= p1 <= 12:
                return date(yr, p1, p0)

    return None

test_vals = [
  '18-05-2024', '18/05/2024', '18.05.2024', '2024-05-18', '2024/05/18',
  '18-05-24', '18/05/24', '18.05.24', '5/18/24', '05/18/24', '24-05-18', '24/05/18',
  '18-May-2024', '18-May-24', '18 May 2024', '18 May 24', 'May 18, 2024', 'May 18, 24',
  '18-January-2024', '18-Jan-24', '18/Jan/24', '18.Jan.24',
  '20240518', '18052024',
  '18-05-2024 14:30:00', '18/05/24 12:00:00 AM', '2024-05-18T10:15:00', '18-05-24 10:30 AM',
  45430, '45430', '45430.5',
  '-', 'NA', 'N/A', None, '', '0'
]
for v in test_vals:
    res = _to_date(v)
    print(f"{repr(v):<25} -> {res}")

