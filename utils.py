from contextlib import asynccontextmanager
from time import monotonic
import contextvars

analyze_time = contextvars.ContextVar('atime')

@asynccontextmanager
async def measure_time_manager(func):
    start = monotonic()
    try:
        yield func
    finally:
        end = monotonic()
        analyze_time.set(end - start)
