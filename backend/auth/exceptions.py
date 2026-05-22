class UserAlreadyExistsError(Exception):
    """Сигнализирует, что пользователь с таким email уже есть в БД."""

    def __init__(self, email: str) -> None:
        """Сохраняет конфликтующий email."""
        self.email = email
        super().__init__(f"User with email {email} already exists")


class AccountMismatchError(Exception):
    """Сигнализирует, что email уже привязан к другому github-аккаунту."""

    def __init__(self, email: str, stored_id: str, incoming_id: str) -> None:
        """Сохраняет email, а также сохранённый и входящий идентификаторы аккаунта."""
        self.email = email
        self.stored_id = stored_id
        self.incoming_id = incoming_id
        super().__init__(
            f"GitHub account mismatch for {email}: stored={stored_id}, incoming={incoming_id}"
        )
