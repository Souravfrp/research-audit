"""Counterexamples from review, separate from the original 20 examples."""
import tempfile
import unittest
from pathlib import Path
from researchaudit.rule_checker import check_source, check_project, has_tests

class RegressionCases(unittest.TestCase):
    def fired(self,source,rule):
        return any(f.rule_id==rule for f in check_source(source))
    def test_generator_does_not_seed_global_rng(self):
        self.assertTrue(self.fired('import numpy as np\nrng=np.random.default_rng(1)\nx=np.random.rand(5)','RC04'))
    def test_late_seed_does_not_cover_earlier_draw(self):
        self.assertTrue(self.fired('import numpy as np\nx=np.random.rand(5)\nnp.random.seed(1)','RC04'))
    def test_top_level_fixed_seed_covers_later_draw(self):
        self.assertFalse(self.fired('import numpy as np\nnp.random.seed(1)\nx=np.random.rand(5)','RC04'))
    def test_none_seed_resets_known_seed(self):
        self.assertTrue(self.fired('import numpy as np\nnp.random.seed(1)\nnp.random.seed(None)\nx=np.random.rand(5)','RC04'))
    def test_function_draw_is_not_certified_by_module_seed(self):
        self.assertTrue(self.fired('import numpy as np\nnp.random.seed(1)\ndef f():\n return np.random.rand(5)','RC04'))
    def test_comment_seed_is_not_execution(self):
        self.assertTrue(self.fired('import numpy as np\n# np.random.seed(1)\nx=np.random.rand(5)','RC04'))
    def test_numpy_alias(self):
        self.assertTrue(self.fired('import numpy as number\nx=number.random.rand(5)','RC04'))
    def test_direct_random_alias(self):
        self.assertTrue(self.fired('from numpy.random import rand as draw\nx=draw(5)','RC04'))
    def test_none_random_state(self):
        self.assertTrue(self.fired('m=RandomForestRegressor(random_state=None)','RC04'))
    def test_none_generator_seed(self):
        self.assertTrue(self.fired('rng=np.random.default_rng(None)','RC04'))
    def test_ordered_folds_are_not_randomness_findings(self):
        self.assertFalse(self.fired('cv=KFold()','RC04'))
        self.assertFalse(self.fired('cv=StratifiedKFold(shuffle=False)','RC04'))
    def test_shuffled_fold_without_seed(self):
        self.assertTrue(self.fired('cv=KFold(shuffle=True)','RC04'))
    def test_positional_only_cost(self):
        self.assertTrue(self.fired('def f(cost_bps, /):\n return 1','RC05'))
    def test_shadowed_nested_parameter(self):
        self.assertTrue(self.fired('def f(cost_bps):\n def g(cost_bps):\n  return cost_bps\n return g(1)','RC05'))
    def test_real_closure_reference(self):
        self.assertFalse(self.fired('def f(cost_bps):\n def g():\n  return cost_bps\n return g()','RC05'))
    def test_invalid_scope_syntax_is_reported(self):
        self.assertTrue(self.fired('return 1','RC00'))
    def test_conditional_unknown_seed_invalidates_fixed_seed(self):
        self.assertTrue(self.fired('import numpy as np\nnp.random.seed(1)\nif flag:\n np.random.seed(None)\nx=np.random.rand(5)','RC04'))
    def test_missing_project_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): check_project(Path(d)/'missing')
    def test_file_is_not_project(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.py';p.write_text('x=1')
            with self.assertRaises(ValueError):check_project(p)
    def test_empty_tests_directory_is_not_test_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'tests').mkdir();self.assertFalse(has_tests(p))
            (p/'tests'/'test_x.py').write_text('# file presence only; not test validity')
            self.assertTrue(has_tests(p))

if __name__=='__main__':unittest.main()
