from __future__ import annotations
from abc import ABC
from datetime import datetime

from enum import Enum
from typing import Optional, Callable

from . import scheduler, tasks, utils


class TaskType(Enum):
    one_time = "one_time"
    secondly = "secondly"
    minutely = "minutely"
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class FutureTask:
    def __init__(self, scheduler: scheduler.AsyncScheduler) -> None:
        self.scheduler: scheduler.AsyncScheduler = scheduler
        self.type: TaskType = TaskType.one_time
        self.at_time: list[int] = []
        self.at_date: list[int] = []
        self.interval: int = 1
        self.tags: list[str] = []

        self.fixed_datetime: Optional[datetime] = None
        self.fixed_month: Optional[int] = None
        self.fixed_month_day: Optional[int] = None
        self.fixed_weekday: Optional[int] = None

    def create(self, func: Callable, *args, **kwargs):
        return tasks.ScheduledTask(
            self.scheduler,
            self.type,
            self.at_time,
            self.at_date,
            self.interval,
            self.tags,
            self.fixed_datetime,
            self.fixed_month,
            self.fixed_month_day,
            self.fixed_weekday,
            func,
            args,
            kwargs,
        )


class Creator(ABC):
    def __init__(self, future_task: FutureTask) -> None:
        self._future_task = future_task


class TaskFinalizer(Creator):
    def __init__(self, future_task: FutureTask) -> None:
        super().__init__(future_task)

    def run(self, func: Callable, *args, **kwargs) -> tasks.ScheduledTask:
        """apply the task to the scheduler"""
        scheduled_task = self._future_task.create(func, *args, **kwargs)
        return scheduled_task


class UnitSelector(Creator):
    def __init__(self, future_task: FutureTask) -> None:
        super().__init__(future_task)

    @property
    def second(self) -> TaskFinalizer:
        self._future_task.type = TaskType.secondly
        return TaskFinalizer(self._future_task)

    @property
    def minute(self) -> SecondSelector:
        self._future_task.type = TaskType.minutely
        return SecondSelector(self._future_task)

    @property
    def hour(self) -> MinuteSelector:
        self._future_task.type = TaskType.hourly
        return MinuteSelector(self._future_task)

    @property
    def day(self) -> HourSelector:
        self._future_task.type = TaskType.daily
        return HourSelector(self._future_task)

    @property
    def monday(self) -> HourSelector:
        self._future_task.type = TaskType.weekly
        self._future_task.fixed_weekday = 0
        return HourSelector(self._future_task)

    @property
    def tuesday(self) -> HourSelector:
        self._future_task.type = TaskType.weekly
        self._future_task.fixed_weekday = 1
        return HourSelector(self._future_task)

    @property
    def wednesday(self) -> HourSelector:
        self._future_task.type = TaskType.weekly
        self._future_task.fixed_weekday = 2
        return HourSelector(self._future_task)

    @property
    def thursday(self) -> HourSelector:
        self._future_task.type = TaskType.weekly
        self._future_task.fixed_weekday = 3
        return HourSelector(self._future_task)

    @property
    def friday(self) -> HourSelector:
        self._future_task.type = TaskType.weekly
        self._future_task.fixed_weekday = 4
        return HourSelector(self._future_task)

    @property
    def saturday(self) -> HourSelector:
        self._future_task.type = TaskType.weekly
        self._future_task.fixed_weekday = 5
        return HourSelector(self._future_task)

    @property
    def sunday(self) -> HourSelector:
        self._future_task.type = TaskType.weekly
        self._future_task.fixed_weekday = 6
        return HourSelector(self._future_task)

    def month(self, day: int) -> HourSelector:
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 31:
            raise ValueError("day must be in 1..31")
        self._future_task.at_date = [day]
        self._future_task.type = TaskType.monthly
        self._future_task.fixed_month_day = day
        return HourSelector(self._future_task)

    def january(self, day: int) -> HourSelector:
        """
        each january at the given day
        :param day: must be in 1..31
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 31:
            raise ValueError("day is out of range for this month")
        return self.__year(1, day)

    def february(self, day: int) -> HourSelector:
        """
        each february at the given day
        :param day: must be in 1..29
        NOTE: if day is 29, the function only gets executed in leap years
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 29:
            raise ValueError("day is out of range for this month")
        if day == 29:
            #! TODO: Warn user
            pass
        return self.__year(2, day)

    def march(self, day: int) -> HourSelector:
        """
        each march at the given day
        :param day: must be in 1..31
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 31:
            raise ValueError("day is out of range for this month")
        return self.__year(3, day)

    def april(self, day: int) -> HourSelector:
        """
        each april at the given day
        :param day: must be in 1..30
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 30:
            raise ValueError("day is out of range for this month")
        return self.__year(4, day)

    def may(self, day: int) -> HourSelector:
        """
        each may at the given day
        :param day: must be in 1..31
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 31:
            raise ValueError("day is out of range for this month")
        return self.__year(5, day)

    def june(self, day: int) -> HourSelector:
        """
        each june at the given day
        :param day: must be in 1..30
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 30:
            raise ValueError("day is out of range for this month")
        return self.__year(6, day)

    def july(self, day: int) -> HourSelector:
        """
        each july at the given day
        :param day: must be in 1..31
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 31:
            raise ValueError("day is out of range for this month")
        return self.__year(7, day)

    def august(self, day: int) -> HourSelector:
        """
        each august at the given day
        :param day: must be in 1..31
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 31:
            raise ValueError("day is out of range for this month")
        return self.__year(8, day)

    def septeber(self, day: int) -> HourSelector:
        """
        each september at the given day
        :param day: must be in 1..30
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 30:
            raise ValueError("day is out of range for this month")
        return self.__year(9, day)

    def october(self, day: int) -> HourSelector:
        """
        each october at the given day
        :param day: must be in 1..31
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 31:
            raise ValueError("day is out of range for this month")
        return self.__year(10, day)

    def november(self, day: int) -> HourSelector:
        """
        each november at the given day
        :param day: must be in 1..30
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= int(day) <= 30:
            raise ValueError("day is out of range for this month")
        return self.__year(11, day)

    def december(self, day: int) -> HourSelector:
        """
        each december at the given day
        :param day: must be in 1..31
        """
        if not isinstance(day, int):
            raise TypeError("day must be an `int`")
        if not 1 <= day <= 31:
            raise ValueError("day is out of range for this month")
        return self.__year(12, day)

    def __year(self, month: int, day: int) -> HourSelector:
        """
        Dont use this function yourself!
        Better use .month_name instead.
        Example:
            `each.december(24).at(18).run(some_func, *args, **kwargs)`
            -> runs each year on December 24 at 18:00:00
        """
        self._future_task.fixed_month = month
        self._future_task.fixed_month_day = day
        self._future_task.at_date = [month, day]
        self._future_task.type = TaskType.yearly
        return HourSelector(self._future_task)


class UnitsSelector(Creator):
    def __init__(self, future_task: FutureTask) -> None:
        super().__init__(future_task)

    @property
    def seconds(self) -> TaskFinalizer:
        self._future_task.type = TaskType.secondly
        return TaskFinalizer(self._future_task)

    @property
    def minutes(self) -> SecondSelector:
        self._future_task.type = TaskType.minutely
        return SecondSelector(self._future_task)

    @property
    def hours(self) -> MinuteSelector:
        self._future_task.type = TaskType.hourly
        return MinuteSelector(self._future_task)

    @property
    def days(self) -> HourSelector:
        self._future_task.type = TaskType.daily
        return HourSelector(self._future_task)


class SecondSelector(Creator):
    def __init__(self, future_task: FutureTask) -> None:
        super().__init__(future_task)

    def at(self, second: int = 0) -> TaskFinalizer:
        """
        The second to run.
        :param second: must be in 0..59
        """
        utils.validate_time(second)
        self._future_task.at_time = [second]
        return TaskFinalizer(self._future_task)

    def run(self, func: Callable, *args, **kwargs) -> tasks.ScheduledTask:
        """run every minute at HH:MM:00"""
        return self.at().run(func, *args, **kwargs)


class MinuteSelector(Creator):
    def __init__(self, future_task: FutureTask) -> None:
        super().__init__(future_task)

    def at(self, minute: int = 0, second: int = 0) -> TaskFinalizer:
        """
        The minute to run.
        :param minute: must be in 0..59
        :param second: must be in 0..59
        """
        utils.validate_time(second, minute)
        self._future_task.at_time = [minute, second]
        return TaskFinalizer(self._future_task)

    def run(self, func: Callable, *args, **kwargs) -> tasks.ScheduledTask:
        """run every hour at HH:00:00"""
        return self.at().run(func, *args, **kwargs)


class HourSelector(Creator):
    def __init__(self, future_task: FutureTask) -> None:
        super().__init__(future_task)

    def at(self, hour: int = 0, minute: int = 0, second: int = 0) -> TaskFinalizer:
        """
        The time to run.
        :param hour: must be in 0..23
        :param minute: must be in 0..59
        :param second: must be in 0..59
        """
        utils.validate_time(second, minute, hour)
        self._future_task.at_time = [hour, minute, second]
        return TaskFinalizer(self._future_task)

    # TODO: Maybe implement this
    # @property
    # def midnight(self) -> TaskFinalizer:
    #     """at 00:00:00"""
    #     return self.at()

    # @property
    # def noon(self) -> TaskFinalizer:
    #     """at 12:00:00"""
    #     return self.at(12)

    def run(self, func: Callable, *args, **kwargs) -> tasks.ScheduledTask:
        """run at 00:00:00"""
        return self.at().run(func, *args, **kwargs)
