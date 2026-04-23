.PHONY: help install test demo demo-kirc demo-templates clean status audit paper skeptic-review prereg prereg-validate prereg-audit

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
	@echo "  make install       Install package + dependencies (editable)"
	@echo "  make test          Run the test suite (no API calls)"
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

install:
	$(PYTHON) -m pip install -e .

test:
	$(PYTHONPATH_SRC) $(PYTHON) -m pytest tests/ -v --tb=short \
		--ignore=tests/test_contracts.py \
		--ignore=tests/test_reuse_inventory.py \
		--ignore=tests/test_reuse_plan.py \
		--ignore=tests/test_staging.py \
		--ignore=tests/test_workflow_data.py

# --- Demo (synthetic flagship + transfer) ---
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
	@if git grep -i -l -f .audit-patterns -- ':!Makefile' ':!.audit-patterns' >/dev/null; then \
		echo "LEAK DETECTED — fix before committing:"; \
		git grep -i -n -f .audit-patterns -- ':!Makefile' ':!.audit-patterns'; \
		exit 1; \
	else \
		echo ">>> OK — no sensitive strings in tracked files."; \
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

# --- Paper (docs/paper/paper.md → PDF via pandoc + xelatex) ---
paper:
	@echo ">>> Building docs/paper/paper.pdf via pandoc..."
	@if ! command -v pandoc >/dev/null 2>&1; then \
		echo "pandoc not installed. Install: brew install pandoc (macOS) or apt install pandoc (Linux)."; \
		exit 1; \
	fi
	@pandoc docs/paper/paper.md \
		--pdf-engine=xelatex \
		-V geometry:margin=1in -V fontsize=11pt -V linkcolor=blue -V urlcolor=blue \
		-V mainfont="Times New Roman" -V monofont="Menlo" \
		-o docs/paper/paper.pdf
	@echo ">>> Wrote docs/paper/paper.pdf"
