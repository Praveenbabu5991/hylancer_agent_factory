.PHONY: install dev adk-web run clean help

# Default target
help:
	@echo "Content Studio Agent - Available commands:"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Run with custom UI (FastAPI server)"
	@echo "  make adk-web    - Run with ADK Web UI (development)"
	@echo "  make clean      - Clean generated files"
	@echo ""

# Install dependencies
install:
	pip install -e .

# Run with custom UI
dev:
	python -m app.fast_api_app

# Run with ADK Web UI
adk-web:
	adk web

# Clean generated files
clean:
	rm -rf generated/*
	rm -rf uploads/*
	rm -rf __pycache__
	rm -rf app/__pycache__
	rm -rf tools/__pycache__
	rm -rf memory/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
