"""Claim 7: the portfolio backtest applies proportional transaction costs correctly.

I do not run the whole frozen project here, because its source data are not in the
audit snapshot and the optimizer needs CVXPY. Instead I take the frozen function
`execute_rebalance` straight from the frozen source file, compile only that function,
and test it against answers I can work out by hand. I also read the frozen code
statically to confirm that every backtest passes the cost rate to that function.
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np

TARGET = Path(__file__).resolve().parents[1] / "targets" / "quant-ai-market-lab-v1.0.0" / "src"


def load_function(path: Path, name: str):
    """Compile one function from a Python file without importing the rest of the file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            module = ast.Module(body=[node], type_ignores=[])
            namespace = {"np": np}
            exec(compile(module, str(path), "exec"), namespace)
            return namespace[name]
    raise LookupError(f"{name} not found in {path}")


def calls_with_keyword(path: Path, function_name: str, keyword: str) -> list[int]:
    """Line numbers of calls to function_name that pass `keyword=...`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name == function_name and any(kw.arg == keyword for kw in node.keywords):
                lines.append(node.lineno)
    return lines


def module_level_list(path: Path, name: str):
    """Value of a module-level or function-level assignment `name = [...]` or `name = {...}`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node.value
    return None


def loop_values(path: Path, variable: str):
    """Literal list used in `for <variable> in [..]:`, if any."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == variable \
                and isinstance(node.iter, ast.List):
            return [elt.value for elt in node.iter.elts]
    return None
