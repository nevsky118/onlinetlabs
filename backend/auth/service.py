import asyncio
from concurrent.futures import ThreadPoolExecutor

import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.exceptions import AccountMismatchError, UserAlreadyExistsError
from models.user import Account, User, UserRole

_bcrypt_executor = ThreadPoolExecutor(max_workers=4)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def hash_password_async(password: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _bcrypt_executor,
        lambda: bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
    )


def verify_password(password: str, hashed: str | None) -> bool:
    if hashed is None:
        return False
    return bcrypt.checkpw(password.encode(), hashed.encode())


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
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
    user = User(email=email, password_hash=password_hash, name=name, role=role.value)
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise UserAlreadyExistsError(email)
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: str) -> bool:
    user = await db.get(User, user_id)
    if user is None:
        return False
    await db.delete(user)
    await db.commit()
    return True


async def upsert_github_user(
    db: AsyncSession,
    email: str,
    name: str | None,
    image: str | None,
    provider_account_id: str,
) -> User:
    user = await get_user_by_email(db, email)

    if user is None:
        user = User(email=email, name=name, image=image, role=UserRole.STUDENT.value)
        user.accounts = []
        db.add(user)
        await db.flush()

    # Check if github account already linked
    existing_account = next(
        (a for a in user.accounts if a.provider == "github"),
        None,
    )

    if existing_account is not None:
        if existing_account.provider_account_id != provider_account_id:
            raise AccountMismatchError(
                email, existing_account.provider_account_id, provider_account_id
            )
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

    await db.commit()
    await db.refresh(user, ["accounts"])
    return user
