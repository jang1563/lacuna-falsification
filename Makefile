.PHONY: help install test demo demo-kirc demo-templates clean status audit paper skeptic-review prereg prereg-validate prereg-audit rejection-log h1 h2 venv

# ============================================================
# Theory Copilot Falsification — Developer Commands
# ============================================================
# Run `make help` for the list of targets.
# ============================================================

PYTHON ?= .venv/bin/python
PYTHONPATH_SRC := PYTHONPATH=src
DEMO_OUT := artifacts/flagship_run
TRANSFER_OUT := artifacts/transfer_run

# Note: PYTHON defaults to the project-local virtualenv to guarantee
# Python 3.10+ (pyproject.toml requires >=3.10 for modern X | Y type hints).
# If the venv does not yet exist, run `make install` after
# `python3 -m venv .venv && . .venv/bin/activate && pip install -e .`, or
# override with `make test PYTHON=python3.12`.

help:
	@echo "Theory Copilot Falsification — available targets:"
	@echo ""
	@echo "  make venv          Create .venv and install the package (fresh-clone one-liner)"
	@echo "  make install       Install package + dependencies into existing .venv (editable)"
	@echo "  make test          Run the local-runnable test suite (no API calls)"
	@echo "  make demo          End-to-end demo on synthetic data"
	@echo "  make demo-kirc     KIRC-flavoured demo (flagship_kirc_demo.csv)"
	@echo "  make status        Print project status snapshot"
	@echo "  make audit         Run compliance grep (no sensitive strings)"
	@echo "  make skeptic-review  Parallel 3-model skeptic consensus (dry-run; LIVE=1 for real)"
	@echo "  make clean         Remove build + cache + transient artifacts"
	@echo ""
	@echo "Environment:"
	@echo "  Set ANTHROPIC_API_KEY in .env for live Opus calls."
	@echo "  Copy .env.example -> .env and fill values."

# Fresh-clone convenience: build .venv and install the package in one step.
# If .venv already exists this is a no-op for venv creation; pip install -e .
# still runs to pick up any pyproject edits.
venv:
	@test -d .venv || python3 -m venv .venv
	@$(PYTHON) -m pip install --quiet --upgrade pip
	@$(PYTHON) -m pip install --quiet -e .
	@echo ">>> .venv ready. Try: make test"

install:
	$(PYTHON) -m pip install -e .

# Runs the local-runnable subset of the test suite: 105 tests (as of
# 2026-04-23) across falsification gate, managed_agent_runner, routines
# client, opus_client, PySR sweep, DatasetCard, CLI, MCP biology
# validator, preregistration, and the Phase-H SR-loop harness.
# Five pre-hackathon scaffold suites (contracts / reuse_inventory /
# reuse_plan / staging / workflow_data) are ignored via the gitignored
# file list — those files are not in `git ls-files` (see .gitignore) and
# their fixtures depend on pre-hackathon HPC/staging state that the
# submitted repo deliberately does not include.
test:
	$(PYTHONPATH_SRC) $(PYTHON) -m pytest tests/ -v --tb=short \
		--ignore=tests/test_contracts.py \
		--ignore=tests/test_reuse_inventory.py \
		--ignore=tests/test_reuse_plan.py \
		--ignore=tests/test_staging.py \
		--ignore=tests/test_workflow_data.py

# --- Demo (synthetic flagship + transfer) ---
# NOTE: This target runs `compare` then `replay`, but `compare` only writes
# `proposer_output.json` and prints the next `python src/pysr_sweep.py` and
# `python src/falsification_sweep.py` commands — it does NOT generate
# `falsification_report.json` itself. `replay` will then fail because the
# report doesn't exist. Treat `make demo` as the GUIDED first step that
# tells you what to run next, not a one-shot end-to-end target. For a
# fast sanity check, prefer `make test` (105 local-runnable tests, no
# API key needed). Reviewer-facing happy path is `make venv && make test
# && make audit`. See README.
demo:
	@echo ">>> Running end-to-end demo on synthetic data..."
	@mkdir -p $(DEMO_OUT) $(TRANSFER_OUT)
	$(PYTHONPATH_SRC) $(PYTHON) -m theory_copilot.cli compare \
		--config config/datasets.json \
		--proposals config/law_proposals.json \
		--flagship-dataset flagship_demo \
		--output-root artifacts
	$(PYTHONPATH_SRC) $(PYTHON) -m theory_copilot.cli replay \
		--flagship-artifacts $(DEMO_OUT) \
		--transfer-dataset transfer_demo \
		--output-root artifacts
	@echo ">>> Demo complete. See $(DEMO_OUT)/ and $(TRANSFER_OUT)/"

# --- KIRC-flavoured demo (uses flagship_kirc_demo.csv + transfer_kirc_demo.csv) ---
demo-kirc:
	@echo ">>> Running KIRC-flavoured demo..."
	@mkdir -p $(DEMO_OUT) $(TRANSFER_OUT)
	$(PYTHONPATH_SRC) $(PYTHON) -m theory_copilot.cli compare \
		--config config/datasets.json \
		--proposals config/law_proposals.json \
		--flagship-dataset flagship_kirc_demo \
		--output-root artifacts
	$(PYTHONPATH_SRC) $(PYTHON) -m theory_copilot.cli replay \
		--flagship-artifacts $(DEMO_OUT) \
		--transfer-dataset transfer_kirc_demo \
		--output-root artifacts

# --- Status snapshot ---
status:
	@echo "=== Branch ==="; git rev-parse --abbrev-ref HEAD
	@echo "=== Last commits ==="; git log --oneline -5
	@echo "=== Artifacts ==="
	@ls -la artifacts/ 2>/dev/null || echo "(no artifacts yet)"
	@echo "=== Cost ledger (last 5 entries) ==="
	@tail -5 artifacts/cost_ledger.jsonl 2>/dev/null || echo "(no cost ledger yet)"

# --- Compliance audit (no institutional strings in tracked files) ---
# Pattern list lives in .audit-patterns; audit excludes itself and the
# Makefile so the search terms do not self-trigger.
audit:
	@echo ">>> Scanning tracked files for sensitive strings..."
	@if git grep -i -l -f .audit-patterns -- \
		':!Makefile' ':!.audit-patterns' \
		':(exclude)*.png' ':(exclude)*.jpg' ':(exclude)*.jpeg' \
		':(exclude)*.gif' ':(exclude)*.pdf' ':(exclude)*.ico' \
		':(exclude)*.ipynb' >/dev/null; then \
		echo "LEAK DETECTED — fix before committing:"; \
		git grep -i -n -f .audit-patterns -- \
			':!Makefile' ':!.audit-patterns' \
			':(exclude)*.png' ':(exclude)*.jpg' ':(exclude)*.jpeg' \
			':(exclude)*.gif' ':(exclude)*.pdf' ':(exclude)*.ico' \
			':(exclude)*.ipynb'; \
		exit 1; \
	else \
		echo ">>> OK — no sensitive strings in tracked files (binary assets excluded)."; \
	fi

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

# --- Parallel sub-agent skeptic review (E12) ---
# Spawns three Claude sub-agents (Opus 4.7, Sonnet 4.6, Haiku 4.5) in parallel
# on the 9 metastasis_expanded survivors and emits a consensus JSON + SUMMARY.md.
# Default is dry-run (no API calls). Pass `LIVE=1` for a real sweep; requires
# ANTHROPIC_API_KEY to be set.
skeptic-review:
	@echo ">>> Parallel sub-agent skeptic review (3 models x 9 survivors)..."
	@mkdir -p results/skeptic_consensus
	@if [ "$(LIVE)" = "1" ]; then \
		echo ">>> LIVE mode (requires ANTHROPIC_API_KEY)"; \
		$(PYTHONPATH_SRC) $(PYTHON) src/parallel_skeptic.py \
			--input results/track_a_task_landscape/metastasis_expanded/falsification_report.json \
			--output-dir results/skeptic_consensus; \
	else \
		echo ">>> DRY-RUN mode (pass LIVE=1 for real calls)"; \
		$(PYTHONPATH_SRC) $(PYTHON) src/parallel_skeptic.py \
			--input results/track_a_task_landscape/metastasis_expanded/falsification_report.json \
			--output-dir results/skeptic_consensus \
			--dry-run; \
	fi
	@echo ">>> Wrote results/skeptic_consensus/SUMMARY.md + consensus.json"

# --- Lane H: Falsification-Guided SR Loop + 1M Context Synthesis ---
# H1: run the falsification-guided SR loop (Opus-steered, up to 10 iters).
#   make h1          — full run with Opus 4.7 steering (requires ANTHROPIC_API_KEY)
#   make h1 NO_OPUS=1 — rule-based fallback, no API calls
# H2: 1M-context synthesis over all rejections + survivors.
#   make h2          — live Opus 4.7 call (requires ANTHROPIC_API_KEY)
#   make h2 DRYRUN=1 — write prompt to disk, no API call
H1_CSV ?= data/kirc_metastasis_expanded.csv
H1_ITERS ?= 10
H1_PYSR ?= 200

h1:
	@echo ">>> [H1] Falsification-Guided SR Loop ($(H1_ITERS) iterations)..."
	@mkdir -p results/overhang
	@if [ "$(NO_OPUS)" = "1" ]; then \
		$(PYTHONPATH_SRC) $(PYTHON) src/falsification_sr_loop.py \
			--csv $(H1_CSV) \
			--max-iterations $(H1_ITERS) \
			--pysr-iterations $(H1_PYSR) \
			--no-opus \
			--output results/overhang/sr_loop_run.json; \
	else \
		$(PYTHONPATH_SRC) $(PYTHON) src/falsification_sr_loop.py \
			--csv $(H1_CSV) \
			--max-iterations $(H1_ITERS) \
			--pysr-iterations $(H1_PYSR) \
			--output results/overhang/sr_loop_run.json; \
	fi

h2:
	@echo ">>> [H2] 1M-context synthesis (Opus 4.7)..."
	@mkdir -p results/overhang
	@if [ "$(DRYRUN)" = "1" ]; then \
		$(PYTHONPATH_SRC) $(PYTHON) src/opus_1m_synthesis.py \
			--dry-run \
			--output results/overhang/synthesis_1m.json; \
	else \
		$(PYTHONPATH_SRC) $(PYTHON) src/opus_1m_synthesis.py \
			--output results/overhang/synthesis_1m.json; \
	fi

# --- Pre-registration YAML artifacts (PhF-1) ---
# Emit one machine-readable pre-registration per law family BEFORE any search.
# Files are committed once and never modified; their git history is the
# tamper-evidence audit trail (FDA-EMA 2026-01 / EU AI Act 2026-08-02 alignment).
prereg:
	@echo ">>> Emitting pre-registration YAMLs for every law family..."
	$(PYTHONPATH_SRC) $(PYTHON) src/preregistration.py emit \
		--proposals config/law_proposals.json \
		--out preregistrations \
		--retroactive \
		--analyst "theory-copilot-team"

prereg-validate:
	$(PYTHONPATH_SRC) $(PYTHON) src/preregistration.py validate --dir preregistrations

prereg-audit:
	$(PYTHONPATH_SRC) $(PYTHON) src/preregistration.py audit --dir preregistrations

# --- Rejection log (PhF-4): one static HTML page listing every candidate,
# accept rows at the top, filters by cohort/task/panel/source.
rejection-log:
	$(PYTHONPATH_SRC) $(PYTHON) src/render_rejection_log.py

# --- Paper (docs/paper/paper.md → PDF via pandoc; xelatex > typst > html) ---
# Tries pdf-engine=xelatex first (best quality). Falls back to typst if a
# LaTeX distribution is not installed, then to HTML as last resort. All
# three outputs land at docs/paper/paper.pdf (or .html) — Makefile prints
# which engine ran.
paper:
	@echo ">>> Building docs/paper/paper.pdf via pandoc..."
	@if ! command -v pandoc >/dev/null 2>&1; then \
		echo "pandoc not installed. Install: brew install pandoc (macOS) or apt install pandoc (Linux)."; \
		exit 1; \
	fi
	@if command -v xelatex >/dev/null 2>&1; then \
		echo "  using xelatex engine..."; \
		pandoc docs/paper/paper.md \
			--pdf-engine=xelatex \
			-V geometry:margin=1in -V fontsize=11pt -V linkcolor=blue -V urlcolor=blue \
			-V mainfont="Times New Roman" -V monofont="Menlo" \
			-o docs/paper/paper.pdf && \
		echo ">>> Wrote docs/paper/paper.pdf (xelatex)"; \
	elif command -v typst >/dev/null 2>&1; then \
		echo "  xelatex not found; using typst engine..."; \
		pandoc docs/paper/paper.md \
			--pdf-engine=typst \
			-V papersize=a4 -V fontsize=11pt \
			-o docs/paper/paper.pdf && \
		echo ">>> Wrote docs/paper/paper.pdf (typst)"; \
	else \
		echo "  neither xelatex nor typst found; emitting HTML fallback..."; \
		pandoc docs/paper/paper.md \
			-s --mathjax \
			-o docs/paper/paper.html && \
		echo ">>> Wrote docs/paper/paper.html (install LaTeX or typst for PDF)"; \
	fi
