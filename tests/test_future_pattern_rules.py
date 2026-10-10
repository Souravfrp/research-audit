import unittest
from researchaudit.rule_checker import check_source

class FuturePatternRules(unittest.TestCase):
    def fires(self,source,rule='RC01'):
        return any(f.rule_id==rule for f in check_source(source))
    def test_centered_rolling(self):
        self.assertTrue(self.fires('x=df.rolling(5, center=True).mean()'))
    def test_uncentered_rolling(self):
        self.assertFalse(self.fires('x=df.rolling(5, center=False).mean()'))
    def test_negative_diff_positional_and_keyword(self):
        self.assertTrue(self.fires('x=df.diff(-1)'))
        self.assertTrue(self.fires('x=df.diff(periods=-1)'))
    def test_negative_pct_change_positional_and_keyword(self):
        self.assertTrue(self.fires('x=df.pct_change(-1)'))
        self.assertTrue(self.fires('x=df.pct_change(periods=-1)'))
    def test_positive_and_zero_periods(self):
        for method in ['shift','diff','pct_change']:
            self.assertFalse(self.fires(f'x=df.{method}(1)'))
            self.assertFalse(self.fires(f'x=df.{method}(-0)'))
    def test_documented_variable_and_alias_blind_spots(self):
        # Current limitations, not desirable detection performance.
        self.assertFalse(self.fires('p=-1\nx=df.shift(p)'))
        self.assertFalse(self.fires('do_shuffle=True\na=train_test_split(X,y,shuffle=do_shuffle)','RC02'))
        self.assertFalse(self.fires('from sklearn.model_selection import train_test_split as tts\na=tts(X,y)','RC02'))
    def test_main_guard_seed_is_conservative_candidate(self):
        source="import numpy as np\nif __name__ == '__main__':\n np.random.seed(1)\n x=np.random.rand(5)"
        self.assertTrue(self.fires(source,'RC04'))

if __name__=='__main__':unittest.main()
