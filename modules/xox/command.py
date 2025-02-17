__all__ = ()

from hata import Client

from .multi_player import xox_multi_player
from .single_player import xox_single_player


SLASH_CLIENT: Client


@SLASH_CLIENT.interactions(is_global = True)
async def xox(
    client,
    event,
    mode : ([('single-player', 'sg'), ('multi-player', 'mp')], 'Game mode') = 'sg',
):
    """The X-O-X game with buttons."""
    if mode == 'sg':
        coroutine_function = xox_single_player
    else:
        coroutine_function = xox_multi_player
    
    await coroutine_function(client, event)
