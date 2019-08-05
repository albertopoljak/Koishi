# -*- coding: utf-8 -*-
import sys, os
#moving to the outer folder, so hata ll count as a package and stuffs
sys.path.append(os.path.abspath('..'))

from hata import Client,start_clients
from hata.activity import Activity_game
from hata.channel import Channel_text
from hata.events import (reaction_add_waitfor,command_processer,
    reaction_delete_waitfor,)
from hata.webhook import Webhook
from hata.role import Role

import pers_data

import koishi
import mokou
import elphelt

from tools import commit_extractor,message_delete_waitfor
from booru import booru_commands
############################## SETUP KOISHI ##############################

Koishi=Client(pers_data.KOISHI_TOKEN,
    secret=pers_data.KOISHI_SECRET,
    client_id=pers_data.KOISHI_ID,
    activity=Activity_game.create(name='with Satori'),
        )

Koishi.events(reaction_add_waitfor)
Koishi.events(reaction_delete_waitfor)
Koishi.events(message_delete_waitfor)
Koishi.events(koishi.once_on_ready)

koishi_commands=Koishi.events(command_processer(koishi.PREFIXES)).shortcut
koishi_commands.extend(koishi.commands)
koishi_commands.extend(booru_commands)

webhook_sender=commit_extractor(
    Koishi,
    Channel_text.precreate(555476090382974999),
    Webhook.precreate(555476334210580508),
    role=Role.precreate(538397994421190657),
    color=0x2ad300,
        )

Koishi.events.message_create.append(webhook_sender,webhook_sender.channel)

############################## SETUP MOKOU ##############################


Mokou=Client(pers_data.MOKOU_TOKEN,
    client_id=pers_data.MOKOU_ID,
        )

Mokou.events(mokou.message_create)
Mokou.events(mokou.typing)
Mokou.events(mokou.channel_delete)


############################## SETUP ELPHELT ##############################

Elphelt=Client(pers_data.ELPHELT_TOKEN,
    client_id=pers_data.ELPHELT_ID,
    status='idle'
        )

Elphelt.events(reaction_add_waitfor)
Elphelt.events(reaction_delete_waitfor)

elphelt_commands=Elphelt.events(command_processer('/')).shortcut
elphelt_commands.extend(elphelt.commands)
elphelt_commands(Koishi.events.message_create.commands['random'])

############################## TEST COMMANDS ##############################

from hata.events_compiler import content_parser

@koishi_commands
@content_parser('condition, flags=r, default="not client.is_owner(message.author)"',
    'user, mode="0+"')
async def i_love(client,message,users):
    for user in users:
        await client.message_create(message.channel,f'{user:m} I love u!')

@koishi_commands
async def guess_user(client,message,content):
    guild=message.guild
    if (guild is None) or (not client.is_owner(message.author)):
        return
    users = await client.request_member(guild,content,10)
    if users:
        text=', '.join([user.full_name for user in users])
    else:
        text='No result'
    await client.message_create(message.channel,text)

@koishi_commands
async def get_users_like_guild(client,message,content):
    guild=message.guild
    if (guild is None) or (not client.is_owner(message.author)):
        return
    users=guild.get_users_like(content)
    if users:
        text=', '.join([user.full_name for user in users])
    else:
        text='No result'
    await client.message_create(message.channel,text)

@koishi_commands
async def get_user_like_guild(client,message,content):
    guild=message.guild
    if (guild is None) or (not client.is_owner(message.author)):
        return
    user=guild.get_user_like(content)
    if user is None:
        text='No result'
    else:
        text=user.full_name
    await client.message_create(message.channel,text)

@koishi_commands
async def get_users_like_channel(client,message,content):
    if not client.is_owner(message.author):
        return
    users=message.channel.get_users_like(content)
    if users:
        text=', '.join([user.full_name for user in users])
    else:
        text='No result'
    await client.message_create(message.channel,text)

@koishi_commands
async def get_user_like_channel(client,message,content):
    if not client.is_owner(message.author):
        return
    user=message.channel.get_user_like(content)
    if user is None:
        text='No result'
    else:
        text=user.full_name
    await client.message_create(message.channel,text)

@koishi_commands
async def get_users_like_ordered(client,message,content):
    guild=message.guild
    if (guild is None) or (not client.is_owner(message.author)):
        return
    users=guild.get_users_like_ordered(content)
    if users:
        text=', '.join([user.full_name for user in users])
    else:
        text='No result'
    await client.message_create(message.channel,text)
    
############################## START ##############################

start_clients()

