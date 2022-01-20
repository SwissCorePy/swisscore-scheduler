import logging as __logging

logger = __logging.getLogger(__name__)
__formatter = __logging.Formatter(
    "%(levelname)s: (%(asctime)s.%(msecs)03d) - %(message)s", 
    "%m/%d/%Y %H:%M:%S"
)
__stream_handler = __logging.StreamHandler()
__stream_handler.setFormatter(__formatter)
logger.addHandler(__stream_handler)

from .scheduler import AsyncScheduler
from .tasks import ScheduledTask, CancelledTask, TaskResult
from .creation_helper import TaskType
