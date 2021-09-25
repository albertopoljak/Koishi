import re
from datetime import datetime, timedelta
from functools import partial as partial_func

from hata import BUILTIN_EMOJIS, sleep,  Client, KOKORO, cchunkify, alchemy_incendiary, Permission
from hata.backend.futures import render_exc_to_list
from hata.discord.utils import sanitise_mention_escaper

from bot_utils.tools import MessageDeleteWaitfor, GuildDeleteWaitfor, RoleDeleteWaitfor, EmojiDeleteWaitfor, \
    RoleEditWaitfor
from bot_utils.constants import GUILD__NEKO_DUNGEON, CHANNEL__SYSTEM__SYNC, CHANNEL__NEKO_DUNGEON__DEFAULT_TEST



_KOISHI_NOU_RP = re.compile(r'n+\s*o+\s*u+', re.I)
_KOISHI_OWO_RP = re.compile('(owo|uwu|0w0)', re.I)
_KOISHI_OMAE_RP = re.compile('omae wa mou', re.I)

Koishi: Client
Satori: Client

Koishi.events(MessageDeleteWaitfor)
Koishi.events(GuildDeleteWaitfor)
Koishi.events(RoleDeleteWaitfor)
Koishi.events(EmojiDeleteWaitfor)
Koishi.events(RoleEditWaitfor)


PERMISSION_MASK_MESSAGING = Permission().update_by_keys(
    send_messages = True,
    send_messages_in_threads = True,
)

@Satori.events
async def message_create(client, message):
    if (message.guild_id != GUILD__NEKO_DUNGEON):
        return
    
    if (message.referenced_message is not None):
        return
    
    if not message.channel.cached_permissions_for(Koishi)&PERMISSION_MASK_MESSAGING:
        return
    
    if message.author.is_bot:
        return
    
    content = message.content
    if content is None:
        return
    
    user_mentions = message.user_mentions
    if (user_mentions is not None) and (Koishi in user_mentions):
        author = message.author
        m1 = author.mention
        m2 = Koishi.mention
        m3 = author.mention_nick
        m4 = Koishi.mention_nick
        replace = {
            '@everyone'   : '@\u200beveryone',
            '@here'       : '@\u200bhere',
            re.escape(m1) : m2,
            re.escape(m2) : m1,
            re.escape(m3) : m4,
            re.escape(m4) : m3,
        }
        pattern = re.compile('|'.join(replace.keys()))
        result = pattern.sub(partial_func(sanitise_mention_escaper, replace), content)
        await Koishi.message_create(message.channel, result, allowed_mentions=[author])
        return
        
    if message.channel.cached_permissions_for(Koishi).can_add_reactions and (_KOISHI_NOU_RP.match(content) is not None):
        for value in 'nou':
            emoji = BUILTIN_EMOJIS[f'regional_indicator_{value}']
            await Koishi.reaction_add(message, emoji)
        return
    
    matched = _KOISHI_OWO_RP.fullmatch(content,)
    if (matched is not None):
        text = f'{content[0].upper()}{content[1].lower()}{content[2].upper()}'
    
    elif (_KOISHI_OMAE_RP.match(content) is not None):
        text = 'NANI?'
    
    else:
        return
    
    await Koishi.message_create(message.channel, text)


@Koishi.events(overwrite=True)
async def error(client, name, err):
    extracted = [
        client.full_name,
        ' ignores occurred exception at ',
        name,
        '\n',
    ]
    
    if isinstance(err, BaseException):
        await KOKORO.run_in_executor(alchemy_incendiary(render_exc_to_list, (err, extracted)))
    else:
        if not isinstance(err, str):
            err = repr(err)
        
        extracted.append(err)
        extracted.append('\n')
    
    extracted = ''.join(extracted).split('\n')
    for chunk in cchunkify(extracted, lang='py'):
        await client.message_create(CHANNEL__NEKO_DUNGEON__DEFAULT_TEST, chunk)
