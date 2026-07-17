class UserAlreadyExistsError(Exception):
    """Сигнализирует, что пользователь с таким email уже есть в БД."""

    def __init__(self, email: str) -> None:
        """Сохраняет конфликтующий email."""
        self.email = email
        super().__init__(f"User with email {email} already exists")
