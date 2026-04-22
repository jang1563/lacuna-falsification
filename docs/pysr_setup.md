# PySR + Julia Setup Guide

## This Machine (detected)

| Property | Value |
|----------|-------|
| OS | macOS Darwin 25.2.0 |
| Architecture | **arm64 (Apple Silicon)** |
| Python | 3.14.3 |
| Julia | **Not installed** |
| PySR | **Not installed** |

---

## Install Steps for This Mac (Apple Silicon arm64)

### Step 1 — Install Julia via juliaup (recommended)

```bash
# Option A: official installer (works on Intel and Apple Silicon)
curl -fsSL https://install.julialang.org | sh

# Option B: Homebrew
brew install juliaup
```

After install, restart your terminal (or `source ~/.zshrc`), then confirm:

```bash
julia --version   # should show 1.10.x
```

> **Julia version note:**  
> PySR requires Julia ≥ 1.6.7. Use **1.10.0** specifically if possible.  
> **Avoid 1.10.1 and 1.10.2** — those versions contain a libgomp bug that causes hard crashes.  
> If juliaup installs a newer patch, pin with: `juliaup default 1.10.0`

### Step 2 — Install PySR into the project venv

```bash
# From repo root
.venv/bin/pip install pysr
```

Stable release as of 2025-07: **v1.5.9**  
(v2.0.0a1 is available but alpha — do not use for hackathon.)

### Step 3 — First import (triggers Julia compilation)

```python
import pysr   # first run compiles Julia packages — takes 5–15 min
```

This only runs once per environment. Subsequent imports are fast (~5 s).

### Apple Silicon Gotchas

1. **No Rosetta needed.** Julia has Tier 1 native arm64 support; do not run under Rosetta.
2. **GLIBCXX crash on import.** If PySR crashes with `GLIBCXX_... not found`, another Python
   dependency has loaded the wrong `libstdc++`. Fix by prepending Julia's lib path:
   ```bash
   export LD_LIBRARY_PATH="$(julia -e 'print(Sys.BINDIR)')/../lib:$LD_LIBRARY_PATH"
   ```
3. **Python ≥ 3.9 required.** This machine has 3.14.3 — compatible.

---

## Minimum Smoke Test

```python
import pysr
import numpy as np

X = np.random.randn(100, 2)
y = 2.5 * X[:, 0] ** 2 + X[:, 1]

model = pysr.PySRRegressor(niterations=5)
model.fit(X, y)
print(model)
```

Expected output: a table of symbolic expressions ranked by complexity vs. loss.  
If this runs without error, the Julia backend is wired up correctly.

---

## Estimated Install Time

| Step | Time |
|------|------|
| juliaup + Julia 1.10.0 download | 2–5 min (network-dependent) |
| `pip install pysr` | 1–2 min |
| First `import pysr` (Julia compilation) | **5–15 min** (one-time, per-env) |
| **Total first-time setup** | **~10–25 min** |

> Plan for this on Day 2 morning before the coding sprint — do not start it mid-sprint.

---

## Sources

- PySR GitHub repository: https://github.com/MilesCranmer/PySR
- PySR CHANGELOG (stable v1.5.9 confirmed): https://github.com/MilesCranmer/PySR/blob/master/CHANGELOG.md
- juliaup (official Julia version manager): https://github.com/JuliaLang/juliaup
- Julia macOS install guide: https://julialang.org/downloads/platform/
- Contact your institution's HPC support team to request Julia if unavailable as a module.
