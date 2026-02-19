# ──────────────────────────────────────────────────────────────
# Delinea Secret Server — AAP/AWX Credential Plugin
# ──────────────────────────────────────────────────────────────

VENV_DIR      ?= .venv
PYTHON        ?= python3
VENV_PYTHON   := $(VENV_DIR)/bin/python
VENV_PIP      := $(VENV_DIR)/bin/pip
PYTEST        := $(VENV_DIR)/bin/pytest
SRC_DIR       := credential_plugins
TEST_DIR      := tests

.PHONY: help init venv install install-dev test test-verbose test-only lint build clean

# ── Default target ────────────────────────────────────────────
help: ## Show this help message
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Project initialisation ───────────────────────────────────
init: ## Create __init__.py files and requirements.txt if missing
	@mkdir -p $(SRC_DIR) $(TEST_DIR) examples
	@touch $(SRC_DIR)/__init__.py $(TEST_DIR)/__init__.py
	@echo "Project structure initialised."

# ── Virtual environment ──────────────────────────────────────
venv: ## Create local virtual environment and upgrade pip
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip

# ── Dependency installation ──────────────────────────────────
install: venv ## Install runtime package in editable mode
	$(VENV_PIP) install -e .

install-dev: venv ## Install package with development dependencies
	$(VENV_PIP) install -e ".[dev]"

# ── Testing ──────────────────────────────────────────────────
test: install-dev ## Run all unit tests
	$(PYTEST) $(TEST_DIR) -v --tb=short

test-verbose: install-dev ## Run all unit tests with full output
	$(PYTEST) $(TEST_DIR) -v --tb=long -s

test-only: ## Run tests without installing dependencies (faster)
	$(PYTEST) $(TEST_DIR) -v --tb=short

# ── Code quality ─────────────────────────────────────────────
lint: ## Run basic linting with py_compile on all plugin sources
	@echo "Checking syntax..."
	@find $(SRC_DIR) -name '*.py' -exec $(VENV_PYTHON) -m py_compile {} +
	@echo "All files OK."

# ── Packaging ────────────────────────────────────────────────
build: install-dev ## Build source and wheel distributions
	$(VENV_PYTHON) -m build

# ── Cleanup ──────────────────────────────────────────────────
clean: ## Remove caches, bytecode, and test artifacts
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	find . -type f -name '*.pyo' -delete 2>/dev/null || true
	rm -rf build dist *.egg-info
	@echo "Cleaned."