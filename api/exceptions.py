class MyError(Exception):
    identifier: str

class NotFoundError(MyError):
    identifier = "NOT_FOUND"

class AlreadyExistsError(MyError):
    identifier = "ALREADY_EXISTS"

class UserSlotTakenError(MyError):
    identifier = "USER_SLOT_TAKEN"

class InvalidCredentials(MyError):
    identifier = "INVALID_CREDENTIALS"

class UsernameTooShort(MyError):
    identifier = "USERNAME_TOO_SHORT"

class UsernameTooLong(MyError):
    identifier = "USERNAME_TOO_LONG"

class PasswordTooShort(MyError):
    identifier = "PASSWORD_TOO_SHORT"

class PasswordTooLong(MyError):
    identifier = "PASSWORD_TOO_LONG"

class UsernameInvalidCharacters(MyError):
    identifier = "USERNAME_INVALID_CHARACTERS"

class NoSession(MyError):
    identifier = "UNAUTHENTICATED"

class CannotBeNamedAnonymous(MyError):
    identifier = "CANNOT_BE_NAMED_ANONYMOUS"

class Unauthorized(MyError):
    identifier = "UNAUTHORIZED"

class Unimplemented(MyError):
    identifier = "UNIMPLEMENTED"