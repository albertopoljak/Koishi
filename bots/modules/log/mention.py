from hata import Client, Embed, DATETIME_FORMAT_CODE, Status, elapsed_time, ACTIVITY_TYPES
from hata.ext.extension_loader import require

from bot_utils.constants import CHANNEL__NEKO_DUNGEON__LOG_MENTION, GUILD__NEKO_DUNGEON, CATEGORY__NEKO_DUNGEON__BIG_BRO

require(Satori=Client)


CLEAN_CONTENT_MAX_LENGTH = 1000
USER_MENTION_MAX = 7
ROLE_MENTION_MAX = 5
SEPARATOR_LINE = '\\_'*30


Satori: Client

def setup(lib):
    Satori.events.message_create.append(GUILD__NEKO_DUNGEON, mention_logger)


def teardown(lib):
    Satori.events.message_create.remove(GUILD__NEKO_DUNGEON, mention_logger)


async def mention_logger(client, message):
    everyone_mention = message.everyone_mention
    user_mentions = message.user_mentions
    role_mentions = message.role_mentions
    if (not everyone_mention) and (user_mentions is None) and (role_mentions is None):
        return
    
    content_parts = []
    
    author = message.author
    
    guild = message.guild
    guild_profile = author.get_guild_profile_for(guild)
    if guild_profile is None:
        nick = None
    else:
        nick = guild_profile.nick
    
    content_parts.append('**Author:** ')
    content_parts.append(author.full_name)
    content_parts.append(' ')
    if (nick is not None):
        content_parts.append('[')
        content_parts.append(nick)
        content_parts.append('] ')
    content_parts.append('(')
    content_parts.append(repr(author.id))
    content_parts.append(')\n')
    
    channel = message.channel
    content_parts.append('**Channel:** ')
    content_parts.append(channel.display_name)
    content_parts.append(' (')
    content_parts.append(repr(channel.id))
    content_parts.append(')\n')
    
    message_id = message.id
    content_parts.append('**Message id**: ')
    content_parts.append(repr(message_id))
    content_parts.append('\n')
    
    message_type = message.type
    content_parts.append('**Message type**: ')
    content_parts.append(message_type.name)
    content_parts.append(' (')
    content_parts.append(repr(message_type.value))
    content_parts.append(')\n')
    
    created_at = message.created_at
    content_parts.append('**Created at**: ')
    content_parts.append(created_at.__format__(DATETIME_FORMAT_CODE))
    content_parts.append('\n')
    
    content_length = len(message)
    content_parts.append('**Message Length:** ')
    content_parts.append(repr(content_length))
    content_parts.append('\n')
    
    clean_content = message.clean_content
    if (clean_content is not None):
        content_parts.append('\n**Content**:\n')
        content_parts.append(SEPARATOR_LINE)
        content_parts.append('\n')
        
        clean_content_length = len(clean_content)
        if clean_content_length > CLEAN_CONTENT_MAX_LENGTH:
            clean_content = clean_content[:CLEAN_CONTENT_MAX_LENGTH]
            truncated = clean_content_length - CLEAN_CONTENT_MAX_LENGTH
        else:
            truncated = 0
        
        content_parts.append(clean_content)
        if truncated:
            content_parts.append('\n*<Truncated )')
            content_parts.append(repr(truncated))
            content_parts.append('>*')
    
    description = ''.join(content_parts)
    embed = Embed('Ping Log!', description)
    
    if everyone_mention:
        embed.add_field('Everyone mention', 'Hecatia Yeah!')
    
    if (user_mentions is not None):
        content_parts = []
        
        mention_count = len(user_mentions)
        if mention_count > USER_MENTION_MAX:
            truncated = mention_count - USER_MENTION_MAX
        else:
            truncated = 0
        
        content_parts.append('**Total:** ')
        content_parts.append(repr(mention_count))
        if truncated:
            content_parts.append(' (')
            content_parts.append(repr(truncated))
            content_parts.append(' truncated)')
        content_parts.append('\n')
        content_parts.append(SEPARATOR_LINE)
        content_parts.append('\n')
        
        index = 0
        limit = mention_count-truncated
        
        while True:
            user = user_mentions[index]
            index += 1
            
            guild_profile = user.get_guild_profile_for(guild)
            if guild_profile is None:
                nick = None
            else:
                nick = guild_profile.nick
            
            content_parts.append('**')
            content_parts.append(repr(index))
            content_parts.append('.:** ')
            content_parts.append(user.full_name)
            content_parts.append(' ')
            if (nick is not None):
                content_parts.append('[')
                content_parts.append(nick)
                content_parts.append('] ')
            content_parts.append('(')
            content_parts.append(repr(user.id))
            content_parts.append(')')
            
            if index == limit:
                break
            
            content_parts.append('\n')
            continue
        
        field_value = ''.join(content_parts)
        
        embed.add_field('User mentions', field_value)
    
    if (role_mentions is not None):
        content_parts = []
        
        mention_count = len(role_mentions)
        if mention_count > ROLE_MENTION_MAX:
            truncated = mention_count - ROLE_MENTION_MAX
        else:
            truncated = 0
        
        content_parts.append('**Total:** ')
        content_parts.append(repr(mention_count))
        if truncated:
            content_parts.append(' (')
            content_parts.append(repr(truncated))
            content_parts.append(' truncated)')
        content_parts.append('\n')
        content_parts.append(SEPARATOR_LINE)
        content_parts.append('\n')
        
        index = 0
        limit = mention_count-truncated
        
        while True:
            role = role_mentions[index]
            index += 1
            
            content_parts.append('**')
            content_parts.append(repr(index))
            content_parts.append('.:** ')
            content_parts.append(role.name)
            content_parts.append(' (')
            content_parts.append(repr(role.id))
            content_parts.append(')')
            
            if index == limit:
                break
            
            content_parts.append('\n')
            continue
        
        field_value = ''.join(content_parts)
        
        embed.add_field('Role mentions', field_value)
    
    await client.message_create(CHANNEL__NEKO_DUNGEON__LOG_MENTION, embed=embed, allowed_mentions=None)
