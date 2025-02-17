from .ban import *
from .helpers import *
from .kick import *
from .mute import *


__all__ = (
    *ban.__all__,
    *helpers.__all__,
    *kick.__all__,
    *mute.__all__,
)

# Construct command

from hata import Client

from .ban import ban_command
from .kick import kick_command
from .mute import mute_command

SLASH_CLIENT: Client


MAIN_COMMAND = SLASH_CLIENT.interactions(
    None,
    name = 'self-mod',
    description = 'Moderate yourself?!',
    allow_in_dm = False,
    is_global = True,
)

MAIN_COMMAND.interactions(ban_command, name = 'ban')
MAIN_COMMAND.interactions(kick_command, name = 'kick')
MAIN_COMMAND.interactions(mute_command, name = 'mute')
