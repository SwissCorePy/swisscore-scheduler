
# import the scheduler class
from swisscore_scheduler import AsyncScheduler

# creating the scheduler instance
scheduler = AsyncScheduler()

# creating a function or async function to schedule
async def func(msg):
    print(f"Running {msg}!")

# Run `func` each second with the msg argument beeing "each second"
# This task runs forever until the scheduler or the task are stopped manually
scheduler.each.second.run(func, "each second")

# Run `func` every 3 seconds with the msg argument beeing "every 3 seconds"
# This task runs forever until the scheduler or the task are stopped manually
scheduler.every(3).seconds.run(func, "every 3 seconds")
 
# Run `func` once after 5 seconds with the msg argument beeing "once after 5 secondsd"
# This task runs only once
scheduler.after(seconds=5).run(func, "once after 5 seconds")

# starting the scheduler
scheduler.start()
