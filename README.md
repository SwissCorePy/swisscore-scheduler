

# <p align="left">swisscore-scheduler
<a href="https://pypi.org/project/swisscore-scheduler"><img src="https://img.shields.io/pypi/v/swisscore-scheduler.svg"></a>
<a href="https://pypi.org/project/swisscore-scheduler"><img src="https://img.shields.io/pypi/pyversions/swisscore-scheduler.svg"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
 
 ***NOTE: This documentation is not complete yet!***
 
 An easy to use scheduler that works with both regular and coroutine functions.<br />
 It can running concurrently.<br />
 ***It requires python 3.10 or higher, because it was written and testet in this version. But lower versions may be supported in the future. <br />
 The syntax is inspired by the `schedule` module.*** 

---
 
## <p align="left">Installation

### install latest release <i>(recommended)</i>
 ***NOTE: If you are on macOS or Linux you may have to use `pip3`.***
```
pip install swisscore-scheduler
```
### install from source
 ***NOTE: If you are on macOS or Linux you may have to use `pip3`.***
```
pip install git+https://github.com/SwissCorePy/swisscore-scheduler
```

---
 
## <p align="left">Quick Start

### Setup the scheduler
 First we need to import and setup our scheduler.
```python
# import the scheduler class
from swisscore_scheduler import AsyncScheduler

# creating the scheduler instance
scheduler = AsyncScheduler()
```
 Lets add some test function to have something to schedule. <br />
 In this example we create an async function that prints "I am running {msg}". <br />
 <br />
 ***NOTE: It does not matter if you use reqular functions or async functions. But it's recommended to use async functions because the scheduler works asynchronously as well.***
```python
# creating a function or async function to schedule
async def func(msg):
    print(f"Running {msg}!")
```

### Schedule the function
 Now we need to tell the scheduler what to do with this function. <br />
 In this case, we schedule the same function in three different ways.
```python
# run `func` each second with the msg argument beeing "each second"
scheduler.each.second.run(func, "each second")

# run `func` every 3 seconds with the msg argument beeing "every 3 seconds"
scheduler.every(3).seconds.run(func, "every 3 seconds")
 
# run `func` once after 5 seconds with the msg argument beeing "once after 5 secondsd"
scheduler.after(seconds=5).run(func, "once after 5 seconds")
```

### Starting the scheduler
 In a simple use case you just call `scheduler.start()` <br />
 The scheduler will run until no pending tasks are left or CTRL+C is pressed. <br />
 
```python
# starting the scheduler
scheduler.start()
```
 
 The scheduler creates an async event loop and invokes all scheduled tasks in that loop. <br />
 Since we scheduled tasks to run forever, the scheduler will always have pending tasks and will never stop to run. <br />
 This method may be suitable for many use cases. 
 But it has the downside of blocking your code from running further, because the main loop of the program is running inside the `AsyncScheduler` class. <br />
 
### Starting the scheduler concurrently
 
 If you want to run other code along the scheduler you should start the sheluler concurrently.
```python
# starting the scheduler concurrently
async def main():
    try:
        scheduler.start_concurrently()
 
        # Now you can run other async code concurrently
        asyncio.sleep(60)
        
        # But if nothing more is to do (in this case after 60 seconds) the scheduler and the program are stoped
        print("Nothing more to do, stopping scheduler")
    
    except KeyboardInterrupt:
        pass
    
    finally:
        scheduler.stop()

asyncio.run(main)
```
 
---
 
## <p align="left">Tags and callbacks
### tags
 You can add and remove tags to scheduled tasks.
```python
# first way
task1 = scheduler.each.second.run(func, *args, **kwargs)
task1.add_tags("some", "tags")

# second way
task2 = scheduler.each.second.run(func, *args, **kwargs).add_tags("some", "other", "tags")
task2.remove_tags("other")

# now you can get the tasks by the tags
tasks = scheduler.get_tasks("some", "tags")

```
 
### callbacks
Tags are also very useful if you want to use callback functions. <br />
There is a handy decorator to setup callback functions

```python
# setup a callback function
# this callback function will run after each scheduled tasks execution where the tags are matching
# the ScheduledTask instance is passed to your function
@scheduler.callback("some", "tags")
async def callback_handler(task: ScheduledTask):
    print (f"task last result: {task.last_run.result}")
    if task.previous_runs == 5:
        task.cancel()

```
 
---

## <p align="left">Task types
 The scheduler has different methods and properties to schedule different types of tasks. <br />
 In the table below you can see how they are created. <br />
 The `.run(...)` function at the end applies the task to the scheduler and returns a `ScheduledTask` instance. <br />
 
| keyword | ussage                                                                      | description                      |
|---------|-----------------------------------------------------------------------------|----------------------------------|
| each    | scheduler.each.second.run(func, *args, **kwargs)                            | runs every second                |
| every   | scheduler.every(2).seconds.run(func, *args, **kwargs)                       | runs every 2 seconds             |
| after   | scheduler.after(seconds=5).run(func, *args, **kwargs)                       | runs once after 5 seconds        |
| at      | scheduler.at(datetime(y, m, d, H, M, S)).run(func, *args, **kwargs)         | runs once at a specific datetime |

<details>
  <summary>More examples using <i>each</i></summary>
 
```python
#### examples of using `each`
 
# Run each minute at HH:MM:30
scheduler.each.minute.at(30).run(func, *args, **kwargs)

# Run each hour HH:10:00
scheduler.each.hour.at(10, 0).run(func, *args, **kwargs)

# Run each day at 12:25:00
scheduler.each.day.at(12, 25).run(func, *args, **kwargs)

# Run each month on the 3rd day at 13:00:00
scheduler.each.month(3).at(13).run(func, *args, **kwargs)

# Run each monday at 18:30:00
# (All other weekdays are also available) 
scheduler.each.monday.at(18, 30).run(func, *args, **kwargs)

# Run each year on December 24 at 20:45:00
# (All other months are also available) 
scheduler.each.december(24).at(20, 45).run(func, *args, **kwargs)

#### You can skip the `at` function which defaults hour, minute and second to zero

# Note: The `second` property does not have an `at` function
# since the scheduler works with 1 second accuracy
scheduler.each.second.run(func, *args, **kwargs) 
 
# Run each minute at HH:MM:00 
# (second is zero by default)
scheduler.each.minute.run(func, *args, **kwargs)

# Run each hour HH:00:00 
# (minute and second are zero by default)
scheduler.each.hour.run(func, *args, **kwargs)

# Run each day at 00:00:00 
# (hour, minute and second are zero by default)
scheduler.each.day.run(func, *args, **kwargs)

# Run each month on the 1st day at 00:00:00 
# (hour minute and second are zero by default)
# (the month day defaults to one)
scheduler.each.month().run(func, *args, **kwargs)

# Run each friday at 00:00:00
# (hour minute and second are zero by default)
scheduler.each.friday.run(func, *args, **kwargs)

# Run each year on January 1st at 00:00:00
# (hour minute and second are zero by default)
# (the month day defaults to one)
scheduler.each.january().run(func, *args, **kwargs)
```
</details>

<details>
  <summary>More examples using <i>every</i></summary>
 
```python
#### examples of using `every`
 
# Run every 2 minutes at HH:MM:30
scheduler.every(2).minutes.at(30).run(func, *args, **kwargs)

# Run every 2 hour HH:10:00
scheduler.every(2).hours.at(10, 0).run(func, *args, **kwargs)

# Run every 2 days at 12:25:00
scheduler.every(2).days.at(12, 25).run(func, *args, **kwargs)

#### You can skip the `at` function which defaults hour, minute and second to zero

# Note: The `seconds` property does not have an `at` function
# since the scheduler works with 1 second accuracy
scheduler.every(10).seconds.run(func, *args, **kwargs) 
 
# Run every 5 minutes at HH:MM:00 
# (second is zero by default)
scheduler.every(5).minutes.run(func, *args, **kwargs)

# Run every 2 hours HH:00:00 
# (minute and second are zero by default)
scheduler.every(2).hours.run(func, *args, **kwargs)

# Run every 3 days at 00:00:00 
# (hour, minute and second are zero by default)
scheduler.every(3).days.run(func, *args, **kwargs)
```
</details>

<details>
  <summary>More examples using <i>after</i></summary>
 
```python
#### examples of using `after`
 
# Run after 10 seconds
scheduler.after(seconds=10).run(func, *args, **kwargs)

# Run after 25 minutes
scheduler.after(minutes=25).run(func, *args, **kwargs)

# Run after 1 day, 2 hours and 30 minutes
scheduler.after(days=1, hours=2, minutes=30).run(func, *args, **kwargs)
```
</details>

<details>
  <summary>More examples using <i>at</i></summary>
 
```python
#### examples of using `at`

# `at` works with the datetime module
from datetime import datetime
 
# Run at 2023-01-05 12:00:00 
scheduler.at(datetime(2023, 1, 5, 12)).run(func, *args, **kwargs)

# Attention! the date must be in the future! Else a ValueError is raised
# Raises Error: Run at 1992-07-08 12:00:00 
scheduler.at(datetime(1992, 7, 8, 12)).run(func, *args, **kwargs)
```
</details>

