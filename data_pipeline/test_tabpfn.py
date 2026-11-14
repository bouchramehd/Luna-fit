import numpy as np
import torch

from sklearn.datasets import make_regression
from tabpfn import TabPFNRegressor

X, y = make_regression(
    n_samples=120,
    n_features=5,
    noise=5,
    random_state=42,
)

model = TabPFNRegressor(
    device="cuda",
    n_estimators=1,
    auto_scale_n_estimators=False,
    fit_mode="low_memory",
    memory_saving_mode=True,
    keep_cache_on_device=False,
    random_state=42,
)

print("Loading model and fitting 100 synthetic rows...", flush=True)
model.fit(X[:100], y[:100])

predictions = model.predict(X[100:])
assert len(predictions) == 20
assert np.isfinite(predictions).all()

print("PASS: TabPFN generated 20 finite predictions.")
print(
    "Peak GPU memory:",
    round(torch.cuda.max_memory_allocated() / 1024**3, 2),
    "GB",
)