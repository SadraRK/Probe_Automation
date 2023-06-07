import inspect


async def run_function_with_args(func, *args, **kwargs):
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


async def run_function(func, arguments):
    if inspect.iscoroutinefunction(func):
        if type(arguments) is list:
            return await func(*arguments)
        else:
            return await func(**arguments)
    else:
        if type(arguments) is list:
            return func(*arguments)
        else:
            return func(**arguments)
