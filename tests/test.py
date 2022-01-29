import asyncio
from datetime import datetime, timedelta
import logging
import unittest

from swisscore_scheduler import AsyncScheduler, TaskType, ScheduledTask

logger = logging.getLogger("swisscore_scheduler")
logger.setLevel(logging.CRITICAL)


def func(x=1):
    return 1 / x


async def coro(x=1):
    return 1 / x


class TestTags(unittest.TestCase):
    def test_tags(self):
        scheduler = AsyncScheduler()

        t = scheduler.each.second.run(func)
        self.assertTrue(t.matching_tags())
        self.assertFalse(t.matching_tags("A"))

        t.add_tags("A", "B")
        self.assertTrue(t.matching_tags())
        self.assertTrue(t.matching_tags("A"))
        self.assertTrue(t.matching_tags("A", "B"))


class TestPeriodic(unittest.TestCase):
    def test_secondly(self):
        scheduler = AsyncScheduler()
        t = scheduler.each.second.run(func, 1)
        self.assertEqual(t.type, TaskType.secondly)
        self.assertLessEqual(t.wait_time, 1)

    def test_minutely(self):
        scheduler = AsyncScheduler()
        t = scheduler.each.minute.at(30).run(func, 1)
        self.assertEqual(t.type, TaskType.minutely)
        self.assertLessEqual(t.wait_time, 60)
        self.assertEqual(t.next_run.second, 30)

    def test_hourly(self):
        scheduler = AsyncScheduler()
        t = scheduler.each.hour.at(45).run(func, 1)
        self.assertEqual(t.type, TaskType.hourly)
        self.assertLessEqual(t.wait_time, 60 * 60)
        self.assertEqual(t.next_run.minute, 45)

    def test_daily(self):
        scheduler = AsyncScheduler()
        t = scheduler.each.day.at(12, 30).run(func, 1)
        self.assertEqual(t.type, TaskType.daily)
        self.assertEqual(t.next_run.hour, 12)
        self.assertEqual(t.next_run.minute, 30)

    def test_weekly(self):
        scheduler = AsyncScheduler()
        t = scheduler.each.monday.at(6, 30).run(func, 1)
        self.assertEqual(t.type, TaskType.weekly)
        self.assertEqual(t.fixed_weekday, 0)
        self.assertEqual(t.next_run.hour, 6)
        self.assertEqual(t.next_run.minute, 30)

    def test_monthly(self):
        scheduler = AsyncScheduler()
        t = scheduler.each.month(13).at(6, 30).run(func, 1)
        self.assertEqual(t.type, TaskType.monthly)
        self.assertEqual(t.fixed_month_day, 13)
        self.assertIsNone(t.fixed_month)
        self.assertIsNone(t.fixed_weekday)
        self.assertEqual(t.next_run.day, 13)
        self.assertEqual(t.next_run.hour, 6)
        self.assertEqual(t.next_run.minute, 30)

    def test_yearly(self):
        scheduler = AsyncScheduler()
        t = scheduler.each.january(5).at(6, 30).run(func, 1)
        self.assertEqual(t.type, TaskType.yearly)
        self.assertEqual(t.fixed_month_day, 5)
        self.assertEqual(t.fixed_month, 1)
        self.assertIsNone(t.fixed_weekday)
        self.assertEqual(t.next_run.month, 1)
        self.assertEqual(t.next_run.day, 5)
        self.assertEqual(t.next_run.hour, 6)
        self.assertEqual(t.next_run.minute, 30)


class TestPeriodicInterval(unittest.TestCase):
    def test_secondly(self):
        scheduler = AsyncScheduler()
        t = scheduler.every(2).seconds.run(func, 1)
        self.assertEqual(t.type, TaskType.secondly)
        self.assertLessEqual(t.wait_time, 2)

    def test_minutely(self):
        scheduler = AsyncScheduler()
        t = scheduler.every(2).minutes.at(30).run(func, 1)
        self.assertEqual(t.type, TaskType.minutely)
        self.assertLessEqual(t.wait_time, 120)
        self.assertEqual(t.next_run.second, 30)

    def test_hourly(self):
        scheduler = AsyncScheduler()
        t = scheduler.every(2).hours.at(45).run(func, 1)
        self.assertEqual(t.type, TaskType.hourly)
        self.assertLessEqual(t.wait_time, 2 * 60 * 60)
        self.assertEqual(t.next_run.minute, 45)

    def test_daily(self):
        scheduler = AsyncScheduler()
        t = scheduler.every(2).days.at(12, 30).run(func, 1)
        self.assertEqual(t.type, TaskType.daily)
        self.assertEqual(t.next_run.hour, 12)
        self.assertEqual(t.next_run.minute, 30)


class TestOnetime(unittest.TestCase):
    def test_after(self):
        scheduler = AsyncScheduler()
        t = scheduler.after(seconds=30).run(func, 1)
        self.assertEqual(t.type, TaskType.one_time)
        self.assertLessEqual(t.wait_time, 30)

    def test_after_mixed(self):
        scheduler = AsyncScheduler()
        t = scheduler.after(days=1, hours=1, minutes=1, seconds=30).run(func, 1)
        self.assertEqual(t.type, TaskType.one_time)
        self.assertLessEqual(t.wait_time, 90 + 60 * 60 + 24 * 60 * 60)

    def test_at(self):
        scheduler = AsyncScheduler()
        dt = datetime.now() + timedelta(seconds=30)
        t = scheduler.at(dt).run(func, 1)
        self.assertEqual(t.type, TaskType.one_time)
        self.assertEqual(t.fixed_datetime, dt)
        self.assertLessEqual(t.wait_time, 30)


class TestSchedulerConcurrently(unittest.IsolatedAsyncioTestCase):
    async def test_scheduler(self):
        scheduler = AsyncScheduler()

        @scheduler.callback("working")
        async def callback1(task: ScheduledTask):
            self.assertTrue(task.last_run.succeed)
            self.assertEqual(task.last_run.result, 1)

            if task.previous_runs == 1:
                ct = task.cancel()
                self.assertEqual(ct.last_run, task.last_run)

        @scheduler.callback("failing")
        async def callback2(task: ScheduledTask):
            self.assertFalse(task.last_run.succeed)
            self.assertIsInstance(task.last_run.result, ZeroDivisionError)

            if task.previous_runs == 1:
                ct = task.cancel()
                self.assertEqual(ct.last_run, task.last_run)

        scheduler.each.second.run(coro, 1).add_tags("working")
        scheduler.each.second.run(coro, 0).add_tags("failing")

        scheduler.every(2).seconds.run(coro, 1).add_tags("working")
        scheduler.every(2).seconds.run(coro, 0).add_tags("failing")

        scheduler.after(seconds=1).run(coro, 1).add_tags("working")
        scheduler.after(seconds=1).run(coro, 0).add_tags("failing")

        scheduler.at(datetime.now() + timedelta(seconds=1)).run(coro, 1).add_tags(
            "working"
        )
        scheduler.at(datetime.now() + timedelta(seconds=1)).run(coro, 0).add_tags(
            "failing"
        )

        scheduler.start_concurrently()
        while len(scheduler.tasks) > 0:
            await asyncio.sleep(0.1)
        scheduler.stop()


class TestScheduler(unittest.TestCase):
    def test_scheduler(self):
        scheduler = AsyncScheduler()

        @scheduler.callback("working")
        def callback1(task: ScheduledTask):
            self.assertTrue(task.last_run.succeed)
            self.assertEqual(task.last_run.result, 1)

            if task.previous_runs == 1:
                ct = task.cancel()
                self.assertEqual(ct.last_run, task.last_run)

        @scheduler.callback("failing")
        def callback2(task: ScheduledTask):
            self.assertFalse(task.last_run.succeed)
            self.assertIsInstance(task.last_run.result, ZeroDivisionError)

            if task.previous_runs == 1:
                ct = task.cancel()
                self.assertEqual(ct.last_run, task.last_run)

        scheduler.each.second.run(func, 1).add_tags("working")
        scheduler.each.second.run(func, 0).add_tags("failing")

        scheduler.every(2).seconds.run(func, 1).add_tags("working")
        scheduler.every(2).seconds.run(func, 0).add_tags("failing")

        scheduler.after(seconds=1).run(func, 1).add_tags("working")
        scheduler.after(seconds=1).run(func, 0).add_tags("failing")

        scheduler.at(datetime.now() + timedelta(seconds=1)).run(func, 1).add_tags(
            "working"
        )
        scheduler.at(datetime.now() + timedelta(seconds=1)).run(func, 0).add_tags(
            "failing"
        )

        scheduler.start()


if __name__ == "__main__":
    unittest.main()
