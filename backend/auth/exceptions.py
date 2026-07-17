class UserAlreadyExistsError(Exception):
    """Signals that a user with this email already exists in the DB."""

    def __init__(self, email: str) -> None:
        """Stores the conflicting email."""
        self.email = email
        super().__init__(f"User with email {email} already exists")
