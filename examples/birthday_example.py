import logging
from swisscore_scheduler import AsyncScheduler, ScheduledTask

scheduler = AsyncScheduler()

logger = logging.getLogger("swisscore_scheduler")
logger.setLevel(logging.DEBUG)


@scheduler.callback("birthday")
async def callback_handler(task: ScheduledTask):
    if task.last_run.succeed:
        print(f"{task.last_run.result} was congratulated!")


async def birthday_congratulation(name: str):
    print(f"Happy Birhday {name}!")
    return name


scheduler.each.january(5).at(6).run(birthday_congratulation, "Sarah").add_tags(
    "birthday", "sarah"
)
scheduler.each.july(8).at(6).run(birthday_congratulation, "Patrick").add_tags(
    "birthday", "patrick"
)

scheduler.start()
