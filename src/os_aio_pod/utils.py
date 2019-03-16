import collections
import inspect
import re
import types
from importlib import import_module
from logging import _nameToLevel
from pkgutil import iter_modules


def model_from_string(base_class, instance=False, package=None):
    assert inspect.isclass(base_class)

    class Model(str):
        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v):
            if isinstance(v, str):
                obj = load_obj(v, package=package) if instance else load_class(
                    v, base_class, package=package)

                if obj is None:
                    raise ValueError(f'Can not load {v}')
                
                v = obj
            if instance:
                if isinstance(v, base_class):
                    return v
            else:
                if inspect.isclass(v) and issubclass(v, base_class):
                    return v
            raise ValueError(f'{repr(base_class)} expected')
    return Model


def walk_modules(module_path, skip_fail=True):

    mod = None
    try:
        mod = import_module(module_path)
        yield mod
    except Exception as e:
        if not skip_fail:
            raise e

    if mod and hasattr(mod, '__path__'):
        for _, subpath, _ in iter_modules(mod.__path__):
            fullpath = '.'.join((module_path, subpath))
            for m in walk_modules(fullpath, skip_fail):
                yield m


def expected_cls(module, cls, base_class, include_base_class=False):
    if inspect.isclass(cls) and \
            issubclass(cls, base_class) and \
            cls.__module__ == module.__name__ and \
            (include_base_class or (all([cls != base for base in base_class])
                                    if isinstance(base_class, tuple)
                                    else cls != base_class)):
        return True
    return False


def load_obj(obj_path, package=None):
    module_path, obj_name = obj_path.rsplit('.', 1)
    module = import_module(module_path, package=package)
    return getattr(module, obj_name, None)


def load_class(class_path, base_class, include_base_class=False, package=None):
    module_path, class_name = class_path.rsplit('.', 1)
    module = import_module(module_path, package=package)
    cls = getattr(module, class_name)
    if expected_cls(module, cls, base_class, include_base_class):
        return cls
    return None


def load_module_from_pyfile(filename):
    module = types.ModuleType('config')
    module.__file__ = filename
    try:
        with open(filename) as config_file:
            exec(compile(config_file.read(), filename, 'exec'),
                 module.__dict__)
    except IOError as e:
        e.strerror = 'Unable to load configuration file (%s)' % e.strerror
        raise
    return module
