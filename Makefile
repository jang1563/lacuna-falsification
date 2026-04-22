.PHONY: help install test demo demo-kirc demo-templates clean status audit

# ============================================================
# Theory Copilot Falsification — Developer Commands
# ============================================================
# Run `make help` for the list of targets.
# ============================================================

PYTHON ?= python3
PYTHONPATH_SRC := PYTHONPATH=src
DEMO_OUT := artifacts/flagship_run
TRANSFER_OUT := artifacts/transfer_run

help:
	@echo "Theory Copilot Falsification — available targets:"
	@echo ""
	@echo "  make install       Install package + dependencies (editable)"
	@echo "  make test          Run the test suite (no API calls)"
	@echo "  make demo          End-to-end demo on synthetic data"
	@echo "  make demo-kirc     KIRC-flavoured demo (flagship_kirc_demo.csv)"
	@echo "  make status        Print project status snapshot"
	@echo "  make audit         Run compliance grep (no sensitive strings)"
	@echo "  make clean         Remove build + cache + transient artifacts"
	@echo ""
	@echo "Environment:"
	@echo "  Set ANTHROPIC_API_KEY in .env for live Opus calls."
	@echo "  Copy .env.example -> .env and fill values."

install:
	$(PYTHON) -m pip install -e .

test:
	$(PYTHONPATH_SRC) $(PYTHON) -m pytest tests/ -v

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
