import asyncio
from asyncio import sleep

from common.run_with_async import run_function_with_args

ASYNCIO_LOOP = asyncio.get_event_loop()
ASYNCIO_COROUTINES = []
ASYNCIO_LOOP_STARTED = False


async def warp_while_time_step(function, time_step, *args, **kwargs):
    while True:
        kwargs["time_step"] = time_step
        await run_function_with_args(function, *args, **kwargs)
        await sleep(time_step)


def add_function_to_asyncio_loop(coroutine, run_until_complete=False, run_forever=False, time_step: float = None, *args,
                                 **kwargs):
    if run_until_complete:
        ASYNCIO_LOOP.run_until_complete(coroutine)

    if run_forever:
        ASYNCIO_COROUTINES.append(coroutine)

    if time_step is not None and time_step > 0.01 and not ASYNCIO_LOOP_STARTED:
        kwargs["run_until_complete"] = run_until_complete
        kwargs["run_forever"] = run_forever
        kwargs["time_step"] = time_step
        ASYNCIO_COROUTINES.append(warp_while_time_step(coroutine, time_step, *args, **kwargs))


def asyncio_run_forever():
    global ASYNCIO_LOOP_STARTED
    ASYNCIO_LOOP.run_until_complete(asyncio.gather(*ASYNCIO_COROUTINES))
    ASYNCIO_LOOP.run_forever()
    ASYNCIO_LOOP_STARTED = True
