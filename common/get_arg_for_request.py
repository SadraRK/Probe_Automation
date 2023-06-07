import inspect
from typing import Callable


def get_arg_for_request(function: Callable, obj_args):
    specs = inspect.getfullargspec(function)
    all_args = specs.args + specs.kwonlyargs
    final_args = {}
    for i in all_args:
        if i in obj_args:
            final_args[i] = obj_args[i]
    return final_args
