__all__ = ()

import re
from hata.ext.slash import Button, ButtonStyle, Row


CHANNEL_MOVER_ACTIVE_FROM = set()
CHANNEL_MOVER_ACTIVE_TO = set()
CHANNEL_MOVER_BY_STATUS_MESSAGE_ID = {}


CHANNEL_MOVE_STATE_NONE = 0
CHANNEL_MOVE_STATE_FINISHED = 1
CHANNEL_MOVE_STATE_WEBHOOK_DELETED = 2
CHANNEL_MOVE_STATE_ERROR = 3
CHANNEL_MOVE_STATE_CLIENT_SHUTDOWN = 4
CHANNEL_MOVE_STATE_CANCELLED = 5

UPDATE_INTERVAL = 15.0


CUSTOM_ID_CHANNEL_MOVER_CANCEL = 'channel_mover.cancel'
CUSTOM_ID_RP_CHANNEL_MOVER_RESUME = re.compile('channel_mover\.resume\.(\d+)\.(\d+)\.(\d+)')


BUTTON_CHANNEL_MOVE_CANCEL = Button(
    'Cancel',
    custom_id = CUSTOM_ID_CHANNEL_MOVER_CANCEL,
    style = ButtonStyle.red,
)
    

CHANNEL_MOVE_COMPONENTS = Row(
    BUTTON_CHANNEL_MOVE_CANCEL,
)
