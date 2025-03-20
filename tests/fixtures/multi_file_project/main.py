from near_sdk_py import init, view


@init
def new() -> None:
    """Initialize the contract"""
    pass


@view
def get_account_info(account_id: str):
    """Get account information"""
    from models.account import get_account_detail

    return get_account_detail(account_id)
