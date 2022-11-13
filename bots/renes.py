from hata import ActivityType, Client, Embed
from scarletio import LOOP_TIME

from bot_utils.constants import (
    CHANNEL__ESTS_HOME__STREAM_NOTIFICATION, GUILD__ESTS_HOME, ROLE__ESTS_HOME__STREAM_NOTIFICATION, USER__EST
)

Renes: Client
Satori: Client

@Renes.events
async def guild_user_add(client, guild, user):
    if guild is not GUILD__ESTS_HOME:
        return
    
    if user.bot:
        return
    
    system_channel = guild.system_channel
    if system_channel is None:
        return
    
    await client.message_create(
        system_channel,
        f'Thanks for coming {user:m}, enjoy your stay~\n'
        f'If you wish to get notification every time Est goes live please use the {ping_me_hime:m} command.'
    )


@Renes.interactions(guild = GUILD__ESTS_HOME)
async def ping_me_hime(client, event):
    user = event.user
    if user.has_role(ROLE__ESTS_HOME__STREAM_NOTIFICATION):
        await client.user_role_delete(user, ROLE__ESTS_HOME__STREAM_NOTIFICATION)
        return 'You will **not** be pinged for stream notifications anymore.'
    
    
    await client.user_role_add(user, ROLE__ESTS_HOME__STREAM_NOTIFICATION)
    return 'You will be pinged when Est goes live.'


ALICE_STREAMING_SETUP_IMAGE_URL = 'https://cdn.discordapp.com/attachments/568837922288173058/984793641254015016/est-alice-streaming-0000-cut-0000.png'

@Satori.events
class user_presence_update:
    STREAM_PING_DIFFERENCE = 10.0 * 60.0 # 10 min
    LAST_STREAM_OVER = -STREAM_PING_DIFFERENCE
    
    async def __new__(cls, client, user, presence_update):
        if user is not USER__EST:
            return
        
        try:
            activity_change = presence_update['activities']
        except KeyError:
            return
        
        for activity in activity_change.iter_removed():
            if activity.type == ActivityType.stream:
                removed_streaming_activity = activity
                break
        else:
            removed_streaming_activity = None
        
        if (removed_streaming_activity is not None):
            cls.LAST_STREAM_OVER = LOOP_TIME()
        
        
        for activity in activity_change.iter_added():
            if activity.type == ActivityType.stream:
                added_streaming_activity = activity
                break
        else:
            added_streaming_activity = None
        
        if (added_streaming_activity is not None):
            if LOOP_TIME() > cls.LAST_STREAM_OVER + cls.STREAM_PING_DIFFERENCE:
                
                image_url = added_streaming_activity.twitch_preview_image_url
                if (image_url is None):
                    image = None
                else:
                    async with Renes.http.get(image_url) as response:
                        if response.status == 200:
                            image = await response.read()
                        else:
                            image = None
                
                embed = Embed(
                    added_streaming_activity.state,
                    added_streaming_activity.details,
                ).add_author(
                    f'{USER__EST.name_at(GUILD__ESTS_HOME)} went live!',
                    USER__EST.avatar_url_as(size=128),
                    added_streaming_activity.url,
                ).add_thumbnail(
                    ALICE_STREAMING_SETUP_IMAGE_URL,
                )
                
                if (image is not None):
                    embed.add_image('attachment://image.png')
                
                if image is None:
                    file = None
                else:
                    file = ('image.png', image)
                
                
                message = await Renes.message_create(
                    CHANNEL__ESTS_HOME__STREAM_NOTIFICATION,
                    f'> {ROLE__ESTS_HOME__STREAM_NOTIFICATION:m}',
                    embed = embed,
                    file = file,
                )
                
                await Renes.message_crosspost(message)
