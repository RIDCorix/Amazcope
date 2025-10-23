"""Pytest configuration with Tortoise ORM support for async testing."""

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Load environment variables BEFORE importing settings
# Load .env file from the src directory
env_path = src_path / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"\n✅ Loaded environment variables from: {env_path}")
else:
    print(f"\n⚠️  Warning: .env file not found at: {env_path}")

# Now import everything else after env is loaded
import time  # noqa:E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

from core.config import settings  # noqa: E402
from core.database import Base  # noqa: E402
from core.security import hash_password  # noqa: E402
from main import app  # noqa: E402
from users.models import User  # noqa: E402

# Test database configuration
# Option 1: SQLite in-memory (fast, but some PostgreSQL-specific features won't work)
# DISABLED: Our models use PostgreSQL-specific features like UUID, JSONB, etc.
USE_SQLITE = os.getenv("TEST_USE_SQLITE", "false").lower() == "true"

# Generate unique test database name
TEST_DATABASE_NAME = f"test_amazcope_{int(time.time())}"

if USE_SQLITE:
    TEST_DB_URL = "sqlite://:memory:"
else:
    # Option 2: PostgreSQL with unique database per test session
    # Ensures complete isolation and auto-cleanup
    TEST_DATABASE_HOST = os.getenv("TEST_DB_HOST", settings.DATABASE_HOST)
    TEST_DATABASE_PORT = int(os.getenv("TEST_DB_PORT", settings.DATABASE_PORT))
    TEST_DATABASE_USER = os.getenv("TEST_DB_USER", settings.DATABASE_USERNAME)
    TEST_DATABASE_PASS = os.getenv("TEST_DB_PASS", settings.DATABASE_PASSWORD)

    # URL to connect to default 'postgres' database for creating/dropping test database
    POSTGRES_DB_URL = f"postgresql+asyncpg://{TEST_DATABASE_USER}:{TEST_DATABASE_PASS}@{TEST_DATABASE_HOST}:{TEST_DATABASE_PORT}/postgres"

    # URL to connect to our test database
    TEST_DB_URL = f"postgresql+asyncpg://{TEST_DATABASE_USER}:{TEST_DATABASE_PASS}@{TEST_DATABASE_HOST}:{TEST_DATABASE_PORT}/{TEST_DATABASE_NAME}"


def pytest_sessionstart(session):
    """Create test database at the start of test session.

    This is a pytest hook that runs before any tests.
    """
    if USE_SQLITE:
        return

    from sqlalchemy import create_engine
    from sqlalchemy import text as sync_text

    # Use synchronous engine for database creation
    sync_engine = create_engine(
        POSTGRES_DB_URL.replace("+asyncpg", ""),  # Use psycopg2
        isolation_level="AUTOCOMMIT",
        echo=False,
    )

    with sync_engine.connect() as conn:
        # Drop database if it exists (cleanup from previous failed runs)
        conn.execute(sync_text(f"DROP DATABASE IF EXISTS {TEST_DATABASE_NAME}"))
        # Create test database
        conn.execute(sync_text(f"CREATE DATABASE {TEST_DATABASE_NAME}"))
        print(f"\n✅ Created test database: {TEST_DATABASE_NAME}")

    sync_engine.dispose()


def pytest_sessionfinish(session, exitstatus):
    """Drop test database at the end of test session.

    This is a pytest hook that runs after all tests complete.
    """
    if USE_SQLITE:
        return

    from sqlalchemy import create_engine
    from sqlalchemy import text as sync_text

    # Use synchronous engine for database cleanup
    sync_engine = create_engine(
        POSTGRES_DB_URL.replace("+asyncpg", ""),  # Use psycopg2
        isolation_level="AUTOCOMMIT",
        echo=False,
    )

    with sync_engine.connect() as conn:
        # Terminate all connections to the test database
        conn.execute(
            sync_text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{TEST_DATABASE_NAME}'
                AND pid <> pg_backend_pid()
            """)
        )
        # Drop test database
        conn.execute(sync_text(f"DROP DATABASE IF EXISTS {TEST_DATABASE_NAME}"))
        print(f"\n✅ Dropped test database: {TEST_DATABASE_NAME}")

    sync_engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def initialize_tests():
    """Initialize test database schema before each test and clean up after.

    This ensures complete isolation between tests by:
    1. Creating all tables before test
    2. Running the test
    3. Dropping all tables after test
    4. Closing connections
    """
    # Create test database engine with test URL
    test_engine = create_async_engine(TEST_DB_URL, echo=False)

    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup: drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for each test."""
    from sqlalchemy.ext.asyncio import AsyncSession as SA_AsyncSession
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker

    test_engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
    )
    async_session_factory = sessionmaker(
        test_engine, class_=SA_AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for API testing with database dependency override."""
    from httpx import ASGITransport

    from api.deps import get_async_db

    # Override the database dependency to use the test session
    async def override_get_async_db():
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_async_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    # Clean up override
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for authentication tests."""
    user = User(
        email="testuser@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_superuser(db_session: AsyncSession) -> User:
    """Create a test superuser for admin tests."""
    user = User(
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        hashed_password=hash_password("adminpassword123"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient, test_user: User) -> str:
    """Get JWT access token for test user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email_or_username": test_user.username,
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token: str) -> dict[str, str]:
    """Get authorization headers with JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, test_superuser: User) -> str:
    """Get JWT access token for admin user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email_or_username": test_superuser.username,
            "password": "adminpassword123",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def admin_headers(admin_token: str) -> dict[str, str]:
    """Get authorization headers with admin JWT token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture
async def test_product(test_user: User, db_session: AsyncSession):
    """Create a test product."""
    from products.models import Product, UserProduct

    product = Product(
        asin="B01TEST123",
        marketplace="com",
        title="Test Product",
        brand="Test Brand",
        category="Electronics",
        url="https://www.amazon.com/dp/B01TEST123",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Create user-product relationship
    user_product = UserProduct(
        user_id=test_user.id,
        product_id=product.id,
        is_active=True,
    )
    db_session.add(user_product)
    await db_session.commit()

    return product


@pytest_asyncio.fixture
async def test_product_uk(test_user: User, db_session: AsyncSession):
    """Create a test product from UK marketplace."""
    from products.models import Product, UserProduct

    product = Product(
        asin="B01TEST456",
        marketplace="co.uk",
        title="Test Product UK",
        brand="Test Brand UK",
        category="Books",
        url="https://www.amazon.co.uk/dp/B01TEST456",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    user_product = UserProduct(
        user_id=test_user.id,
        product_id=product.id,
        is_active=True,
    )
    db_session.add(user_product)
    await db_session.commit()

    return product


@pytest_asyncio.fixture
async def test_snapshot(test_product, db_session: AsyncSession):
    """Create a test product snapshot."""
    from products.models import ProductSnapshot

    snapshot = ProductSnapshot(
        product_id=test_product.id,
        price=29.99,
        currency="USD",
        in_stock=True,
        stock_status="In Stock",
        bsr_main_category=1500,
        main_category_name="Electronics",
        rating=4.5,
        review_count=250,
    )
    db_session.add(snapshot)
    await db_session.commit()
    await db_session.refresh(snapshot)
    return snapshot


@pytest_asyncio.fixture
async def test_notification(test_user: User, db_session: AsyncSession):
    """Create a test notification."""
    from notification.models import Notification

    notification = Notification(
        user_id=test_user.id,
        title="Test Notification",
        message="This is a test notification",
        notification_type="info",
        is_read=False,
    )
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)
    return notification


@pytest_asyncio.fixture
async def test_alert(test_product, test_user: User, db_session: AsyncSession):
    """Create a test alert."""
    from alert.models import Alert, AlertSeverity

    alert = Alert(
        product_id=test_product.id,
        user_id=test_user.id,
        alert_type="price_drop",
        severity=AlertSeverity.WARNING,
        title="Price Drop Alert",
        message="Product price has dropped below threshold",
        old_value="29.99",
        new_value="25.00",
        change_percentage=-16.66,
        is_read=False,
    )
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)
    return alert


@pytest.fixture
def mock_apify_response() -> dict[str, Any]:
    """Mock Apify API response for product scraping."""
    return {
        "asin": "B094WLFGD3",
        "title": "Echo Dot (4th Gen) | Smart speaker",
        "brand": "Amazon",
        "category": "Electronics > Smart Home",
        "price": 49.99,
        "currency": "USD",
        "availability": "In Stock",
        "rating": 4.7,
        "review_count": 50000,
        "sales_rank": 1,
        "sales_rank_category": "Amazon Devices & Accessories",
        "image_url": "https://m.media-amazon.com/images/I/test.jpg",
        "url": "https://www.amazon.com/dp/B094WLFGD3",
    }


@pytest.fixture
def mock_openai_response() -> dict[str, Any]:
    """Mock OpenAI API response for optimization suggestions."""
    return {
        "suggestions": [
            {
                "type": "title",
                "current": "Old Title",
                "suggested": "Optimized SEO Title with Keywords",
                "confidence": 0.85,
                "reasoning": "Include primary keywords",
            },
            {
                "type": "description",
                "current": "Basic description",
                "suggested": "Enhanced description with benefits and features",
                "confidence": 0.78,
                "reasoning": "Add value proposition",
            },
        ]
    }
