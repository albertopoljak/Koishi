from .ban import *
from .constants import *
from .helpers import *
from .is_banned import *
from .kick import *
from .mute import *
from .orin import *
from .regret_helpers import *
from .regret_un_ban import *
from .regret_un_kick import *
from .un_ban import *
from .un_mute import *


__all__ = (
    *ban.__all__,
    *constants.__all__,
    *helpers.__all__,
    *is_banned.__all__,
    *kick.__all__,
    *mute.__all__,
    *orin.__all__,
    *regret_helpers.__all__,
    *regret_un_ban.__all__,
    *regret_un_kick.__all__,
    *un_ban.__all__,
    *un_mute.__all__,
)

# Construct command

from hata import Client

from .ban import ban_command
from .is_banned import is_banned_command
from .kick import kick_command
from .mute import mute_command
from .regret_un_ban import regret_un_ban_command
from .regret_un_kick import regret_un_kick_command
from .un_ban import un_ban_command
from .un_mute import un_mute_command

SLASH_CLIENT: Client


MAIN_COMMAND = SLASH_CLIENT.interactions(
    None,
    name = 'mod',
    description = 'Moderate users.',
    allow_in_dm = False,
    is_global = True,
)

MAIN_COMMAND.interactions(ban_command, name = 'ban')
MAIN_COMMAND.interactions(is_banned_command, name = 'is-banned')
MAIN_COMMAND.interactions(kick_command, name = 'kick')
MAIN_COMMAND.interactions(mute_command, name = 'mute')
MAIN_COMMAND.interactions(regret_un_ban_command, name = 'regret-un-ban')
MAIN_COMMAND.interactions(regret_un_kick_command, name = 'regret-un-kick')
MAIN_COMMAND.interactions(un_ban_command, name = 'un-ban')
MAIN_COMMAND.interactions(un_mute_command, name = 'un-mute')
