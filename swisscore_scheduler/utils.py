from datetime import MAXYEAR, datetime, timedelta, time, date
from typing import Callable, Optional


def to_datetime(t) -> datetime:
    if isinstance(t, datetime):
        return t
    elif isinstance(t, timedelta):
        return datetime.now() + t
    elif isinstance(t, time):
        return datetime.combine(datetime.now(), t)
    else:
        raise TypeError(f"excepted datetime.datetime, datetime.timedelta")


def function_str(func: Callable, *args, **kwargs) -> str:
    args_str = ", ".join(f"{a.__repr__()}" for a in args)
    if kwargs:
        args_str += ", " + ", ".join(
            [f"{k}={v.__repr__()}" for (k, v) in kwargs.items()]
        )
    return f"{func.__name__}({args_str})"


def is_leap_year(year: int) -> bool:
    try:
        date(year, 2, 29)
        return True
    except ValueError:
        return False


def day_in_month_range(day: int, month: int, year: Optional[int] = None) -> bool:
    if day <= 28:
        return True
    if day == 29:
        if year is not None:
            return True if month != 2 else is_leap_year(year)
        else:
            return True
    if day == 30:
        return month != 2
    if day == 31:
        return month in [1, 3, 5, 7, 8, 10, 12]
    return False


def validate_date(
    day: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> None:
    if year is not None:
        if not isinstance(month, int):
            raise TypeError(f"`year` must be an `int`")

        current_year = datetime.now().year
        if not current_year <= month <= MAXYEAR:
            raise ValueError(f"`year` must be in {current_year}..{MAXYEAR}")

    if month is not None:
        if not isinstance(month, int):
            raise TypeError(f"`month` must be an `int`")

        if not 1 <= month <= 12:
            raise ValueError(f"`month` must be in 1..12")

    if day is not None:
        if not isinstance(day, int):
            raise TypeError(f"`day` must be an `int`")

        if not 0 <= day <= 31:
            raise ValueError(f"`day` must be in 0..31")

        if month is not None:
            if year is not None:
                if not day_in_month_range(day, month, year):
                    raise ValueError("day is out of range for month")
            elif month == 2 and day == 29:
                #! TODO: Warn User
                #! Only executed if leap year
                pass

        elif day == 29:
            #! TODO: Warn User
            #! Not Executed in February if not leap year
            pass

        elif day == 30:
            #! TODO: Warn User
            #! Not Executed in February
            pass

        elif day == 31:
            #! TODO: Warn User
            #! Only Executed in January, March, May, July, August, October and December
            #! Not Executed in February, April, June, September and November
            pass


def validate_time(
    second: int, minute: Optional[int] = None, hour: Optional[int] = None
) -> None:

    if hour is not None:
        if not isinstance(hour, int):
            raise TypeError(f"`hour` must be an `int`")
        if not 0 <= hour <= 23:
            raise ValueError(f"`hour` must be in 0..23")

    if minute is not None:
        if not isinstance(minute, int):
            raise TypeError(f"`minute` must be an `int`")
        if not 0 <= minute <= 59:
            raise ValueError(f"`minute` must be in 0..59")

    if not isinstance(second, int):
        raise TypeError(f"`second` must be an `int`")
    if not 0 <= second <= 59:
        raise ValueError(f"`second` must be in 0..59")
