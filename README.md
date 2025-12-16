# FastAPI Base Project

<p align="center">
  <a href="docs/README-pt.md">🇧🇷 Português</a> |
  <a href="docs/README-fr.md">🇫🇷 Français</a> |
  <a href="docs/README-es.md">🇪🇸 Español</a>
</p>

<p align="center">
    <a href="https://github.com/GabrielVGS/fastapi-base/actions">
        <img alt="GitHub Actions Status" src="https://github.com/GabrielVGS/fastapi-base/actions/workflows/main.yml/badge.svg">
    </a>
    <a href="https://codecov.io/gh/GabrielVGS/fastapi-base">
     <img src="https://codecov.io/gh/GabrielVGS/fastapi-base/branch/main/graph/badge.svg?token=899NB4AK7J"/>
    </a>
    <a href="https://github.com/GabrielVGS/fastapi-base/releases">
        <img alt="Release Status" src="https://img.shields.io/github/v/release/GabrielVGS/fastapi-base">
    </a>
</p>

A modern, production-ready FastAPI backend template with best practices, Docker support, and comprehensive tooling for rapid development.</p>

## 🏗️ Project Template

This project was created using the excellent [cookiecutter-fastapi-backend](https://github.com/nickatnight/cookiecutter-fastapi-backend) template by [@nickatnight](https://github.com/nickatnight), which provides a solid foundation for FastAPI applications with best practices and modern tooling.

## 📚 Documentation

- [Architecture](docs/architecture.md) - System architecture overview
- [Development Guide](docs/developing.md) - Local development guidelines
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to this project
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## ✨ Features

- **FastAPI** - Modern, fast web framework for building APIs
- **Docker** - Containerized development and deployment
- **PostgreSQL** - Robust relational database with async support
- **Redis** - Caching and session management
- **Celery** - Background task processing
- **Alembic** - Database migration management
- **Testing** - Comprehensive test suite with pytest
- **Code Quality** - Pre-commit hooks, linting, and formatting
- **Type Safety** - Full type hints with mypy validation
- **Documentation** - Auto-generated API docs with Swagger UI

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.13+ (for local development)
- [uv](https://docs.astral.sh/uv/) package manager

### Running with Docker (Recommended)

1. **Clone the repository**:

   ```bash
   git clone https://github.com/GabrielVGS/fastapi-base.git
   cd fastapi-base
   ```

2. **Copy environment variables**:

   ```bash
   cp .env.example .env
   ```

3. **Start the services**:

   ```bash
   make up
   ```

4. **Access the application**:
   - API: `http://localhost:8666/v1/`
   - Health check: `http://localhost:8666/v1/ping`
   - Interactive docs: `http://localhost:8666/docs`
   - Alternative docs: `http://localhost:8666/redoc`

## 🛠️ Local Development

### Setting up Local Environment

1. **Install uv** (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Navigate to the project directory**:

   ```bash
   cd fastapi-base/
   ```

3. **Install dependencies**:

   ```bash
   uv sync
   ```

4. **Install pre-commit hooks**:

   ```bash
   make hooks
   ```

### Database Migrations

Initialize the first migration (project must be running with `docker compose up` and contain no 'version' files):

```bash
make alembic-init
```

Create new migration file:

```bash
make alembic-make-migrations "describe your changes"
```

Apply migrations:

```bash
make alembic-migrate
```

### Migration Workflow

After each migration, you can create new migrations and apply them with:

```bash
make alembic-make-migrations "describe your changes"
make alembic-migrate
```

## 📋 Environment Variables

Create a `.env` file based on `.env.example`:

### Application Settings

- `PROJECT_NAME` - Name of the project (default: fastapi-base)
- `VERSION` - API version (default: v1)
- `DEBUG` - Enable debug mode (default: True)
- `SECRET_KEY` - Secret key for JWT and encryption
- `ENV` - Environment (dev/staging/production)

### Database Configuration

- `POSTGRES_USER` - PostgreSQL username
- `POSTGRES_PASSWORD` - PostgreSQL password
- `POSTGRES_DB` - Database name
- `POSTGRES_HOST` - Database host (default: localhost)
- `POSTGRES_PORT` - Database port (default: 5432)
- `POSTGRES_URL` - Complete database URL (optional, auto-generated if not provided)

### Redis Configuration

- `REDIS_HOST` - Redis host (default: redis)
- `REDIS_PORT` - Redis port (default: 6379)
- `REDIS_URL` - Complete Redis URL (optional, auto-generated if not provided)

### Optional Settings

- `SENTRY_DSN` - Sentry error tracking DSN
- `LOG_LEVEL` - Logging level (default: INFO)
- `CACHE_TTL` - Cache time-to-live in seconds (default: 60)

## 🏃 Running the Application

### Using Docker Compose (Recommended)

```bash
# Build and start all services
make build

# Start services (without building)
make up

# Stop services
make down

# Access container bash
make bash
```

### Local Development (without Docker)

```bash
# Ensure PostgreSQL and Redis are running locally
# Update .env with local database/redis connections

# Run the FastAPI application
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Development Workflow

Check the [Makefile](Makefile) to view all available commands.

### Available Make Commands

```bash
# Development
make up          # Start all services with Docker Compose
make down        # Stop all services
make build       # Build and start services
make bash        # Access the main container shell

# Database
make alembic-init              # Initialize first migration
make alembic-make-migrations   # Create new migration
make alembic-migrate          # Apply migrations
make alembic-reset            # Reset database
make init-db                  # Initialize database with sample data

# Code Quality
make test           # Run test suite with coverage
make lint           # Run ruff linter
make black          # Format code with black
make isort          # Sort imports
make mypy           # Type checking
make precommit-run  # Run all pre-commit hooks

# Maintenance
make hooks          # Install pre-commit hooks
```

### Dependencies

By default, dependencies are managed with [uv](https://docs.astral.sh/uv/). Please visit the link and install it.

From `./fastapi-base/` you can install all dependencies with:

```bash
uv sync
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality. Install them with:

```bash
make hooks
```

This will install hooks that run automatically before each commit to:

- Format code with `black`
- Sort imports with `isort`
- Lint code with `ruff`
- Check types with `mypy`
- Run tests

## 🧪 Testing

Run the complete test suite:

```bash
make test
```

Run specific tests:

```bash
# Inside the container
docker compose exec fastapi-base pytest tests/test_specific.py

# Locally (if dependencies installed)
uv run pytest tests/test_specific.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for detailed information about:

- Setting up your development environment
- Code style and standards
- Testing requirements
- Pull request process
- Code of conduct

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛠️ Built With

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM with full async support
- [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type annotations
- [Alembic](https://alembic.sqlalchemy.org/) - Database migration tool
- [Celery](https://docs.celeryproject.org/) - Distributed task queue
- [Redis](https://redis.io/) - In-memory data structure store
- [PostgreSQL](https://www.postgresql.org/) - Advanced open source database
- [Docker](https://www.docker.com/) - Containerization platform
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## ⭐️ Support

If you found this project useful, please consider:

- Giving it a star ⭐️ on GitHub
- Sharing it with your colleagues
- Contributing to its development
- Reporting issues or suggesting improvements

---

**Happy coding!** 🚀
