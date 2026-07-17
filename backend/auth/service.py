import asyncio
from concurrent.futures import ThreadPoolExecutor

import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.exceptions import UserAlreadyExistsError
from models.user import Account, User, UserRole

_bcrypt_executor = ThreadPoolExecutor(max_workers=4)


async def hash_password_async(password: str) -> str:
    """Hashes password with bcrypt in a separate thread, without blocking the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _bcrypt_executor,
        lambda: bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
    )


async def verify_password_async(password: str, hashed: str | None) -> bool:
    """Verifies password with bcrypt in a separate thread, without blocking the event loop."""
    if hashed is None:
        return False
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _bcrypt_executor,
        lambda: bcrypt.checkpw(password.encode(), hashed.encode()),
    )


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Looks up a user by email along with their accounts. None if not found."""
    result = await db.execute(
        select(User).options(selectinload(User.accounts)).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password_hash: str,
    name: str | None = None,
    role: UserRole = UserRole.STUDENT,
) -> User:
    """Creates a user in the DB. Raises UserAlreadyExistsError on duplicate email."""
    # Credential registration (tests/internal path), active immediately. Real
    # users sign in via GitHub OAuth (upsert_github_user) and are created
    # inactive; an admin activates them in the admin panel.
    user = User(
        email=email, password_hash=password_hash, name=name, role=role.value, is_active=True
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise UserAlreadyExistsError(email)
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: str) -> bool:
    """Deletes a user by id. Returns False if it didn't exist."""
    user = await db.get(User, user_id)
    if user is None:
        return False
    await db.delete(user)
    return True


async def upsert_github_user(
    db: AsyncSession,
    email: str,
    name: str | None,
    image: str | None,
    provider_account_id: str,
) -> User:
    """Creates or updates a user from GitHub data and links the account.

    The identifier is the email confirmed by GitHub OAuth. The github account
    link is updated on change because better-auth in cookie mode sends an ephemeral
    user.id that changes on every fresh login.
    """
    user = await get_user_by_email(db, email)

    if user is None:
        user = User(email=email, name=name, image=image, role=UserRole.STUDENT.value)
        user.accounts = []
        db.add(user)
        await db.flush()

    # Link the github account, updating provider_account_id on change.
    existing_account = next(
        (a for a in user.accounts if a.provider == "github"),
        None,
    )

    if existing_account is not None:
        existing_account.provider_account_id = provider_account_id
    else:
        account = Account(
            user_id=user.id,
            type="oauth",
            provider="github",
            provider_account_id=provider_account_id,
        )
        db.add(account)

    # Update profile from GitHub
    if name:
        user.name = name
    if image:
        user.image = image

    await db.flush()
    await db.refresh(user, ["accounts"])
    return user
