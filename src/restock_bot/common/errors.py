class DomainError(Exception):
    """Base class for domain-level errors."""


class RoomNotFound(DomainError):
    pass


class NoActiveSession(DomainError):
    pass


class NoTransactions(DomainError):
    pass
