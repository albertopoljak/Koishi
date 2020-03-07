# -*- coding: utf-8 -*-
import sys, json
from random import choice

from hata import Task, ERROR_CODES, eventlist, ChannelText, ChannelCategory,\
    CHANNELS, elapsed_time, Status, Permission, Status, DiscordException,   \
    Color, GUILDS, USERS, BUILTIN_EMOJIS, Embed, CLIENTS, ActivityUnknown,  \
    ActivitySpotify, AuditLogEvent, ChannelBase, User

from hata.prettyprint import pchunkify
from hata.others import cchunkify

from hata.events import Pagination, Timeouter, GUI_STATE_READY,             \
    GUI_STATE_SWITCHING_PAGE, GUI_STATE_CANCELLING, GUI_STATE_CANCELLED,    \
    GUI_STATE_SWITCHING_CTX, Converter, ConverterFlag, checks

from help_handler import KOISHI_HELP_COLOR, KOISHI_HELPER

class show_help(object):
    __slots__=('func',)
    __async_call__=True
    def __init__(self,func):
        self.func=func
    def __call__(self,client,message,*args):
        return self.func(client,message)

infos=eventlist()


def add_activity(text,activity):
    ACTIVITY_FLAG=activity.ACTIVITY_FLAG
    
    text.append(activity.name)
    text.append('\n')
    text.append(f'**>>** type : {("game","stream","spotify","watching","custom")[activity.type]} ({activity.type})\n')

    if ACTIVITY_FLAG&0b0000000000000001:
        if activity.timestamp_start:
            text.append(f'**>>** started : {elapsed_time(activity.start)} ago\n')
        if activity.timestamp_end:
            text.append(f'**>>** ends after : {elapsed_time(activity.end)}\n')

    if ACTIVITY_FLAG&0b0000000000000010:
        if activity.details:
            text.append(f'**>>** details : {activity.details}\n')

    if ACTIVITY_FLAG&0b0000000000000100:
        if activity.state is not None:
            text.append(f'**>>** state : {activity.state}\n')
            
    if ACTIVITY_FLAG&0b0000000000001000:
        if activity.party_id:
            text.append(f'**>>** party id : {activity.party_id}\n')
        if activity.party_size:
            text.append(f'**>>** party size : {activity.party_size}\n')
        if activity.party_max:
            text.append(f'**>>** party limit : {activity.party_max}\n')

    if ACTIVITY_FLAG&0b0000000000010000:
        if ACTIVITY_FLAG&0b0000010000000000:
            if activity.asset_image_large:
                text.append(f'**>>** asset image large url : {activity.image_large_url}\n')
            if activity.asset_text_large:
                text.append(f'**>>** asset text large : {activity.asset_text_large}\n')
            if activity.asset_image_small:
                text.append(f'**>>** asset image small url : {activity.image_small_url}\n')
            if activity.asset_text_small:
                text.append(f'**>>** asset text small : {activity.asset_text_small}\n')
            
        elif activity.type==ActivitySpotify.type:
            album_cover_url=activity.album_cover_url
            if album_cover_url is not None:
                text.append(f'**>>** album cover : {album_cover_url}\n')
        
    if ACTIVITY_FLAG&0b0000000000100000:
        if activity.secret_join:
            text.append(f'**>>** secret join : {activity.secret_join}\n')
        if activity.secret_spectate:
            text.append(f'**>>** secret spectate : {activity.secret_spectate}\n')
        if activity.secret_match:
            text.append(f'**>>** secret match : {activity.secret_match}\n')
            
    if ACTIVITY_FLAG&0b0000000001000000:
        if activity.url:
            text.append(f'**>>** url : {activity.url}\n')

    if ACTIVITY_FLAG&0b0000000010000000:
        if activity.sync_id:
            text.append(f'**>>** sync id : {activity.sync_id}\n')

    if ACTIVITY_FLAG&0b0000000100000000:
        if activity.session_id:
            text.append(f'**>>** session id : {activity.session_id}\n')

    if ACTIVITY_FLAG&0b0000001000000000:
        if activity.flags:
            text.append(f'**>>** flags : {activity.flags} ({", ".join(list(activity.flags))})\n')

    if ACTIVITY_FLAG&0b0000010000000000:
        if activity.application_id:
            text.append(f'**>>** application id : {activity.application_id}\n')

    if ACTIVITY_FLAG&0b0000100000000000:
        if activity.emoji is not None:
            text.append(f'**>>** emoji : {activity.emoji.as_emoji}\n')

    created_at=activity.created_at
    if created_at is not None:
        text.append(f'**>>** created at : {elapsed_time(created_at)} ago\n')

    if ACTIVITY_FLAG&0b0001000000000000:
        text.append(f'**>>** id : {activity.id}\n')
            
@infos(name='user', aliases=['profile'])
async def user_info(client, message, user : Converter('user', ConverterFlag.user_default.update_by_keys(everywhere = True, profile = True), default_code='message.author')):
    guild=message.guild
    
    embed=Embed(user.full_name)
    embed.add_field('User Information',
        f'Created: {elapsed_time(user.created_at)} ago\n'
        f'Profile: {user:m}\n'
        f'ID: {user.id}')
    
    try:
        profile=user.guild_profiles[guild]
    except KeyError:
        if user.avatar:
            embed.color=user.avatar&0xFFFFFF
        else:
            embed.color=user.default_avatar.color
    else:
        embed.color=user.color(guild)
        if profile.roles:
            roles=', '.join(role.mention for role in reversed(profile.roles))
        else:
            roles='none'
        text=[]
        if profile.nick is not None:
            text.append(f'Nick: {profile.nick}')
        if profile.joined_at is None:
            await client.guild_user_get(user.id)
        text.append(f'Joined: {elapsed_time(profile.joined_at)} ago')
        boosts_since=profile.boosts_since
        if boosts_since is not None:
            text.append(f'Booster since: {elapsed_time(boosts_since)}')
        text.append(f'Roles: {roles}')
        embed.add_field('In guild profile','\n'.join(text))
    
    embed.add_thumbnail(user.avatar_url_as(size=128))

    if user.activity is not ActivityUnknown or user.status is not Status.offline:
        text=[]
        
        if user.status is Status.offline:
            text.append('Status : offline\n')
        elif len(user.statuses)==1:
            for platform,status in user.statuses.items():
                text.append(f'Status : {status} ({platform})\n')
        else:
            text.append('Statuses :\n')
            for platform,status in user.statuses.items():
                text.append(f'**>>** {status} ({platform})\n')
        
        if user.activity is ActivityUnknown:
            text.append('Activity : *unknown*\n')
        elif len(user.activities)==1:
            text.append('Activity : ')
            add_activity(text,user.activities[0])
        else:
            text.append('Activities : \n')
            for index,activity in enumerate(user.activities,1):
                text.append(f'{index}.: ')
                add_activity(text,activity)
                
        embed.add_field('Status and Activity',''.join(text))
    await client.message_create(message.channel,embed=embed)

async def _help_user(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('user',(
        'I show you some information about the given user.\n'
        'If you use it inside of a guild and the user is inside as well, '
        'will show information, about their guild profile too.\n'
        f'Usage: `{prefix}user <user>`\n'
        'If no user is passed, I will tell your secrets :3'
        ),color=KOISHI_HELP_COLOR)
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('user',_help_user)

@infos(name='guild')
async def guild_info(client,message,content):
    guild=message.guild
    if guild is None:
        return

    #most usual first
    s_grey  = Status.offline
    s_green = Status.online
    s_yellow= Status.idle
    s_red   = Status.dnd
    
    v_grey  = 0
    v_green = 0
    v_yellow= 0
    v_red   = 0

    for user in guild.users.values():
        status=user.status
        if   status is s_grey:
            v_grey+=1
        elif status is s_green:
            v_green+=1
        elif status is s_yellow:
            v_yellow+=1
        elif status is s_red:
            v_red+=1
        else: #if we change our satus to invisible, it will be invisible till we get the dispatch event, then it turns offline.
            v_grey+=1
        
    del s_grey
    del s_green
    del s_yellow
    del s_red

    channel_text    = 0
    channel_category= 0
    channel_voice   = 0

    for channel in guild.all_channel.values():
        if type(channel) is ChannelText:
            channel_text+=1
        elif type(channel) is ChannelCategory:
            channel_category+=1
        else:
            channel_voice+=1

    if guild.features:
        features=', '.join(feature.name for feature in guild.features)
    else:
        features='none'

    embed=Embed(guild.name,color=guild.icon&0xFFFFFF if guild.icon else (guild.id>>22)&0xFFFFFF)
    embed.add_field('Guild information',
        f'Created: {elapsed_time(guild.created_at)} ago\n'
        f'Voice region: {guild.region}\n'
        f'Features: {features}\n')
    embed.add_field('Counts',
        f'Users: {guild.user_count}\n'
        f'Roles: {len(guild.roles)}\n'
        f'Text channels: {channel_text}\n'
        f'Voice channels: {channel_voice}\n'
        f'Category channels: {channel_category}\n')
    embed.add_field('Users',
        f'{BUILTIN_EMOJIS["green_heart"]:e} {v_green}\n'
        f'{BUILTIN_EMOJIS["yellow_heart"]:e} {v_yellow}\n'
        f'{BUILTIN_EMOJIS["heart"]:e} {v_red}\n'
        f'{BUILTIN_EMOJIS["black_heart"]:e} {v_grey}\n')

    boosters=guild.boosters
    if boosters:
        emoji=BUILTIN_EMOJIS['gift_heart']
        count=len(boosters)
        to_render=count if count<21 else 21
        
        embed.add_field('Most awesome people of the guild',
                        f'{to_render} {emoji:e} out of {count} {emoji:e}')

        for user in boosters[:21]:
            embed.add_field(user.full_name,
                f'since: {elapsed_time(user.guild_profiles[guild].boosts_since)}')
    
    embed.add_thumbnail(guild.icon_url_as(size=128))

    await client.message_create(message.channel,embed=embed)

async def _help_guild(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('user',(
        'Do you want me to list, some information about this guild?\n'
        f'Usage: `{prefix}guild`\n'
            ),color=KOISHI_HELP_COLOR).add_footer(
            'Guild only!')
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('guild',_help_guild)


@infos(checks = [checks.has_guild_permissions(Permission().update_by_keys(manage_channel=True))])
async def invites(client,message,channel:ChannelBase=None):
    guild = message.channel.guild
    if channel is None:
        if not guild.cached_permissions_for(client).can_manage_guild:
            await client.message_create(message.channel,
                'I dont have enough permission, to request the invites.')
            return
        invites = await client.invite_get_guild(guild)
    else:
        if not channel.cached_permissions_for(client).can_manage_channel:
            await client.message_create(message.channel,
                'I dont have enough permission, to request the invites.')
            return
        invites = await client.invite_get_channel(channel)
    
    pages=[Embed(description=chunk) for chunk in pchunkify(invites,write_parents=False,show_code=False)]
    await Pagination(client,message.channel,pages,120.)

async def _help_invites(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('invites',(
        'I can list you the invites of the guild.\n'
        f'Usage: `{prefix}invites <channel>`\n'
        'If `channel` is passed, I ll check the invites only at that channel.'
            ),color=KOISHI_HELP_COLOR).add_footer(
            'Guild only! You must have manage_channel permission to use this command.')
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('invites',_help_invites,checker=KOISHI_HELPER.check_permission(Permission().update_by_keys(manage_channel=True)))

def generate_love_level():
    value = {
        'titles' : (
            f'{BUILTIN_EMOJIS["blue_heart"]:e} There\'s no real connection between you two {BUILTIN_EMOJIS["blue_heart"]:e}',
                ),
        'text' : (
            'The chance of this relationship working out is really low. You '
            'can get it to work, but with high costs and no guarantee of '
            'working out. Do not sit back, spend as much time together as '
            'possible, talk a lot with each other to increase the chances of '
            'this relationship\'s survival.'
                ),
            }

    for x in range(0,2):
        yield value

    value = { 
        'titles' : (
            f'{BUILTIN_EMOJIS["blue_heart"]:e} A small acquaintance {BUILTIN_EMOJIS["blue_heart"]:e}',
                ),
        'text' : (
            'There might be a chance of this relationship working out somewhat '
            'well, but it is not very high. With a lot of time and effort '
            'you\'ll get it to work eventually, however don\'t count on it. It '
            'might fall apart quicker than you\'d expect.'
                ),
            }
    
    for x in range(2,6):
        yield value

    value = { 
        'titles' : (
            f'{BUILTIN_EMOJIS["purple_heart"]:e} You two seem like casual friends {BUILTIN_EMOJIS["purple_heart"]:e}',
                ),
        'text' : (
            'The chance of this relationship working is not very high. You both '
            'need to put time and effort into this relationship, if you want it '
            'to work out well for both of you. Talk with each other about '
            'everything and don\'t lock yourself up. Spend time together. This '
            'will improve the chances of this relationship\'s survival by a lot.'
                ),
            }

    for x in range(6,21):
        yield value

    value = { 
        'titles' : (
            f'{BUILTIN_EMOJIS["heartpulse"]:e} You seem like you are good friends {BUILTIN_EMOJIS["heartpulse"]:e}',
                ),
        'text' : (
            'The chance of this relationship working is not very high, but its '
            'not that low either. If you both want this relationship to work, '
            'and put time and effort into it, meaning spending time together, '
            'talking to each other etc., than nothing shall stand in your way.'
                ),
            }

    for x in range(21,31):
        yield value


    value = { 
        'titles':(
            f'{BUILTIN_EMOJIS["cupid"]:e} You two are really close aren\'t you? {BUILTIN_EMOJIS["cupid"]:e}',
                ),
        'text' : (
            'Your relationship has a reasonable amount of working out. But do '
            'not overestimate yourself there. Your relationship will suffer '
            'good and bad times. Make sure to not let the bad times destroy '
            'your relationship, so do not hesitate to talk to each other, '
            'figure problems out together etc.'
                ),
            }

    for x in range(31,46):
        yield value
    
    value = { 
        'titles' : (
            f'{BUILTIN_EMOJIS["heart"]:e} So when will you two go on a date? {BUILTIN_EMOJIS["heart"]:e}',
                ),
        'text' : (
            'Your relationship will most likely work out. It won\'t be perfect '
            'and you two need to spend a lot of time together, but if you keep '
            'on having contact, the good times in your relationship will '
            'outweigh the bad ones.'
                ),
            }

    for x in range(46,61):
        yield value

    value = { 
        'titles' : (
            f'{BUILTIN_EMOJIS["two_hearts"]:e} Aww look you two fit so well together {BUILTIN_EMOJIS["two_hearts"]:e}',
                ),
        'text' : (
            'Your relationship will most likely work out well. Don\'t hesitate '
            'on making contact with each other though, as your relationship '
            'might suffer from a lack of time spent together. Talking with '
            'each other and spending time together is key.'
                ),
            }

    for x in range(61,86):
        yield value

    value = { 
        'titles' : (
            f'{BUILTIN_EMOJIS["sparkling_heart"]:e} Love is in the air {BUILTIN_EMOJIS["sparkling_heart"]:e}',
            f'{BUILTIN_EMOJIS["sparkling_heart"]:e} Planned your future yet? {BUILTIN_EMOJIS["sparkling_heart"]:e}',
                ),
        'text' : (
            'Your relationship will most likely work out perfect. This '
            'doesn\'t mean thought that you don\'t need to put effort into it. '
            'Talk to each other, spend time together, and you two won\'t have '
            'a hard time.'
                ),
            }

    for x in range(86,96):
        yield value

    value = { 
        'titles' : (
            f'{BUILTIN_EMOJIS["sparkling_heart"]:e} When will you two marry? {BUILTIN_EMOJIS["sparkling_heart"]:e}',
            f'{BUILTIN_EMOJIS["sparkling_heart"]:e} Now kiss already {BUILTIN_EMOJIS["sparkling_heart"]:e}',
                ),
        'text' : (
            'You two will most likely have the perfect relationship. But don\'t '
            'think that this means you don\'t have to do anything for it to '
            'work. Talking to each other and spending time together is key, '
            'even in a seemingly perfect relationship.'
                ),
            }

    for x in range(96,101):
        yield value

LOVE_VALUES=tuple(generate_love_level())
del generate_love_level

async def _help_love(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('love',(
        'How much you two fit together?'
        f'Usage: `{prefix}user *user*`\n'
        ),color=KOISHI_HELP_COLOR)
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('love',_help_love)

@infos(parser_failure_handler=show_help(_help_love))
async def love(client,message,target:Converter('user',flags=ConverterFlag.user_default.update_by_keys(everywhere=True))):
    source=message.author
    if source is target:
        await _help_love(client, message)
        return
    
    percent=((source.id&0x1111111111111111111111)+(target.id&0x1111111111111111111111))%101
    element=LOVE_VALUES[percent]
    
    embed=Embed(
        choice(element['titles']),
        f'{source:f} {BUILTIN_EMOJIS["heart"]:e} {target:f} scored {percent}%!',
        0xad1457,
            )
    embed.add_field('My advice:',element['text'])

    await client.message_create(message.channel,embed=embed)

class once(object):
    __slots__=('content','embed','ready')
    def __init__(self,content='',embed=None):
        self.ready=False
        self.content=content
        self.embed=embed
    async def __call__(self,client,message,content):
        if self.ready:
            await client.message_create(message.channel,self.content,self.embed)

ABOUT=once()
infos(ABOUT,'about')
def update_about(client):
    implement=sys.implementation
    text=''.join([
        f'Me, {client.full_name}, I am general purpose/test client.',
        '\n',
        'My code base is',
        ' [open source](https://github.com/HuyaneMatsu/Koishi). ',
        'One of the main goal of my existence is to test the best *cough*',
        ' [discord API wrapper](https://github.com/HuyaneMatsu/hata). ',
        '\n\n',
        f'My Masutaa is {client.owner.full_name} (send neko pictures pls).\n\n',
        '**Client info**\n',
        f'Python version: {implement.version[0]}.{implement.version[1]}',
        f'{"" if implement.version[3]=="final" else " "+implement.version[3]}\n',
        f'Interpreter: {implement.name}\n',
        f'Clients: {len(CLIENTS)}\n',
        f'Users: {len(USERS)}\n',
        f'Guilds: {len(GUILDS)}\n',
        f'Channels: {len(CHANNELS)}\n',
        'Power level: over 9000!\n',
            ])
    embed=Embed('About',text,0x5dc66f)
    embed.add_thumbnail(client.application.icon_url_as(size=128))
    ABOUT.embed=embed
    ABOUT.ready=True

async def _help_about(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('about',(
        'Just some information about me.'
        f'Usage: `{prefix}about`'
            ),color=KOISHI_HELP_COLOR)
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('about',_help_about)


@infos(checks=[checks.has_guild_permissions(Permission().update_by_keys(view_audit_log=True))])
async def logs(client,message,guild:Converter('guild'),user:User=None,event_name:str=''):
    if not guild.cached_permissions_for(client).view_audit_log:
        await client.message_create(message.channel,
            'I have no permissions at the guild, to request audit logs.')
        return
    
    event=None
    
    while True:
        if not event_name:
            event=None
            break
        
        try:
            event=AuditLogEvent.INSTANCES[int(event_name)]
            break
        except (KeyError,ValueError):
            pass
        
        try:
            event=getattr(AuditLogEvent,event_name.upper())
            break
        except AttributeError:
            pass
        
        event=None
        break

    with client.keep_typing(message.channel):
        iterator = client.audit_log_iterator(guild,user,event)
        await iterator.load_all()
        logs = iterator.transform()
    
    await Pagination(client,message.channel,[Embed(description=chunk) for chunk in pchunkify(logs)])

async def _help_logs(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('logs',(
        'I can list you the audit logs of the guild.\n'
        f'Usage: `{prefix}logs <user> <event>`\n'
        'Both `user` and `event` is optional.\n'
        '`user` is the user, who executed the logged oprations.\n'
        'The `event` is the internal value or name of the type of the '
        'operation.'
            ),color=KOISHI_HELP_COLOR).add_footer(
            'Guild only!')
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('logs',_help_logs,checker=KOISHI_HELPER.check_permission(Permission().update_by_keys(view_audit_log=True)))


@infos(checks=[checks.has_guild_permissions(Permission(8)),],)
async def message(client,message,message_id:int,channel:Converter('channel', default_code='message.channel')):
    if not channel.cached_permissions_for(client).can_read_message_history:
        await client.message_create(message.channel,
            'I am unable to read the messages at the specified channel.')
        return
    
    try:
        target_message = await client.message_get(channel,message_id)
    except DiscordException as err:
        await client.message_create(message.channel,err.__repr__())
        return
    await Pagination(client,message.channel,[Embed(description=chunk) for chunk in pchunkify(target_message)])

async def _help_message(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('message',(
        'If you want, I show the representation of a message.\n'
        f'Usage: `{prefix}message *message_id* <channel>`\n'
        'By default `channel` is the channel, where you used the command.'
            ),color=KOISHI_HELP_COLOR).add_footer(
            'Guild only! Administrator only!')
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('message',_help_message,checker=KOISHI_HELPER.check_permission(Permission().update_by_keys(administrator=True)))

@infos(checks=[checks.has_guild_permissions(Permission(8))])
async def message_pure(client,message,message_id:int,channel:Converter('channel',default_code='message.channel')):
    if not channel.cached_permissions_for(client).can_read_message_history:
        await client.message_create(message.channel,
            'I am unable to read the messages at the specified channel.')
        return
    
    try:
        data = await client.http.message_get(channel.id,message_id)
    except DiscordException as err:
        await client.message_create(message.channel,repr(err))
        return
    
    await Pagination(client,message.channel,[Embed(description=chunk) for chunk in cchunkify(json.dumps(data,indent=4,sort_keys=True).splitlines())])

async def _help_message_pure(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('message_pure',(
        'If you want, I show the pure json representing a message.\n'
        f'Usage: `{prefix}message_pure *message_id* <channel>`\n'
        'By default `channel` is the channel, where you used the command.'
            ),color=KOISHI_HELP_COLOR).add_footer(
            'Guild only! Administrator only!')
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('message_pure',_help_message_pure,checker=KOISHI_HELPER.check_permission(Permission().update_by_keys(administrator=True)))

class role_details(object):
    __slots__=('cache','guild','roles',)
    def __new__(cls,client,channel):
        self=object.__new__(cls)
        self.roles=list(reversed(channel.guild.roles))
        self.cache=[None for _ in range(self.roles.__len__()+1)]
        self.createpage0(channel.guild)
        #we return awaitable, so it is OK
        return embedination_rr(client,channel,self)
        
    def __len__(self):
        return self.cache.__len__()
    
    def createpage0(self,guild):
        embed=Embed(f'Roles of **{guild.name}**:',
            '\n'.join([role.mention for role in self.roles]),
            color=guild.icon&0xFFFFFF if guild.icon else (guild.id>>22)&0xFFFFFF)
        embed.add_footer(f'Page 1 /  {len(self.cache)}')
        self.cache[0]=embed
    
    def __getitem__(self,index):
        page=self.cache[index]
        if page is None:
            return self.create_page(index)
        return page

    def create_page(self,index):
        role=self.roles[index-1]
        embed=Embed(role.name,
            '\n'.join([
                f'id : {role.id!r}',
                f'color : {role.color.as_html}',
                f'permission number : {role.permissions}',
                f'managed : {role.managed}',
                f'separated : {role.separated}',
                f'mentionable : {role.mentionable}',
                '\nPermissions:\n```diff',
                *(f'{"+" if value else "-"}{key}' for key,value in role.permissions.items()),
                '```',
                    ]),
            color=role.color)
        embed.add_footer(f'Page {index+1} /  {len(self.cache)}')

        self.cache[index]=embed
        return embed

class embedination_rr(object):
    LEFT2   = BUILTIN_EMOJIS['rewind']
    LEFT    = BUILTIN_EMOJIS['arrow_backward']
    RIGHT   = BUILTIN_EMOJIS['arrow_forward']
    RIGHT2  = BUILTIN_EMOJIS['fast_forward']
    RESET   = BUILTIN_EMOJIS['arrows_counterclockwise']
    CANCEL  = BUILTIN_EMOJIS['x']
    EMOJIS  = (LEFT2,LEFT,RIGHT,RIGHT2,RESET,CANCEL)
    
    __slots__ = ('canceller', 'channel', 'client', 'message', 'page', 'pages',
        'task_flag', 'timeouter')

    async def __new__(cls,client,channel,pages):
        self=object.__new__(cls)
        self.client=client
        self.channel=channel
        self.pages=pages
        self.page=0
        self.canceller=cls._canceller
        self.task_flag=GUI_STATE_READY
        self.timeouter=None
        
        try:
            message = await client.message_create(self.channel,embed=self.pages[0])
        except:
            self.message=None
            raise
        
        self.message=message

        if not channel.cached_permissions_for(client).can_add_reactions:
            return self
        
        message.weakrefer()
        
        if len(self.pages)>1:
            for emoji in self.EMOJIS:
                await client.reaction_add(message,emoji)
        else:
            await client.reaction_add(message,self.CANCEL)
        
        client.events.reaction_add.append(self,message)
        client.events.reaction_delete.append(self,message)
        self.timeouter=Timeouter(client.loop,self,timeout=300.)
        return self
    
    async def __call__(self,client,emoji,user):
        if user.is_bot or (emoji not in self.EMOJIS):
            return
        
        message=self.message
        
        if self.channel.cached_permissions_for(client).can_manage_messages:
            if not message.did_react(emoji,user):
                return

            task=Task(client.reaction_delete(message,emoji,user),client.loop)
            if __debug__:
                task.__silence__()
            
        task_flag=self.task_flag
        if task_flag!=GUI_STATE_READY:
            if task_flag==GUI_STATE_SWITCHING_PAGE:
                if emoji is self.CANCEL:
                    self.task_flag=GUI_STATE_CANCELLING
                return

            # ignore GUI_STATE_CANCELLED and GUI_STATE_SWITCHING_CTX
            return
        
        while True:
            if emoji is self.LEFT:
                page=self.page-1
                break
                
            if emoji is self.RIGHT:
                page=self.page+1
                break
                
            if emoji is self.RESET:
                page=0
                break
                
            if emoji is self.CANCEL:
                self.task_flag=GUI_STATE_CANCELLED
                try:
                    await client.message_delete(message)
                except BaseException as err:
                    self.cancel()
                    
                    if isinstance(err,ConnectionError):
                        # no internet
                        return
                    
                    if isinstance(err,DiscordException):
                        if err.code == ERROR_CODES.missing_access: # client removed
                            return
                    
                    await client.events.error(client,f'{self!r}.__call__',err)
                    return
                
                else:
                    self.cancel()
                    return
            
            if emoji is self.LEFT2:
                page=self.page-10
                break
                
            if emoji is self.RIGHT2:
                page=self.page+10
                break

            return
        
        Task(self._reaction_delete(emoji,user),client.loop)

        if page<0:
            page=0
        elif page>=len(self.pages):
            page=len(self.pages)-1
        
        if self.page==page:
            return

        self.page=page
        self.task_flag=GUI_STATE_SWITCHING_PAGE
        try:
            await client.message_edit(message,embed=self.pages[page])
        except BaseException as err:
            self.task_flag=GUI_STATE_CANCELLED
            self.cancel()
            
            if isinstance(err,ConnectionError):
                # no internet
                return
            
            if isinstance(err,DiscordException):
                if err.code in (
                        ERROR_CODES.missing_access, # client removed
                        ERROR_CODES.unknown_message, # message already deleted
                            ):
                    return
            
            # We definitedly do not want to silence `ERROR_CODES.invalid_form_body`
            await client.events.error(client,f'{self!r}.__call__',err)
            return

        if self.task_flag==GUI_STATE_CANCELLING:
            self.task_flag=GUI_STATE_CANCELLED
            try:
                await client.message_delete(message)
            except BaseException as err:
                
                if isinstance(err,ConnectionError):
                    # no internet
                    return
                
                if isinstance(err,DiscordException):
                    if err.code==ERROR_CODES.missing_access: # client removed
                        return
                
                await client.events.error(client,f'{self!r}.__call__',err)
                return
            
            return
        
        self.task_flag=GUI_STATE_READY
        
        self.timeouter.set_timeout(150.0)
        
    @staticmethod
    async def _canceller(self,exception,):
        client=self.client
        message=self.message
        
        client.events.reaction_add.remove(self,message)
        client.events.reaction_delete.remove(self,message)

        if self.task_flag==GUI_STATE_SWITCHING_CTX:
            # the message is not our, we should not do anything with it.
            return
        
        self.task_flag=GUI_STATE_CANCELLED
        
        if exception is None:
            return
        
        if isinstance(exception,TimeoutError):
            if self.channel.cached_permissions_for(client).can_manage_messages:
                try:
                    await client.reaction_clear(message)
                except BaseException as err:
                    
                    if isinstance(err,ConnectionError):
                        # no internet
                        return
                    
                    if isinstance(err,DiscordException):
                        if err.code in (
                                ERROR_CODES.missing_access, # client removed
                                ERROR_CODES.unknown_message, # message deleted
                                ERROR_CODES.missing_permissions, # permissions changed meanwhile
                                    ):
                            return
                    
                    await client.events.error(client,f'{self!r}._canceller',err)
                    return
            return
        
        timeouter=self.timeouter
        if timeouter is not None:
            timeouter.cancel()
        #we do nothing
    
    def cancel(self,exception=None):
        canceller=self.canceller
        if canceller is None:
            return
        
        self.canceller=None
        
        timeouter=self.timeouter
        if timeouter is not None:
            timeouter.cancel()
        
        return Task(canceller(self,exception),self.client.loop)

    async def _reaction_delete(self,emoji,user):
        client=self.client
        try:
            await client.reaction_delete(self.message,emoji,user)
        except BaseException as err:
            
            if isinstance(err,ConnectionError):
                # no internet
                return
            
            if isinstance(err,DiscordException):
                if err.code in (
                        ERROR_CODES.missing_access, # client removed
                        ERROR_CODES.unknown_message, # message deleted
                        ERROR_CODES.missing_permissions, # permissions changed meanwhile
                            ):
                    return
            
            await client.events.error(client,f'{self!r}._reaction_delete',err)
            return

@infos
async def roles(client,message,content):
    if message.guild is None:
        return
    await role_details(client,message.channel)

async def _help_roles(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('roles',(
        'Cutie, do you want me, to list the roles of the guild and their '
        'permissions?\n'
        f'Usage: `{prefix}roles`'
            ),color=KOISHI_HELP_COLOR).add_footer(
            'Guild only!')
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('roles',_help_roles)


@infos
async def avatar(client, message, user : Converter('user',flags=ConverterFlag.user_default.update_by_keys(everywhere=True),default_code='message.author')):
    color = user.avatar&0xffffff
    if color==0:
        color = user.default_avatar.color
    
    url=user.avatar_url_as(size=4096)
    embed=Embed(f'{user:f}\'s avatar', color=color, url=url)
    embed.add_image(url)
    
    await client.message_create(message.channel, embed=embed)

async def _help_avatar(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('avatar',(
        'Pure 4K user avatar showcase!\n'
        f'Usage: `{prefix}avatar <user>`\n'
        'If no `user` is passed, I will showcase your avatar.'
            ),color=KOISHI_HELP_COLOR)
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('avatar',_help_avatar)

@infos(name='guild-icon')
async def guild_icon(client, message, content):
    guild = message.guild
    if guild is None:
        return
    
    icon_url = guild.icon_url_as(size=4096)
    if icon_url is None:
        embed=Embed(description=f'`{guild.name}` has no icon.')
    else:
        color=guild.icon&0xffffff
        embed=Embed(f'{guild.name}\' icon', color=color, url=icon_url)
        embed.add_image(icon_url)
    
    await client.message_create(message.channel,embed=embed)

async def _help_guild_icon(client,message):
    prefix=client.events.message_create.prefix(message)
    embed=Embed('guild-icon',(
        'Do you wanna see the guild\'s icon in 4K?!\n'
        f'Usage: `{prefix}guild-icon`\n'
            ),color=KOISHI_HELP_COLOR).add_footer(
            'Guild only!')
    await client.message_create(message.channel,embed=embed)

KOISHI_HELPER.add('guild-icon',_help_guild_icon)

