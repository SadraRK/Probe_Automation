from asyncio import sleep

from common.run_with_async import run_function_with_args


async def wait_for_working_device(is_working_function, timeout=600):
    x = 0
    time_step = 0.25
    while True:
        await sleep(time_step)
        x += time_step

        is_working = await run_function_with_args(is_working_function)
        if not is_working:
            break

        if x > timeout:
            break
