from near_sdk_py import call, view


@call
def set_other(account_id: str):
    return "Hello world"
