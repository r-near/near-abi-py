# ruff: noqa
# mypy: ignore-errors
# This has a syntax error
from near_sdk_py import view

@view
def get_data() -> str
    return "Missing colon here"