from near_sdk_py import call, view


@view
def get_greeting():
    pass


@call
def set_greeting(message: str):
    return "Hello world"
