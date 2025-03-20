from near_sdk_py import call, init, view


@view
def get_greeting() -> str:
    """Get the stored greeting"""
    return "Hello"


@call
def set_greeting(message: str) -> None:
    """Set the greeting"""
    pass


@init
def new() -> None:
    """Initialize the contract"""
    pass
