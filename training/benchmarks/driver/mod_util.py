# Copyright © 2022 BAAI. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License")

from pkgutil import iter_modules
import importlib
import inspect
import os, sys


def set_extern_module_ns(module):
    try:
        mod = sys.modules.get('extern') or module
        if mod is not module:
            raise 'Naming conflict occurs. `extern` is found to be a different module.'
        # rebind
        sys.modules['extern'] = mod
        if module.__name__ != 'extern':
            del sys.modules[module.__name__]
    except Exception as ex:
        raise ex


def install_extern_modules(path: str, mod_dict: dict = None):
    """ Imports externel modules and installs them all under the `extern` package.
    This action is supposed to be invoked only once for setting up envrionment.

    Args:
        path: the path to the base directory of the external modules.
        mod_dict: add modules to this dictionary.
    """
    if not os.path.isdir(path):
        raise 'Directory {path} does not exist!'

    fullpath = os.path.abspath(path)
    basename = os.path.basename(fullpath)
    sys.path.append(os.path.dirname(fullpath))

    try:
        base_module = importlib.import_module(basename)
    except Exception as ex:
        raise ex
    finally:
        sys.path.pop(-1)

    set_extern_module_ns(base_module)

    for _, modname, ispkg in iter_modules([fullpath]):
        try:
            module = importlib.import_module(f".{modname}", package='extern')
            if mod_dict is not None:
                mod_dict[modname] = module
        except Exception as ex:
            raise ex


def replace_submodules(package, mod_dict: dict = None):
    assert inspect.ismodule(package)
    for name, _ in inspect.getmembers(package, inspect.ismodule):
        mod = mod_dict.get(name)
        if mod:
            package.__dict__[name] = mod


def remap_modules(ns: dict, mod_dict: dict = None):
    if not mod_dict:
        return
    for name, mod in mod_dict.items():
        value = ns.get(name)
        if value and inspect.ismodule(value):
            replaced_item = replace_function(value, mod)
            print(f"Remapped {value}.{replaced_item} to {mod}.{replaced_item}")


def find_derived_classes(base: type, module):
    for cls_name, cls in inspect.getmembers(
            module, lambda x: inspect.isclass(x) and issubclass(x, base)):
        yield cls


def replace_function(src_module, new_module):
    replaced_item = []
    items = [e for e in dir(src_module) if not e.startswith('__')]
    for item in items:
        if hasattr(new_module, item):
            attr = getattr(new_module, item)
            if isinstance(attr, type):
                methods_src = [e for e in dir(attr) if not e.startswith('__')]
                for method in methods_src:
                    if hasattr(attr, method):
                        cls_method = getattr(attr, method)
                        setattr(attr, method, cls_method)
            setattr(src_module, item, attr)
            replaced_item.append(item)
    return replaced_item
