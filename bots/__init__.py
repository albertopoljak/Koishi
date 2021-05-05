# -*- coding: utf-8 -*-
import os

import config

from hata import Client, ActivityRich, ActivityTypes
from hata.ext.extension_loader import EXTENSION_LOADER
from bot_utils.shared import PATH__KOISHI

MARISA_MODE = config.MARISA_MODE

EXTENSION_LOADER.add_default_variables(MARISA_MODE=MARISA_MODE)

if MARISA_MODE:
    Marisa = Client(config.MARISA_TOKEN,
        client_id = config.MARISA_ID,
        #application_id = config.MARISA_ID,
            )
    
    EXTENSION_LOADER.add_default_variables(Marisa=Marisa, COMMAND_CLIENT=Marisa, SLASH_CLIENT=Marisa)
    
    EXTENSION_LOADER.load_extension('bots.marisa', locked=True)
    
    EXTENSION_LOADER.add('bots.testers', MAIN_CLIENT=Marisa)

else:
    Koishi = Client(config.KOISHI_TOKEN,
        secret = config.KOISHI_SECRET,
        client_id = config.KOISHI_ID,
        activity = ActivityRich('with Satori'),
        shard_count = 2,
        application_id = config.KOISHI_ID,
            )
    
    EXTENSION_LOADER.add_default_variables(Koishi=Koishi, SLASH_CLIENT=Koishi)
    
    Satori = Client(config.SATORI_TOKEN,
        secret = config.SATORI_SECRET,
        client_id = config.SATORI_ID,
        activity = ActivityRich('with Koishi'),
        status = 'dnd',
        application_id = config.SATORI_ID,
            )
    
    EXTENSION_LOADER.add_default_variables(Satori=Satori, COMMAND_CLIENT=Satori)
    
    Flan = Client(config.FLAN_TOKEN,
        client_id = config.FLAN_ID,
        activity = ActivityRich('Chesuto development', type_=ActivityTypes.watching),
        status = 'idle',
        application_id = config.FLAN_ID,
            )
    
    EXTENSION_LOADER.add_default_variables(Flan=Flan)
    
    EXTENSION_LOADER.load_extension('bots.koishi', locked=True)
    EXTENSION_LOADER.load_extension('bots.satori', locked=True)
    EXTENSION_LOADER.load_extension('bots.flan'  , locked=True)

MODULE_NAMES = set()

path = None
for path in os.listdir(os.path.join(PATH__KOISHI, 'bots', 'modules')):
    if not path.endswith('.py'):
        continue
    
    MODULE_NAMES.add(path[:-3])

if MARISA_MODE:
    MARISA_ALLOWED_MODULES = set()
    
    if config.ALLOW_MARISA_SNEKBOX:
        MARISA_ALLOWED_MODULES.add('snekbox')
    
    MARISA_ALLOWED_MODULES.add('voice')
    MARISA_ALLOWED_MODULES.add('extensions')
    
    for path in list(MODULE_NAMES):
        if path not in MARISA_ALLOWED_MODULES:
            MODULE_NAMES.remove(path)
    
else:
    if not config.ALLOW_KOISHI_SNEKBOX:
        try:
            MODULE_NAMES.remove('snekbox')
        except KeyError:
            pass

        try:
            MODULE_NAMES.remove('witch_craft')
        except KeyError:
            pass

for path in MODULE_NAMES:
    EXTENSION_LOADER.add('bots.modules.'+path)

del path

EXTENSION_LOADER.load_all()
