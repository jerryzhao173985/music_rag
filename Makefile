.PHONY: help install test clean run-api run-demo docker-build docker-run lint format

help:
	@echo "Music RAG - Available Commands:"
	@echo ""
	@echo "  make install        - Create venv and install dependencies"
	@echo "  make test          - Run test suite"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make run-api       - Run FastAPI server"
	@echo "  make run-demo      - Run quickstart demo"
	@echo "  make init-data     - Initialize with sample data"
	@echo "  make clean         - Clean up generated files"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run with Docker Compose"
	@echo "  make docker-stop   - Stop Docker containers"
	@echo "  make lint          - Run code linting"
	@echo "  make format        - Format code with black"
	@echo ""

install:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	@echo "\n✓ Installation complete!"
	@echo "Activate venv with: source venv/bin/activate"

test:
	./venv/bin/pytest tests/ -v

test-cov:
	./venv/bin/pytest tests/ -v --cov=music_rag --cov-report=html --cov-report=term

run-api:
	./venv/bin/python -m uvicorn music_rag.api:app --reload --host 0.0.0.0 --port 8000

run-demo:
	./venv/bin/python quickstart.py

init-data:
	./venv/bin/python -m music_rag.cli init-sample-data

search:
	@read -p "Enter search query: " query; \
	./venv/bin/python -m music_rag.cli search "$$query" --top-k 5

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf music_rag/__pycache__ music_rag/src/__pycache__
	rm -rf tests/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned up build artifacts"

docker-build:
	docker build -t music-rag:latest .

docker-run:
	docker-compose up -d
	@echo "\n✓ Music RAG API running at http://localhost:8000"
	@echo "View logs: docker-compose logs -f"

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

lint:
	@echo "Installing linting tools..."
	./venv/bin/pip install flake8 black isort mypy
	@echo "\nRunning flake8..."
	./venv/bin/flake8 music_rag/ --max-line-length=100 --ignore=E203,W503
	@echo "\nRunning mypy..."
	./venv/bin/mypy music_rag/ --ignore-missing-imports

format:
	@echo "Installing formatting tools..."
	./venv/bin/pip install black isort
	@echo "\nFormatting with black..."
	./venv/bin/black music_rag/ tests/
	@echo "\nSorting imports..."
	./venv/bin/isort music_rag/ tests/
	@echo "\n✓ Code formatted"

dev:
	@echo "Setting up development environment..."
	make install
	cp .env.example .env
	@echo "\n✓ Development environment ready!"
	@echo "Next steps:"
	@echo "  1. source venv/bin/activate"
	@echo "  2. make init-data"
	@echo "  3. make run-demo"
