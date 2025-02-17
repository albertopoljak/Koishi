__all__ = ()

from datetime import datetime as DateTime

from hata import DATETIME_FORMAT_CODE, Embed, elapsed_time


def render_roles_into(into, roles):
    """
    Puts the given roles representation into the given string container. 
    
    Parameters
    ----------
    into : `list` of `str`
        Container.
    roles : `None`, `tuple` of ``Role``
        Date time to convert.
    
    Returns
    -------
    into : `list` of `str`
    """
    if roles is None:
        into.append('*none*')
    
    else:
        roles_reversed = [*reversed(roles)]
        
        length = len(roles_reversed)
        if length > 20:
            removed = length - 20
            length = 20
            del roles_reversed[20:]
        
        else:
            removed = 0
        
        index = 0
        
        while True:
            role = roles_reversed[index]
            into.append(role.mention)
            
            index += 1
            if index == length:
                break
            
            into.append(', ')
            continue
        
        if removed:
            into.append(', ... +')
            into.append(str(removed))
        
    return into


def render_date_time_into(into, date_time, add_ago):
    """
    Puts the given date time's string value into the given string container. 
    
    Parameters
    ----------
    into : `list` of `str`
        Container.
    date_time : `None`, `DateTime`
        Date time to convert.
    add_ago : `bool`
        Whether ago should be added to the relative representation.
    
    Returns
    -------
    into : `list` of `str`
    """
    if date_time is None:
        into.append('*none*')
    
    else:
        into.append(format(date_time, DATETIME_FORMAT_CODE))
        into.append(' [*')
        into.append(elapsed_time(date_time))
        into.append(' ')
        if add_ago:
            into.append('ago')
        into.append('*]')
    
    return into


def add_user_info_embed_field(embed, user):
    """
    Adds user info field to the given embed.
    
    Parameters
    ----------
    embed : ``Embed``
        The embed to add the field to.
    user : ``ClientUserBase``
        The respective user.
    
    Returns
    -------
    embed : ``Embed``
    """
    value_parts = ['Created: ']
    render_date_time_into(value_parts, user.created_at, True)
    value_parts.append('\nProfile: ')
    value_parts.append(user.mention)
    value_parts.append('\nID: ')
    value_parts.append(str(user.id))
    
    return embed.add_field('User Information', ''.join(value_parts))


def add_user_guild_profile_info_embed_field(embed, guild_profile):
    """
    Adds user guild profile info field to the given embed.
    
    Parameters
    ----------
    embed : ``Embed``
        The embed to add the field to.
    guild_profile : ``GuildProfile``
        The user's guild profile.
    
    Returns
    -------
    embed : ``Embed``
    """
    value_parts = ['Joined: ']
    render_date_time_into(value_parts, guild_profile.joined_at, True)
    value_parts.append('\nRoles: ')
    render_roles_into(value_parts, guild_profile.roles)
    
    nick = guild_profile.nick
    if (nick is not None):
        value_parts.append('\nNick: ')
        value_parts.append(nick)
    
    
    boosts_since = guild_profile.boosts_since
    if (boosts_since is not None):
        value_parts.append('\nBooster since: ')
        render_date_time_into(value_parts, boosts_since, False)
    
    
    timed_out_until = guild_profile.timed_out_until
    if (timed_out_until is not None) and (timed_out_until > DateTime.utcnow()):
        value_parts.append('\nTimed out until: ')
        render_date_time_into(value_parts, timed_out_until, False)
    
    return embed.add_field('In guild profile', ''.join(value_parts))

