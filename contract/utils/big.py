from near_sdk_py import view, callback


@view
def get_async(account_id: str):
    pass


@callback
def test_callback_fn(data: str):
    pass
