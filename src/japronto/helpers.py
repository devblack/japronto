from sys import version_info
from asyncio import all_tasks, Task
from types import CodeType
from inspect import CO_COROUTINE

PY_37 = version_info > (3, 7)
PY_38 = version_info > (3, 8)

if PY_37:
    all_tasks = all_tasks
else:
    def all_tasks(loop):
        return set(filter(lambda t: not t.done(), Task.all_tasks(loop)))

if PY_38:
    def dismiss_coroutine(code):
        return code.replace(co_flags=code.co_flags & ~CO_COROUTINE)
else:
    def dismiss_coroutine(code):
        return CodeType(
            code.co_argcount, code.co_kwonlyargcount, code.co_nlocals, code.co_stacksize,
            code.co_flags & ~CO_COROUTINE,
            code.co_code, code.co_consts, code.co_names, code.co_varnames, code.co_filename,
            code.co_name, code.co_firstlineno, code.co_lnotab, code.co_freevars,
            code.co_cellvars)
