"""Tests for the rule-based checker."""

import tempfile
import unittest
from pathlib import Path

from evaluation.seeded_cases import CASES
from researchaudit.rule_checker import check_project, check_source, summarize


class SeededCases(unittest.TestCase):
    def test_every_seeded_case_behaves_as_designed(self):
        for rule, name, source, should_fire in CASES:
            with self.subTest(rule=rule, case=name):
                fired = any(f.rule_id == rule for f in check_source(source, "case.py"))
                self.assertEqual(fired, should_fire)


class Details(unittest.TestCase):
    def test_finding_has_file_line_and_code(self):
        findings = check_source("x = 1\ny = df.shift(-5)\n", "a.py")
        self.assertEqual((findings[0].file, findings[0].line, findings[0].code), ("a.py", 2, "y = df.shift(-5)"))

    def test_docstring_mention_of_a_parameter_does_not_count_as_use(self):
        source = 'def f(x, cost_bps=0):\n    """Uses cost_bps."""\n    return x\n'
        self.assertTrue(any(f.rule_id == "RC05" for f in check_source(source)))

    def test_syntax_error_is_reported_not_raised(self):
        self.assertEqual(check_source("def (:\n")[0].rule_id, "RC00")

    def test_clean_code_has_no_findings(self):
        source = ("import numpy as np\n\ndef portfolio_value(prices, cost_bps=0.0):\n"
                  "    return prices.sum() * (1 - cost_bps / 10000)\n")
        self.assertEqual(check_source(source), [])


class ProjectLevel(unittest.TestCase):
    def test_project_without_tests_gets_rc08_and_with_tests_does_not(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "a.py").write_text("x = 1\n")
            self.assertIn("RC08", summarize(check_project(root))["by_rule"])
            (root / "tests").mkdir()
            self.assertIn("RC08", summarize(check_project(root))["by_rule"])
            (root / "tests" / "test_example.py").write_text("def test_example(): pass\n")
            self.assertNotIn("RC08", summarize(check_project(root))["by_rule"])


if __name__ == "__main__":
    unittest.main()
