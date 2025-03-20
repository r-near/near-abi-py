"""
Complex Types Test Contract for NEAR Python ABI generator

This contract demonstrates various complex Python type annotations
to test the new simplified ABI generator.
"""

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Set, Tuple, TypedDict, Union

# ------------ Enums ------------


class AssetType(str, Enum):
    """Type of digital asset"""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MODEL = "model"
    OTHER = "other"


class TokenStandard(IntEnum):
    """Token standard version"""

    NFT = 1
    MULTI_TOKEN = 2
    FUNGIBLE_TOKEN = 3


# ------------ TypedDict ------------


class AssetMetadata(TypedDict):
    """Metadata for an asset"""

    name: str
    description: str
    uri: Optional[str]


class TokenData(TypedDict):
    """Data for a token"""

    owner_id: str
    metadata: AssetMetadata
    royalty: Dict[str, float]


class SaleTerms(TypedDict, total=False):
    """Sale terms with optional fields"""

    price: str  # yoctoNEAR amount
    is_auction: bool
    min_bid: Optional[str]
    end_time: Optional[int]


# ------------ Dataclasses ------------


@dataclass
class RoyaltyInfo:
    """Royalty information for secondary sales"""

    percentage: float
    beneficiary: str


@dataclass
class CollectionStats:
    """Collection statistics"""

    total_supply: int = 0
    num_owners: int = 0
    floor_price: Optional[str] = None
    volume: str = "0"


# ------------ Contract Storage ------------

tokens: Dict[str, TokenData] = {}
collections: Dict[str, CollectionStats] = {}
royalties: Dict[str, RoyaltyInfo] = {}
sales: Dict[str, SaleTerms] = {}
supported_standards: List[TokenStandard] = [
    TokenStandard.NFT,
    TokenStandard.MULTI_TOKEN,
]


# ------------ Contract Methods ------------

# View methods


def view(func):
    """View method decorator"""
    func.__decorators__ = getattr(func, "__decorators__", []) + ["view"]
    return func


def call(func):
    """Call method decorator"""
    func.__decorators__ = getattr(func, "__decorators__", []) + ["call"]
    return func


@view
def get_token(token_id: str) -> Optional[TokenData]:
    """
    Get token data by ID.

    Args:
        token_id: The token's unique identifier

    Returns:
        The token data or None if not found
    """
    return tokens.get(token_id)


@view
def get_royalty(token_id: str) -> Optional[RoyaltyInfo]:
    """
    Get royalty information for a token.

    Args:
        token_id: The token's unique identifier

    Returns:
        Royalty information or None if not set
    """
    return royalties.get(token_id)


@view
def get_collection_stats(collection_id: str) -> CollectionStats:
    """
    Get collection statistics.

    Args:
        collection_id: The collection's identifier

    Returns:
        Collection statistics
    """
    return collections.get(collection_id, CollectionStats())


@view
def get_sale_info(token_id: str) -> Union[SaleTerms, None]:
    """
    Get sale information for a token.

    Args:
        token_id: The token's unique identifier

    Returns:
        Sale terms or None if not for sale
    """
    return sales.get(token_id)


@view
def get_supported_standards() -> List[TokenStandard]:
    """
    Get supported token standards.

    Returns:
        List of supported token standards
    """
    return supported_standards


@view
def get_asset_types() -> Dict[str, AssetType]:
    """
    Get mapping of asset type codes to full types.

    Returns:
        Dictionary of asset type codes to enum values
    """
    return {
        "img": AssetType.IMAGE,
        "vid": AssetType.VIDEO,
        "aud": AssetType.AUDIO,
        "3d": AssetType.MODEL,
        "other": AssetType.OTHER,
    }


@view
def get_asset_type_options() -> Tuple[str, ...]:
    """
    Get allowed asset type values as a tuple.

    Returns:
        Tuple of allowed asset type values
    """
    return tuple(t.value for t in AssetType)


@view
def get_owner_tokens(owner_id: str) -> Set[str]:
    """
    Get set of token IDs owned by an account.

    Args:
        owner_id: The owner's account ID

    Returns:
        Set of token IDs
    """
    return {
        token_id for token_id, data in tokens.items() if data["owner_id"] == owner_id
    }


# Call methods


@call
def mint_token(
    token_id: str,
    owner_id: str,
    metadata: AssetMetadata,
    asset_type: AssetType,
    royalty: Optional[RoyaltyInfo] = None,
) -> bool:
    """
    Mint a new token.

    Args:
        token_id: Unique token identifier
        owner_id: Token owner's account ID
        metadata: Token metadata
        asset_type: Type of digital asset
        royalty: Optional royalty information

    Returns:
        Success status
    """
    tokens[token_id] = {"owner_id": owner_id, "metadata": metadata, "royalty": {}}

    # Set royalty if provided
    if royalty:
        royalties[token_id] = royalty
        tokens[token_id]["royalty"] = {royalty.beneficiary: royalty.percentage / 100.0}

    return True


@call
def list_for_sale(token_id: str, terms: SaleTerms) -> bool:
    """
    List a token for sale.

    Args:
        token_id: Token ID to list for sale
        terms: Sale terms

    Returns:
        Success status
    """
    if token_id not in tokens:
        return False

    sales[token_id] = terms
    return True


@call
def update_collection_stats(collection_id: str, stats: CollectionStats) -> None:
    """
    Update collection statistics.

    Args:
        collection_id: Collection identifier
        stats: New statistics
    """
    collections[collection_id] = stats


@call
def batch_update(updates: List[Tuple[str, TokenData]]) -> Dict[str, bool]:
    """
    Batch update multiple tokens.

    Args:
        updates: List of (token_id, token_data) tuples

    Returns:
        Dictionary of token_id to success status
    """
    results = {}
    for token_id, data in updates:
        tokens[token_id] = data
        results[token_id] = True
    return results


@call
def complex_action(
    token_ids: Set[str],
    options: Dict[str, Union[int, str, bool]],
    priority: Optional[List[int]] = None,
) -> Dict[str, Union[bool, str]]:
    """
    Perform a complex action with mixed types.

    Args:
        token_ids: Set of token IDs to process
        options: Options for the action with various types
        priority: Optional priority list

    Returns:
        Results of the action
    """
    # This is just a demonstration of complex types
    results: Dict[str, Union[bool, str]] = {}
    for token_id in token_ids:
        results[token_id] = token_id in tokens

    return results
