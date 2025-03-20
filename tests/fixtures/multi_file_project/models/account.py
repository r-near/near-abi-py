from typing import Any, Dict

from near_sdk_py import view


@view
def get_account_detail(account_id: str) -> Dict[str, Any]:
    """Get detailed account information"""
    return {"id": account_id, "balance": "1000"}


@view
def get_account_history(account_id: str) -> list:
    """Get account transaction history"""
    return []
