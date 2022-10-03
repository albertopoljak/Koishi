__all__ = ()

from datetime import datetime as DateTime

from hata import Embed, KOKORO, datetime_to_unix_time
from hata.ext.slash import Button, Row
from scarletio import LOOP_TIME

from ...constants import (
    BOORU_COLOR, EMOJI_NEW, EMOJI_TAGS, NSFW_BOORU_ENDPOINT, NSFW_BOORU_PROVIDER, NSFW_TAGS_BANNED, SAFE_BOORU_ENDPOINT,
    SAFE_BOORU_PROVIDER, SAFE_TAGS_BANNED
)
from ...helpers import add_provider
from ...image_handler import ImageHandlerBooru



def setup(lib):
    """
    Called after the plugin is loaded.
    
    Parameters
    ----------
    lib : `ModuleType`
        This module.
    """
    start_cleanup_handle()


def teardown(lib):
    """
    Called before the plugin is destroyed.
    
    Parameters
    ----------
    lib : `ModuleType`
        This module.
    """
    stop_cleanup_handle()


SESSION_ID = datetime_to_unix_time(DateTime.utcnow())

CLEANUP_AFTER = 300.0
CLEANUP_INTERVAL = 300.0

CUSTOM_ID_NEW_DISABLED = 'booru.ex.new'
CUSTOM_ID_TAGS_DISABLED = 'booru.ex.tags'

CACHES = {}


def build_booru_embed(image_detail):
    """
    Builds a booru embed.
    
    Parameters
    ----------
    image_detail : ``ImageDetail``
        The image detail to work from.
    
    Returns
    -------
    embed : ``Embed``
    """
    if (image_detail is None):
        embed = Embed(None, '*Could not get any images, please try again later.*', color = BOORU_COLOR)
    
    else:
        embed = Embed(
            'Link', url = image_detail.url, color = BOORU_COLOR,
        ).add_image(
            image_detail.url,
        )
        
        add_provider(embed, image_detail)
    
    return embed


def build_booru_components(cache_id):
    """
    Builds the components of the displayed under the embed.
    
    Parameters
    ----------
    cache_id : `int`
        The identifier of the cache.
    
    Returns
    -------
    components : ``ComponentBase``
    """
    return Row(
        Button(
            emoji = EMOJI_NEW,
            custom_id = f'booru.{SESSION_ID}.{cache_id}.new',
        ),
        Button(
            emoji = EMOJI_TAGS,
            custom_id = f'booru.{SESSION_ID}.{cache_id}.tags',
        ),
    )


def build_booru_disabled_components():
    """
    Builds disabled components.
    
    Returns
    -------
    components : ``ComponentBase``
    """
    return Row(
        Button(
            emoji = EMOJI_NEW,
            custom_id = CUSTOM_ID_NEW_DISABLED,
            enabled = False,
        ),
        Button(
            emoji = EMOJI_TAGS,
            custom_id = CUSTOM_ID_NEW_DISABLED,
            enabled = False,
        ),
    )



def build_tag_embed(image_detail):
    """
    Builds tag embed for the given image detail.
    
    Parameters
    ----------
    image_detail : `None`, ``ImageDetail``
        The image detail to build embed for.
    
    Returns
    -------
    embed : ``Embed``
    """
    if image_detail is None:
        tags = None
    else:
        set_tags = image_detail.tags
        if (set_tags is None) or (not set_tags):
            tags = None
        else:
            tags = sorted(set_tags)
    
    if tags is None:
        description = '*none*'
    else:
        description = ' | '.join([tag.replace('_', '\_') for tag in set_tags])
    
    if image_detail is None:
        url = None
    else:
        url = image_detail.url
    
    embed = Embed(
        'Tags',
        description,
        url = url,
        color = BOORU_COLOR,
    )
    
    if (url is not None):
        embed.add_thumbnail(url)
    
    return embed


class ImageCache:
    """
    Booru image cache.
    
    Attributes
    ----------
    cache_id : `int`
        The identifier of the cache.
    handler : ``ImageHandlerBooru``
        Handler used to request images.
    last : `None`, ``ImageDetail``
        The last show image detail.
    last_call : `float`
        When was the handler last called.
    """
    CACHE_ID_COUNTER = 0
    CLEANUP_HANDLE = None
    
    __slots__ = ('cache_id', 'handler', 'last', 'last_call')
    
    def __new__(cls, safe, raw_tags):
        """
        Creates a new image cache for booru commands.
        
        Parameters
        ----------
        safe : `bool`
            Whether we want safe images.
        raw_tags : `str`
            Joined tags to query for.
        """
        requested_tags = {*raw_tags.split()}
        
        if safe:
            endpoint = SAFE_BOORU_ENDPOINT
            provider = SAFE_BOORU_PROVIDER
            banned_tags = SAFE_TAGS_BANNED
        else:
            endpoint = NSFW_BOORU_ENDPOINT
            provider = NSFW_BOORU_PROVIDER
            banned_tags = NSFW_TAGS_BANNED
        
        handler = ImageHandlerBooru(provider, endpoint, None, banned_tags, requested_tags, False)
        
        cache_id = cls.CACHE_ID_COUNTER
        cls.CACHE_ID_COUNTER = cache_id + 1
        
        self = object.__new__(cls)
        self.cache_id = cache_id
        self.handler = handler
        self.last = None
        self.last_call = 0.0
        return self
    
    
    async def invoke_initial(self, client, event):
        """
        Invokes the booru cacher to produce a message with an image.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client instance who received the event.
        event : ``InteractionEvent``
            The received event.
        
        Returns
        -------
        success : `bool`
            Whether we ended up with great success.
        """
        image_detail = await self.handler.get_image(client, event)
        
        embed = build_booru_embed(image_detail)
        
        if image_detail is None:
            components = None
        else:
            components = build_booru_components(self.cache_id)
        
        if event.is_unanswered():
            function = type(client).interaction_response_message_create
        else:
            function = type(client).interaction_response_message_edit
        
        await function(
            client,
            event,
            embed = embed,
            components = components,
        )
        
        if (image_detail is None):
            return False
        
        self.last = image_detail
        self.last_call = LOOP_TIME()
        CACHES[self.cache_id] = self
        return True
    
    
    async def invoke_continuous(self, client, event):
        """
        Invokes the booru cacher to return a message with an image.
        
        This method is a coroutine.

        Parameters
        ----------
        client : ``Client``
            The respective client instance who received the event.
        event : ``InteractionEvent``
            The received event.
        
        Returns
        -------
        success : `bool`
            Whether we ended up with great success.
        """
        image_detail = await self.handler.get_image(client, event)
        
        embed = build_booru_embed(image_detail)
        
        if image_detail is None:
            components = build_booru_disabled_components()
        else:
            components = build_booru_components(self.cache_id)
        
        if event.is_unanswered():
            function = type(client).interaction_component_message_edit
        else:
            function = type(client).interaction_response_message_edit
        
        await function(
            client,
            event,
            embed = embed,
            components = components,
        )
        
        if (image_detail is None):
            self.unbind()
            return False
        
        self.last = image_detail
        self.last_call = LOOP_TIME()
        return True
    
    
    def unbind(self):
        """
        Unbinds self from cache.
        """
        try:
            del CACHES[self.cache_id]
        except KeyError:
            pass


def start_cleanup_handle():
    """
    Starts the cleanup handle.
    """
    cleanup_handle = ImageCache.CLEANUP_HANDLE
    if (cleanup_handle is not None) and (not cleanup_handle.cancelled):
        return
    
    ImageCache.CLEANUP_HANDLE = KOKORO.call_later(CLEANUP_INTERVAL, cleanup)


def cleanup():
    """
    Cleans up the caches which where used outside of the expected margin.
    """
    ImageCache.CLEANUP_HANDLE = KOKORO.call_later(CLEANUP_INTERVAL, cleanup)
    
    to_unbind = []
    
    call_margin = LOOP_TIME() - CLEANUP_AFTER
    
    for cache in CACHES.values():
        if cache.last_call < call_margin:
            to_unbind.append(cache)
    
    for cache in to_unbind:
        cache.unbind()


def stop_cleanup_handle():
    """
    Stops the cleanup handle.
    """
    cleanup_handle = ImageCache.CLEANUP_HANDLE
    if (cleanup_handle is None):
        return
    
    if (not cleanup_handle.cancelled):
        cleanup_handle.cancel()
    
    ImageCache.CLEANUP_HANDLE = None
