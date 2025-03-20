from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Dict, List, Optional, TypedDict, Union

from near_sdk_py import call, view


class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class UserMetadata(TypedDict, total=False):
    display_name: str
    email: Optional[str]
    bio: str


@dataclass
class AccountSettings:
    theme: str
    notifications_enabled: bool = True
    language: Optional[str] = None


@view
def get_user_profile(user_id: str) -> UserMetadata:
    """Get a user profile by ID"""
    return {"display_name": "Test User"}


@view
def get_items_by_status(status: Status) -> List[str]:
    """Get items filtered by status"""
    return ["item1", "item2"]


@view
def get_settings(user_id: str) -> AccountSettings:
    """Get user settings"""
    return AccountSettings(theme="dark")


@call
def update_profile(
    user_id: str, profile: UserMetadata, priority: Priority = Priority.MEDIUM
) -> bool:
    """Update a user profile"""
    return True


@call
def batch_operation(
    items: List[str], options: Dict[str, Union[str, int, bool]]
) -> Dict[str, bool]:
    """Process multiple items at once"""
    return {item: True for item in items}
