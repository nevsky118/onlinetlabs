class UserAlreadyExistsError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"User with email {email} already exists")


class AccountMismatchError(Exception):
    def __init__(self, email: str, stored_id: str, incoming_id: str) -> None:
        self.email = email
        self.stored_id = stored_id
        self.incoming_id = incoming_id
        super().__init__(
            f"GitHub account mismatch for {email}: stored={stored_id}, incoming={incoming_id}"
        )
