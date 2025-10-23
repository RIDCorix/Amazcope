import asyncio
from getpass import getpass

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from core.database import get_async_db_context
from core.security import hash_password
from pydantic_commands import command
from users.models import User as User


class CreateUserArgs(BaseModel):
    """Arguments for creating a new user."""

    username: str = Field(..., min_length=3, max_length=100, description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: str | None = Field(None, description="Full name (optional)")
    is_superuser: bool = Field(False, description="Create as superuser")


@command(
    name="create-user",
    help="Create a new user",
    arguments=CreateUserArgs,
)
def create_user(args: CreateUserArgs) -> None:
    """Create a new user in the system."""

    async def _create_user() -> None:
        # Check if user already exists
        async with get_async_db_context() as session:
            stmt = select(User).where(User.username == args.username)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            print(existing_user)
            if existing_user:
                print(f"❌ Error: User '{args.username}' already exists")
                return

            stmt = select(User).where(User.email == args.email)
            result = await session.execute(stmt)
            existing_email = result.scalar_one_or_none()
            if existing_email:
                print(f"❌ Error: Email '{args.email}' is already registered")
                return

            # Get password from user
            password = getpass("Enter password for the new user: ")
            if not password:
                print("❌ Error: Password cannot be empty")
                return

            confirm_password = getpass("Confirm password: ")
            if password != confirm_password:
                print("❌ Error: Passwords do not match")
                return

            # Hash password
            hashed_password = hash_password(password)

            user = User(
                username=args.username,
                email=args.email,
                full_name=args.full_name,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=args.is_superuser,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print("\n✅ Successfully created user!")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Full Name: {user.full_name or 'N/A'}")
            print(f"   Superuser: {'Yes' if user.is_superuser else 'No'}")
            print(f"   ID: {user.id}")

    # Run async function
    asyncio.run(_create_user())


class MarkSuperuserArgs(BaseModel):
    """Arguments for promoting a user to superuser."""

    username: str = Field(
        ..., min_length=3, max_length=100, description="Username of the user to promote"
    )


@command(
    name="mark-superuser",
    help="Promote an existing user to superuser",
    arguments=MarkSuperuserArgs,
)
def mark_superuser(args: MarkSuperuserArgs) -> None:
    """Promote an existing user to superuser."""

    async def _mark_superuser() -> None:
        async with get_async_db_context() as session:
            stmt = select(User).where(User.username == args.username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                print(f"❌ Error: User '{args.username}' not found")
                return

            if user.is_superuser:
                print(f"ℹ️  User '{args.username}' is already a superuser")
                return

            user.is_superuser = True
            await session.commit()
            print(f"\n✅ Successfully promoted user '{args.username}' to superuser!")

    # Run async function
    asyncio.run(_mark_superuser())
