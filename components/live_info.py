import inspect
import traceback
from typing import Dict, Callable

from server.requests.add_action import add_action
from server.requests.one_time_request import action_str_to_func
from server.requests.subscription import add_to_subscription_loop

LIVE_INFO_UUID = "live_info"
LIVE_INFO_DB: Dict[str, object] = {}
LIVE_INFO_REPORT: Dict[str, Callable] = {}


def add_live_info_function(function: Callable):
    if inspect.isfunction(function) or inspect.ismethod(function):
        LIVE_INFO_DB[function.__name__] = function
    return function


def add_live_info_class(object_name, class_object):
    LIVE_INFO_DB[object_name] = class_object


@add_action
def add_to_live_info(function_name):
    if function_name in LIVE_INFO_REPORT:
        return

    action_object = action_str_to_func(function_name, LIVE_INFO_DB)

    if inspect.ismethod(action_object) or inspect.isfunction(action_object):
        LIVE_INFO_REPORT[function_name] = action_object


@add_action
def remove_from_live_info(function_name):
    LIVE_INFO_REPORT.pop(function_name, None)


def func_live_info():
    live_info_result = {"uuid": LIVE_INFO_UUID}

    for i in LIVE_INFO_REPORT.keys():
        try:
            live_info_result[i] = LIVE_INFO_REPORT[i]()
        except Exception as e:
            print(f"Live info problem in fetching data from '{i}': {e} : {traceback.format_tb(e.__traceback__)}")
    return live_info_result


@add_action
def get_live_info(subscription: bool):
    if subscription:
        add_to_subscription_loop(func_live_info, 0.1)
    else:
        return func_live_info()
