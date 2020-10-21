import inspect
from functools import update_wrapper


def pass_context(f=None, *, label=None):

    if f is not None:
        if not inspect.iscoroutinefunction(f):
            raise TypeError(f"Not coroutine function {f}")

        def wrapper(context, **kwargs):
            return f(context, **kwargs)

        wrapper.__bean_label = label
        return update_wrapper(wrapper, f)

    def inner(f):
        if not inspect.iscoroutinefunction(f):
            raise TypeError(f"Not coroutine function {f}")

        def wrapper(context, **kwargs):
            return f(context, **kwargs)

        wrapper.__bean_label = label
        return update_wrapper(wrapper, f)

    return inner
