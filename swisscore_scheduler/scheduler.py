from __future__ import annotations

import asyncio
from ctypes import Union
from datetime import datetime, time, timedelta
from typing import Awaitable, Dict, List, Optional, Callable

from . import creation_helper, tasks
from . import logger


class CallbackHandler:
    def __init__(self, func: Callable, *tags: str) -> None:
        self.func: Callable = func
        self.tags = list(tags)

    async def run(self, task: tasks.ScheduledTask):
        try:
            await self.func(task)

        except Exception:
            logger.exception("Caught Exception while running a callback handler:")


class AsyncScheduler:
    def __init__(self) -> None:
        self.tasks: list[tasks.ScheduledTask] = []
        self.conditional_tasks: list[tasks.ConditionalTask] = []

        self.is_running: bool = False

        self._callback_handlers: List[CallbackHandler] = []
        self._exception_handler: Optional[CallbackHandler] = None

    def start_concurrently(self):
        """
        start scheduler concurrently.
        runs until the main script ends.
        """
        if self.is_running:
            raise RuntimeError("Scheduler is already running")
        self.is_running = True
        logger.info("Starting scheduler concurrently!")
        self._main_task = asyncio.create_task(self._main(run_forever=True))

    def start(self, *, run_forever: bool = False) -> None:
        """
        start scheduler as main event loop.

        if `run_forever` is True:
            runs until `stop()` is called or `CTRL+C` is pressed.
        else:
            runs until no pending tasks are left or `CTRL+C` is pressed.
        """
        if self.is_running:
            raise RuntimeError("Scheduler is already running")
        self.is_running = True
        try:
            logger.info("Starting scheduler as main loop!\n(Press CTRL+C to quit)")
            asyncio.run(self._main(run_forever))

        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """
        Cancel all pending Tasks and stop scheduler
        """
        if not self.is_running:
            raise RuntimeError("Scheduler is not running")

        for task in self.tasks:
            self.cancel_task(task)

        self.is_running = False
        logger.info("Scheduler was stopped!")

    async def _main(self, run_forever: bool = False):
        loop = asyncio.get_running_loop()
        for t in self.tasks:
            t._task = loop.create_task(t._run())

        while 1:
            await asyncio.sleep(0.5 if not run_forever else 60)
            if len(self.tasks) == 0 and not run_forever:
                self.stop()

            if not self.is_running:
                break

    def callback(self, *tags: str):
        """
        Use this decorator to setup a callback handler
        for all `ScheduledTask`s matching the given `tags`.
        The handler gets called after the `ScheduledTask`s execution.

        NOTE: The first matching handler (in order you defined them) will be executed
        """

        def wrapper(func):
            async def handler(*args, **kwargs):
                if asyncio.iscoroutinefunction(func) or isinstance(func, Awaitable):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            self._callback_handlers.append(CallbackHandler(handler, *tags))
            return handler

        return wrapper

    async def _run_callback(self, task: tasks.ScheduledTask) -> None:
        for handler in self._callback_handlers:
            if task.matching_tags(*handler.tags):
                logger.debug(f"Running callback with tags: {handler.tags}")
                return await handler.run(task)

    @property
    def each(self) -> creation_helper.UnitSelector:
        """schedule a function or coroutine to run periodically"""
        return creation_helper.UnitSelector(creation_helper.FutureTask(self))

    def every(
        self, interval: int, limit: Optional[int] = None
    ) -> creation_helper.UnitsSelector:
        """schedule a function or coroutine to run periodically in a fixed interval"""
        if not isinstance(interval, int):
            raise TypeError(f"`interval` must be an `int`")
        if interval <= 1:
            raise ValueError("use `each` instead")
        if limit:
            if not isinstance(limit, int):
                raise TypeError(f"`limit` must be an `int`")
            if limit < 1:
                raise ValueError("`limit` cannot be smaller then 1")
        future_task = creation_helper.FutureTask(self)
        future_task.interval = interval
        return creation_helper.UnitsSelector(future_task)

    def at(self, at: datetime) -> creation_helper.TaskFinalizer:
        """schedule a function or coroutine to run once at a specific time"""
        if at < datetime.now():
            raise ValueError("cannot schedule a task to run in the past!")
        future_task = creation_helper.FutureTask(self)
        future_task.type = creation_helper.TaskType.one_time
        future_task.fixed_datetime = at
        return creation_helper.TaskFinalizer(future_task)

    def after(
        self,
        days: Optional[int] = 0,
        hours: Optional[int] = 0,
        minutes: Optional[int] = 0,
        seconds: Optional[int] = 0,
    ) -> creation_helper.TaskFinalizer:
        """schedule a function or coroutine to run once after a specific delay"""
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        at = datetime.now() + delta
        return self.at(at)

    def get_tasks(self, *tags: str) -> List[tasks.ScheduledTask]:
        """
        returns all `ScheduledTask`s matching the given `tags`.
        if no tags are defined, all tasks are returned.
        if no task matches, an empty list is returned.
        """
        if len(tags) == 0:
            return self.tasks
        return [task for task in self.tasks if task.matching_tags(*tags)]

    def cancel_task(self, task: tasks.ScheduledTask):
        """cancel a task immediately"""
        if task._task and not task._task.cancelled():
            task._task.cancel()
        self._remove_task(task)
        return tasks.CancelledTask(task)

    def _append_task(self, task: tasks.ScheduledTask) -> None:
        if not task in self.tasks:
            logger.debug(f"Created {task}")
            self.tasks.append(task)

    def _remove_task(self, task: tasks.ScheduledTask) -> None:
        if task in self.tasks:
            logger.debug(f"Cancelled {task}")
            self.tasks.remove(task)
