"""A rule-based checker for quantitative research code.

I wrote this checker as the baseline for ResearchAudit. It reads Python files
as syntax trees and lists places that deserve a human look, for example a split
that shuffles time-ordered data or a cost parameter that a function never uses.

It does not decide whether a project is correct. Each finding is a candidate
issue with its file, line and reason. Some candidates are legitimate by design
(for example a negative shift that builds a forecasting target), so every
finding still needs a person, or later an agent, to judge it.
"""

from __future__ import annotations

import argparse
import ast
import json
import hashlib
import io
import os
import tokenize
from datetime import datetime, timezone
import re
import symtable
from dataclasses import asdict, dataclass
from pathlib import Path

SEEDED_CONSTRUCTORS = {
    "RandomForestRegressor", "RandomForestClassifier", "KMeans", "GaussianMixture",
    "GaussianHMM", "MiniBatchKMeans", "ShuffleSplit", "KFold", "StratifiedKFold",
}
GLOBAL_RNG_FUNCTIONS = {
    "rand", "randn", "random", "normal", "uniform", "choice", "permutation",
    "shuffle", "randint", "standard_normal", "sample",
}
FIT_CLASS_PATTERN = re.compile(r"(Scaler|PCA|Imputer|Normalizer|PowerTransformer)$")
SENSITIVE_PARAMETER_PATTERN = re.compile(r"(cost|fee|slippage|lag|delay|gap|seed|random_state|horizon)", re.I)
ABSOLUTE_PATH_PATTERN = re.compile(r"^(/(Users|home|mnt|var|tmp|opt)/|[A-Za-z]:\\)")

RULES = {
    "RC00": ("high", "File could not be parsed"),
    "RC09": ("info", "No eligible Python source files"),
    "RC10": ("medium", "Source could not be read"),
    "RC01": ("review", "Future-aligned shift/difference or centered rolling window"),
    "RC02": ("high", "Shuffled split of possibly time-ordered data"),
    "RC03": ("review", "Fitted transformer: check it is fitted on training data only"),
    "RC04": ("medium", "Randomness without a fixed seed"),
    "RC05": ("medium", "Cost, lag or seed parameter that the function never uses"),
    "RC06": ("low", "Hard-coded absolute path"),
    "RC07": ("medium", "Silent exception handling"),
    "RC08": ("info", "No matching Python test files found"),
}


@dataclass
class Finding:
    rule_id: str
    severity: str
    title: str
    file: str
    line: int
    code: str
    reason: str


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _keyword(node: ast.Call, name: str):
    for kw in node.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _is_negative_number(node) -> bool:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = getattr(node.operand, "value", None)
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
    value = getattr(node, "value", None)
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value < 0


def check_source(source: str, filename: str = "<string>") -> list[Finding]:
    """Apply rules RC01 to RC07 to one Python source string."""
    lines = source.splitlines()

    def add(rule, node, reason):
        severity, title = RULES[rule]
        line = getattr(node, "lineno", 1)
        code = lines[line - 1].strip() if 0 < line <= len(lines) else ""
        findings.append(Finding(rule, severity, title, filename, line, code, reason))

    findings: list[Finding] = []
    try:
        tree = ast.parse(source)
        compile(tree, filename, "exec")  # Validate scope syntax without executing it.
    except SyntaxError as error:
        findings.append(Finding("RC00", "high", "File could not be parsed", filename, error.lineno or 1, "",
                                f"Syntax error: {error.msg}"))
        return findings

    # A separately seeded Generator never seeds NumPy's global RNG.
    # I only recognize a literal, preceding top-level global seed call.
    numpy_aliases, random_aliases, direct_random = set(), set(), {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if alias.name == "numpy": numpy_aliases.add(alias.asname or "numpy")
                if alias.name == "numpy.random":
                    if alias.asname: random_aliases.add(alias.asname)
                    else: numpy_aliases.add("numpy")
        elif isinstance(stmt, ast.ImportFrom):
            for alias in stmt.names:
                if stmt.module == "numpy" and alias.name == "random": random_aliases.add(alias.asname or alias.name)
                if stmt.module == "numpy.random": direct_random[alias.asname or alias.name] = alias.name

    def global_rng_name(call):
        fn = call.func
        if isinstance(fn, ast.Name): return direct_random.get(fn.id)
        if not isinstance(fn, ast.Attribute): return None
        owner = fn.value
        if isinstance(owner, ast.Name) and owner.id in random_aliases: return fn.attr
        if (isinstance(owner, ast.Attribute) and owner.attr == "random"
                and isinstance(owner.value, ast.Name) and owner.value.id in numpy_aliases): return fn.attr
        return None

    global_calls = sorted((node for node in ast.walk(tree) if isinstance(node, ast.Call)
                           and global_rng_name(node)), key=lambda node: (node.lineno, node.col_offset))
    active_seed = False
    # False means I cannot establish a fixed seed syntactically, not that none exists.
    seeded_global_calls = set()
    top_level_calls = {id(stmt.value) for stmt in tree.body
                       if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)}
    for call in global_calls:
        if global_rng_name(call) == "seed":
            if id(call) in top_level_calls:
                arg = call.args[0] if call.args else _keyword(call, "seed")
                active_seed = (isinstance(arg, ast.Constant) and isinstance(arg.value, int)
                               and not isinstance(arg.value, bool) and 0 <= arg.value <= 2**32-1)
            else:
                active_seed = False
            continue
        # A top-level statement's expression is evaluated now. I do not infer
        # when function/class/comprehension bodies execute from their line numbers.
        owning_statement = next((stmt for stmt in tree.body
                                 if stmt.lineno <= call.lineno <= getattr(stmt, "end_lineno", stmt.lineno)), None)
        if active_seed and not isinstance(owning_statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            seeded_global_calls.add(id(call))

    try:
        symbols = symtable.symtable(source, filename, "exec")
    except SyntaxError as error:
        return [Finding("RC00", "high", "File could not be parsed", filename,
                        error.lineno or 1, "", f"Scope syntax error: {error.msg}")]
    function_scopes = {}
    def collect_scopes(scope):
        for child in scope.get_children():
            if child.get_type() == "function":
                function_scopes[(child.get_name(), child.get_lineno())] = child
            collect_scopes(child)
    collect_scopes(symbols)

    def parameter_referenced(scope, name):
        try:
            if scope.lookup(name).is_referenced(): return True
        except KeyError:
            return False
        def closure_reference(child):
            try:
                symbol = child.lookup(name)
            except KeyError:
                return False
            if not symbol.is_free(): return False
            return symbol.is_referenced() or any(closure_reference(grandchild) for grandchild in child.get_children())
        return any(closure_reference(child) for child in scope.get_children())

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            # RC01: shift with a negative period pulls future values into the current row.
            if name in {"shift", "diff", "pct_change"}:
                period = node.args[0] if node.args else _keyword(node, "periods")
                if period is not None and _is_negative_number(period):
                    add("RC01", node, f"{name} with a negative literal period uses later observations. Targets may legitimately do this; review whether the result feeds a feature.")
            if name == "rolling":
                center = _keyword(node, "center")
                if isinstance(center, ast.Constant) and center.value is True:
                    add("RC01", node, "A centered rolling window can include future observations. Review its use as a forecasting feature; no receiver or dataflow validation is performed.")
            # RC02: shuffling splits.
            if name == "train_test_split":
                shuffle = _keyword(node, "shuffle")
                if shuffle is None:
                    add("RC02", node, "train_test_split shuffles by default. Pass shuffle=False for time-ordered data.")
                elif isinstance(shuffle, ast.Constant) and shuffle.value is True:
                    add("RC02", node, "shuffle=True mixes future rows into the training set.")
            elif name in {"KFold", "StratifiedKFold", "ShuffleSplit"}:
                shuffle = _keyword(node, "shuffle")
                if name == "ShuffleSplit" or (isinstance(shuffle, ast.Constant) and shuffle.value is True):
                    add("RC02", node, f"{name} draws random folds, which ignores time order.")
            # RC03: fitted transformers.
            if name == "fit_transform":
                add("RC03", node, "Check that this transformer is fitted on training dates only.")
            elif FIT_CLASS_PATTERN.search(name):
                add("RC03", node, f"{name} learns parameters from data. Check which dates it is fitted on.")
            # RC04: unseeded randomness.
            seed = _keyword(node, "random_state")
            shuffled_fold = name not in {"KFold", "StratifiedKFold"} or (
                isinstance(_keyword(node, "shuffle"), ast.Constant) and _keyword(node, "shuffle").value is True)
            if name in SEEDED_CONSTRUCTORS and shuffled_fold and (
                    seed is None or isinstance(seed, ast.Constant) and seed.value is None):
                add("RC04", node, f"{name} has no explicit non-None random_state; review its reproducibility.")
            rng_seed = node.args[0] if node.args else _keyword(node, "seed")
            if name == "default_rng" and (rng_seed is None or isinstance(rng_seed, ast.Constant) and rng_seed.value is None):
                add("RC04", node, "default_rng has no explicit non-None seed.")
            if global_rng_name(node) in GLOBAL_RNG_FUNCTIONS and id(node) not in seeded_global_calls:
                add("RC04", node, "This NumPy global-RNG call has no recognized preceding fixed top-level seed. Review its seed path.")
        # RC05: parameters that are accepted but never used.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scope = function_scopes.get((node.name, node.lineno))
            args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            args += [arg for arg in (node.args.vararg, node.args.kwarg) if arg is not None]
            for arg in args:
                if (scope is not None and SENSITIVE_PARAMETER_PATTERN.search(arg.arg)
                        and not parameter_referenced(scope, arg.arg)):
                    add("RC05", node, f"Parameter '{arg.arg}' of {node.name}() has no static reference in its scope or an unshadowed closure.")
        # RC06: absolute paths.
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and ABSOLUTE_PATH_PATTERN.match(node.value):
            add("RC06", node, "An absolute path makes the code hard to run on another machine.")
        # RC07: silent exception handling.
        if isinstance(node, ast.ExceptHandler):
            only_pass = all(isinstance(stmt, ast.Pass) for stmt in node.body)
            if node.type is None:
                add("RC07", node, "A bare except also hides unrelated errors.")
            elif only_pass:
                add("RC07", node, "The exception is caught and ignored.")
    return sorted(findings, key=lambda f: (f.file, f.line, f.rule_id))


EXCLUDED_DIRS = {".git", ".venv", "venv", "env", ".tox", "node_modules", "site-packages", "__pycache__", ".mypy_cache", ".pytest_cache"}

def project_files(root):
    """I prune dependency directories and refuse to follow symlinks."""
    files, skipped = [], []
    for directory, dirs, names in os.walk(root, followlinks=False):
        base = Path(directory)
        retained = []
        for name in sorted(dirs):
            path = base/name
            if path.is_symlink() or name in EXCLUDED_DIRS:
                skipped.append({"path": str(path.relative_to(root)), "reason": "symlink" if path.is_symlink() else "excluded dependency/cache directory"})
            else:
                retained.append(name)
        dirs[:] = retained
        for name in sorted(names):
            path = base/name
            if path.suffix != ".py": continue
            if path.is_symlink():
                skipped.append({"path": str(path.relative_to(root)), "reason": "symlink"})
            else: files.append(path)
    return sorted(files), skipped

def has_tests(root: Path) -> bool:
    files, _ = project_files(root)
    return any(p.name.startswith("test_") or p.name.endswith("_test.py") for p in files)

def scan_project(root: Path) -> dict:
    """I return findings plus explicit file coverage and source fingerprints."""
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Target must be an existing project directory: {root}")
    files, skipped = project_files(root)
    findings, records = [], []
    for path in files:
        relative = str(path.relative_to(root))
        record = {"path": relative}
        try:
            data = path.read_bytes()
            record["sha256"] = hashlib.sha256(data).hexdigest()
            encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
            source = data.decode(encoding)
            current = check_source(source, relative)
            record["status"] = "parse_failed" if any(f.rule_id == "RC00" for f in current) else "checked"
            findings.extend(current)
        except (OSError, UnicodeError, SyntaxError) as error:
            record["status"] = "read_failed"
            record["error"] = str(error)
            findings.append(Finding("RC10", "medium", "Source could not be read", relative, 0, "", str(error)))
        records.append(record)
    if not files:
        findings.append(Finding("RC09", "info", "No eligible Python source files", ".", 0, "", "No Python files were checked; this is not a successful code audit."))
    if not any(p.name.startswith("test_") or p.name.endswith("_test.py") for p in files):
        severity, title = RULES["RC08"]
        findings.append(Finding("RC08", severity, title, ".", 0, "", "No eligible Python test filenames. File presence alone would not prove valid tests or coverage."))
    checked = sum(r["status"] == "checked" for r in records)
    return {"target": root.name, "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Syntax-based candidate screening; not a correctness or leakage certificate",
            "scan_status": "no_eligible_sources" if not files else "partial" if checked != len(files) else "complete_for_eligible_files",
            "python_files_considered": len(files), "python_files_checked": checked,
            "file_records": records, "skipped": skipped, "excluded_directory_names": sorted(EXCLUDED_DIRS),
            "implemented_rules": list(RULES),
            "not_checked": ["Dataflow and cross-file seed execution", "Mathematical correctness", "Result reproduction", "Statistical validity", "Test execution or coverage", "Variable-valued periods, shuffle and center settings",
                            "Aliased model/split imports such as train_test_split as tts",
                            "RandomState seed tracking and lambda execution/scope handling",
                            "Conditional seeds including if __name__ == '__main__' are not certified"],
            "summary": summarize(findings), "findings": [asdict(f) for f in findings]}

def check_project(root: Path) -> list[Finding]:
    """I retain the original list-returning API for callers and tests."""
    return [Finding(**f) for f in scan_project(root)["findings"]]


def summarize(findings: list[Finding]) -> dict:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.rule_id] = counts.get(finding.rule_id, 0) + 1
    return {"total": len(findings), "by_rule": dict(sorted(counts.items()))}


def to_markdown(findings: list[Finding], target: str, report=None) -> str:
    out = [f"# Rule-based checker report: {target}", "",
           "Each row is a candidate issue for a human to judge. A finding is not a verdict.", ""]
    if report is not None:
        out += [f"Scan status: {report['scan_status']}",
                f"Python files checked: {report['python_files_checked']} / {report['python_files_considered']}.",
                "Complete means only that eligible files were readable and parsed; it is not a correctness verdict.",
                "Not checked: " + "; ".join(report['not_checked']) + ".", ""]
        if report['skipped']:
            out += ["## Skipped paths", ""]
            out += ["- " + x['path'] + ": " + x['reason'] for x in report['skipped']]
            out.append("")
    summary = summarize(findings)
    out.append(f"Total findings: {summary['total']}.")
    out.append("")
    out.append("| Rule | Title | Severity | Count |")
    out.append("|---|---|---|---|")
    for rule_id, count in summary["by_rule"].items():
        severity, title = RULES.get(rule_id, ("high", "Parse error"))
        out.append(f"| {rule_id} | {title} | {severity} | {count} |")
    out += ["", "## Findings", "", "| Rule | File | Line | Code | Reason |", "|---|---|---|---|---|"]
    for f in findings:
        code = f.code.replace("|", "\\|")
        out.append(f"| {f.rule_id} | `{f.file}` | {f.line} | `{code}` | {f.reason} |")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="Folder containing the project to check.")
    parser.add_argument("--out", type=Path, default=Path("results"), help="Folder for the report files.")
    parser.add_argument("--force", action="store_true", help="Explicitly replace existing reports; otherwise I refuse overwrite.")
    args = parser.parse_args()
    stem = f"rule_checker_{args.target.name}"
    destinations = [args.out/(stem+suffix) for suffix in (".json", ".md")]
    if not args.force and any(p.exists() for p in destinations):
        parser.error("A report already exists. Choose a new --out directory or explicitly use --force.")
    try:
        report = scan_project(args.target)
    except (ValueError, OSError, UnicodeError) as error:
        parser.error(str(error))
    args.out.mkdir(parents=True, exist_ok=True)
    findings = [Finding(**f) for f in report["findings"]]
    destinations[0].write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    destinations[1].write_text(to_markdown(findings, args.target.name, report), encoding="utf-8")
    print(json.dumps({"scan_status":report["scan_status"], "checked":report["python_files_checked"], **report["summary"]}, indent=2))


if __name__ == "__main__":
    main()
