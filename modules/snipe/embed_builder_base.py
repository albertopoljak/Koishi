__all__ = ()

from hata import InteractionType, Embed, Emoji


def add_embed_author(embed, event, type_name, message_url):
    """
    Adds the event's user as embed author.
    
    Parameters
    ----------
    embed : ``Embed``
        The embed to extend.
    event : ``InteractionEvent``
        The received interaction event.
    type_name : `str`
        The action's type's name.
    message_url : `None`, `str`
        The sniped message's url. Can be `None` if the event originates from a slash command.
    """
    user = event.user
    
    embed.add_author(
        f'{user.name_at(event.guild_id)}\'s sniped {type_name}! ({user.id})',
        user.avatar_url,
        message_url,
    )


def add_embed_footer(embed, entity):
    """
    Adds the source of the entity as an embed footer.
    
    Parameters
    ----------
    embed : ``Embed``
        The embed to extend.
    entity : ``Emoji``, ``Sticker``
        The entity in context.
    """
    guild = entity.guild
    if (guild is None):
        footer_text = 'Unknown guild'
        footer_icon_url = None
    else:
        footer_text = f'from {guild.name} ({guild.id})'
        footer_icon_url = guild.icon_url
    
    embed.add_footer(
        footer_text,
        footer_icon_url,
    )


def is_entity_unicode_emoji(entity):
    """
    Returns whether the given entity is a unicode emoji.
    
    Parameters
    ----------
    entity : ``Emoji``, ``Sticker``
        The entity to check.
    
    Returns
    -------
    is_unicode_emoji : `bool`
    """
    return isinstance(entity, Emoji) and entity.is_unicode_emoji()


def is_url_raster_graphics(url):
    """
    Returns whether the given url references a raster graphic image.
    
    Parameters
    ----------
    url : `None`, `str`
        The url to check.
    
    Returns
    -------
    is_url_raster_graphics : `bool`
    """
    if url is None:
        return False
    
    return url.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))


def create_base_embed(entity, title):
    """
    Creates a base embed used to represent both an embed and a sticker..
    
    Parameters
    ----------
    entity : ``Emoji``, ``Sticker``
        The entity's representation.
    title : `str`
        The embed's title.
    
    Returns
    -------
    embed : ``Embed``
    """
    entity_url = entity.url
    
    embed = Embed(
        title,
        color = (entity.id >> 22) & 0xffffff,
        url = entity_url,
    ).add_field(
        'Name',
        f'```\n{entity.name}\n```',
        inline = True,
    ).add_field(
        'Internal identifier' if is_entity_unicode_emoji(entity) else 'Identifier',
        f'```\n{entity.id}\n```',
        inline = True,
    )
    
    if is_url_raster_graphics(entity_url):
        embed.add_image(entity_url)
    
    return embed


def copy_extra_fields(embed, event):
    """
    Copies the extra fields (author and footer) of the event's embed to the given one.
    
    Parameters
    ----------
    embed : ``Embed``
        The embed to extend.
    event : ``InteractionEvent``
        The received interaction event.
    
    Returns
    -------
    copied : `bool`
    """
    if event.type is InteractionType.message_component:
        source_embed = event.message.embed
        if (source_embed is not None):
            embed.author = source_embed.author
            embed.footer = source_embed.footer
            return True
    
    return False
