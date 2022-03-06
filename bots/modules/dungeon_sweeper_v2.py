import os
from zlib import compress, decompress
from json import load as from_json_file, dumps as to_json, loads as from_json
from math import ceil, floor
from scarletio import AsyncIO, Lock,  CancelledError, WaitTillAll, Task
from hata import Emoji, Embed, Color, DiscordException, BUILTIN_EMOJIS, ERROR_CODES, Client, KOKORO
from hata.ext.slash import abort, Row, Button, ButtonStyle, Timeouter

from sqlalchemy.sql import select

from bot_utils.models import DB_ENGINE, DS_V2_TABLE, ds_v2_model, user_common_model, USER_COMMON_TABLE, \
    ds_v2_result_model, DS_V2_RESULT_TABLE, get_create_common_user_expression
from bot_utils.constants import PATH__KOISHI

DUNGEON_SWEEPER_COLOR = Color(0xa000c4)
DUNGEON_SWEEPER_GAMES = {}
COLOR_TUTORIAL = Color(0xa000c4)
DIFFICULTY_COLORS = dict(enumerate((COLOR_TUTORIAL, Color(0x00cc03), Color(0xffe502), Color(0xe50016))))
DIFFICULTY_NAMES = dict(enumerate(('Tutorial', 'Easy', 'Normal', 'Hard',)))
CHAPTER_UNLOCK_DIFFICULTY = 1
CHAPTER_UNLOCK_STAGE = 9
CHAPTER_UNLOCK_DIFFICULTY_NAME = DIFFICULTY_NAMES[CHAPTER_UNLOCK_DIFFICULTY]
STAGE_STEP_MULTI_STEP_BUTTON = 10

EMOJI_KOISHI_WAVE = Emoji.precreate(648173118392762449)

GUI_TIMEOUT = 600.0
MAX_RENDER_EMOJI = 150

GUI_STATE_NONE = 0
GUI_STATE_READY = 1
GUI_STATE_EDITING = 2
GUI_STATE_CANCELLING = 3
GUI_STATE_CANCELLED = 4
GUI_STATE_SWITCHING_CONTEXT = 5

GUI_STATE_VALUE_TO_NAME = {
    GUI_STATE_READY: 'ready',
    GUI_STATE_EDITING: 'editing',
    GUI_STATE_CANCELLING: 'cancelling',
    GUI_STATE_CANCELLED: 'cancelled',
    GUI_STATE_SWITCHING_CONTEXT: 'switching context',
}

RUNNER_STATE_MENU = 1
RUNNER_STATE_PLAYING = 2
RUNNER_STATE_END_SCREEN = 3
RUNNER_STATE_CLOSED = 4

RUNNER_STATE_VALUE_TO_NAME = {
    RUNNER_STATE_MENU: 'menu',
    RUNNER_STATE_PLAYING: 'playing',
    RUNNER_STATE_END_SCREEN: 'end screen',
    RUNNER_STATE_CLOSED: 'closed',
}


FILE_LOCK            = Lock(KOKORO)
FILE_NAME            = 'ds_v2.json'
FILE_PATH            = os.path.join(PATH__KOISHI, 'library', FILE_NAME)

EMOJI_WEST           = BUILTIN_EMOJIS['arrow_left']
EMOJI_NORTH          = BUILTIN_EMOJIS['arrow_up']
EMOJI_SOUTH          = BUILTIN_EMOJIS['arrow_down']
EMOJI_EAST           = BUILTIN_EMOJIS['arrow_right']

EMOJI_BACK           = BUILTIN_EMOJIS['leftwards_arrow_with_hook']
EMOJI_RESET          = BUILTIN_EMOJIS['arrows_counterclockwise']
EMOJI_CANCEL         = BUILTIN_EMOJIS['x']

EMOJI_UP             = BUILTIN_EMOJIS['arrow_up_small']
EMOJI_DOWN           = BUILTIN_EMOJIS['arrow_down_small']
EMOJI_UP2            = BUILTIN_EMOJIS['arrow_double_up']
EMOJI_DOWN2          = BUILTIN_EMOJIS['arrow_double_down']
EMOJI_LEFT           = BUILTIN_EMOJIS['arrow_backward']
EMOJI_RIGHT          = BUILTIN_EMOJIS['arrow_forward']
EMOJI_SELECT         = BUILTIN_EMOJIS['ok']

EMOJI_NEXT           = BUILTIN_EMOJIS['arrow_right']
EMOJI_CLOSE          = BUILTIN_EMOJIS['x']
EMOJI_RESTART        = BUILTIN_EMOJIS['arrows_counterclockwise']

EMOJI_NOTHING        = Emoji.precreate(568838460434284574, name='0Q')

EMOJI_REIMU          = Emoji.precreate(574307645347856384, name='REIMU')
EMOJI_FLAN           = Emoji.precreate(575387120147890210, name='FLAN')
EMOJI_YUKARI         = Emoji.precreate(575389643424661505, name='YUKARI')

IDENTIFIER_UP        = '1'
IDENTIFIER_DOWN      = '2'
IDENTIFIER_UP2       = '3'
IDENTIFIER_DOWN2     = '4'
IDENTIFIER_RIGHT     = '5'
IDENTIFIER_LEFT      = '6'
IDENTIFIER_SELECT    = '7'

IDENTIFIER_WEST      = '8'
IDENTIFIER_NORTH     = '9'
IDENTIFIER_SOUTH     = 'A'
IDENTIFIER_EAST      = 'B'

IDENTIFIER_BACK      = 'C'
IDENTIFIER_RESET     = 'D'
IDENTIFIER_CANCEL    = 'E'

IDENTIFIER_NEXT      = 'F'
IDENTIFIER_CLOSE     = 'G'
IDENTIFIER_RESTART   = 'H'

IDENTIFIER_EMPTY_1   = 'I'
IDENTIFIER_EMPTY_2   = 'J'
IDENTIFIER_EMPTY_3   = 'K'
IDENTIFIER_EMPTY_4   = 'L'
IDENTIFIER_SKILL     = '0'


IDENTIFIERS = frozenset((
    IDENTIFIER_UP,
    IDENTIFIER_DOWN,
    IDENTIFIER_UP2,
    IDENTIFIER_DOWN2,
    IDENTIFIER_LEFT,
    IDENTIFIER_SELECT,
    IDENTIFIER_WEST,
    IDENTIFIER_NORTH,
    IDENTIFIER_SOUTH,
    IDENTIFIER_EAST,
    IDENTIFIER_BACK,
    IDENTIFIER_RESET,
    IDENTIFIER_CANCEL,
    IDENTIFIER_EMPTY_1,
    IDENTIFIER_EMPTY_2,
    IDENTIFIER_EMPTY_3,
    IDENTIFIER_EMPTY_4,
    IDENTIFIER_SKILL,
))

BIT_MASK_PASSABLE    = 0b0000000000000111

BIT_MASK_FLOOR       = 0b0000000000000001
BIT_MASK_TARGET      = 0b0000000000000010
BIT_MASK_HOLE_P      = 0b0000000000000011
BIT_MASK_OBJECT_P    = 0b0000000000000100


BIT_MASK_PUSHABLE    = 0b0000000000111000

BIT_MASK_BOX         = 0b0000000000001000
BIT_MASK_BOX_TARGET  = 0b0000000000010000
BIT_MASK_BOX_HOLE    = 0b0000000000011000
BIT_MASK_BOX_OBJECT  = 0b0000000000100000


BIT_MASK_SPECIAL     = 0b0000000011000000

BIT_MASK_HOLE_U      = 0b0000000001000000
BIT_MASK_OBJECT_U    = 0b0000000010000000


BIT_MASK_CHAR        = 0b0000011100000000
BIT_MASK_CHAR_N      = 0b0000010000000000
BIT_MASK_CHAR_E      = 0b0000010100000000
BIT_MASK_CHAR_S      = 0b0000011000000000
BIT_MASK_CHAR_W      = 0b0000011100000000

# BIT_MASK_CN_FLOOR    = 0b0000010000000001
# BIT_MASK_CE_FLOOR    = 0b0000010100000001
# BIT_MASK_CS_FLOOR    = 0b0000011000000001
# BIT_MASK_CW_FLOOR    = 0b0000011100000001
# 
# BIT_MASK_CN_TARGET   = 0b0000010000000010
# BIT_MASK_CE_TARGET   = 0b0000010100000010
# BIT_MASK_CS_TARGET   = 0b0000011000000010
# BIT_MASK_CW_TARGET   = 0b0000011100000010
# 
# BIT_MASK_CN_OBJECT_P = 0b0000010000000011
# BIT_MASK_CE_OBJECT_P = 0b0000010100000011
# BIT_MASK_CS_OBJECT_P = 0b0000011000000011
# BIT_MASK_CW_OBJECT_P = 0b0000011100000011
# 
# BIT_MASK_CN_HOLE_P   = 0b0000010000000100
# BIT_MASK_CE_HOLE_P   = 0b0000010100000100
# BIT_MASK_CS_HOLE_P   = 0b0000011000000100
# BIT_MASK_CW_HOLE_P   = 0b0000011100000100

BIT_MASK_WALL        = 0b1111100000000000

BIT_MASK_NOTHING     = 0b0000100000000000
BIT_MASK_WALL_N      = 0b0001000000000000
BIT_MASK_WALL_E      = 0b0010000000000000
BIT_MASK_WALL_S      = 0b0100000000000000
BIT_MASK_WALL_W      = 0b1000000000000000
# BIT_MASK_WALL_A      = 0b1111000000000000
# BIT_MASK_WALL_SE     = 0b0110000000000000
# BIT_MASK_WALL_SW     = 0b1100000000000000

BIT_MASK_UNPUSHABLE  = BIT_MASK_WALL | BIT_MASK_SPECIAL
BIT_MASK_BLOCKS_LOS  = BIT_MASK_WALL | BIT_MASK_PUSHABLE | BIT_MASK_OBJECT_U

STYLE_DEFAULT_PARTS = {
    BIT_MASK_NOTHING                    : EMOJI_NOTHING.as_emoji,
    BIT_MASK_WALL_E                     : Emoji.precreate(568838488464687169, name='0P').as_emoji,
    BIT_MASK_WALL_S                     : Emoji.precreate(568838546853462035, name='0N').as_emoji,
    BIT_MASK_WALL_W                     : Emoji.precreate(568838580278132746, name='0K').as_emoji,
    BIT_MASK_WALL_N | BIT_MASK_WALL_E | BIT_MASK_WALL_S | BIT_MASK_WALL_W:
                                          Emoji.precreate(578678249518006272, name='0X').as_emoji,
    BIT_MASK_WALL_E | BIT_MASK_WALL_S     : Emoji.precreate(568838557318250499, name='0M').as_emoji,
    BIT_MASK_WALL_S | BIT_MASK_WALL_W     : Emoji.precreate(568838569087598627, name='0L').as_emoji,
    BIT_MASK_WALL_N | BIT_MASK_WALL_E     : Emoji.precreate(574312331849498624, name='01').as_emoji,
    BIT_MASK_WALL_N | BIT_MASK_WALL_W     : Emoji.precreate(574312332453216256, name='00').as_emoji,
    BIT_MASK_WALL_N | BIT_MASK_WALL_E | BIT_MASK_WALL_S:
                                          Emoji.precreate(578648597621506048, name='0R').as_emoji,
    BIT_MASK_WALL_N | BIT_MASK_WALL_S | BIT_MASK_WALL_W:
                                          Emoji.precreate(578648597546139652, name='0S').as_emoji,
    BIT_MASK_WALL_N | BIT_MASK_WALL_S     : Emoji.precreate(578654051848421406, name='0T').as_emoji,
    BIT_MASK_WALL_E | BIT_MASK_WALL_W     : Emoji.precreate(578674409968238613, name='0U').as_emoji,
    BIT_MASK_WALL_N | BIT_MASK_WALL_E | BIT_MASK_WALL_W:
                                          Emoji.precreate(578676096829227027, name='0V').as_emoji,
    BIT_MASK_WALL_E | BIT_MASK_WALL_S | BIT_MASK_WALL_W:
                                          Emoji.precreate(578676650389274646, name='0W').as_emoji,
}

STYLE_REIMU = {**STYLE_DEFAULT_PARTS,
    BIT_MASK_WALL_N                     : Emoji.precreate(580141387631165450, name='0O').as_emoji,
    BIT_MASK_FLOOR                      : Emoji.precreate(574211101638656010, name='0H').as_emoji,
    BIT_MASK_TARGET                     : Emoji.precreate(574234087645249546, name='0A').as_emoji,
    BIT_MASK_OBJECT_P                   : EMOJI_NOTHING.as_emoji,
    BIT_MASK_HOLE_P                     : Emoji.precreate(574202754134835200, name='0I').as_emoji,
    BIT_MASK_BOX                        : Emoji.precreate(574212211434717214, name='0G').as_emoji,
    BIT_MASK_BOX_TARGET                 : Emoji.precreate(574213002190913536, name='0F').as_emoji,
    BIT_MASK_BOX_HOLE                   : Emoji.precreate(574212211434717214, name='0G').as_emoji,
    BIT_MASK_BOX_OBJECT                 : EMOJI_NOTHING.as_emoji,
    BIT_MASK_HOLE_U                     : Emoji.precreate(574187906642477066, name='0J').as_emoji,
    BIT_MASK_OBJECT_U                   : EMOJI_NOTHING.as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_FLOOR      : Emoji.precreate(574214258871500800, name='0D').as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_FLOOR      : Emoji.precreate(574213472347226114, name='0E').as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_FLOOR      : Emoji.precreate(574220751662612502, name='0B').as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_FLOOR      : Emoji.precreate(574218036156825629, name='0C').as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_TARGET     : Emoji.precreate(574249292496371732, name='04').as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_TARGET     : Emoji.precreate(574249292026478595, name='07').as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_TARGET     : Emoji.precreate(574249292261490690, name='06').as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_TARGET     : Emoji.precreate(574249292487720970, name='05').as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_HOLE_P     : Emoji.precreate(574249293662388264, name='02').as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_HOLE_P     : Emoji.precreate(574249291074240523, name='09').as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_HOLE_P     : Emoji.precreate(574249291145543681, name='08').as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_HOLE_P     : Emoji.precreate(574249292957614090, name='03').as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_OBJECT_P   : EMOJI_NOTHING.as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_OBJECT_P   : EMOJI_NOTHING.as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_OBJECT_P   : EMOJI_NOTHING.as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_OBJECT_P   : EMOJI_NOTHING.as_emoji,
}

STYLE_FLAN = {**STYLE_DEFAULT_PARTS,
    BIT_MASK_WALL_N                     : Emoji.precreate(580143707534262282, name='0X').as_emoji,
    BIT_MASK_FLOOR                      : Emoji.precreate(580150656501940245, name='0Y').as_emoji,
    BIT_MASK_TARGET                     : Emoji.precreate(580153111545511967, name='0b').as_emoji,
    BIT_MASK_OBJECT_P                   : Emoji.precreate(580163014045728818, name='0e').as_emoji,
    BIT_MASK_HOLE_P                     : Emoji.precreate(580159124466303001, name='0d').as_emoji,
    BIT_MASK_BOX                        : Emoji.precreate(580151963937931277, name='0a').as_emoji,
    BIT_MASK_BOX_TARGET                 : Emoji.precreate(580188214086598667, name='0f').as_emoji,
    BIT_MASK_BOX_HOLE                   : Emoji.precreate(580151963937931277, name='0a').as_emoji,
    BIT_MASK_BOX_OBJECT                 : Emoji.precreate(580151963937931277, name='0a').as_emoji,
    BIT_MASK_HOLE_U                     : Emoji.precreate(580156463888990218, name='0c').as_emoji,
    BIT_MASK_OBJECT_U                   : Emoji.precreate(580151385258065925, name='0Z').as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_FLOOR      : Emoji.precreate(580357693022142485, name='0g').as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_FLOOR      : Emoji.precreate(580357693093576714, name='0h').as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_FLOOR      : Emoji.precreate(580357693160685578, name='0i').as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_FLOOR      : Emoji.precreate(580357693152165900, name='0j').as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_TARGET     : Emoji.precreate(580357693018210305, name='0k').as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_TARGET     : Emoji.precreate(580357693085188109, name='0l').as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_TARGET     : Emoji.precreate(580357693181657089, name='0m').as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_TARGET     : Emoji.precreate(580357693361881089, name='0n').as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_HOLE_P     : Emoji.precreate(580357693324132352, name='0o').as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_HOLE_P     : Emoji.precreate(580357693072736257, name='0p').as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_HOLE_P     : Emoji.precreate(580357693131456513, name='0q').as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_HOLE_P     : Emoji.precreate(580357693366337536, name='0r').as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_OBJECT_P   : Emoji.precreate(580357693143777300, name='0s').as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_OBJECT_P   : Emoji.precreate(580357692711763973, name='0t').as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_OBJECT_P   : Emoji.precreate(580357693269606410, name='0u').as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_OBJECT_P   : Emoji.precreate(580357693387177984, name='0v').as_emoji,
}

STYLE_YUKARI = {**STYLE_DEFAULT_PARTS,
    BIT_MASK_WALL_N                     : Emoji.precreate(593179300270702593, name='0w').as_emoji,
    BIT_MASK_FLOOR                      : Emoji.precreate(593179300426022914, name='0x').as_emoji,
    BIT_MASK_TARGET                     : Emoji.precreate(593179300019306556, name='0y').as_emoji,
    BIT_MASK_OBJECT_P                   : EMOJI_NOTHING.as_emoji,
    BIT_MASK_HOLE_P                     : Emoji.precreate(593179300287479833, name='0z').as_emoji,
    BIT_MASK_BOX                        : Emoji.precreate(593179300296130561, name='10').as_emoji,
    BIT_MASK_BOX_TARGET                 : Emoji.precreate(593179300136615936, name='11').as_emoji,
    BIT_MASK_BOX_HOLE                   : Emoji.precreate(593179300149067790, name='12').as_emoji,
    BIT_MASK_BOX_OBJECT                 : EMOJI_NOTHING.as_emoji,
    BIT_MASK_HOLE_U                     : Emoji.precreate(593179300153262196, name='13').as_emoji,
    BIT_MASK_OBJECT_U                   : EMOJI_NOTHING.as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_FLOOR      : Emoji.precreate(593179300161650871, name='14').as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_FLOOR      : Emoji.precreate(593179300153262257, name='15').as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_FLOOR      : Emoji.precreate(593179300300324887, name='16').as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_FLOOR      : Emoji.precreate(593179300237410314, name='17').as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_TARGET     : Emoji.precreate(593179300207919125, name='18').as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_TARGET     : Emoji.precreate(593179300145135646, name='19').as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_TARGET     : Emoji.precreate(593179300170301451, name='1A').as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_TARGET     : Emoji.precreate(593179300153262189, name='1B').as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_HOLE_P     : Emoji.precreate(593179300199399531, name='1C').as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_HOLE_P     : Emoji.precreate(593179300300193800, name='1D').as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_HOLE_P     : Emoji.precreate(593179300216176760, name='1E').as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_HOLE_P     : Emoji.precreate(593179300153524224, name='1F').as_emoji,
    BIT_MASK_CHAR_N | BIT_MASK_OBJECT_P   : EMOJI_NOTHING.as_emoji,
    BIT_MASK_CHAR_E | BIT_MASK_OBJECT_P   : EMOJI_NOTHING.as_emoji,
    BIT_MASK_CHAR_S | BIT_MASK_OBJECT_P   : EMOJI_NOTHING.as_emoji,
    BIT_MASK_CHAR_W | BIT_MASK_OBJECT_P   : EMOJI_NOTHING.as_emoji,
}

RULES_HELP = Embed(
    'Rules of Dungeon sweeper',
    (
        f'Your quest is to help our cute Touhou characters to put their stuffs on places, where they supposed be. '
        f'These places are marked with an {BUILTIN_EMOJIS["x"]:e} on the floor. Because our characters are lazy, the '
        f'less steps required to sort their stuffs, makes them give you a better rating.\n'
        f'\n'
        f'You can move with the buttons under the embed, to activate your characters\' skill, or go back, reset the '
        f'map or cancel the game:\n'
        f'{EMOJI_NOTHING:e}{EMOJI_NORTH:e}{EMOJI_NOTHING:e}{EMOJI_BACK:e}\n'
        f'{EMOJI_WEST:e}{EMOJI_REIMU:e}{EMOJI_EAST:e}{EMOJI_RESET:e}\n'
        f'{EMOJI_NOTHING:e}{EMOJI_SOUTH:e}{EMOJI_NOTHING:e}{EMOJI_CANCEL:e}\n'
        f'\n'
        f'You can push boxes by moving towards them, but you cannot push more at the same time or push into the '
        f'wall:\n'
        f'{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_BOX]}{STYLE_REIMU[BIT_MASK_FLOOR]}'
        f'{EMOJI_EAST:e}'
        f'{STYLE_REIMU[BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_BOX]}'
        f'\n'
        f'You can push the boxes into the holes to pass them, but be careful, you might lose too much boxes to finish'
        f'the stages!\n'
        f'{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_BOX]}{STYLE_REIMU[BIT_MASK_HOLE_U]}'
        f'{EMOJI_EAST:e}{STYLE_REIMU[BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}'
        f'{STYLE_REIMU[BIT_MASK_HOLE_P]}{EMOJI_EAST:e}{STYLE_REIMU[BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_FLOOR]}'
        f'{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_HOLE_P]}\n'
        f'{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_BOX]}{STYLE_REIMU[BIT_MASK_HOLE_P]}'
        f'{EMOJI_EAST:e}{STYLE_REIMU[BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}'
        f'{STYLE_REIMU[BIT_MASK_BOX_HOLE]}\n'
        f'If you get a box on the it\'s desired place it\'s color will change:\n'
        f'{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_BOX]}{STYLE_REIMU[BIT_MASK_TARGET]}'
        f'{EMOJI_EAST:e}{STYLE_REIMU[BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}'
        f'{STYLE_REIMU[BIT_MASK_BOX_TARGET]}\n'
        f'The game has 3 chapters. *(there will be more maybe.)* Each chapter introduces a different character to '
        f'play with.'
    ),
    color = DUNGEON_SWEEPER_COLOR,
).add_field(
    f'Chapter 1 {EMOJI_REIMU:e}',
    (
        f'Your character is Hakurei Reimu (博麗　霊夢), who needs some help at her basement to sort her *boxes* out.\n'
        f'Reimu can jump over a box or hole.\n'
        f'{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_BOX]}{STYLE_REIMU[BIT_MASK_FLOOR]}'
        f'{EMOJI_EAST:e}{STYLE_REIMU[BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_BOX]}'
        f'{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}\n'
        f'{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]:}{STYLE_REIMU[BIT_MASK_HOLE_U]}{STYLE_REIMU[BIT_MASK_FLOOR]}'
        f'{EMOJI_EAST:e}{STYLE_REIMU[BIT_MASK_FLOOR]}{STYLE_REIMU[BIT_MASK_HOLE_U]}'
        f'{STYLE_REIMU[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}'
    ),
).add_field(
    f'Chapter 2 {EMOJI_FLAN:e}',
    (
        f'Your character is Scarlet Flandre (スカーレット・フランドール Sukaaretto Furandooru), who want to put her '
        f'*bookshelves* on their desired place.\n'
        f'Flandre can destroy absolutely anything and everything, and she will get rid of the pillars for you.\n'
        f'{STYLE_FLAN[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_FLAN[BIT_MASK_OBJECT_U]}{EMOJI_EAST:e}'
        f'{STYLE_FLAN[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_FLAN[BIT_MASK_OBJECT_P]}{EMOJI_EAST:e}'
        f'{STYLE_FLAN[BIT_MASK_FLOOR]}{STYLE_FLAN[BIT_MASK_CHAR_E | BIT_MASK_OBJECT_P]}\n'
        f'{STYLE_FLAN[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_FLAN[BIT_MASK_BOX]}{STYLE_FLAN[BIT_MASK_OBJECT_P]}'
        f'{EMOJI_EAST:e}{STYLE_FLAN[BIT_MASK_FLOOR]}{STYLE_FLAN[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}'
        f'{STYLE_FLAN[BIT_MASK_BOX_OBJECT]}'
    ),
).add_field(
    f'Chapter 3 {EMOJI_YUKARI:e}',
    (
        f'Your character is Yakumo Yukari (八雲　紫). Her beddings needs some replacing at her home.\n'
        f'Yukari can create gaps and travel trough them. She will open gap to the closest place straightforward, '
        f'which is separated by a bedding or with wall from her.\n'
        f'{STYLE_YUKARI[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_YUKARI[BIT_MASK_WALL_N]}{STYLE_YUKARI[BIT_MASK_WALL_N]}'
        f'{STYLE_YUKARI[BIT_MASK_FLOOR]}{EMOJI_EAST:e}{STYLE_YUKARI[BIT_MASK_FLOOR]}{STYLE_YUKARI[BIT_MASK_WALL_N]}'
        f'{STYLE_YUKARI[BIT_MASK_WALL_N]}{STYLE_YUKARI[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}\n'
        f'{STYLE_YUKARI[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}{STYLE_YUKARI[BIT_MASK_BOX]}{STYLE_YUKARI[BIT_MASK_BOX]}'
        f'{STYLE_YUKARI[BIT_MASK_FLOOR]}{EMOJI_EAST:e}{STYLE_YUKARI[BIT_MASK_FLOOR]}{STYLE_YUKARI[BIT_MASK_BOX]}'
        f'{STYLE_YUKARI[BIT_MASK_BOX]}{STYLE_YUKARI[BIT_MASK_CHAR_E | BIT_MASK_FLOOR]}'
    ),
).add_footer(
    'Game based on Sweeper of Suika.'
)

BUTTON_UP_ENABLED = Button(
    emoji = EMOJI_UP,
    custom_id = IDENTIFIER_UP,
    style = ButtonStyle.violet,
)

BUTTON_UP_DISABLED = BUTTON_UP_ENABLED.copy()
BUTTON_UP_DISABLED.enabled = False

BUTTON_DOWN_ENABLED = Button(
    emoji = EMOJI_DOWN,
    custom_id = IDENTIFIER_DOWN,
    style = ButtonStyle.violet,
)

BUTTON_DOWN_DISABLED = BUTTON_DOWN_ENABLED.copy()
BUTTON_DOWN_DISABLED.enabled = False

BUTTON_UP2_ENABLED = Button(
    emoji = EMOJI_UP2,
    custom_id = IDENTIFIER_UP2,
    style = ButtonStyle.violet,
)

BUTTON_UP2_DISABLED = BUTTON_UP2_ENABLED.copy()
BUTTON_UP2_DISABLED.enabled = False

BUTTON_DOWN2_ENABLED = Button(
    emoji = EMOJI_DOWN2,
    custom_id = IDENTIFIER_DOWN2,
    style = ButtonStyle.violet,
)

BUTTON_DOWN2_DISABLED = BUTTON_DOWN2_ENABLED.copy()
BUTTON_DOWN2_DISABLED.enabled = False

BUTTON_LEFT_ENABLED = Button(
    emoji = EMOJI_LEFT,
    custom_id = IDENTIFIER_LEFT,
    style = ButtonStyle.violet,
)

BUTTON_LEFT_DISABLED = BUTTON_LEFT_ENABLED.copy()
BUTTON_LEFT_DISABLED.enabled = False

BUTTON_RIGHT_ENABLED = Button(
    emoji = EMOJI_RIGHT,
    custom_id = IDENTIFIER_RIGHT,
    style = ButtonStyle.violet,
)

BUTTON_RIGHT_DISABLED = BUTTON_RIGHT_ENABLED.copy()
BUTTON_RIGHT_DISABLED.enabled = False

BUTTON_SELECT_ENABLED = Button(
    emoji = EMOJI_SELECT,
    custom_id = IDENTIFIER_SELECT,
    style = ButtonStyle.green,
)

BUTTON_SELECT_DISABLED = BUTTON_SELECT_ENABLED.copy()
BUTTON_SELECT_DISABLED.enabled = False

BUTTON_EMPTY_1 = Button(
    emoji = EMOJI_NOTHING,
    custom_id = IDENTIFIER_EMPTY_1,
    style = ButtonStyle.gray,
    enabled = False,
)

BUTTON_EMPTY_2 = BUTTON_EMPTY_1.copy_with(custom_id=IDENTIFIER_EMPTY_2)
BUTTON_EMPTY_3 = BUTTON_EMPTY_1.copy_with(custom_id=IDENTIFIER_EMPTY_3)
BUTTON_EMPTY_4 = BUTTON_EMPTY_1.copy_with(custom_id=IDENTIFIER_EMPTY_4)

BUTTON_SKILL_REIMU_ENABLED = Button(
    emoji = EMOJI_REIMU,
    custom_id = IDENTIFIER_SKILL,
    style = ButtonStyle.violet,
)

BUTTON_SKILL_REIMU_DISABLED = BUTTON_SKILL_REIMU_ENABLED.copy()
BUTTON_SKILL_REIMU_DISABLED.enabled = False

BUTTON_SKILL_REIMU_USED = BUTTON_SKILL_REIMU_DISABLED.copy()
BUTTON_SKILL_REIMU_USED.style = ButtonStyle.gray

BUTTON_SKILL_REIMU_ACTIVATED = BUTTON_SKILL_REIMU_ENABLED.copy()
BUTTON_SKILL_REIMU_ACTIVATED.style = ButtonStyle.green

BUTTON_SKILL_FLAN_ENABLED = BUTTON_SKILL_REIMU_ENABLED.copy()
BUTTON_SKILL_FLAN_ENABLED.emoji = EMOJI_FLAN

BUTTON_SKILL_FLAN_DISABLED = BUTTON_SKILL_FLAN_ENABLED.copy()
BUTTON_SKILL_FLAN_DISABLED.enabled = False

BUTTON_SKILL_FLAN_USED = BUTTON_SKILL_FLAN_DISABLED.copy()
BUTTON_SKILL_FLAN_USED.style = ButtonStyle.gray

BUTTON_SKILL_FLAN_ACTIVATED = BUTTON_SKILL_FLAN_ENABLED.copy()
BUTTON_SKILL_FLAN_ACTIVATED.style = ButtonStyle.green

BUTTON_SKILL_YUKARI_ENABLED = BUTTON_SKILL_REIMU_ENABLED.copy()
BUTTON_SKILL_YUKARI_ENABLED.emoji = EMOJI_YUKARI

BUTTON_SKILL_YUKARI_DISABLED = BUTTON_SKILL_YUKARI_ENABLED.copy()
BUTTON_SKILL_YUKARI_DISABLED.enabled = False

BUTTON_SKILL_YUKARI_USED = BUTTON_SKILL_YUKARI_DISABLED.copy()
BUTTON_SKILL_YUKARI_USED.style = ButtonStyle.gray

BUTTON_SKILL_YUKARI_ACTIVATED = BUTTON_SKILL_YUKARI_ENABLED.copy()
BUTTON_SKILL_YUKARI_ACTIVATED.style = ButtonStyle.green

BUTTON_WEST_ENABLED = Button(
    emoji = EMOJI_WEST,
    custom_id = IDENTIFIER_WEST,
    style = ButtonStyle.violet,
)

BUTTON_WEST_DISABLED = BUTTON_WEST_ENABLED.copy()
BUTTON_WEST_DISABLED.enabled = False

BUTTON_NORTH_ENABLED = Button(
    emoji = EMOJI_NORTH,
    custom_id = IDENTIFIER_NORTH,
    style = ButtonStyle.violet,
)

BUTTON_NORTH_DISABLED = BUTTON_NORTH_ENABLED.copy()
BUTTON_NORTH_DISABLED.enabled = False

BUTTON_SOUTH_ENABLED = Button(
    emoji = EMOJI_SOUTH,
    custom_id = IDENTIFIER_SOUTH,
    style = ButtonStyle.violet,
)

BUTTON_SOUTH_DISABLED = BUTTON_SOUTH_ENABLED.copy()
BUTTON_SOUTH_DISABLED.enabled = False

BUTTON_EAST_ENABLED = Button(
    emoji = EMOJI_EAST,
    custom_id = IDENTIFIER_EAST,
    style = ButtonStyle.violet,
)

BUTTON_EAST_DISABLED = BUTTON_EAST_ENABLED.copy()
BUTTON_EAST_DISABLED.enabled = False

BUTTON_BACK_ENABLED = Button(
    emoji = EMOJI_BACK,
    custom_id = IDENTIFIER_BACK,
    style = ButtonStyle.violet,
)

BUTTON_BACK_DISABLED = BUTTON_BACK_ENABLED.copy()
BUTTON_BACK_DISABLED.enabled = False

BUTTON_RESET_ENABLED = Button(
    emoji = EMOJI_RESET,
    custom_id = IDENTIFIER_RESET,
    style = ButtonStyle.violet,
)

BUTTON_RESET_DISABLED = BUTTON_RESET_ENABLED.copy()
BUTTON_RESET_DISABLED.enabled = False

BUTTON_CANCEL = Button(
    emoji = EMOJI_CANCEL,
    custom_id = IDENTIFIER_CANCEL,
    style = ButtonStyle.violet,
)

BUTTON_NEXT = Button(
    emoji = EMOJI_NEXT,
    custom_id = IDENTIFIER_NEXT,
    style = ButtonStyle.violet,
)

BUTTON_NEXT_DISABLED = BUTTON_NEXT.copy()
BUTTON_NEXT_DISABLED.enabled = False

BUTTON_CLOSE = Button(
    emoji = EMOJI_CLOSE,
    custom_id = IDENTIFIER_CLOSE,
    style = ButtonStyle.violet,
)

BUTTON_RESTART = Button(
    emoji = EMOJI_RESTART,
    custom_id = IDENTIFIER_RESTART,
    style = ButtonStyle.violet,
)


RATING_MAX = 5
RATINGS = ('S', 'A', 'B', 'C', 'D', 'E')
RATING_REWARDS = (750, 500, 400, 300, 200, 100)
NEW_RECORD_REWARD = 1000


def stage_source_sort_key(stage_source):
    """
    Sort key used when sorting stage sources based on their identifier.
    
    Parameters
    ----------
    stage_source : ``StageSource``
        The stage source to get sort key of.
    
    Returns
    -------
    identifier : `int`
        Sort key.
    """
    return stage_source.id


async def save_stage_sources():
    """
    Saves stage sources.
    
    This function is a coroutine.
    """
    async with FILE_LOCK:
        stage_sources = sorted(STAGES_BY_ID.values(), key=stage_source_sort_key)
        data = pretty_dump_stage_sources(stage_sources)
        with await AsyncIO(FILE_PATH, 'w') as file:
            await file.write(data)


def set_new_best(stage, steps):
    """
    Sets a new best value to the given stage.
    
    Parameters
    ----------
    stage : ``StageSource``
        The stage to modify it's best value.
    steps : `int`
        The stage's new best rating.
    """
    stage.best = steps
    Task(save_stage_sources(), KOKORO)


def get_rating_for(stage, steps):
    """
    Gets the rating for the given stage and step combination.
    
    Parameters
    ----------
    stage : ``StageSource``
        The stage to get the rating of.
    steps : `int`
        The user's step count.
    
    Returns
    -------
    rating : `str`
        The step's rating.
    """
    stage_best = stage.best
    rating_factor = floor(stage_best / 20.0) + 5.0
    
    rating_level = ceil((steps - stage_best) / rating_factor)
    if rating_level > RATING_MAX:
        rating_level = RATING_MAX
    
    return RATINGS[rating_level]


def get_reward_for_steps(stage_id, steps):
    """
    Gets reward amount for the given amount of steps.
    
    Parameters
    ----------
    stage_id : `int`
        The stage's identifier.
    steps : `int`
        The amount of steps.
    
    Returns
    -------
    reward : `str`
        The user's rewards.
    """
    stage = STAGES_BY_ID[stage_id]
    stage_best = stage.best
    
    if steps < stage_best:
        set_new_best(stage, steps)
        return NEW_RECORD_REWARD + RATING_REWARDS[0]
    
    rating_factor = floor(stage_best / 20.0) + 5.0
    
    rating_level = ceil((steps - stage_best) / rating_factor)
    if rating_level > RATING_MAX:
        rating_level = RATING_MAX
    
    return RATING_REWARDS[rating_level]


def get_reward_difference(stage_id, steps_1, steps_2):
    """
    Gets additional reward if a user received better result.
    
    Parameters
    ----------
    stage_id : `int`
        The stage's identifier.
    steps_1 : `int`
        The amount of steps.
    steps_2 : `int`
        The new amount of steps.
    
    Returns
    -------
    reward : `int`
        Extra hearts, what the respective user should get.
    """
    stage = STAGES_BY_ID[stage_id]
    stage_best = stage.best
    rating_factor = floor(stage_best / 20.0) + 5.0
    
    rating_level = ceil((steps_1 - stage_best) / rating_factor)
    if rating_level > RATING_MAX:
        rating_level = RATING_MAX
    
    reward_1 = RATING_REWARDS[rating_level]
    
    if steps_2 < stage_best:
        set_new_best(stage, steps_2)
        reward_2 = NEW_RECORD_REWARD + RATING_REWARDS[0]
    else:
        rating_level = ceil((steps_2 - stage_best) / rating_factor)
        if rating_level > RATING_MAX:
            rating_level = RATING_MAX
        
        reward_2 = RATING_REWARDS[rating_level]
    
    
    reward = reward_2 - reward_1
    if reward < 0:
        reward = 0
    
    return reward


class MoveDirectories:
    """
    Container class to store to which positions a character can move or use skill.
    
    Attributes
    ----------
    north : `bool`
        Whether the character can move or use skill in north directory.
    east : `bool`
        Whether the character can move or use skill in east directory.
    south : `bool`
        Whether the character can move or use skill in south directory.
    west : `bool`
        Whether the character can move or use skill in west directory.
    """
    __slots__ = ('north', 'east', 'south', 'west')

SKILL_DIRECTORY_DESCRIPTORS = (
    MoveDirectories.north.__set__,
    MoveDirectories.east.__set__,
    MoveDirectories.south.__set__,
    MoveDirectories.west.__set__,
)


def REIMU_SKILL_CAN_ACTIVATE(game_state):
    """
    Returns whether Reimu skill can be activated.
    
    Parameters
    ----------
    game_state : ``GameState``
        The respective game state.
    
    Returns
    -------
    can_active : `bool`
    """
    x_size = game_state.stage.x_size
    position = game_state.position
    map_ = game_state.map
    
    for step in ( -x_size, 1, x_size, -1):
        target_tile=map_[position + step]
        
        if not target_tile & (BIT_MASK_PUSHABLE | BIT_MASK_SPECIAL):
            continue
        
        after_tile = map_[position + (step << 1)]

        if not after_tile & BIT_MASK_PASSABLE:
            continue
        
        return True
    
    return False


def REIMU_SKILL_GET_DIRECTORIES(game_state):
    """
    Returns to which directories Reimu's skill could be used.
    
    Parameters
    ----------
    game_state : ``GameState``
        The respective game state.
    
    Returns
    -------
    move_directories : ``MoveDirectories``
    """
    x_size = game_state.stage.x_size
    position = game_state.position
    map_ = game_state.map
    
    move_directories = MoveDirectories()
    
    for step, descriptor in zip(( -x_size, 1, x_size, -1), SKILL_DIRECTORY_DESCRIPTORS):
        target_tile = map_[position + step]
        
        if target_tile & (BIT_MASK_PUSHABLE | BIT_MASK_SPECIAL):
            after_tile = map_[position + (step << 1)]
    
            if after_tile & BIT_MASK_PASSABLE:
                can_go_to_directory = True
            else:
                can_go_to_directory = False
        else:
            can_go_to_directory = False
        
        descriptor(move_directories, can_go_to_directory)
    
    return move_directories


def REIMU_SKILL_USE(game_state, step, align):
    """
    Uses Reimu's skill to the represented directory.
    
    Parameters
    ----------
    game_state : ``GameState``
        The respective game state.
    step : `int`
        Difference between 2 adjacent tile-s translated to 1 dimension based on the map's size.
    align : `int`
        The character's new align if the move is successful.
    
    Returns
    -------
    success : `bool`
        Whether the move was completed successfully.
    """
    map_ = game_state.map
    position = game_state.position
    
    target_tile = map_[position + step]
    
    if not target_tile & (BIT_MASK_PUSHABLE | BIT_MASK_SPECIAL):
        return False
    
    after_tile = map_[position + (step << 1)]
    
    if not after_tile & BIT_MASK_PASSABLE:
        return False
    
    actual_tile = map_[position]
    game_state.history.append(
        HistoryElement(position, True, ((position, actual_tile), (position + (step << 1), after_tile)))
    )
    
    map_[position] = actual_tile & BIT_MASK_PASSABLE
    game_state.position = position = position + (step << 1)
    
    map_[position] = after_tile | align
    game_state.has_skill = False
    
    return True


def FLAN_SKILL_CAN_ACTIVATE(game_state):
    """
    Returns whether Flandre skill can be activated.
    
    Parameters
    ----------
    game_state : ``GameState``
        The respective game state.
    
    Returns
    -------
    can_active : `bool`
    """
    x_size = game_state.stage.x_size
    position = game_state.position
    map_ = game_state.map
    
    for step in ( -x_size, 1, x_size, -1):
        target_tile = map_[position + step]
        
        if target_tile == BIT_MASK_OBJECT_U:
            return True
    
    return False


def FLAN_SKILL_GET_DIRECTORIES(game_state):
    """
    Returns to which directories Flandre's skill could be used.
    
    Parameters
    ----------
    game_state : ``GameState``
        The respective game state.
    
    Returns
    -------
    move_directories : ``MoveDirectories``
    """
    x_size = game_state.stage.x_size
    position = game_state.position
    map_ = game_state.map
    
    move_directories = MoveDirectories()
    
    for step, descriptor in zip(( -x_size, 1, x_size, -1), SKILL_DIRECTORY_DESCRIPTORS):
        target_tile = map_[position + step]
        if target_tile == BIT_MASK_OBJECT_U:
            can_go_to_directory = True
        else:
            can_go_to_directory = False
        
        descriptor(move_directories, can_go_to_directory)
    
    return move_directories


def FLAN_SKILL_USE(game_state, step, align):
    """
    Uses Flan's skill to the represented directory.
    
    Parameters
    ----------
    game_state : ``GameState``
        The respective game state.
    step : `int`
        Difference between 2 adjacent tile-s translated to 1 dimension based on the map's size.
    align : `int`
        The character's new align if the move is successful.
    
    Returns
    -------
    success : `bool`
        Whether the move was completed successfully.
    """
    map_ = game_state.map
    position = game_state.position
    
    target_tile = map_[position + step]
    
    if target_tile != BIT_MASK_OBJECT_U:
        return False
    
    actual_tile = map_[position]
    game_state.history.append(HistoryElement(position, True, ((position, actual_tile), (position + step, target_tile))))
    
    map_[position] = actual_tile & BIT_MASK_PASSABLE | align
    map_[position + step] = BIT_MASK_OBJECT_P
    game_state.has_skill = False
    
    return True


def YUKARI_SKILL_CAN_ACTIVATE(game_state):
    """
    Returns whether Yukari skill can be activated.
    
    Parameters
    ----------
    game_state : ``GameState``
        The respective game state.
    
    Returns
    -------
    can_active : `bool`
    """
    map_ = game_state.map
    
    x_size = game_state.stage.x_size
    y_size = len(map_) // x_size

    position = game_state.position
    y_position, x_position = divmod(position, x_size)

    # x_min = x_size*y_position
    # x_max = x_size*(y_position + 1)-1
    # y_min = x_position
    # y_max = x_position + (x_size*(y_size-1))
    
    for step, limit in (
            (-x_size , -x_size                       ,),
            (1       , x_size * (y_position + 1) - 1       ,),
            (x_size  , x_position + (x_size * (y_size - 1)),),
            ( -1      , x_size * y_position             ,),
     ):
        target_position = position + step
        if target_position == limit:
            continue
        
        if not map_[target_position]&BIT_MASK_BLOCKS_LOS:
            continue
        
        while True:
            target_position = target_position + step
            if target_position == limit:
                break
            
            target_tile = map_[target_position]
            if target_tile & BIT_MASK_BLOCKS_LOS:
                continue
            
            if target_tile & BIT_MASK_PASSABLE:
                return True
            
            break
    
    return False


def YUKARI_SKILL_GET_DIRECTORIES(game_state):
    """
    Returns to which directories Yukari's skill could be used.
    
    Parameters
    ----------
    game_state : ``GameState``
        The respective game state.
    
    Returns
    -------
    move_directories : ``MoveDirectories``
    """
    map_ = game_state.map
    
    x_size = game_state.stage.x_size
    y_size = len(map_) // x_size
    
    move_directories = MoveDirectories()
    
    position = game_state.position
    y_position, x_position = divmod(position, x_size)

    # x_min = x_size*y_position
    # x_max = x_size*(y_position + 1)-1
    # y_min = x_position
    # y_max = x_position + (x_size*(y_size-1))
    
    for (step, limit), descriptor in zip(
        (
            ( -x_size , -x_size                             ,),
            (1        , x_size * (y_position + 1) - 1       ,),
            (x_size   , x_position + (x_size * (y_size - 1)),),
            ( -1      , x_size * y_position                 ,),
        ),
        SKILL_DIRECTORY_DESCRIPTORS,
    ):
        
        target_position = position + step
        if target_position == limit:
            can_go_to_directory = False
        else:
            if map_[target_position]&BIT_MASK_BLOCKS_LOS:
                while True:
                    target_position = target_position + step
                    if target_position == limit:
                        can_go_to_directory = False
                        break
                    
                    target_tile = map_[target_position]
                    if target_tile & BIT_MASK_BLOCKS_LOS:
                        continue
                    
                    if target_tile & BIT_MASK_PASSABLE:
                        can_go_to_directory = True
                        break
                    
                    can_go_to_directory = False
                    break
            else:
                can_go_to_directory = False
        
        descriptor(move_directories, can_go_to_directory)
    
    return move_directories


def YUKARI_SKILL_USE(game_state, step, align):
    """
    Uses Yukari's skill to the represented directory.
    
    Parameters
    ----------
    game_state : ``GameState``
        The respective game state.
    step : `int`
        Difference between 2 adjacent tile-s translated to 1 dimension based on the map's size.
    align : `int`
        The character's new align if the move is successful.
    
    Returns
    -------
    success : `bool`
        Whether the move was completed successfully.
    """
    map_ = game_state.map

    x_size = game_state.stage.x_size
    y_size = len(map_) // x_size
    
    position = game_state.position
    y_position, x_position = divmod(position, x_size)

    if step > 0:
        if step == 1:
            limit = x_size * (y_position + 1) - 1
        else:
            limit = x_position + (x_size * (y_size - 1))
    else:
        if step == -1:
            limit = x_size * y_position
        else:
            limit = -x_size

    target_position = position + step
    
    if target_position == limit:
        return False
    
    if not map_[target_position]&BIT_MASK_BLOCKS_LOS:
        return False
    
    while True:
        target_position = target_position + step
        if target_position == limit:
            return False
        
        target_tile = map_[target_position]
        if target_tile & BIT_MASK_BLOCKS_LOS:
            continue
        
        if target_tile & BIT_MASK_PASSABLE:
            break
        
        return False
    
    actual_tile = map_[position]
    game_state.history.append(HistoryElement(position, True, ((position, actual_tile), (target_position, target_tile))))
    
    map_[position] = actual_tile & BIT_MASK_PASSABLE
    game_state.position = target_position
    
    map_[target_position] = target_tile | align
    game_state.has_skill = False
    
    return True


class HistoryElement:
    """
    An element of a ``GameState``'s history.
    
    Attributes
    ----------
    changes : `tuple` of (`tuple` (`int`, `int`), ...)
        A tuple containing each changed tile inside of a `position - tile` value pair.
    position : `int`
        The character's old position.
    was_skill : `bool`
        Whether the step was skill usage.
    """
    __slots__ = ('changes', 'position', 'was_skill')
    
    def __init__(self, position, was_skill, changes):
        """
        Creates a new ``HistoryElement`` from the given parameters.
        
        Parameters
        ----------
        position : `int`
            The character's old position.
        was_skill : `bool`
            Whether the step was skill usage.
        changes : `tuple` of (`tuple` (`int`, `int`), ...)
            A tuple containing each changed tile inside of a `position - tile` value pair.
        """
        self.position = position
        self.was_skill = was_skill
        self.changes = changes
    
    @classmethod
    def from_json(cls, data):
        """
        Creates a new history element from json data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Decoded json data.
        
        Returns
        -------
        self : ``HistoryElement``
        """
        self = object.__new__(cls)
        self.position = data[JSON_KEY_HISTORY_ELEMENT_POSITION]
        self.was_skill = data[JSON_KEY_HISTORY_ELEMENT_WAS_SKILL]
        self.changes = tuple(tuple(change) for change in data[JSON_KEY_HISTORY_ELEMENT_CHANGES])
        return self
    
    def to_json(self):
        """
        Converts the history element to json serializable data.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        return {
            JSON_KEY_HISTORY_ELEMENT_POSITION: self.position,
            JSON_KEY_HISTORY_ELEMENT_WAS_SKILL: self.was_skill,
            JSON_KEY_HISTORY_ELEMENT_CHANGES: self.changes,
        }


TILE_NAME_TO_VALUE = {
    'FLOOR'     : BIT_MASK_FLOOR,
    'TARGET'    : BIT_MASK_TARGET,
    'BOX'       : BIT_MASK_BOX,
    'BOX_TARGET': BIT_MASK_BOX_TARGET,
    'HOLE_U'    : BIT_MASK_HOLE_U,
    'HOLE_P'    : BIT_MASK_HOLE_P,
    'OBJECT_U'  : BIT_MASK_OBJECT_U,
    'CN_FLOOR'  : BIT_MASK_CHAR_N | BIT_MASK_FLOOR,
    'CE_FLOOR'  : BIT_MASK_CHAR_E | BIT_MASK_FLOOR,
    'CS_FLOOR'  : BIT_MASK_CHAR_S | BIT_MASK_FLOOR,
    'CW_FLOOR'  : BIT_MASK_CHAR_W | BIT_MASK_FLOOR,
    'NOTHING'   : BIT_MASK_NOTHING,
    'WALL_N'    : BIT_MASK_WALL_N,
    'WALL_E'    : BIT_MASK_WALL_E,
    'WALL_S'    : BIT_MASK_WALL_S,
    'WALL_W'    : BIT_MASK_WALL_W,
    'WALL_HV'   : BIT_MASK_WALL_N | BIT_MASK_WALL_E | BIT_MASK_WALL_S | BIT_MASK_WALL_W,
    'WALL_SE'   : BIT_MASK_WALL_E | BIT_MASK_WALL_S,
    'WALL_SW'   : BIT_MASK_WALL_S | BIT_MASK_WALL_W,
    'WALL_NE'   : BIT_MASK_WALL_N | BIT_MASK_WALL_E,
    'WALL_NW'   : BIT_MASK_WALL_N | BIT_MASK_WALL_W,
    'WALL_HE'   : BIT_MASK_WALL_N | BIT_MASK_WALL_E | BIT_MASK_WALL_S,
    'WALL_HW'   : BIT_MASK_WALL_N | BIT_MASK_WALL_S | BIT_MASK_WALL_W,
    'WALL_H'    : BIT_MASK_WALL_N | BIT_MASK_WALL_S,
    'CN_TARGET' : BIT_MASK_CHAR_N | BIT_MASK_TARGET,
    'CE_TARGET' : BIT_MASK_CHAR_E | BIT_MASK_TARGET,
    'CS_TARGET' : BIT_MASK_CHAR_S | BIT_MASK_TARGET,
    'CW_TARGET' : BIT_MASK_CHAR_W | BIT_MASK_TARGET,
    'WALL_V'    : BIT_MASK_WALL_E | BIT_MASK_WALL_W,
    'WALL_NV'   : BIT_MASK_WALL_E | BIT_MASK_WALL_S | BIT_MASK_WALL_W,
    'WALL_SV'   : BIT_MASK_WALL_N | BIT_MASK_WALL_E | BIT_MASK_WALL_W,
}

TILE_VALUE_TO_NAME = {value: key for key, value in TILE_NAME_TO_VALUE.items()}

JSON_KEY_STAGE_SOURCE_BEST = 'b'
JSON_KEY_STAGE_SOURCE_CHAPTER_INDEX = 'c'
JSON_KEY_STAGE_SOURCE_DIFFICULTY_INDEX = 'd'
JSON_KEY_STAGE_SOURCE_STAGE_INDEX = 's'
JSON_KEY_STAGE_SOURCE_ID = 'i'
JSON_KEY_STAGE_SOURCE_START = 'p'
JSON_KEY_STAGE_SOURCE_TARGET_COUNT = 't'
JSON_KEY_STAGE_SOURCE_MAP = 'm'
JSON_KEY_STAGE_SOURCE_X_SIZE = 'x'

JSON_KEY_HISTORY_ELEMENT_POSITION = '0'
JSON_KEY_HISTORY_ELEMENT_WAS_SKILL = '1'
JSON_KEY_HISTORY_ELEMENT_CHANGES = '2'

JSON_KEY_RUNNER_STATE_STAGE_ID = '0'
JSON_KEY_RUNNER_STATE_MAP = '1'
JSON_KEY_RUNNER_STATE_POSITION = '2'
JSON_KEY_RUNNER_STATE_HAS_SKILL = '3'
JSON_KEY_RUNNER_STATE_NEXT_SKILL = '4'
JSON_KEY_RUNNER_STATE_HISTORY = '5'
JSON_KEY_RUNNER_STATE_STAGE_BEST = '6'

STAGES_BY_ID = {}
STAGES_BY_ACCESS_ROUTE = {}


class StageSource:
    """
    A stage's source.
    
    Attributes
    ----------
    after_stage_source : `None`, ``StageSource``
        The next stage source.
    before_stage_source : `None`, ``StageSource``
        The before stage source.
    best : `int`
        The lowest amount of steps needed to solve the stage.
    chapter_index : `int`
        The index of the stage's chapter.
    difficulty_index : `int`
        The index of the stage's difficulty inside of it's chapter.
    id : `int`
        The identifier of the stage.
    index : `int`
        The local index of the stage.
    map : `list` of `int`
        The stage's map.
    stage_index : `int`
        The stage's index inside of it's difficulty.
    start : `int`
        The position, where the character starts on the stage.
    target_count : `int`
        The amount of targets on the map to fulfill.
    x_size : `int`
        The map's size on the x axis.
    """
    __slots__ = ('after_stage_source', 'before_stage_source', 'best', 'chapter_index', 'difficulty_index', 'id',
        'index', 'map', 'stage_index', 'start', 'target_count', 'x_size')
    
    @classmethod
    def from_json(cls, data):
        """
        Creates a new a ``StageSource`` from json data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Decoded json data.
        
        Returns
        -------
        self : ``StageSource``
        """
        chapter_index = data[JSON_KEY_STAGE_SOURCE_CHAPTER_INDEX]
        difficulty_index = data[JSON_KEY_STAGE_SOURCE_DIFFICULTY_INDEX]
        stage_index = data[JSON_KEY_STAGE_SOURCE_STAGE_INDEX]
        identifier = data[JSON_KEY_STAGE_SOURCE_ID]
        
        self = object.__new__(cls)
        
        self.best = data[JSON_KEY_STAGE_SOURCE_BEST]
        self.chapter_index = chapter_index
        self.difficulty_index = difficulty_index
        self.stage_index = stage_index
        self.id = identifier
        self.start = data[JSON_KEY_STAGE_SOURCE_START]
        self.target_count = data[JSON_KEY_STAGE_SOURCE_TARGET_COUNT]
        self.map = [TILE_NAME_TO_VALUE[tile_name] for tile_name in data[JSON_KEY_STAGE_SOURCE_MAP]]
        self.x_size = data[JSON_KEY_STAGE_SOURCE_X_SIZE]
        self.index = 0
        self.before_stage_source = None
        self.after_stage_source = None
        
        STAGES_BY_ID[identifier] = self
        STAGES_BY_ACCESS_ROUTE[(chapter_index, difficulty_index, stage_index)] = self
        
        return self
    
    @property
    def chapter(self):
        """
        Returns the stage source's chapter.
        
        Returns
        -------
        chapter : ``Chapter``
        """
        return CHAPTERS[self.chapter_index]
    
    def __repr__(self):
        """Returns the stage source's representation."""
        return f'<{self.__class__.__name__} id={self.id!r}>'


def pretty_dump_stage_sources(stage_sources):
    """
    Dumps the given stages into pretty json format.
    
    Parameters
    ----------
    stage_sources : `list` of ``StageSource``
        The stages to save.
    
    Returns
    -------
    json_data : `str`
    """
    json_parts = []
    
    json_parts.append('[\n')
    
    is_first = True
    
    for stage_source in stage_sources:
        if is_first:
            json_parts.append(' '*4)
            is_first = False
        else:
            json_parts.append(' ')
        
        json_parts.append('{')
        json_parts.append(' '*8)
        json_parts.append('\n')
        
        json_parts.append(' '*8)
        json_parts.append('"')
        json_parts.append(JSON_KEY_STAGE_SOURCE_CHAPTER_INDEX)
        json_parts.append('": ')
        json_parts.append(stage_source.chapter_index)
        json_parts.append(',\n')
        json_parts.append(' '*8)
        json_parts.append('"')
        json_parts.append(JSON_KEY_STAGE_SOURCE_DIFFICULTY_INDEX)
        json_parts.append('": ')
        json_parts.append(repr(stage_source.difficulty_index))
        json_parts.append(',\n')
        json_parts.append(' '*8)
        json_parts.append('"')
        json_parts.append(JSON_KEY_STAGE_SOURCE_STAGE_INDEX)
        json_parts.append('": ')
        json_parts.append(repr(stage_source.stage_index))
        json_parts.append(',\n')
        json_parts.append(' '*8)
        json_parts.append('"')
        json_parts.append(JSON_KEY_STAGE_SOURCE_ID)
        json_parts.append('": ')
        json_parts.append(repr(stage_source.id))
        json_parts.append(',\n')
        json_parts.append(' '*8)
        json_parts.append('"')
        json_parts.append(JSON_KEY_STAGE_SOURCE_START)
        json_parts.append('": ')
        json_parts.append(repr(stage_source.start))
        json_parts.append(',\n')
        json_parts.append(' '*8)
        json_parts.append('"')
        json_parts.append(JSON_KEY_STAGE_SOURCE_TARGET_COUNT)
        json_parts.append('": ')
        json_parts.append(repr(stage_source.target_count))
        json_parts.append(',\n')
        json_parts.append(' '*8)
        json_parts.append('"')
        json_parts.append(JSON_KEY_STAGE_SOURCE_X_SIZE)
        json_parts.append('": ')
        json_parts.append(repr(stage_source.x_size))
        json_parts.append(',\n')
        json_parts.append(' '*8)
        json_parts.append('"')
        json_parts.append(JSON_KEY_STAGE_SOURCE_BEST)
        json_parts.append('": ')
        json_parts.append(repr(999))
        json_parts.append(',\n')
        json_parts.append(' '*8)
        json_parts.append('"')
        json_parts.append(JSON_KEY_STAGE_SOURCE_MAP)
        json_parts.append('": [\n')
        
        map_ = stage_source.map
        map_.reverse()
        while map_:
            is_first_in_line = True
            for _ in range(stage_source.x_size):
                tile_value = map_.pop()
                tile_name = TILE_VALUE_TO_NAME[tile_value]
                
                if is_first_in_line:
                    is_first_in_line = False
                else:
                    json_parts.append(' ')
                
                json_parts.append('"')
                json_parts.append(tile_name)
                json_parts.append('"')
                json_parts.append(' '*(10 - len(tile_name)))
                json_parts.append(',')
            
            json_parts.append('\n')
        
        if (json_parts[-1] == '\n') and (json_parts[-2] == ','):
            del json_parts[-2]
        
        json_parts.append(' '*8)
        json_parts.append(']\n')
        json_parts.append(' '*4)
        json_parts.append('}')
        json_parts.append(',')
    
    if json_parts[-1] == ',':
        del json_parts[-1]
    
    json_parts.append('\n]\n')
    
    return ''.join(json_parts)

CHAPTER_REIMU_NAME = 'REIMU'
CHAPTER_FLAN_NAME = 'FLAN'
CHAPTER_YUKARI_NAME = 'YUKARI'

CHAPTER_REIMU_INDEX = 0
CHAPTER_FLAN_INDEX = 1
CHAPTER_YUKARI_INDEX = 2

CHAPTER_NAME_TO_INDEX = {
    CHAPTER_REIMU_NAME: CHAPTER_REIMU_INDEX,
    CHAPTER_FLAN_NAME: CHAPTER_FLAN_INDEX,
    CHAPTER_YUKARI_INDEX: CHAPTER_YUKARI_INDEX,
}

CHAPTERS = {}

class Chapter:
    """
    A chapter storing exact data about it's stages, skills and buttons.
    
    Attributes
    ----------
    button_skill_activated : ``ComponentButton``
        The skill button when the next move is a skill.
    button_skill_disabled : ``ComponentButton``
        The skill button, when the skill cannot be used.
    button_skill_enabled : ``ComponentButton``
        The skill button, when the skill can be used.
    button_skill_activated : ``ComponentButton``
        The skill button, when it was already used.
    difficulties : `dict` of (`int`, `dict` (`int`, ``StageSource``) items) items
        The difficulties of the chapter.
    emoji : ``Emoji``
        The chapter's character's emoji.
    id : `int`
        The chapter's identifier.
    skill_can_activate : `Function`
        Checks whether the chapter's character's skill can be activated.
        
        Accepts the following parameters.
        
        +---------------+---------------+
        | Name          | Type          |
        +===============+===============+
        | game_state    | ``GameState`` |
        +---------------+---------------+
        
        Should returns the following values.
        
        +---------------+---------------+
        | Name          | Type          |
        +===============+===============+
        | can_active    | `bool`        |
        +---------------+---------------+
    
    skill_get_move_directories : `Function`
        Checks whether the chapter's character's skill can be activated.
        
        Accepts the following parameters.
        
        +---------------+---------------+
        | Name          | Type          |
        +===============+===============+
        | game_state    | ``GameState`` |
        +---------------+---------------+
        
        Should returns the following values.
        
        +-------------------+-----------------------+
        | Name              | Type                  |
        +===================+=======================+
        | move_directories  | ``MoveDirectories``   |
        +-------------------+-----------------------+
    
    skill_use : `Function`
        Uses the skill of the chapter's character.
        
        Accepts the following parameters.
        
        +---------------+---------------+
        | Name          | Type          |
        +===============+===============+
        | game_state    | ``GameState`` |
        +---------------+---------------+
        | step          | `int`         |
        +---------------+---------------+
        | align         | `int`         |
        +---------------+---------------+
        
        Should returns the following values.
        
        +---------------+---------------+
        | Name          | Type          |
        +===============+===============+
        | success       | `bool`        |
        +---------------+---------------+
    
    stages_sorted : `list` of ``StageSource``
        The stages of the chapter in order.
    
    style : `dict` of (`int`, `str`) items
        The tiles of the stage based on the tile's value.
    next_stage_unlock_id : `int`
        The stage to complete for the next chapter.
    """
    __slots__ = ('button_skill_activated', 'button_skill_disabled', 'button_skill_enabled', 'button_skill_used',
        'difficulties', 'emoji', 'id', 'skill_can_activate', 'skill_get_move_directories', 'skill_use',
        'stages_sorted', 'style', 'next_stage_unlock_id', )
    
    def __init__(self, identifier, emoji, style, button_skill_enabled, button_skill_disabled, button_skill_used,
            button_skill_activated, skill_can_activate, skill_get_move_directories, skill_use):
        """
        Creates a new stage from the given parameters.
        
        Parameters
        ----------
        identifier : `int`
            The chapter's identifier.
        emoji : ``Emoji``
            The chapter's character's emoji.
        style : `dict` of (`int`, `str`) items
            The tiles of the stage based on the tile's value.
        button_skill_enabled : ``ComponentButton``
            The skill button, when the skill can be used.
        button_skill_disabled : ``ComponentButton``
            The skill button, when the skill cannot be used.
        button_skill_used : ``ComponentButton``
            The skill button, when it was already used.
        button_skill_activated : ``ComponentButton``
            The skill button when the next move is a skill.
        skill_can_activate : `Function`
            Checks whether the chapter's character's skill can be activated.
        skill_get_move_directories : `Function`
            Checks whether the chapter's character's skill can be activated.
        skill_use : `Function`
            Uses the skill of the chapter's character.
        """
        self.id = identifier
        self.difficulties = {}
        self.stages_sorted = []
        self.emoji = emoji
        self.style = style
        self.button_skill_enabled = button_skill_enabled
        self.button_skill_disabled = button_skill_disabled
        self.button_skill_used = button_skill_used
        self.button_skill_activated = button_skill_activated
        self.skill_can_activate = skill_can_activate
        self.skill_get_move_directories = skill_get_move_directories
        self.skill_use = skill_use
        self.next_stage_unlock_id = 0


CHAPTERS[CHAPTER_REIMU_INDEX] = Chapter(
    CHAPTER_REIMU_INDEX,
    EMOJI_REIMU,
    STYLE_REIMU,
    BUTTON_SKILL_REIMU_ENABLED,
    BUTTON_SKILL_REIMU_DISABLED,
    BUTTON_SKILL_REIMU_USED,
    BUTTON_SKILL_REIMU_ACTIVATED,
    REIMU_SKILL_CAN_ACTIVATE,
    REIMU_SKILL_GET_DIRECTORIES,
    REIMU_SKILL_USE,
)

CHAPTERS[CHAPTER_FLAN_INDEX] = Chapter(
    CHAPTER_FLAN_INDEX,
    EMOJI_FLAN,
    STYLE_FLAN,
    BUTTON_SKILL_FLAN_ENABLED,
    BUTTON_SKILL_FLAN_DISABLED,
    BUTTON_SKILL_FLAN_USED,
    BUTTON_SKILL_FLAN_ACTIVATED,
    FLAN_SKILL_CAN_ACTIVATE,
    FLAN_SKILL_GET_DIRECTORIES,
    FLAN_SKILL_USE,
)

CHAPTERS[CHAPTER_YUKARI_INDEX] = Chapter(
    CHAPTER_YUKARI_INDEX,
    EMOJI_YUKARI,
    STYLE_YUKARI,
    BUTTON_SKILL_YUKARI_ENABLED,
    BUTTON_SKILL_YUKARI_DISABLED,
    BUTTON_SKILL_YUKARI_USED,
    BUTTON_SKILL_YUKARI_ACTIVATED,
    YUKARI_SKILL_CAN_ACTIVATE,
    YUKARI_SKILL_GET_DIRECTORIES,
    YUKARI_SKILL_USE,
)


def load_stages():
    """
    Loads the stages and fills the chapters with them up.
    """
    with open(FILE_PATH, 'r') as file:
        stage_source_datas = from_json_file(file)
    
    stage_sources = []
    for stage_source_data in stage_source_datas:
        stage_source = StageSource.from_json(stage_source_data)
        stage_sources.append(stage_source)
    
    chapter_dictionaries = {}
    for stage_source in stage_sources:
        try:
            chapter_dictionary = chapter_dictionaries[stage_source.chapter_index]
        except KeyError:
            chapter_dictionary = chapter_dictionaries[stage_source.chapter_index] = {}
        
        try:
            difficulty_dictionary = chapter_dictionary[stage_source.difficulty_index]
        except KeyError:
            difficulty_dictionary = chapter_dictionary[stage_source.difficulty_index] = {}
        
        difficulty_dictionary[stage_source.stage_index] = stage_source
    
    sorted_chapters = []
    for expected_chapter_index, (chapter_index, chapter_dictionary) in enumerate(sorted(chapter_dictionaries.items())):
        if expected_chapter_index != chapter_index:
            raise RuntimeError(
                f'expected_chapter_index={expected_chapter_index!r} != '
                f'chapter_index={chapter_index!r})'
            )
        
        if chapter_index not in CHAPTERS:
            raise RuntimeError(
                f'chapter_index={chapter_index} not in '
                f'CHAPTERS={CHAPTERS}'
            )
        
        sorted_difficulty = []
        sorted_chapters.append(sorted_difficulty)
        
        for expected_difficulty_index, (difficulty_index, difficulty_dictionary) in \
                enumerate(sorted(chapter_dictionary.items())):
            
            if expected_difficulty_index != difficulty_index:
                raise RuntimeError(
                    f'expected_difficulty_index={expected_difficulty_index!r} != '
                    f'difficulty_index={difficulty_index!r})'
                )
                
            sorted_stages = []
            sorted_difficulty.append(sorted_stages)
            for expected_stage_index, (stage_index, stage) in enumerate(sorted(difficulty_dictionary.items())):
                if expected_difficulty_index != difficulty_index:
                    raise RuntimeError(
                        f'expected_stage_index={expected_stage_index!r} != '
                        f'stage_index={stage_index!r})'
                    )
                    
                sorted_stages.append(stage)
    
    for chapter_index, sorted_chapter in enumerate(sorted_chapters):
        chapter_dictionary = chapter_dictionaries[chapter_index]
        chapter = CHAPTERS[chapter_index]
        chapter.difficulties.update(chapter_dictionary)
        
        try:
            difficulty_dictionary = chapter_dictionary[CHAPTER_UNLOCK_DIFFICULTY]
        except KeyError:
            pass
        else:
            try:
                stage = difficulty_dictionary[CHAPTER_UNLOCK_STAGE]
            except KeyError:
                pass
            else:
                chapter.next_stage_unlock_id = stage.id
        
        chapter_stages_sorted = chapter.stages_sorted
        for sorted_difficulty in sorted_chapter:
            chapter_stages_sorted.extend(sorted_difficulty)
        
        chapter_stages_sorted_length = len(chapter_stages_sorted)
        if chapter_stages_sorted_length > 1:
            stage = chapter_stages_sorted[0]
            stage.after_stage_source = chapter_stages_sorted[1]
            stage.index = 0
            
            index = chapter_stages_sorted_length - 1
            stage = chapter_stages_sorted[index]
            stage.before_stage_source = chapter_stages_sorted[chapter_stages_sorted_length - 2]
            
            for index in range(1, chapter_stages_sorted_length - 1):
                stage = chapter_stages_sorted[index]
                stage.after_stage_source = chapter_stages_sorted[index + 1]
                stage.before_stage_source = chapter_stages_sorted[index - 1]
                stage.index = index

load_stages()


class StageResult:
    """
    Represents a user's state of a stage.
    
    Attributes
    ----------
    id : `int`
        The entry's identifier in the database.
    stage_id : `int`
        The stage's identifier.
    best : `int`
        The user's best solution of the stage.
    """
    __slots__ = ('best', 'id', 'stage_id')
    
    
    def __new__(cls, identifier, stage_id, best):
        """
        Creates a new stage state from the given parameters.
        
        Parameters
        ----------
        identifier : `int`
            The entry's identifier in the database.
        stage_id : `int`
            The stage's identifier.
        best : `int`
            The user's best solution of the stage.
        """
        self = object.__new__(cls)
        self.id = identifier
        self.stage_id = stage_id
        self.best = best
        return self
    
    
    @classmethod
    def from_entry(cls, entry):
        """
        Creates a new ``StageResult`` from the given entry.
        
        Parameters
        ----------
        entry : `sqlalchemy.???`
        
        Returns
        -------
        self : ``StageResult``
        """
        self = object.__new__(cls)
        self.id = entry.id
        self.stage_id = entry.stage_id
        self.best = entry.best
        return self
    
    def __repr__(self):
        """Returns the stage result's representation."""
        return f'<{self.__class__.__name__} id={self.id!r}, stage_id={self.stage_id!r}, best={self.best!r}>'


class UserState:
    """
    A user's state in dungeon sweeper.
    
    Attributes
    ----------
    entry_id : `int`
        The field identifier in the database.
    field_exists : `bool`
        Whether the field is stored in the database.
    game_state : `None`, ``GameState``
        The state of the actual game.
    selected_stage_id : `int`
        The selected stage's identifier.
    stage_results: `dict` of (`int`, ``StageResult``) items
        Result of each completed stage by the user.
    user_id : `int`
        The respective user's identifier.
    """
    __slots__ = ('entry_id', 'field_exists', 'game_state', 'selected_stage_id', 'stage_results', 'user_id')
    
    async def __new__(cls, user_id):
        """
        Creates a new ``UserState`` based on he given `user_id`.
        
        This method is a coroutine.
        
        Parameters
        ----------
        user_id : `int`
            The user' respective identifier.
        """
        async with DB_ENGINE.connect() as connector:
            response = await connector.execute(
                DS_V2_TABLE.select(
                    ds_v2_model.user_id == user_id,
                )
            )
            results = await response.fetchall()
            
            if results:
                result = results[0]
                game_state_data = result.game_state
                if (game_state_data is None):
                    game_state = None
                else:
                    game_state_json_data = from_json(decompress(game_state_data))
                    game_state = GameState.from_json(game_state_json_data)
                
                selected_stage_id = result.selected_stage_id
                field_exists = True
                entry_id = result.id
                
                response = await connector.execute(
                    DS_V2_RESULT_TABLE.select(
                        ds_v2_result_model.user_id == user_id,
                    )
                )
                
                results = await response.fetchall()
                
                stage_results = {}
                if results:
                    for result in results:
                        stage_result = StageResult.from_entry(result)
                        stage_results[stage_result.stage_id] = stage_result
                else:
                    selected_stage_id = CHAPTERS[0].difficulties[0][0].id
                
                if (entry_id is not None):
                    await connector.execute(
                        DS_V2_TABLE.update(
                            ds_v2_model.id == entry_id,
                        ).values(
                            game_state = None,
                        )
                    )
            
            else:
                game_state = None
                stage_results = {}
                selected_stage_id = CHAPTERS[0].difficulties[0][0].id
                field_exists = False
                entry_id = 0
        
        self = object.__new__(cls)
        self.game_state = game_state
        self.selected_stage_id = selected_stage_id
        self.field_exists = field_exists
        self.entry_id = entry_id
        self.stage_results = stage_results
        self.user_id = user_id
        return self
    
    
    def get_game_state_data(self):
        """
        Gets the user state's game state's data in json serializable from.
        
        Returns
        -------
        game_state_data : `None`, `dict`
        """
        game_state = self.game_state
        if (game_state is None) or (not game_state.history):
            game_state_data = None
        else:
            game_state_json_data = game_state.to_json()
            game_state_data = compress(to_json(game_state_json_data).encode())
        
        return game_state_data
    
    
    async def upload_game_state_on_init_failure(self):
        """
        Uploads only the game's state if applicable. Only called when exception occurs at initialization.
        
        This method is a coroutine.
        """
        if self.field_exists:
            game_state_data = self.get_game_state_data()
            if (game_state_data is not None):
                async with DB_ENGINE.connect() as connector:
                    await connector.execute(
                        DS_V2_TABLE.update(
                            ds_v2_model.id == self.entry_id
                        ).values(
                            game_state = game_state_data,
                        )
                    )
    
    
    
    async def upload(self):
        """
        Saves the current state of te game state.
        
        This method is a coroutine.
        """
        game_state_data = self.get_game_state_data()
        
        async with DB_ENGINE.connect() as connector:
            if self.field_exists:
                await connector.execute(
                    DS_V2_TABLE.update(
                        ds_v2_model.id == self.entry_id,
                    ).values(
                        game_state = game_state_data,
                        selected_stage_id = self.selected_stage_id,
                    )
                )
            else:
                response = await connector.execute(
                    DS_V2_TABLE.insert().values(
                        user_id = self.user_id,
                        game_state = game_state_data,
                        selected_stage_id = self.selected_stage_id,
                    ).returning(
                        ds_v2_model.id,
                    )
                )
                result = await response.fetchone()
                self.entry_id = result[0]
                self.field_exists = True
    
    
    async def set_best(self, stage_id, steps):
        """
        Updates the state of the given stage.
        
        This method is a coroutine.
        
        Parameters
        ----------
        stage_id : `int`
            The respective stage's identifier.
        steps : `int`
            The step count of the user.
        """
        if not self.field_exists:
            async with DB_ENGINE.connect() as connector:
                game_state_data = self.get_game_state_data()
                
                response = await connector.execute(
                    DS_V2_TABLE.insert().values(
                        user_id = self.user_id,
                        game_state = game_state_data,
                        selected_stage_id = self.selected_stage_id,
                    ).returning(
                        ds_v2_model.id,
                    )
                )
                
                result = await response.fetchone()
                self.entry_id = result[0]
                self.field_exists = True
        
        state_stage = self.stage_results.get(stage_id, None)
        if state_stage is None:
            self_best = -1
        else:
            self_best = state_stage.best
        
        if (self_best == -1) or (steps < self_best):
            async with DB_ENGINE.connect() as connector:
                if state_stage is None:
                    response = await connector.execute(
                        DS_V2_RESULT_TABLE.insert().values(
                            user_id = self.user_id,
                            stage_id = stage_id,
                            best = steps,
                        ).returning(
                            ds_v2_result_model.id,
                        )
                    )
                    
                    result = await response.fetchone()
                    entry_id = result[0]
                    self.stage_results[stage_id] = StageResult(entry_id, stage_id, steps)
                else:
                    await connector.execute(
                        DS_V2_RESULT_TABLE.update(
                            ds_v2_result_model.id == state_stage.id
                        ).values(
                            best = steps,
                        )
                    )
                    
                    state_stage.best = steps
                
                if state_stage is None:
                    reward = get_reward_for_steps(stage_id, steps)
                else:
                    reward = get_reward_difference(stage_id, self_best, steps)
                
                if reward:
                    response = await connector.execute(
                        select(
                            [
                                user_common_model.id,
                            ]
                        ).where(
                            user_common_model.user_id == self.user_id,
                        )
                    )
                    
                    results = await response.fetchall()
                    if results:
                        entry_id = results[0][0]
                        
                        to_execute = USER_COMMON_TABLE.update(
                            user_common_model.id == entry_id
                        ).values(
                            total_love = user_common_model.total_love + reward
                        )
                    else:
                        to_execute = get_create_common_user_expression(
                            self.user_id,
                            total_love = reward,
                        )
                    
                    await connector.execute(to_execute)



class GameState:
    """
    A user's actual game's state.
    
    Attributes
    ----------
    best : `int`
        The user's best solution for the stage. Set as `-1` by default.
    chapter : ``Chapter``
        The stage's chapter.
    has_skill : `bool`
        Whether the character' skill in the game was not yet used.
    history : `list` of ``HistoryElement``
        The done steps in the game.
    map : `list` of `int`
        The game's actual map.
    next_skill : `bool`
        Whether the next step is a skill usage.
    position : `int`
        The position of the selected stage.
    stage : ``StageSource``
        The represented stage.
    """
    __slots__ = ('best', 'chapter', 'has_skill', 'history', 'map', 'next_skill', 'position', 'stage',)
    
    def __init__(self, stage, best):
        """
        Creates a new game state instance from the given parameters.
        
        Parameters
        ----------
        stage : ``StageSource``
            The stage to execute by the game.
        best : `int`
            The user's best solution for the stage.
        """
        self.chapter = stage.chapter
        self.stage = stage
        self.map = stage.map.copy()
        self.position = stage.start
        self.history = []
        self.has_skill = True
        self.next_skill = False
        self.best = best
    
    
    def restart(self):
        """
        Restarts the game.
        """
        steps = len(self.history)
        
        best = self.best
        if (best == -1) or (steps < best):
            self.best = steps
        
        stage = self.stage
        self.stage = stage
        self.map = stage.map.copy()
        self.position = stage.start
        self.history.clear()
        self.has_skill = True
        self.next_skill = False
    
    
    @classmethod
    def from_json(cls, data):
        """
        Creates stage state from the given json data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Json data.
        
        Returns
        -------
        self : ``GameState``
        """
        self = object.__new__(cls)
        
        stage_id = data[JSON_KEY_RUNNER_STATE_STAGE_ID]
        
        stage = STAGES_BY_ID[stage_id]
        self.chapter = stage.chapter
        self.stage = stage
        
        self.best = data.get(JSON_KEY_RUNNER_STATE_STAGE_BEST, -1)
        
        try:
            map_ = data[JSON_KEY_RUNNER_STATE_MAP]
        except KeyError:
            map_ = stage.map.copy()
        
        self.map = map_
        
        try:
            position = data[JSON_KEY_RUNNER_STATE_POSITION]
        except KeyError:
            position = stage.start
        
        self.position = position
        
        self.has_skill = data.get(JSON_KEY_RUNNER_STATE_HAS_SKILL, True)
        self.next_skill = data.get(JSON_KEY_RUNNER_STATE_NEXT_SKILL, True)
        
        try:
            history_datas = data[JSON_KEY_RUNNER_STATE_HISTORY]
        except KeyError:
            history = []
        else:
            history = [HistoryElement.from_json(history_data) for history_data in history_datas]
        
        self.history = history
        return self
    
    
    def to_json(self):
        """
        Converts the stage state to json serializable data.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        data = {}
        stage = self.stage
        
        data[JSON_KEY_RUNNER_STATE_STAGE_ID] = stage.id
        
        best = self.best
        if best != -1:
            data[JSON_KEY_RUNNER_STATE_STAGE_BEST] = best
        
        if not self.has_skill:
            data[JSON_KEY_RUNNER_STATE_HAS_SKILL] = False
        
        if not self.next_skill:
            data[JSON_KEY_RUNNER_STATE_NEXT_SKILL] = False
        
        history = self.history
        if history:
            data[JSON_KEY_RUNNER_STATE_HISTORY] = [history_element.to_json() for history_element in history]
            data[JSON_KEY_RUNNER_STATE_POSITION] = self.position
            data[JSON_KEY_RUNNER_STATE_MAP] = self.map.copy()
        
        return data
    
    
    def done(self):
        """
        Returns whether all the targets on the stage are satisfied.
        
        Returns
        -------
        done : `bool`
        """
        target_count = self.stage.target_count
        for tile in self.map:
            if tile == BIT_MASK_BOX_TARGET:
                target_count -= 1
                
                if not target_count:
                    if (self.best == -1) or (self.best > len(self.history)):
                        self.best = len(self.history)
                    
                    return True
        
        return False
    
    
    def move_north(self):
        """
        Moves the character north.
        
        Returns
        -------
        moved : `bool`
            Whether the character move successfully.
        """
        return self.move( -self.stage.x_size, BIT_MASK_CHAR_N)
    
    
    def move_east(self):
        """
        Moves the character east.
        
        Returns
        -------
        moved : `bool`
            Whether the character move successfully.
        """
        return self.move(1, BIT_MASK_CHAR_E)
    
    
    def move_south(self):
        """
        Moves the character south.
        
        Returns
        -------
        moved : `bool`
            Whether the character move successfully.
        """
        return self.move(self.stage.x_size, BIT_MASK_CHAR_S)
    
    
    def move_west(self):
        """
        Moves the character west.
        
        Returns
        -------
        moved : `bool`
            Whether the character move successfully.
        """
        return self.move( -1, BIT_MASK_CHAR_W)
    
    
    def get_move_directories(self):
        """
        Returns to which directories the character can move.
        
        Returns
        -------
        move_directories : ``MoveDirectories``
        """
        if self.next_skill:
            return self.chapter.skill_get_move_directories(self)
        else:
            return self.get_own_move_directories()
    
    
    def get_own_move_directories(self):
        """
        Returns to which directories can the character move, excluding the skill of the character.
        
        Returns
        -------
        move_directories : ``MoveDirectories``
        """
        x_size = self.stage.x_size
        position = self.position
        map_ = self.map
        
        move_directories = MoveDirectories()
        
        for step, descriptor in zip(( -x_size, 1, x_size, -1), SKILL_DIRECTORY_DESCRIPTORS):
            target_tile = map_[position + step]
            
            if target_tile & BIT_MASK_UNPUSHABLE:
                can_go_to_directory = False
            elif target_tile & BIT_MASK_PASSABLE:
                can_go_to_directory = True
            else:
                after_tile = map_[position + (step << 1)]
                if target_tile & BIT_MASK_PUSHABLE and after_tile & (BIT_MASK_PASSABLE | BIT_MASK_HOLE_U):
                    can_go_to_directory = True
                else:
                    can_go_to_directory = False
            
            descriptor(move_directories, can_go_to_directory)
        
        return move_directories
    
    
    def move(self, step, align):
        """
        Moves the character to the given directory.
        
        Parameters
        ----------
        step : `int`
            Difference between 2 adjacent tile-s translated to 1 dimension based on the map's size.
        align : `int`
            The character's new align if the move is successful.
        
        Returns
        -------
        success : `bool`
            Whether the move was completed successfully.
        """
        if self.next_skill:
            result = self.chapter.skill_use(self, step, align)
            if result:
                self.next_skill = False
            
            return result
        
        map_ = self.map
        position = self.position
        
        actual_tile = map_[position]
        target_tile = map_[position + step]
        
        if target_tile & BIT_MASK_UNPUSHABLE:
            return False
        
        if target_tile & BIT_MASK_PASSABLE:
            self.history.append(
                HistoryElement(
                    position,
                    False,
                    (
                        (position, actual_tile),
                        (position + step, target_tile),
                    ),
                )
            )
            
            map_[position] = actual_tile & BIT_MASK_PASSABLE
            self.position = position = position + step
            map_[position] = target_tile | align
            
            return True

        after_tile = map_[position + (step << 1)]

        if target_tile & BIT_MASK_PUSHABLE and after_tile & (BIT_MASK_PASSABLE | BIT_MASK_HOLE_U):
            self.history.append(
                HistoryElement(
                    position,
                    False,
                    (
                        (position, actual_tile),
                        (position + step, target_tile),
                        (position + (step << 1), after_tile),
                    ),
                )
            )
            
            map_[position] = actual_tile & BIT_MASK_PASSABLE
            self.position = position = position + step
            map_[position] = (target_tile >> 3) | align
            if after_tile & BIT_MASK_PASSABLE:
                map_[position + step] = after_tile << 3
            else:
                map_[position + step] = BIT_MASK_HOLE_P
            return True
        
        return False
    
    def skill_can_activate(self):
        """
        Activates the character's skill if applicable.
        
        Returns
        -------
        success : `bool`
            Whether the skill was activated.
        """
        if not self.has_skill:
            return False
        
        if self.chapter.skill_can_activate(self):
            return True
        
        return False
    
    
    def skill_activate(self):
        """
        Activates (or deactivates) the character's skill.
        
        Returns
        -------
        success : `bool`
            Whether the skill could be (de)activated.
        """
        if not self.has_skill:
            return False
        
        if self.next_skill:
            self.next_skill = False
            return True
        
        if self.chapter.skill_can_activate(self):
            self.next_skill = True
            return True
        
        return False
    
    
    def button_skill_get(self):
        """
        Gets the actual button skill to show up.
        
        Returns
        -------
        button : `ComponentButton``
        """
        chapter = self.chapter
        if self.next_skill:
            button = chapter.button_skill_activated
        elif not self.has_skill:
            button = chapter.button_skill_used
        elif chapter.skill_can_activate(self):
            button = chapter.button_skill_enabled
        else:
            button = chapter.button_skill_disabled
        
        return button
    
    
    def render_description(self):
        """
        Renders the description of the game's embed.
        
        Returns
        -------
        description : `str`
        """
        style = self.chapter.style
        result = []
        map_ = self.map
        limit = len(map_)
        step = self.stage.x_size
        
        if limit <= MAX_RENDER_EMOJI:
            start = 0
            shift = 0
        else:
            step_count = limit // step
            if step_count < step:
                if (step_count * (step - 2)) <= MAX_RENDER_EMOJI:
                    start = 1
                    step -= 2
                    shift = 2
                else:
                    start = step + 1
                    limit -= step
                    step -= 2
                    shift = 2
            else:
                if ((step_count - 2) * step) <= MAX_RENDER_EMOJI:
                    start = step
                    limit -= step
                    shift = 0
                else:
                    start = step + 1
                    limit -= step
                    step -= 2
                    shift = 2
        
        while start < limit:
            end = start + step
            result.append(''.join([style[element] for element in map_[start:end]]))
            start = end + shift
        
        return '\n'.join(result)
    
    
    def render_playing(self):
        """
        Renders the game's embeds and components.
        
        Returns
        -------
        embed : ``Embed``
            The game's embed.
        components : `tuple` of ``Row`` of ``ComponentButton``
            The components of the game.
        """
        stage = self.stage
        difficulty_name = DIFFICULTY_NAMES.get(stage.difficulty_index, '???')
        title = (
            f'Chapter {stage.chapter_index + 1} {self.chapter.emoji.as_emoji}, {difficulty_name}: '
            f'{stage.stage_index + 1}'
        )
        
        description = self.render_description()
        color = DIFFICULTY_COLORS.get(stage.difficulty_index, DUNGEON_SWEEPER_COLOR)
        
        embed = Embed(title, description, color=color)
        
        steps = len(self.history)
        best = self.best
        if (best == -1):
            footer = f'steps : {steps}'
        else:
            footer = f'steps : {steps}, best : {best}'
        
        embed.add_footer(footer)
        
        button_skill = self.button_skill_get()
        
        directories = self.get_move_directories()
        
        if directories.west:
            button_west = BUTTON_WEST_ENABLED
        else:
            button_west = BUTTON_WEST_DISABLED
        
        if directories.north:
            button_north = BUTTON_NORTH_ENABLED
        else:
            button_north = BUTTON_NORTH_DISABLED
        
        if directories.south:
            button_south = BUTTON_SOUTH_ENABLED
        else:
            button_south = BUTTON_SOUTH_DISABLED
        
        if directories.east:
            button_east = BUTTON_EAST_ENABLED
        else:
            button_east = BUTTON_EAST_DISABLED
        
        if self.can_back_or_reset():
            button_back = BUTTON_BACK_ENABLED
            button_reset = BUTTON_RESET_ENABLED
        else:
            button_back = BUTTON_BACK_DISABLED
            button_reset = BUTTON_RESET_DISABLED
        
        components = (
            Row(BUTTON_EMPTY_1 , button_north , BUTTON_EMPTY_2 , button_back   ,),
            Row(button_west    , button_skill , button_east    , button_reset  ,),
            Row(BUTTON_EMPTY_3 , button_south , BUTTON_EMPTY_4 , BUTTON_CANCEL ,),
        )
        
        return embed, components
    
    
    def render_end_screen(self):
        """
        Renders the game's end-game screen and components.
        
        Returns
        -------
        embed : ``Embed``
            The game's embed.
        components : `tuple` of ``Row`` of ``ComponentButton``
            The components of the game.
        """
        stage = self.stage
        steps = len(self.history)
        rating = get_rating_for(self.stage, steps)
        
        best = self.best
        if (best == -1) or (best > steps):
            best = steps
        
        difficulty_name = DIFFICULTY_NAMES.get(stage.difficulty_index, '???')
        title = (
            f'Chapter {stage.chapter_index + 1} {self.chapter.emoji.as_emoji} {difficulty_name} '
            f'{stage.stage_index + 1} finished with {steps} steps with {rating} rating!'
        )
        
        description = self.render_description()
        color = DIFFICULTY_COLORS.get(stage.difficulty_index, DUNGEON_SWEEPER_COLOR)
        
        embed = Embed(title, description, color=color).add_footer(f'steps : {steps}, best : {best}')
        
        if self.stage.after_stage_source is None:
            button_next = BUTTON_NEXT_DISABLED
        else:
            button_next = BUTTON_NEXT
        
        components = (
            Row(BUTTON_CLOSE , BUTTON_RESTART , button_next ,),
        )
        
        return embed, components
    
    
    def can_back_or_reset(self):
        """
        Returns whether the character can go back, or resetting the game is available.
        
        Returns
        -------
        can_back_or_reset : `bool`
        """
        if self.next_skill:
            return True
        
        if self.history:
            return True
        
        return False
    
    
    def back(self):
        """
        Goes back one step.
        
        Returns
        -------
        success : `bool`
            Whether the character could go back one step.
        """
        if self.next_skill:
            self.next_skill = False
            return True
        
        history = self.history
        if not history:
            return False
        
        element = history.pop( -1)
        map_ = self.map
        self.position = element.position
        
        for position, value in element.changes:
            map_[position] = value
        
        if element.was_skill:
            self.has_skill = True
        
        return True
    
    
    def reset(self):
        """
        Resets the game.
        
        Returns
        -------
        success : `bool`
            Whether the map was reset.
        """
        history = self.history
        if not history:
            return False
        
        history.clear()
        
        self.position = self.stage.start
        self.map = self.stage.map.copy()
        self.has_skill = True
        
        return True


def can_play_selected_stage(user_state):
    """
    Returns whether the user can play the selected chapter.
    
    Returns
    -------
    user_state : ``UserState``
        The respective user state.
    
    Returns
    -------
    can_play_selected_stage : `bool`
        Whether the selected chapter can be played.
    """
    selected_stage_id = user_state.selected_stage_id
    try:
        stage = STAGES_BY_ID[selected_stage_id]
    except KeyError:
        stage = STAGES_BY_ACCESS_ROUTE[(CHAPTER_REIMU_INDEX, 0, 0)]
        user_state.selected_stage_id = stage.id
        return True
    
    if stage.chapter_index == CHAPTER_REIMU_INDEX:
        return True
    
    stage_results = user_state.stage_results
    
    if stage.id in stage_results:
        return True
    
    stage_index = stage.stage_index
    difficulty_index = stage.difficulty_index
    chapter_index = stage.chapter_index
    
    if stage_index:
        stage_index -= 1
    
    else:
        if difficulty_index:
            difficulty_index -= 1
        else:
            if chapter_index:
                if CHAPTERS[chapter_index - 1].next_stage_unlock_id in stage_results:
                    return True
                else:
                    return False
            else:
                return True
    
    if stage.chapter.difficulties[difficulty_index][stage_index].id in stage_results:
        return True
    
    return False


def get_selectable_stages(user_state):
    """
    Parameters
    ----------
    user_state : ``UserState``
        The respective user state.
    
    Returns
    -------
    selectable_stages : `list` of (``StageSource``, `int`, `bool`)
        The selectable stages in a list of tuples. Contains 3 elements: `stage` , `best`, `is_selected`.
    """
    try:
        selected_stage = STAGES_BY_ID[user_state.selected_stage_id]
    except KeyError:
        selected_stage = STAGES_BY_ACCESS_ROUTE[(CHAPTER_REIMU_INDEX, 0, 0)]
        user_state.selected_stage_id = selected_stage.id
    
    stages = []
    
    stage_source = selected_stage
    for times in range(3):
        stage_source = stage_source.before_stage_source
        if stage_source is None:
            break
        
        stages.append(stage_source)
        continue
    
    stages.reverse()
    stages.append(selected_stage)
    
    stage_source = selected_stage
    for times in range(3):
        stage_source = stage_source.after_stage_source
        if stage_source is None:
            break
        
        stages.append(stage_source)
        continue
    
    selectable_stages = []
    stage_results = user_state.stage_results
    
    for stage in stages:
        if stage is selected_stage:
            is_selected = True
        else:
            is_selected = False
        
        stage_id = stage.id
        
        try:
            stage_result = stage_results[stage_id]
        except KeyError:
            user_best = -1
        else:
            user_best = stage_result.best
        
        selectable_stages.append((stage, user_best, is_selected))
        
        if user_best == -1:
            break
    
    selectable_stages.reverse()
    
    return selectable_stages


def render_menu(user_state):
    """
    Renders the user state's menu's embeds and components.
    
    Parameters
    ----------
    user_state : ``UserState``
        The respective user state.
    
    Returns
    -------
    embed : ``Embed``
        The menu's embed.
    components : `tuple` of ``Row`` of ``ComponentButton``
        The components of the menu.
    """
    try:
        stage = STAGES_BY_ID[user_state.selected_stage_id]
    except KeyError:
        # something went wrong
        chapter = CHAPTERS[CHAPTER_REIMU_INDEX]
        user_state.selected_stage_id = STAGES_BY_ACCESS_ROUTE[(CHAPTER_REIMU_INDEX, 0, 0)].id
    else:
        chapter = stage.chapter
    
    embed = Embed(f'Chapter {chapter.id + 1}').add_thumbnail(chapter.emoji.url)
    
    if can_play_selected_stage(user_state):
        get_selectable = get_selectable_stages(user_state)
        color = DIFFICULTY_COLORS[0]
        
        for stage, best, is_selected in get_selectable:
            difficulty_name = DIFFICULTY_NAMES.get(stage.difficulty_index, '???')
            field_name = f'{difficulty_name} level {stage.stage_index + 1}'
            if best == -1:
                field_value = 'No results recorded yet!'
            else:
                rating = get_rating_for(stage, best)
                field_value = f'rating {rating}; steps : {best}'
            
            if is_selected:
                field_name = f'**{field_name} <--**'
                field_value = f'**{field_value}**'
                color = DIFFICULTY_COLORS.get(stage.difficulty_index, DUNGEON_SWEEPER_COLOR)
            
            embed.add_field(field_name, field_value)
        
        embed.color = color
        
        if get_selectable[0][2]:
            button_stage_after = BUTTON_UP_DISABLED
            button_stage_after2 = BUTTON_UP2_DISABLED
        else:
            button_stage_after = BUTTON_UP_ENABLED
            button_stage_after2 = BUTTON_UP2_ENABLED
        
        if get_selectable[-1][2]:
            button_stage_before = BUTTON_DOWN_DISABLED
            button_stage_before2 = BUTTON_DOWN2_DISABLED
        else:
            button_stage_before = BUTTON_DOWN_ENABLED
            button_stage_before2 = BUTTON_DOWN2_ENABLED
        
        button_select = BUTTON_SELECT_ENABLED
    else:
        embed.color = COLOR_TUTORIAL
        embed.description = (
            f'**You must finish chapter {chapter.id} {CHAPTER_UNLOCK_DIFFICULTY_NAME} '
            f'{CHAPTER_UNLOCK_STAGE + 1} first.**'
        )
        
        button_stage_before = BUTTON_DOWN_DISABLED
        button_stage_before2 = BUTTON_DOWN2_DISABLED
        
        button_stage_after = BUTTON_UP_DISABLED
        button_stage_after2 = BUTTON_UP2_DISABLED
        
        button_select = BUTTON_SELECT_DISABLED
    
    if chapter.id + 1 in CHAPTERS:
        button_chapter_next = BUTTON_RIGHT_ENABLED
    else:
        button_chapter_next = BUTTON_RIGHT_DISABLED
    
    if chapter.id == 0:
        button_chapter_before = BUTTON_LEFT_DISABLED
    else:
        button_chapter_before = BUTTON_LEFT_ENABLED
    
    components = (
        Row(BUTTON_EMPTY_1        , button_stage_after     , button_stage_after2   , BUTTON_EMPTY_2      ,),
        Row(button_chapter_before , button_select          , BUTTON_CLOSE          , button_chapter_next ,),
        Row(BUTTON_EMPTY_3        , button_stage_before    , button_stage_before2  , BUTTON_EMPTY_4      ,),
    )
    
    return embed, components


async def process_identifier_up(dungeon_sweeper_runner):
    """
    Processes `up` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `up` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_MENU:
        user_state = dungeon_sweeper_runner.user_state
        
        selected_stage_id = user_state.selected_stage_id
        if selected_stage_id not in user_state.stage_results:
            return False
        
        selected_stage = STAGES_BY_ID[selected_stage_id]
        selected_stage = selected_stage.after_stage_source
        if selected_stage is None:
            return False
        
        user_state.selected_stage_id = selected_stage.id
        return True
    
    return False


async def process_identifier_up2(dungeon_sweeper_runner):
    """
    Processes `up2` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `up2` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_MENU:
        user_state = dungeon_sweeper_runner.user_state
        
        selected_stage_id = user_state.selected_stage_id
        stage_results = user_state.stage_results
        if selected_stage_id not in stage_results:
            return False
        
        selected_stage = STAGES_BY_ID[selected_stage_id]
        
        for x in range(STAGE_STEP_MULTI_STEP_BUTTON):
            next_stage = selected_stage.after_stage_source
            if next_stage is None:
                if x:
                    break
                
                return False
            
            selected_stage = next_stage
            
            if selected_stage.id not in stage_results:
                break
        
        user_state.selected_stage_id = selected_stage.id
        return True
    
    return False


async def process_identifier_down(dungeon_sweeper_runner):
    """
    Processes `down` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `down` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_MENU:
        user_state = dungeon_sweeper_runner.user_state
        
        selected_stage_id = user_state.selected_stage_id
        selected_stage = STAGES_BY_ID[selected_stage_id]
        
        selected_stage = selected_stage.before_stage_source
        if selected_stage is None:
            return False
        
        user_state.selected_stage_id = selected_stage.id
        return True
    
    return False


async def process_identifier_down2(dungeon_sweeper_runner):
    """
    Processes `down2` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `down` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_MENU:
        user_state = dungeon_sweeper_runner.user_state
        
        selected_stage_id = user_state.selected_stage_id
        selected_stage = STAGES_BY_ID[selected_stage_id]
        
        for x in range(STAGE_STEP_MULTI_STEP_BUTTON):
            next_stage = selected_stage.before_stage_source
            if next_stage is None:
                if x:
                    break
                
                return False
            
            selected_stage = next_stage
        
        user_state.selected_stage_id = selected_stage.id
        return True
    
    return False


async def process_identifier_left(dungeon_sweeper_runner):
    """
    Processes `left` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `left` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_MENU:
        user_state = dungeon_sweeper_runner.user_state
        
        stage_source = STAGES_BY_ID[user_state.selected_stage_id]
        
        try:
            chapter = CHAPTERS[stage_source.chapter.id - 1]
        except KeyError:
            return False
        
        index = stage_source.index
        
        chapter_stages_sorted = chapter.stages_sorted
        chapter_stages_sorted_length = len(chapter_stages_sorted)
        if index >= chapter_stages_sorted_length:
            index = chapter_stages_sorted_length - 1
        
        user_state.selected_stage_id = chapter_stages_sorted[index].id
        return True
    
    
    return False


async def process_identifier_right(dungeon_sweeper_runner):
    """
    Processes `right` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `right` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_MENU:
        user_state = dungeon_sweeper_runner.user_state
        
        stage_source = STAGES_BY_ID[user_state.selected_stage_id]
        
        try:
            chapter = CHAPTERS[stage_source.chapter.id + 1]
        except KeyError:
            return False
        
        index = stage_source.index
        
        chapter_stages_sorted = chapter.stages_sorted
        chapter_stages_sorted_length = len(chapter_stages_sorted)
        if index >= chapter_stages_sorted_length:
            index = chapter_stages_sorted_length - 1
        
        
        stage_source_id = chapter_stages_sorted[index].id
        stage_results = user_state.stage_results
        if (
            (stage_source_id not in stage_results) and
            (chapter_stages_sorted[index - 1].id not in stage_results)
        ):
            stage_source_id = chapter.difficulties[0][0].id
        
        user_state.selected_stage_id = stage_source_id
        return True
    
    return False


async def process_identifier_select(dungeon_sweeper_runner):
    """
    Processes `select` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `select` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_MENU:
        user_state = dungeon_sweeper_runner.user_state
        if not can_play_selected_stage(user_state):
            return False
        
        selected_stage_id = user_state.selected_stage_id
        selected_stage = STAGES_BY_ID[selected_stage_id]
        
        try:
            stage_result = user_state.stage_results[selected_stage_id]
        except KeyError:
            best = -1
        else:
            best = stage_result.best
        
        user_state.game_state = GameState(selected_stage, best)
        dungeon_sweeper_runner._runner_state = RUNNER_STATE_PLAYING
        return True
    
    return False


async def process_identifier_west(dungeon_sweeper_runner):
    """
    Processes `west` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `west` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_PLAYING:
        user_state = dungeon_sweeper_runner.user_state
        game_state = user_state.game_state
        
        success = game_state.move_west()
        if success and game_state.done():
            await user_state.set_best(game_state.stage.id, len(game_state.history))
            dungeon_sweeper_runner._runner_state = RUNNER_STATE_END_SCREEN
        
        return success
    
    return False


async def process_identifier_north(dungeon_sweeper_runner):
    """
    Processes `north` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `west` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_PLAYING:
        user_state = dungeon_sweeper_runner.user_state
        game_state = user_state.game_state
        
        success = game_state.move_north()
        if success and game_state.done():
            await user_state.set_best(game_state.stage.id, len(game_state.history))
            dungeon_sweeper_runner._runner_state = RUNNER_STATE_END_SCREEN
        
        return success
    
    return False


async def process_identifier_south(dungeon_sweeper_runner):
    """
    Processes `south` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `south` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_PLAYING:
        user_state = dungeon_sweeper_runner.user_state
        game_state = user_state.game_state
        
        success = game_state.move_south()
        if success and game_state.done():
            await user_state.set_best(game_state.stage.id, len(game_state.history))
            dungeon_sweeper_runner._runner_state = RUNNER_STATE_END_SCREEN
        
        return success
    
    return False


async def process_identifier_east(dungeon_sweeper_runner):
    """
    Processes `east` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `east` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_PLAYING:
        user_state = dungeon_sweeper_runner.user_state
        game_state = user_state.game_state
        
        success = game_state.move_east()
        if success and game_state.done():
            await user_state.set_best(game_state.stage.id, len(game_state.history))
            dungeon_sweeper_runner._runner_state = RUNNER_STATE_END_SCREEN
        
        return success
    
    return False


async def process_identifier_back(dungeon_sweeper_runner):
    """
    Processes `back` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `back` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_PLAYING:
        game_state = dungeon_sweeper_runner.user_state.game_state
        
        return game_state.back()
    
    return False


async def process_identifier_reset(dungeon_sweeper_runner):
    """
    Processes `reset` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `reset` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_PLAYING:
        game_state = dungeon_sweeper_runner.user_state.game_state
        
        return game_state.reset()
    
    return False


async def process_identifier_cancel(dungeon_sweeper_runner):
    """
    Processes `cancel` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `cancel` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_PLAYING:
        dungeon_sweeper_runner._runner_state = RUNNER_STATE_MENU
        user_state = dungeon_sweeper_runner.user_state
        user_state.game_state = None
        return True
    
    return False


async def process_identifier_skill(dungeon_sweeper_runner):
    """
    Processes `skill` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `skill` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_PLAYING:
        game_state = dungeon_sweeper_runner.user_state.game_state
        
        return game_state.skill_activate()
    
    return False


async def process_identifier_close(dungeon_sweeper_runner):
    """
    Processes `close` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `close` button could be pressed.
    """
    runner_state = dungeon_sweeper_runner._runner_state
    if runner_state == RUNNER_STATE_END_SCREEN:
        dungeon_sweeper_runner.user_state.game_state = None
        
        dungeon_sweeper_runner._runner_state = RUNNER_STATE_MENU
        return True
    
    if runner_state == RUNNER_STATE_MENU:
        dungeon_sweeper_runner._runner_state = RUNNER_STATE_CLOSED
        return True
    
    return False


async def process_identifier_next(dungeon_sweeper_runner):
    """
    Processes `next` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `next` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_END_SCREEN:
        user_state = dungeon_sweeper_runner.user_state
        game_state = user_state.game_state
        stage_source = game_state.stage
        selected_stage = stage_source.after_stage_source
        if selected_stage is None:
            return False
        
        
        dungeon_sweeper_runner._runner_state = RUNNER_STATE_PLAYING
        
        selected_stage_id = selected_stage.id
        user_state.selected_stage_id = selected_stage_id
        
        try:
            stage_result = user_state.stage_results[selected_stage_id]
        except KeyError:
            best = -1
        else:
            best = stage_result.best
        
        user_state.game_state = GameState(selected_stage, best)
        return True
    
    return False


async def process_identifier_restart(dungeon_sweeper_runner):
    """
    Processes `restart` button click.
    
    This function is a coroutine.
    
    Parameters
    ----------
    dungeon_sweeper_runner : ``DungeonSweeperRunner``
        The respective dungeon sweeper runner.
    
    Returns
    -------
    success : `bool`
        Whether the `restart` button could be pressed.
    """
    if dungeon_sweeper_runner._runner_state == RUNNER_STATE_END_SCREEN:
        dungeon_sweeper_runner.user_state.game_state.restart()
        dungeon_sweeper_runner._runner_state = RUNNER_STATE_PLAYING
        return True
    
    return False



PROCESS_CUSTOM_ID = {
    IDENTIFIER_UP: process_identifier_up,
    IDENTIFIER_DOWN: process_identifier_down,
    IDENTIFIER_UP2: process_identifier_up2,
    IDENTIFIER_DOWN2: process_identifier_down2,
    IDENTIFIER_RIGHT: process_identifier_right,
    IDENTIFIER_LEFT: process_identifier_left,
    IDENTIFIER_SELECT: process_identifier_select,
    IDENTIFIER_WEST: process_identifier_west,
    IDENTIFIER_NORTH: process_identifier_north,
    IDENTIFIER_SOUTH: process_identifier_south,
    IDENTIFIER_EAST: process_identifier_east,
    IDENTIFIER_BACK: process_identifier_back,
    IDENTIFIER_RESET: process_identifier_reset,
    IDENTIFIER_CANCEL: process_identifier_cancel,
    IDENTIFIER_SKILL: process_identifier_skill,
    IDENTIFIER_CLOSE: process_identifier_close,
    IDENTIFIER_NEXT: process_identifier_next,
    IDENTIFIER_RESTART: process_identifier_restart,
}


class DungeonSweeperRunner:
    """
    Dungeon sweeper game runner.
    
    Attributes
    ----------
    _canceller : None`, `CoroutineFunction`
        Canceller set as `._canceller_function``, meanwhile the gui is not cancelled.
    
    _gui_state : `int`
        The gui's state.
        
        Can be any of the following:
        
        +-------------------------------+-------+
        | Respective name               | Value |
        +===============================+=======+
        | GUI_STATE_NONE                | 0     |
        +===============================+=======+
        | GUI_STATE_READY               | 1     |
        +-------------------------------+-------+
        | GUI_STATE_EDITING             | 2     |
        +-------------------------------+-------+
        | GUI_STATE_CANCELLING          | 3     |
        +-------------------------------+-------+
        | GUI_STATE_CANCELLED           | 4     |
        +-------------------------------+-------+
        | GUI_STATE_SWITCHING_CONTEXT   | 5     |
        +-------------------------------+-------+
    
    _runner_state : `int`
        The state of the runner.
        
        Can be any of the following:
        
        +-------------------------------+-------+
        | Respective name               | Value |
        +===============================+=======+
        | RUNNER_STATE_MENU             | 1     |
        +-------------------------------+-------+
        | RUNNER_STATE_PLAYING          | 2     |
        +-------------------------------+-------+
        | RUNNER_STATE_END_SCREEN       | 3     |
        +-------------------------------+-------+
    
    _timeouter : `None`, ``Timeouter``
        Timeouts the gui if no action is performed within the expected time.
    
    client : ``Client``
        The client, who executes the requests.
    
    message : ``Message``
        The message edited by the runner.
    
    user : ``ClientUserBase``
        The user, who requested the game.
    
    user_state : ``UserState``
        The user's user state.
    """
    __slots__ = ('_canceller', '_gui_state', '_runner_state', '_timeouter', 'client', 'message', 'user', 'user_state')
    
    async def __new__(cls, client, event):
        """
        Creates a new dungeon sweeper runner.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The source client.
        event : ``InteractionEvent``
            The received client.
        """
        if not event.channel.cached_permissions_for(client).can_manage_messages:
            await client.interaction_response_message_create(
                event,
                'I need manage messages permission in the channel to execute this command.',
                show_for_invoking_user_only = True,
            )
            return
        
        user_id = event.user.id
        try:
            existing_game = DUNGEON_SWEEPER_GAMES[user_id]
        except KeyError:
            pass
        else:
            if (existing_game is None):
                await client.interaction_response_message_create(
                    event,
                    'A game is already starting somewhere else.',
                    show_for_invoking_user_only = True,
                )
            else:
                await existing_game.renew(event)
            
            return
        
        DUNGEON_SWEEPER_GAMES[user_id] = None
        user_state = None
        try:
            task_user_state_create = Task(UserState(user_id), KOKORO)
            task_interaction_acknowledge = Task(client.interaction_response_message_create(event), KOKORO)
            await WaitTillAll([task_user_state_create, task_interaction_acknowledge], KOKORO)
            
            user_state = task_user_state_create.result()
            
            try:
                task_interaction_acknowledge.result()
            except BaseException as err:
                if (
                    isinstance(err, ConnectionError) or
                    (
                        isinstance(err, DiscordException) and
                        err.code == ERROR_CODES.unknown_interaction
                    )
                ):
                    await user_state.upload_game_state_on_init_failure()
                    return # Happens, I guess
                
                else:
                    raise
            
            game_state = user_state.game_state
            if game_state is None:
                embed, components = render_menu(user_state)
                
                runner_state = RUNNER_STATE_MENU
            else:
                if game_state.done():
                    embed, components = user_state.game_state.render_end_screen()
                    runner_state = RUNNER_STATE_END_SCREEN
                else:
                    embed, components = user_state.game_state.render_playing()
                    runner_state = RUNNER_STATE_PLAYING
            
            user = event.user
            embed.add_author(user.full_name, user.avatar_url_as('png', 32))
            
            message = await client.interaction_followup_message_create(event, embed=embed, components=components)
        except:
            if (user_state is not None):
                await user_state.upload_game_state_on_init_failure()
            
            del DUNGEON_SWEEPER_GAMES[user_id]
            raise
        
        self = object.__new__(cls)
        self._canceller = cls._canceller_function
        self.client = client
        self.user = event.user
        self.message = message
        self.user_state = user_state
        self._timeouter = Timeouter(self, GUI_TIMEOUT)
        self._gui_state = GUI_STATE_READY
        self._runner_state = runner_state
        
        DUNGEON_SWEEPER_GAMES[user_id] = self
        client.slasher.add_component_interaction_waiter(message, self)
        
        return self
    
    async def renew(self, event):
        """
        Renews the interaction gui creating a new message.
        
        This method is a generator.
        
        Parameters
        ----------
        event : ``InteractionEvent``
            The received interaction event.
        """
        if self._gui_state in (GUI_STATE_CANCELLING, GUI_STATE_CANCELLED, GUI_STATE_SWITCHING_CONTEXT):
            return
        
        user_state = self.user_state
        runner_state = self._runner_state
        if runner_state == RUNNER_STATE_MENU:
            embed, components = render_menu(user_state)
        elif runner_state == RUNNER_STATE_PLAYING:
            embed, components = user_state.game_state.render_playing()
        elif runner_state == RUNNER_STATE_END_SCREEN:
            embed, components = user_state.game_state.render_end_screen()
        else:
            # Hacker trying to hack Huyane
            return
        
        self._gui_state = GUI_STATE_SWITCHING_CONTEXT
        
        client = self.client
        try:
            await client.interaction_response_message_create(event)
            message = await client.interaction_followup_message_create(event, embed=embed, components=components)
        
        except BaseException as err:
            
            if self._gui_state == GUI_STATE_SWITCHING_CONTEXT:
                self._gui_state = GUI_STATE_READY
            
            if (
                isinstance(err, ConnectionError) or
                (
                    isinstance(err, DiscordException) and
                    err.code == ERROR_CODES.unknown_interaction
                )
            ):
                return
            
            raise
        
        
        try:
            await client.message_edit(self.message, components=None)
        except BaseException as err:
            if not (
                isinstance(err, ConnectionError) or
                (
                    isinstance(err, DiscordException) and
                    err.code in (
                        ERROR_CODES.unknown_message, # message deleted
                        ERROR_CODES.unknown_channel, # channel deleted
                        ERROR_CODES.missing_access, # client removed
                        ERROR_CODES.missing_permissions, # permissions changed meanwhile
                    )
                )
            ):
                await client.events.error(client, f'{self!r}.renew', err)
        
        client.slasher.remove_component_interaction_waiter(self.message, self)
        client.slasher.add_component_interaction_waiter(message, self)
        
        self.message = message
        
        if self._gui_state == GUI_STATE_SWITCHING_CONTEXT:
            self._gui_state = GUI_STATE_READY
        
        timeouter = self._timeouter
        if (timeouter is not None):
            timeouter.set_timeout(GUI_TIMEOUT)
    
    async def __call__(self, event):
        """
        Calls the dungeon sweeper runner, processing a component event.
        
        This method is a coroutine.
        
        Parameters
        ----------
        event : ``InteractionEvent``
            The received client.
        """
        client = self.client
        if event.user is not self.user:
            await client.interaction_component_acknowledge(event)
            return
        
        gui_state = self._gui_state
        if gui_state != GUI_STATE_READY:
            await client.interaction_component_acknowledge(event)
            return
        
        custom_id = event.interaction.custom_id
        
        try:
            custom_id_processor = PROCESS_CUSTOM_ID[custom_id]
        except KeyError:
            return
        
        user_state = self.user_state
        if not await custom_id_processor(self):
            return
        
        runner_state = self._runner_state
        if runner_state == RUNNER_STATE_MENU:
            embed, components = render_menu(user_state)
        elif runner_state == RUNNER_STATE_PLAYING:
            embed, components = user_state.game_state.render_playing()
        elif runner_state == RUNNER_STATE_END_SCREEN:
            embed, components = user_state.game_state.render_end_screen()
        elif runner_state == RUNNER_STATE_CLOSED:
            self.cancel(CancelledError())
            return
        else:
            # Hacker trying to hack Huyane
            return
        
        user = self.user
        embed.add_author(user.full_name, user.avatar_url_as('png', 32))
        
        self._gui_state = GUI_STATE_EDITING
        try:
            await client.interaction_component_message_edit(event, embed=embed, components=components)
        except BaseException as err:
            self.cancel(err)
            raise
        
        if self._gui_state == GUI_STATE_EDITING:
            self._gui_state = GUI_STATE_READY
        
        timeouter = self._timeouter
        if (timeouter is not None):
            timeouter.set_timeout(GUI_TIMEOUT)
        
    def cancel(self, exception=None):
        """
        Cancels the dungeon sweeper gui with the given exception if applicable.
        
        Parameters
        ----------
        exception : `None`, ``BaseException``, Optional
            Exception to cancel the pagination with. Defaults to `None`
        
        Returns
        -------
        canceller_task : `None`, ``Task``
        """
        if self._gui_state in (GUI_STATE_READY, GUI_STATE_EDITING, GUI_STATE_CANCELLING):
            self._gui_state = GUI_STATE_CANCELLED
        
        canceller = self._canceller
        if canceller is None:
            return
        
        self._canceller = None
        
        timeouter = self._timeouter
        if (timeouter is not None):
            timeouter.cancel()
        
        return Task(canceller(self, exception), KOKORO)
    
    
    async def _canceller_function(self, exception):
        """
        Cancels the gui state, saving the current game if needed.
        
        This method is a coroutine.
        
        Parameters
        ----------
        exception : `None`, ``BaseException``
        """
        await self.user_state.upload()
        
        user_id = self.user.id
        if DUNGEON_SWEEPER_GAMES.get(user_id, None) is self:
            del DUNGEON_SWEEPER_GAMES[user_id]
        
        
        client = self.client
        message = self.message
        
        client.slasher.remove_component_interaction_waiter(message, self)
        
        
        if self._gui_state == GUI_STATE_SWITCHING_CONTEXT:
            # the message is not our, we should not do anything with it.
            return
        
        self._gui_state = GUI_STATE_CANCELLED
        
        if not await self._handle_close_exception(exception):
            await client.events.error(client, f'{self!r}._canceller_function', exception)

    
    async def _handle_close_exception(self, exception):
        """
        Handles close exception if any.
        
        This method is a coroutine.
        
        Parameters
        ----------
        exception : `None`, `BaseException`
            The close exception to handle.
        
        Returns
        -------
        exception_handled : `bool`
            Whether the exception was handled.
        """
        if exception is None:
            return True
        
        client = self.client
        message = self.message
        
        if isinstance(exception, CancelledError):
            try:
                await client.message_delete(message)
            except BaseException as err:
                if isinstance(err, ConnectionError):
                    # no internet
                    return True
                
                if isinstance(err, DiscordException):
                    if err.code in (
                        ERROR_CODES.unknown_channel, # channel deleted
                        ERROR_CODES.unknown_message, # message deleted
                        ERROR_CODES.missing_access, # client removed
                    ):
                        return True
                
                await client.events.error(client, f'{self!r}._handle_close_exception', err)
            
            return True
        
        if isinstance(exception, TimeoutError):
            try:
                await client.message_edit(message, components=None)
            except BaseException as err:
                if isinstance(err, ConnectionError):
                    # no internet
                    return True
                
                if isinstance(err, DiscordException):
                    if err.code in (
                        ERROR_CODES.unknown_message, # message deleted
                        ERROR_CODES.unknown_channel, # channel deleted
                        ERROR_CODES.missing_access, # client removed
                        ERROR_CODES.missing_permissions, # permissions changed meanwhile
                    ):
                        return True
                
                await client.events.error(client, f'{self!r}._handle_close_exception', err)
            
            return True
        
        if isinstance(exception, SystemExit):
            user = self.user
            embed = Embed(
                f'I am restarting',
                (
                    'Your progress has been saved, please try using the command again later.\n'
                    '\n'
                    'I am sorry for the inconvenience. See ya later qtie!'
                ),
            ).add_author(
                user.full_name,
                user.avatar_url_as('png', 32),
            ).add_thumbnail(
                EMOJI_KOISHI_WAVE.url,
            )
            
            try:
                await client.message_edit(message, embed=embed, components=None)
            except BaseException as err:
                if isinstance(err, ConnectionError):
                    # no internet
                    return True
                
                if isinstance(err, DiscordException):
                    if err.code in (
                        ERROR_CODES.unknown_message, # message deleted
                        ERROR_CODES.unknown_channel, # channel deleted
                        ERROR_CODES.missing_access, # client removed
                        ERROR_CODES.missing_permissions, # permissions changed meanwhile
                    ):
                        return True
                
                await client.events.error(client, f'{self!r}._handle_close_exception', err)
            
            return True
        
        
        if isinstance(exception, PermissionError):
            return True
        
        return False
    
    def __repr__(self):
        """Returns the dungeon sweep runner's representation."""
        repr_parts = [
            '<', self.__class__.__name__,
            ' client=', repr(self.client),
            ', at channel=', repr(self.message.channnel),
            ', gui_state='
        ]
        
        gui_state = self._gui_state
        
        repr_parts.append(repr(gui_state))
        repr_parts.append(' (')
        gui_state_name = GUI_STATE_VALUE_TO_NAME[gui_state]
        repr_parts.append(gui_state_name)
        repr_parts.append('), ')
        
        runner_state = self._runner_state
        repr_parts.append(repr(runner_state))
        repr_parts.append(' (')
        runner_state_name = RUNNER_STATE_VALUE_TO_NAME[runner_state]
        repr_parts.append(runner_state_name)
        repr_parts.append('), ')
        
        repr_parts.append('>')
        return ''.join(repr_parts)



SLASH_CLIENT : Client

DUNGEON_SWEEPER = SLASH_CLIENT.interactions(None,
    name = 'ds',
    description = 'Touhou themed puzzle game.',
    is_global = True,
)


@DUNGEON_SWEEPER.interactions
async def rules(client, event):
    """Shows the rules of DS!"""
    if not event.channel.cached_permissions_for(client).can_use_external_emojis:
        abort('I have no permissions at this channel to render this message.')
    
    return RULES_HELP


@DUNGEON_SWEEPER.interactions(is_default=True)
async def play(client, event):
    """Starts the game"""
    game = DUNGEON_SWEEPER_GAMES.get(event.user.id, None)
    if game is None:
        await DungeonSweeperRunner(client, event)
    else:
        await game.renew(event)


@SLASH_CLIENT.events
async def shutdown(client):
    tasks = []
    exception = SystemExit()
    
    for game in DUNGEON_SWEEPER_GAMES.values():
        task = game.cancel(exception)
        if (task is not None):
            tasks.append(task)
    
    task = None
    game = None
    
    if tasks:
        await WaitTillAll(tasks, KOKORO)
