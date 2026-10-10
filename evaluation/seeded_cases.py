"""Small hand-written examples for checking that each rule fires on a known defect.

Each case is (rule_id, name, source, should_fire). These are my own seeded examples.
They show that a rule does what I designed it to do. They are not a measure of how
well the checker finds real defects in real projects.
"""

CASES = [
    ("RC01", "negative shift as feature", "df['feat'] = df['ret'].shift(-1)\n", True),
    ("RC01", "positive shift (lag)", "df['feat'] = df['ret'].shift(1)\n", False),
    ("RC02", "split with default shuffling", "X_tr, X_te = train_test_split(X, y)\n", True),
    ("RC02", "split with shuffle=True", "a = train_test_split(X, y, shuffle=True)\n", True),
    ("RC02", "split with shuffle=False", "a = train_test_split(X, y, shuffle=False)\n", False),
    ("RC02", "shuffled KFold", "cv = KFold(n_splits=5, shuffle=True)\n", True),
    ("RC02", "ordered KFold", "cv = KFold(n_splits=5)\n", False),
    ("RC03", "scaler fitted then used", "Z = StandardScaler().fit_transform(X)\n", True),
    ("RC03", "no transformer", "Z = X - X.mean()\n", False),
    ("RC04", "forest without seed", "m = RandomForestRegressor(n_estimators=100)\n", True),
    ("RC04", "forest with seed", "m = RandomForestRegressor(n_estimators=100, random_state=1)\n", False),
    ("RC04", "global numpy generator", "import numpy as np\nx = np.random.rand(5)\n", True),
    ("RC04", "global generator with seed", "import numpy as np\nnp.random.seed(1)\nx = np.random.rand(5)\n", False),
    ("RC05", "cost parameter never used", "def run(x, cost_bps=5):\n    return x * 2\n", True),
    ("RC05", "cost parameter used", "def run(x, cost_bps=5):\n    return x * (1 - cost_bps / 10000)\n", False),
    ("RC06", "absolute path", "path = '/Users/someone/data/prices.csv'\n", True),
    ("RC06", "relative path", "path = 'data/prices.csv'\n", False),
    ("RC07", "bare except", "try:\n    f()\nexcept:\n    g()\n", True),
    ("RC07", "ignored exception", "try:\n    f()\nexcept ValueError:\n    pass\n", True),
    ("RC07", "handled exception", "try:\n    f()\nexcept ValueError as e:\n    raise RuntimeError('bad') from e\n", False),
]
