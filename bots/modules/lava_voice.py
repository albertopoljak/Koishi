from hata.ext.extension_loader import require
require(LAVALINK_VOICE=True)

from re import compile as re_compile, escape as re_escape, I as re_ignore_case
from functools import partial as partial_func

from hata import Client, is_url, Embed, CHANNELS, BUILTIN_EMOJIS

from hata.ext.slash import abort, InteractionResponse, Select, Option, wait_for_component_interaction
from hata.ext.solarlink import SolarPlayer

from bot_utils.constants import GUILD__SUPPORT

EMOJI_CURRENT_TRACK = BUILTIN_EMOJIS['satellite']

class Player(SolarPlayer):
    __slots__ = ('text_channel_id', )
    def __new__(cls, node, guild_id, channel_id):
        self = SolarPlayer.__new__(cls, node, guild_id, channel_id)
        self.text_channel_id = 0
        return self
    
    def set_text_channel(self, event):
        self.text_channel_id = event.channel_id
    
    @property
    def text_channel(self):
        text_channel_id = self.text_channel_id
        if text_channel_id:
            return CHANNELS[text_channel_id]
    
    @property
    def queue_duration(self):
        duration = 0.0
        
        for configured_track in self.iter_all_track():
            duration += configured_track.track.duration
        
        return duration

def add_track_title_to(add_to, track):
    title = track.title
    if len(title) > 50:
        add_to.append(title[:47])
        add_to.append('...')
    else:
        add_to.append(title)

def add_track_duration_to(add_to, track):
    duration = int(track.duration)
    add_to.append('(')
    add_to.append(str(duration//60))
    add_to.append(':')
    add_to.append(str(duration%60))
    add_to.append(')')

def add_track_short_description_to(add_to, track):
    # Add title
    url = track.url
    
    add_to.append('**')
    if (url is not None):
        add_to.append('[')
    
    add_track_title_to(add_to, track)
    
    add_to.append('**')
    if (url is not None):
        add_to.append('](')
        add_to.append(url)
        add_to.append(')')
    
    add_to.append(' ')
    
    add_track_duration_to(add_to, track)



def create_track_short_description(track):
    add_to = []
    add_track_short_description_to(add_to, track)
    return ''.join(add_to)


def add_track_short_field_description_to(add_to, configured_track):
    add_track_short_description_to(add_to, configured_track.track)
    
    add_to.append('\n**Queued by:** ')
    
    # Add who queued it
    add_to.append(configured_track.requested.full_name)
    
    return configured_track


def create_track_short_field_description(configured_track):
    add_to = []
    add_track_short_field_description_to(add_to, configured_track)
    return ''.join(add_to)

def add_song_selection_header(embed, user):
    return embed.add_author(
        user.avatar_url,
        'Song selection',
    )

def create_added_music_embed(player, description):
    embed = Embed(
        None,
        description,
    )
    
    add_song_selection_header(embed, user)
    
    track = player.get_current()
    if (track is not None):
        if player.is_paused():
            title = 'paused'
        else:
            title = 'playing'
        
        embed.add_field(
            f'{EMOJI_CURRENT_TRACK} currently {title}',
            create_track_short_field_description(track),
        )
    
    return embed

LAVA_VOICE_TRACK_SELECT_CUSTOM_ID = 'lava_voice.select'

def create_track_select(tracks, length):
    options = []

    index = 0
    while True:
        option_value = str(index)
        
        track = tracks[index]
        index += 1
        
        option_label_parts = []
        
        option_label_parts.append(str(index))
        option_label_parts.append('. ')
        add_track_title_to(option_label_parts, track)
        option_label_parts.append(' ')
        add_track_duration_to(option_label_parts, track)
        
        option_label = ''.join(option_label_parts)
        
        options.append(Option(option_value, option_label))
        
        if index == length:
            break
    
    return Select(
        options,
        LAVA_VOICE_TRACK_SELECT_CUSTOM_ID,
        placeholder = 'Select a track to play',
        max_values = length,
    )
    
        
    

SLASH_CLIENT: Client


VOICE_COMMANDS = SLASH_CLIENT.interactions(
    None,
    name = 'voice',
    description = 'Voice commands',
    guild = GUILD__SUPPORT,
)

@VOICE_COMMANDS.interactions
async def join(client, event,
    volume : ('int', 'Any preset volume?') = None,
):
    """Joins the voice channel."""
    guild = event.guild
    if guild is None:
        abort('Guild only command.')
    
    state = guild.voice_states.get(user.id, None)
    if state is None:
        abort('You must be in a voice channel to invoke this command.')
        return
    
    channel = state.channel
    if not channel.cached_permissions_for(client).can_connect:
        abort(f'I have no permissions to connect to {channel.mention}.')
        return
    
    yield
    
    player = await client.solarlink.join_voice(channel)
    
    content = f'Joined to {state.channel.name}'
    
    if (volume is not None):
        if volume <= 0:
            volume = 0.0
        elif volume >= 200:
            volume = 2.0
        else:
            volume /= 100.0
        
        await player.set_volume(volume)
        content = f'{content}; Volume set to {volume*100.:.0f}%'
    
    yield content
    return


@VOICE_COMMANDS.interactions
async def pause(client, event):
    """Pauses the currently playing track."""
    player = client.solarlink.get_player(event.guild_id)
    
    if player is None:
        abort('There is no player at the guild.')
        return
    
    if player.is_paused():
        title = 'Playing paused. (was paused before)'
    else:
        await player.pause()
        title = 'Playing paused.'
    
    embed = Embed(
        title,
    )
    
    track = player.get_current()
    if (track is not None):
        embed.add_field(
            f'{EMOJI_CURRENT_TRACK} Currently paused',
            create_track_short_field_description(track),
        )
    
    return embed


@VOICE_COMMANDS.interactions
async def resume(client, event):
    """Resumes the currently playing track."""
    player = client.solarlink.get_player(event.guild_id)
    
    if player is None:
        abort('There is no player at the guild.')
        return
    
    if player.is_paused():
        await player.resume()
        title = 'Playing resumed.'
    else:
        title = 'Playing resumed. (was not paused before)'
    
    embed = Embed(
        title,
    )
    
    track = player.get_current()
    if (track is not None):
        embed.add_field(
            f'{EMOJI_CURRENT_TRACK} Currently playing',
            create_track_short_field_description(track),
        )
    
    return embed


@VOICE_COMMANDS.interactions
async def leave(client, event):
    """Leaves from the voice channel."""
    player = client.solarlink.get_player(event.guild_id)
    
    if player is None:
        abort('There is no player at the guild.')
        return
    
    yield
    await player.disconnect()
    
    title =  f'{client.name_at(event.guild)} out.'
    
    embed = Embed(
        title,
    )
    
    track = player.get_current()
    if (track is not None):
        embed.add_field(
            f'{EMOJI_CURRENT_TRACK} Played',
            create_track_short_field_description(track),
        )
    
    queue_length = player.queue_length
    if queue_length:
        embed.add_field(
            'Queue cleared.',
            f'{queue_length} tracks removed.',
        )
    
    yield embed
    return


def create_track_embed(track, title, requester, requested_at):
    return Embed(
        title,
        (
            f'By: {track.author}\n'
            f'Duration: {track.duration:.0f}s'
        ),
        timestamp = requested_at,
    ).add_footer(
        f'Track requested by {requester.full_name}',
        icon_url = requester.avatar_url,
    )

def check_is_user_same(user, event):
    return (user is event.user)

@VOICE_COMMANDS.interactions
async def play(client, event,
    name: ('str', 'The name of the audio to play.')
):
    """Plays an audio from youtube."""
    player = client.solarlink.get_player(event.guild_id)
    
    if player is None:
        abort('There is no player at the guild.')
        return
    
    yield
    
    if is_url(name):
        is_name_an_url = True
    else:
        is_name_an_url = False
        name = f'ytsearch:{name}'
    
    result = await client.solarlink.get_tracks(name)
    
    user = event.user
    
    # Case 0, there are 0 tracks
    if result is None:
        embed = Embed(
            None,
            '*no result*',
        )
        
        add_song_selection_header(embed, user)
        
        yield embed
        return
    
    playlist_name = result.playlist_name
    selected_track_index = result.selected_track_index
    tracks = result.tracks
    
    length = len(tracks)
    description_parts = []

    # We are in a playlist
    if (playlist_name is not None):
        # All track selected -> add all
        if (selected_track_index == -1) or (selected_track_index >= length):
            for track in tracks:
                await player.append(track, requester=user)
            
            description_parts.append('Playlist ')
            
            if len(playlist_name) > 60:
                description_parts.append(playlist_name[:57])
                description_parts.append('...')
            else:
                description_parts.append(playlist_name)
            description_parts.append('\' ')
            
            description_parts.append(str(length))
            description_parts.append(' tracks are added to the queue.\n\n')
            
            if length:
                if length > 5:
                    length_truncated = -(5-length)
                    length = 5
                else:
                    length_truncated = 0
                
                index = 0
                
                while True:
                    track = tracks[index]
                    index += 1
                    description_parts.append('**')
                    description_parts.append(str(index))
                    description_parts.append('.** ')
                    
                    add_track_short_description_to(description_parts, track)
                    
                    if index == length:
                        break
                    
                    description_parts.append('\n')
                    continue
                
                if length_truncated:
                    description_parts.append('\n\n')
                    description_parts.append(str(length_truncated))
                    description_parts.append(' more hidden.')
        
        else:
            # 1 Track is selected, add only that one
            
            track = tracks[selected_track_index]
            await player.append(track, requester=user)
            
            description_parts.append('The selected track from ')
            
            if len(playlist_name) > 60:
                description_parts.append(playlist_name[:57])
                description_parts.append('...')
            else:
                description_parts.append(playlist_name)
            description_parts.append(' ')
            
            description_parts.append(' is added to the queue.\n\n')
            
            add_track_short_description_to(description_parts, track)
        
        yield create_added_music_embed(player, ''.join(description_parts))
        return
    
    if is_name_an_url:
        track = tracks[0]
        await player.append(track, requester=user)
        
        description_parts.append('Track added to queue.\n\n')
        add_track_short_description_to(description_parts, track)
        
        yield create_added_music_embed(player, ''.join(description_parts))
        return
    
    if length > 5:
        length = 5
    
    index = 0
    while True:
        track = tracks[index]
        index += 1
        
        description_parts.append('**')
        description_parts.append(str(index))
        description_parts.append('.** ')
        add_track_short_description_to(description_parts, track)
        
        add_track_short_description_to(description_parts, track)
        
        if index == length:
            break
        
        description_parts.append('\n')
        continue
    
    description = ''.join(description_parts)
    description_parts = None
    
    embed = Embed(
        None,
        description,
    ).add_author(
        user.avatar_url,
        'Song selection. Please select the song to play.',
    ).add_footer(
        'This timeouts in 30s.',
    )
    
    select = create_track_select(tracks, length)
    
    message = yield InteractionResponse(embed=embed, components=select)
    
    try:
        component_interaction = await wait_for_component_interaction(
            message,
            timeout = 30.0,
            check = partial_func(check_is_user_same, user)
        )
    
    except TimeoutError:
        component_interaction = None
        cancelled = True
    else:
        cancelled = False
    
    if cancelled:
        embed.title = 'Adding emoji has been cancelled.'
    else:
        embed.title = 'Emoji has been added!'
        
        async with client.http.get(emoji.url) as response:
            emoji_data = await response.read()
        
        await client.emoji_create(event.guild, name, emoji_data)
    
    yield InteractionResponse(embed=embed, components=None, message=message, event=component_interaction)



@VOICE_COMMANDS.interactions
async def volume_(client, event,
    volume: ('number', 'Percentage?') = None,
):
    """Gets or sets my volume to the given percentage."""
    player = client.solarlink.get_player(event.guild_id)
    
    if player is None:
        abort('There is no player at the guild.')
        return
    
    if volume is None:
        volume = player.get_volume()
        return f'{volume*100.:.0f}%'
    
    if volume <= 0:
        volume = 0.0
    elif volume >= 200:
        volume = 2.0
    else:
        volume /= 100.0
    
    await player.set_volume(volume)
    return f'Volume set to {volume*100.:.0f}%.'


@VOICE_COMMANDS.interactions
async def stop(client, event):
    """Nyahh, if you really want I can stop playing audio."""
    player = client.solarlink.get_player(event.guild_id)

    if player is None:
        abort('There is no player at the guild.')
        return

    await player.stop()
    return 'Stopped playing'

BEHAVIOR_NAME_REPEAT_CURRENT = 'loop current'
BEHAVIOUR_NAME_REPEAT_QUEUE = 'loop queue'
BEHAVIOUR_NAME_SHUFFLE = 'shuffle'

BEHAVIOUR_VALUE_GET = 0
BEHAVIOR_VALUE_REPEAT_CURRENT = 1
BEHAVIOUR_VALUE_REPEAT_QUEUE = 2
BEHAVIOUR_VALUE_SHUFFLE = 3

BEHAVIOR_CHOICES = [
    (BEHAVIOR_NAME_REPEAT_CURRENT, BEHAVIOR_VALUE_REPEAT_CURRENT),
    (BEHAVIOUR_NAME_REPEAT_QUEUE, BEHAVIOUR_VALUE_REPEAT_QUEUE),
    (BEHAVIOUR_NAME_SHUFFLE, BEHAVIOUR_VALUE_SHUFFLE),
]

@VOICE_COMMANDS.interactions
async def behaviour(client, event,
    behaviour : (BEHAVIOR_CHOICES, 'Choose a behaviour') = BEHAVIOUR_VALUE_GET,
    value : (bool, 'Set value') = True,
):
    """Get or set the player's behaviour."""
    player = client.solarlink.get_player(event.guild_id)

    if player is None:
        abort('There is no player at the guild.')
        return
    
    if behaviour == BEHAVIOUR_VALUE_GET:
        if player.is_repeating_queue():
            if player.is_shuffling():
                content = 'Repeating over the queue.'
            else:
                content = 'Repeating and shuffling the queue.'
        elif player.set_repeat_current():
            if player.is_shuffling():
                content = 'Repeating over the current track and shuffling????'
            else:
                content = 'Repeating over the current track.'
        else:
            if player.is_shuffling():
                content = 'No repeat, but shuffle queue.'
            else:
                content = 'No repeat, no shuffle.'
    
    elif behaviour == BEHAVIOR_VALUE_REPEAT_CURRENT:
        player.set_repeat_current(value)
        if value:
            content = 'Started to repeat the current track.'
        else:
            content = 'Stopped to repeat the current track.'
    
    elif behaviour == BEHAVIOUR_VALUE_REPEAT_QUEUE:
        player.set_repeat_queue(value)
        if value:
            content = 'Started to repeat the whole queue.'
        else:
            content = 'Stopped to repeat the whole queue.'
        
    elif behaviour == BEHAVIOUR_VALUE_SHUFFLE:
        player.set_shuffle(value)
        if value:
            content = 'Started shuffling the queue.'
        else:
            content = 'Stopped to shuffle the queue.'
    
    else:
        return # ?
    
    return content


def generate_track_autocomplete_form(configured_track):
    track = configured_track.track
    result = f'{track.title} by {track.author}'
    if len(result) > 69:
        result = result[:66] + '...'
    
    return result


@VOICE_COMMANDS.interactions
async def skip(client, event,
    track : ('str', 'Which track to skip?') = None,
):
    """Skips the track on the given index."""
    player = client.solarlink.get_player(event.guild_id)
    
    if player is None:
        abort('There is no player at the guild.')
        return
    
    if track is None:
        index = 0
    else:
        for index, configured_track in enumerate(player.iter_all_track()):
            if generate_track_autocomplete_form(configured_track) == track:
                break
        else:
            index = -1
    
    configured_track = player.spip(index)
    if configured_track is None:
        return 'Nothing was skipped.'
    else:
        return create_track_embed(configured_track.track, 'Skipped', configured_track.requester, configured_track.requested_at)


@VOICE_COMMANDS.interactions
@skip.autocomplete('track')
async def autocomplete_skip_track(client, event, value):
    player = client.solarlink.get_player(event.guild_id)
    if player is None:
        return None
    
    collected = 0
    track_names = []
    
    if value is None:
        for configured_track in player.iter_all_track():
            track_names.append(generate_track_autocomplete_form(configured_track))
            
            collected += 1
            if collected == 20:
                break
    else:
        pattern = re_compile(re_escape(value), re_ignore_case)
        
        for configured_track in player.iter_all_track():
            track_name = generate_track_autocomplete_form(configured_track)
            if (pattern.search(track_name) is not None):
                track_names.append(track_name)
            
            collected += 1
            if collected == 20:
                break
    
    return track_names
