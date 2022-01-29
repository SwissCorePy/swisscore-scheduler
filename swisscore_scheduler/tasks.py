from __future__ import annotations

import asyncio
from time import perf_counter
from datetime import datetime, timedelta
from typing import Awaitable, Dict, List, Optional, Any, Callable, Tuple, Union

from . import creation_helper, scheduler, utils
from . import logger


class TaskResult:
    """the result of a task"""

    def __init__(
        self,
        succeed: bool,
        result: Union[Any, Exception, None],
        run_time: datetime,
        duration: float,
    ) -> None:
        self._succeed: bool = succeed
        self._result: Union[Any, Exception, None] = result
        self._datetime: datetime = run_time
        self._duration: float = duration

    @property
    def succeed(self) -> bool:
        """True if last run was successfully"""
        return self._succeed

    @property
    def result(self) -> Union[Any, Exception, None]:
        """
        returns the last returned result of the scheduled function.
        if an exception was raised, the exception is returned.
        """
        return self._result

    @property
    def datetime(self) -> datetime:
        """datetime of last run"""
        return self._datetime

    @property
    def duration(self) -> float:
        """the duration of the last run in seconds. measured using `time.perf_counter`"""
        return self._duration

    def __bool__(self) -> bool:
        return self._succeed

    def __repr__(self) -> str:
        d = {"ok": self.ok, "result": self.result, "run_duration": self.run_duration}
        return f"{self.__class__.__name__}: {d}"


class CancelledTask:
    """a cancelled task"""

    def __init__(self, task: ScheduledTask) -> None:
        self.type: creation_helper.TaskType = task.type
        self.tags: List[str] = task.tags
        self.last_run: Optional[TaskResult] = task.last_run
        self.total_runs: int = task.previous_runs

        self.func: Callable = task.func
        self.args: Tuple[Any] = task.args
        self.kwargs: Dict[str, Any] = task.kwargs

        self._funcstr = task._funcstr

    def __repr__(self):
        d = {
            "type": self.type.value,
            "last_run": self.last_run,
            "total_runs": self.total_runs,
            "func": self._funcstr,
            "tags": self.tags,
        }
        return f"{self.__class__.__name__}: {d}"


class ScheduledTask:
    """a scheduled task"""

    def __init__(
        self,
        scheduler: scheduler.AsyncScheduler,
        type: str,
        at_time: list[int],
        at_date: list[int],
        interval: int,
        tags: Optional[list[str]],
        fixed_datetime: Optional[datetime],
        fixed_month: Optional[int],
        fixed_month_day: Optional[int],
        fixed_weekday: Optional[int],
        func: Callable,
        args: Tuple[Any],
        kwargs: Dict[str, Any],
    ) -> None:
        self._scheduler: scheduler.AsyncScheduler = scheduler
        self.type: str = type
        self.at_time: list[int] = at_time
        self.at_date: list[int] = at_date
        self.interval: int = interval

        self.tags: Optional[List[str]] = tags

        self.fixed_datetime: Optional[datetime] = fixed_datetime
        self.fixed_month: Optional[int] = fixed_month
        self.fixed_month_day: Optional[int] = fixed_month_day
        self.fixed_weekday: Optional[int] = fixed_weekday

        self.func: Callable = func
        self.args: Tuple[Any] = args
        self.kwargs: Dict[str, Any] = kwargs

        self._funcstr = utils.function_str(func, *args, **kwargs)

        self._previous_runs = 0
        self._next_run: datetime = (
            self.fixed_datetime
            if self.fixed_datetime
            else self._calculate_next_run(datetime.now())
        )
        self._last_run: Optional[TaskResult] = None
        self._task: Optional[asyncio.Task] = None

        self._scheduler._append_task(self)

        if self._scheduler.is_running:
            self._task = asyncio.get_running_loop().create_task(self._run())

    def __repr__(self):
        d = {
            # "type": self.type.value,
            "func": self._funcstr,
            "tags": self.tags,
        }
        return f"{self.__class__.__name__}: {d}"

    @property
    def last_run(self) -> Optional[TaskResult]:
        """result of the last previous run"""
        return self._last_run

    @property
    def previous_runs(self) -> int:
        """the total number of prevoius runs"""
        return self._previous_runs

    @property
    def next_run(self) -> Optional[datetime]:
        """datetime of the next run"""
        return self._next_run

    @property
    def wait_time(self) -> Optional[float]:
        """seconds until the next run"""
        if self.next_run:
            delta = self.next_run.timestamp() - datetime.now().timestamp()
            if self.last_run:
                delta -= self.last_run.duration
            return delta

    @property
    def timedelta(self) -> Optional[timedelta]:
        """timedelta until the next nun"""
        if self.next_run:
            return timedelta(seconds=self.wait_time)

    def cancel(self) -> CancelledTask:
        return self._scheduler.cancel_task(self)

    def add_tags(self, *tags: str) -> ScheduledTask:
        """add tags to this task"""
        if tags:
            for tag in tags:
                if not tag in self.tags:
                    self.tags.append(tag)
            logger.debug(f"Updated tags of {self}")
        return self

    def remove_tags(self, *tags: str) -> ScheduledTask:
        """remove tags from this task"""
        if tags:
            for tag in tags:
                if tag in self.tags:
                    self.tags.remove(tag)
            logger.debug(f"Updated tags of {self}")
        return self

    def matching_tags(self, *tags) -> bool:
        """check if tags matching"""
        return all([tag in self.tags for tag in tags])

    def _calculate_next_run(self, now: datetime) -> datetime:
        at = [*self.at_date, *self.at_time, now.microsecond]

        if self.type == creation_helper.TaskType.secondly:
            return now + timedelta(seconds=self.interval)

        if self.type == creation_helper.TaskType.minutely:
            then = datetime(now.year, now.month, now.day, now.hour, now.minute, *at)
            # print(now, then)
            return then if then > now else (then + timedelta(minutes=self.interval))

        if self.type == creation_helper.TaskType.hourly:
            then = datetime(now.year, now.month, now.day, now.hour, *at)
            return then if then > now else (then + timedelta(hours=self.interval))

        if self.type == creation_helper.TaskType.daily:
            then = datetime(now.year, now.month, now.day, *at)
            return then if then > now else (then + timedelta(days=self.interval))

        if self.type == creation_helper.TaskType.weekly:
            delta_days = (self.fixed_weekday - now.weekday()) % 7
            then = datetime(now.year, now.month, now.day, *at) + timedelta(
                days=delta_days
            )
            return then if then > now else (then + timedelta(days=7))

        if self.type == creation_helper.TaskType.monthly:
            day = self.fixed_month_day or at[0]
            target_month = now.month
            delta_year = 0
            while not utils.day_in_month_range(
                day, target_month, now.year + delta_year
            ):
                target_month = (target_month % 12) + 1
                delta_year = 0 if target_month > now.month else 1
            then = datetime(now.year + delta_year, target_month, *at)
            if then < now:
                target_month = (target_month % 12) + 1
                while not utils.day_in_month_range(
                    day, target_month, now.year + delta_year
                ):
                    target_month = (target_month % 12) + 1
                    delta_year += 0 if target_month > now.month else 1
                then = datetime(now.year + delta_year, target_month, *at)
            return then

        if self.type == creation_helper.TaskType.yearly:
            then = datetime(now.year, *at)
            return then if then > now else datetime(now.year + 1, *at)

    async def _wait(self) -> bool:
        """
        waits until next run
        returns False if the task was cancelled during wait time else True
        """
        try:
            await asyncio.sleep(self.wait_time)

        except asyncio.CancelledError:
            return False

        return True

    async def _run(self) -> None:
        should_run = await self._wait()
        if not should_run:
            return

        cancelled = False
        succeed = True
        result = None
        start_time = perf_counter()
        try:
            logger.debug(f"Running function: {self._funcstr}")
            if asyncio.iscoroutinefunction(self.func) or isinstance(
                self.func, Awaitable
            ):
                result = await self.func(*self.args, **self.kwargs)
            else:
                result = self.func(*self.args, **self.kwargs)

        except asyncio.CancelledError:
            cancelled = True

        except Exception as e:
            logger.exception("Caught Exception while running a scheduled Task:")
            succeed = False
            result = e

        finally:
            duration = perf_counter() - start_time
            self._last_run = TaskResult(succeed, result, datetime.now(), duration)
            self._previous_runs += 1
            if cancelled or self.type == creation_helper.TaskType.one_time:
                self._next_run = None
                if not cancelled:
                    self.cancel()
                    await self._scheduler._run_callback(self)
            else:
                self._next_run = self._calculate_next_run(self._last_run.datetime)
                await self._scheduler._run_callback(self)
                await self._run()
