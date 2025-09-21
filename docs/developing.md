# Development Guide

This guide provides comprehensive information for developers working on the fastapi-base project, including setup instructions, development workflows, and best practices.

## 🚀 Quick Setup

### Prerequisites

Before starting development, ensure you have the following installed:

- **Docker** and **Docker Compose** (for containerized development)
- **Python 3.13+** (for local development)
- **uv** - Fast Python package manager ([installation guide](https://docs.astral.sh/uv/))
- **Git** - Version control system
- **Make** - Build automation tool (usually pre-installed on Unix systems)

### Initial Setup

1. **Clone and enter the repository**:
   ```bash
   git clone https://github.com/GabrielVGS/fastapi-base.git
   cd fastapi-base
   ```

2. **Copy environment configuration**:
   ```bash
   cp .env.example .env
   ```

3. **Install Python dependencies** (for local development):
   ```bash
   cd fastapi-base/
   uv sync
   ```

4. **Install pre-commit hooks**:
   ```bash
   make hooks
   ```

5. **Start the development environment**:
   ```bash
   make build
   ```

## 🐳 Docker Development Environment

### Starting the Environment

The easiest way to get started is using Docker Compose:

```bash
# Build and start all services
make build

# Or just start services (if already built)
make up
```

This will start:
- **FastAPI application** on `http://localhost:8666`
- **PostgreSQL database** on `localhost:5431`
- **Redis** for caching and sessions
- **Celery workers** for background tasks
- **Celery beat** for periodic tasks

### Useful Docker Commands

```bash
# Stop all services
make down

# Access the application container
make bash

# View logs
docker compose logs -f fastapi-base

# Rebuild specific service
docker compose up --build fastapi-base
```

### Environment Configuration

Edit the `.env` file to configure your development environment:

```bash
# Development settings
DEBUG=True
ENV=dev

# Database (using Docker defaults)
POSTGRES_USER=test
POSTGRES_PASSWORD=test
POSTGRES_DB=test
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis (using Docker defaults)
REDIS_HOST=redis
REDIS_PORT=6379
```

## 🏗️ Database Development

### Database Migrations

The project uses Alembic for database migrations:

#### Initial Setup

For a fresh database:
```bash
make alembic-init      # Create initial migration
make alembic-migrate   # Apply migrations
```

#### Creating New Migrations

When you modify models:
```bash
make alembic-make-migrations "describe your changes"
make alembic-migrate
```

#### Migration Commands

```bash
# Create a new migration
make alembic-make-migrations "add user table"

# Apply pending migrations
make alembic-migrate

# Reset database (careful in production!)
make alembic-reset

# View migration history
docker compose exec fastapi-base alembic history

# Downgrade to previous migration
docker compose exec fastapi-base alembic downgrade -1
```

### Database Models

When creating new models, follow these guidelines:

```python
# Example model in src/models/user.py
from sqlalchemy import Column, String, Boolean
from pydantic import BaseModel, Field
from typing import Optional
from .base import BaseModel as SQLBaseModel

class User(SQLBaseModel):
    __tablename__ = "users"
    
    email = Column(String(100), unique=True, index=True)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String(255))

# Separate Pydantic schemas for API
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: str
    # All fields from BaseModel (id, created_at, updated_at, deleted_at)
    # + email, full_name, is_active from UserBase
```

### Database Best Practices

1. **Always create migrations** for schema changes
2. **Use descriptive migration names** that explain the changes
3. **Test migrations** on a copy of production data
4. **Never edit existing migrations** that have been applied
5. **Use indexes** for frequently queried fields
6. **Define proper relationships** between models

## 🧪 Testing

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
docker compose exec fastapi-base pytest tests/test_api/test_users.py

# Run tests with verbose output
docker compose exec fastapi-base pytest -v

# Run tests matching a pattern
docker compose exec fastapi-base pytest -k "test_user"
```

### Test Structure

Organize tests in the `tests/` directory:

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_api/               # API endpoint tests
│   ├── test_auth.py        # Authentication tests
│   └── test_users.py       # User API tests
├── test_models/            # Model tests
│   └── test_user.py        # User model tests
├── test_services/          # Business logic tests
│   └── test_user_service.py
└── test_utils/             # Utility function tests
    └── test_helpers.py
```

## 🔧 Code Quality

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install hooks
make hooks

# Run hooks manually
make precommit-run

# Run specific hook
pre-commit run black
pre-commit run ruff
```

### Code Style Guidelines

1. **Follow PEP 8** style guidelines
2. **Use type hints** for all functions and methods
3. **Write docstrings** for public APIs
4. **Keep functions small** and focused
5. **Use meaningful variable names**
6. **Add comments** for complex logic

Example of well-formatted code:

```python
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_user_by_email(
    db: AsyncSession,
    email: str
) -> Optional[User]:
    """Retrieve a user by their email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_active_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[User]:
    """Retrieve a list of active users with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of active users
    """
    result = await db.execute(
        select(User)
        .where(User.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
```

## 🔄 Development Workflow

### Feature Development

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/user-authentication
   ```

2. **Make your changes** following the coding standards

3. **Write tests** for new functionality

4. **Run quality checks**:
   ```bash
   make precommit-run
   make test
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat(auth): implement JWT authentication"
   ```

6. **Push and create PR**:
   ```bash
   git push origin feature/user-authentication
   ```

### API Development

When adding new API endpoints:

1. **Define the schema** in `src/schemas/`
2. **Create the endpoint** in `src/api/v1/endpoints/`
3. **Add business logic** in `src/services/`
4. **Write tests** in `tests/test_api/`
5. **Update documentation** if needed

Example API endpoint:

```python
# src/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.api.deps import get_current_user, get_session
from src.schemas.user import UserCreate, UserRead
from src.services.user_service import UserService

router = APIRouter()

@router.post("/", response_model=UserRead)
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_session)
):
    """Create a new user."""
    user_service = UserService(db)

    # Check if user already exists
    if user_service.get_by_email(user_in.email):
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )

    user = user_service.create(user_in)
    return user

@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user
```

### Background Tasks

For Celery tasks, create them in `src/tasks/`:

```python
# src/tasks/email_tasks.py
from celery import Celery
from src.core.config import settings

celery_app = Celery("fastapi-base")

@celery_app.task
def send_welcome_email(user_email: str, user_name: str) -> str:
    """Send welcome email to new user."""
    # Email sending logic here
    print(f"Sending welcome email to {user_email}")
    return f"Welcome email sent to {user_name}"

@celery_app.task
def cleanup_expired_sessions():
    """Clean up expired user sessions."""
    # Cleanup logic here
    print("Cleaning up expired sessions")
    return "Session cleanup completed"
```

## 🐛 Debugging

### Local Debugging

For debugging the application:

```bash
# Run with debugger
docker compose exec fastapi-base python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or run locally
cd fastapi-base/
uv run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn src.main:app --reload
```

### Database Debugging

```bash
# Connect to PostgreSQL
docker compose exec db psql -U test -d test

# View database tables
docker compose exec db psql -U test -d test -c "\dt"

# Check migration status
docker compose exec fastapi-base alembic current

# View migration history
docker compose exec fastapi-base alembic history
```

### Log Debugging

```bash
# View application logs
docker compose logs -f fastapi-base

# View database logs
docker compose logs -f db

# View Celery worker logs
docker compose logs -f celery
```

## 🚀 Performance Tips

### Database Performance

1. **Use database indexes** for frequently queried fields
2. **Optimize queries** with proper joins and filters
3. **Use connection pooling** for better resource management
4. **Monitor slow queries** and optimize them

### API Performance

1. **Use async/await** for I/O operations
2. **Implement caching** for frequently accessed data
3. **Add pagination** for large datasets
4. **Use compression** for large responses

### Caching Strategy

```python
# Example caching with Redis
from src.utils.cache import cache_manager

@cache_manager.cache(expire=300)  # 5 minutes
async def get_user_profile(user_id: int) -> dict:
    """Get user profile with caching."""
    # Database query here
    return user_data
```

## 🔐 Security Best Practices

### Authentication & Authorization

1. **Use JWT tokens** for stateless authentication
2. **Hash passwords** using bcrypt
3. **Validate all inputs** using Pydantic schemas
4. **Implement rate limiting** for API endpoints

### Database Security

1. **Use parameterized queries** to prevent SQL injection
2. **Validate environment variables** for database connections
3. **Use SSL connections** in production
4. **Limit database user permissions**

### Environment Security

1. **Store secrets in environment variables**
2. **Never commit sensitive data** to version control
3. **Use different secrets** for different environments
4. **Rotate secrets regularly**

This guide should help you get started with development on the fastapi-base project. For additional questions, please refer to the [Architecture Overview](architecture.md), [Contributing Guidelines](../CONTRIBUTING.md), or [Troubleshooting Guide](troubleshooting.md) for common issues and solutions.
