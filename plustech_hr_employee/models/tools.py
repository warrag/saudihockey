try:
    from hijri_converter import Gregorian, convert
except ImportError:
    pass


def convert_gregorian_to_hijri(date):
    day = date.day
    month = date.month
    year = date.year
    hijri_date = Gregorian(year, month, day).to_hijri()
    return hijri_date
