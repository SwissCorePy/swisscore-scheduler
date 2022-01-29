# import the scheduler class
from swisscore_scheduler import AsyncScheduler

# creating the scheduler instance
scheduler = AsyncScheduler()


# creating a function or async function to schedule
async def func(msg):
    print(f"Running {msg}!")


### schedule the same function in three different ways.

# run `func` each second with the msg argument beeing "each second"
scheduler.each.second.run(func, "each second")

# run `func` every 3 seconds with the msg argument beeing "every 3 seconds"
scheduler.every(3).seconds.run(func, "every 3 seconds")

# run `func` once after 5 seconds with the msg argument beeing "once after 5 secondsd"
scheduler.after(seconds=5).run(func, "once after 5 seconds")


# starting the scheduler
scheduler.start()
