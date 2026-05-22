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


def hash_password(password: str) -> str:
    """Хеширует пароль алгоритмом bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def hash_password_async(password: str) -> str:
    """Хеширует пароль bcrypt в отдельном потоке, не блокируя event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _bcrypt_executor,
        lambda: bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
    )


def verify_password(password: str, hashed: str | None) -> bool:
    """Проверяет пароль против хеша. Возвращает False, если хеша нет."""
    if hashed is None:
        return False
    return bcrypt.checkpw(password.encode(), hashed.encode())


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Ищет пользователя по email вместе с его аккаунтами. None, если не найден."""
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
    """Создаёт пользователя в БД. При дубле email бросает UserAlreadyExistsError."""
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
    """Удаляет пользователя по id. Возвращает False, если его не было."""
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
    """Создаёт или обновляет пользователя по данным из GitHub и привязывает аккаунт.

    Идентификатор это email, подтверждённый GitHub OAuth. Привязку github-аккаунта
    обновляем при изменении, потому что better-auth в cookie-режиме шлёт эфемерный
    user.id, меняющийся на каждый свежий логин.
    """
    user = await get_user_by_email(db, email)

    if user is None:
        user = User(email=email, name=name, image=image, role=UserRole.STUDENT.value)
        user.accounts = []
        db.add(user)
        await db.flush()

    # Привязываем github-аккаунт, обновляя provider_account_id при изменении.
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

    # Обновляем профиль из GitHub
    if name:
        user.name = name
    if image:
        user.image = image

    await db.commit()
    await db.refresh(user, ["accounts"])
    return user
