# Makefile

.PHONY: help init test clean

help:
	@echo "Makefile for git-change-detect"
	@echo ""
	@echo "Targets:"
	@echo "  help    - Show this help message"
	@echo "  init    - Initialize the development environment"
	@echo "  test    - Run the unit tests"
	@echo "  clean   - Clean up the environment"

init:
	@echo "Initializing environment..."
	@uv venv
	@uv pip install -r requirements.txt
	@uv pip install -e .
	@echo "Environment initialized."

test:
	@echo "Running tests..."
	@uv run pytest

clean:
	@echo "Cleaning up..."
	@rm -rf .venv
	@rm -rf git_change_detect.egg-info
	@rm -rf `find . -name __pycache__`
	@rm -f `find . -name '*.pyc'`
	@echo "Clean up complete."

