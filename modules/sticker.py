__all__ = ()

from functools import partial as partial_func
from datetime import datetime, timedelta
from scarletio import to_json
from scarletio.web_common import quote
from hata import Embed, parse_emoji, DiscordException, ERROR_CODES, Client, STICKERS, USERS, Color, Permission
from hata.ext.slash import abort, InteractionResponse, Button, ButtonStyle, wait_for_component_interaction, Row
from bot_utils.models import DB_ENGINE, sticker_counter_model, STICKER_COUNTER_TABLE
from bot_utils.constants import GUILD__SUPPORT, ROLE__SUPPORT__EMOJI_MANAGER
from dateutil.relativedelta import relativedelta
from sqlalchemy import func as alchemy_function, and_
from sqlalchemy.sql import select, desc

RELATIVE_MONTH = relativedelta(months=1)
MONTH = timedelta(days=367, hours=6) / 12
MOST_USED_PER_PAGE = 30

SLASH_CLIENT: Client

STICKER_COMMANDS = SLASH_CLIENT.interactions(
    None,
    name = 'sticker',
    description = 'Sticker counter commands.',
    guild = GUILD__SUPPORT,
)

ORDER_DECREASING = 1
ORDER_INCREASING = 0
ORDERS = [
    ('decreasing', ORDER_DECREASING),
    ('increasing', ORDER_INCREASING),
    
]

def item_sort_key(item):
    return item[1]


@STICKER_COMMANDS.interactions
async def user_top(event,
    user: ('user', 'By who?') = None,
    count: (range(10, 61, 10), 'The maximal amount of emojis to show') = 30,
    months: (range(1, 13), 'The months to get') = 1,
):
    """List the most used stickers at KW by you or by the selected user."""
    if user is None:
        user = event.user
    
    async with DB_ENGINE.connect() as connector:
        response = await connector.execute(
            select(
                [
                    sticker_counter_model.sticker_id,
                    alchemy_function.count(sticker_counter_model.sticker_id).label('total'),
                ],
            ).where(
                and_(
                    sticker_counter_model.user_id == user.id,
                    sticker_counter_model.timestamp > datetime.utcnow() - RELATIVE_MONTH * months,
                ),
            ).limit(
                count,
            ).group_by(
                sticker_counter_model.sticker_id,
            ).order_by(
                desc('total'),
            )
        )
        
        results = await response.fetchall()
    
    
    embed = Embed(
        f'Most used stickers by {user.full_name}',
        color = user.color_at(GUILD__SUPPORT),
    ).add_thumbnail(
        user.avatar_url,
    )
    
    
    if results:
        description_parts = []
        limit = len(results)
        index = 0
        start = 1
        
        while True:
            sticker_id, count = results[index]
            
            index += 1
            
            try:
                sticker = STICKERS[sticker_id]
            except KeyError:
                continue
            
            description_parts.append(str(index))
            description_parts.append('.: **')
            description_parts.append(str(count))
            description_parts.append('** x ')
            description_parts.append(sticker.name)
            
            if (not index % 10) or (index == limit):
                description = ''.join(description_parts)
                description_parts.clear()
                embed.add_field(f'{start} - {index}', description, inline = True)
                
                if (index == limit):
                    break
                
                start = index + 1
                continue
            
            description_parts.append('\n')
            continue
    else:
        embed.description = '*No recorded data.*'
    
    return embed



@STICKER_COMMANDS.interactions
async def sticker_top(
    raw_sticker: ('str', 'Pick an sticker', 'sticker'),
    months: (range(1, 13), 'The months to get') = 1,
):
    """List the users using the given sticker the most."""
    sticker = GUILD__SUPPORT.get_sticker_like(raw_sticker)
    if sticker is None:
        abort(f'There is not sticker with name `{raw_sticker}` in the guild.')
    
    async with DB_ENGINE.connect() as connector:
        response = await connector.execute(
            select(
                [
                    sticker_counter_model.user_id,
                    alchemy_function.count(sticker_counter_model.user_id).label('total'),
                ],
            ).where(
                and_(
                    sticker_counter_model.sticker_id == sticker.id,
                    sticker_counter_model.timestamp > datetime.utcnow() - RELATIVE_MONTH * months,
                )
            ).limit(
                30,
            ).group_by(
                sticker_counter_model.user_id,
            ).order_by(
                desc('total')
            )
        )
        
        results = await response.fetchall()
    
    
    if results:
        index = 0
        limit = len(results)
        description_parts = []
        
        while True:
            user_id, count = results[index]
            
            index += 1
            
            try:
                user = USERS[user_id]
            except KeyError:
                continue
            
            guild_profile = user.get_guild_profile_for(GUILD__SUPPORT)
            if guild_profile is None:
                nick = None
            else:
                nick = guild_profile.nick
            
            description_parts.append(str(index))
            description_parts.append('.: **')
            description_parts.append(str(count))
            description_parts.append('** x ')
            description_parts.append(user.full_name)
            if (nick is not None):
                description_parts.append(' *[')
                description_parts.append(nick)
                description_parts.append(']*')
            
            if index == limit:
                break
            
            description_parts.append('\n')
            continue
        
        description = ''.join(description_parts)
    else:
        description = '*No usages recorded*'
    
    
    return Embed(
        f'Top sticker users of {sticker.name}',
        description,
    ).add_thumbnail(sticker.url)


def assert_user_permissions(event):
    if not event.user_permissions.can_manage_guild_expressions:
        abort(f'You must have manage emojis & stickers permissions to invoke this command.')


STICKER_SYNC_COMMANDS = STICKER_COMMANDS.interactions(
    None,
    guild = GUILD__SUPPORT,
    name = 'sync',
    description = 'Syncs sticker table. (You must have emoji-council role)',
    required_permissions = Permission().update_by_keys(manage_guild_expressions = True)
)

@STICKER_SYNC_COMMANDS.interactions
async def sync_stickers_(event):
    """Syncs sticker list stickers. (You must have emoji-council role)"""
    assert_user_permissions(event)
    
    async with DB_ENGINE.connect() as connector:
        response = await connector.execute(
            select([sticker_counter_model.sticker_id]).distinct(sticker_counter_model.sticker_id),
        )
        
        results = await response.fetchall()
        
        sticker_ids = [result[0] for result in results]
        guild_stickers = GUILD__SUPPORT.stickers
        
        sticker_ids_to_remove = [sticker_id for sticker_id in sticker_ids if (sticker_id not in guild_stickers)]
        
        if sticker_ids_to_remove:
            await connector.execute(
                STICKER_COUNTER_TABLE.delete().where(
                    sticker_counter_model.sticker_id.in_(sticker_ids_to_remove),
                )
            )
    
    return f'Unused sticker entries removed: {len(sticker_ids_to_remove)}'


@STICKER_SYNC_COMMANDS.interactions
async def sync_users_(event):
    """Syncs sticker list users. (You must have emoji-council role)"""
    assert_user_permissions(event)
    
    async with DB_ENGINE.connect() as connector:
        response = await connector.execute(
            select([sticker_counter_model.user_id]).distinct(sticker_counter_model.user_id),
        )
        
        results = await response.fetchall()
        
        user_ids = [result[0] for result in results]
        guild_users = GUILD__SUPPORT.users
        
        user_ids_to_remove = [user_id for user_id in user_ids if (user_id not in guild_users)]
        
        if user_ids_to_remove:
            await connector.execute(
                STICKER_COUNTER_TABLE.delete().where(
                    sticker_counter_model.user_id.in_(user_ids_to_remove)
                )
            )
    
    return f'Unused user entries removed: {len(user_ids_to_remove)}'



@STICKER_COMMANDS.interactions
async def most_used(
    months: (range(1, 13), 'The months to get') = 1,
    page: ('int', 'Select a page') = 1,
    order: (ORDERS, 'Ordering?') = ORDER_DECREASING,
):
    """Shows the most used stickers."""
    if page < 1:
        abort('Page value can be only positive')
    
    low_date_limit = datetime.utcnow() - RELATIVE_MONTH * months
    is_new_limit = datetime.utcnow() - MONTH
    
    async with DB_ENGINE.connect() as connector:
        
        response = await connector.execute(
            select(
                [
                    sticker_counter_model.sticker_id,
                    alchemy_function.count(sticker_counter_model.user_id).label('total'),
                ],
            ).where(
                sticker_counter_model.timestamp > low_date_limit,
            ).group_by(
                sticker_counter_model.sticker_id,
            )
        )
        
        results = await response.fetchall()
    
    items = []
    
    guild_stickers = set(GUILD__SUPPORT.stickers.values())
    
    for sticker_id, count in results:
        try:
            sticker = STICKERS[sticker_id]
        except KeyError:
            continue
        
        guild_stickers.discard(sticker)
        
        is_new = (sticker.created_at >= is_new_limit)
        items.append((sticker, count, is_new))
    
    for sticker in guild_stickers:
        is_new = (sticker.created_at >= is_new_limit)
        items.append((sticker, 0, is_new))
    
    items.sort(key = item_sort_key, reverse=order)
    
    page_shift = (page - 1) * MOST_USED_PER_PAGE
    
    index = page_shift
    limit = min(len(items), index + MOST_USED_PER_PAGE)
    
    description_parts = []
    
    if index < limit:
        while True:
            sticker, count, is_new = items[index]
            index += 1
            
            description_parts.append(str(index))
            description_parts.append('.: **')
            description_parts.append(str(count))
            description_parts.append('** x ')
            description_parts.append(sticker.name)
            
            if is_new:
                description_parts.append(' *[New!]*')
            
            if index == limit:
                break
            
            description_parts.append('\n')
            continue
        
        description = ''.join(description_parts)
    else:
        description = '*No recorded data*'
    
    return Embed(
        'Most used stickers:',
        description,
    ).add_footer(
        f'Page {page} / {(len(items) // MOST_USED_PER_PAGE) + 1}',
    )


@STICKER_COMMANDS.interactions
async def add_(client, event,
    file: ('attachment', 'File!'),
    name: (str, 'The sticker\'s name.'),
    emoji_value: (str, 'Emoji representation of the sticker.', 'emoji'),
    description: (str, 'Description for the sticker.') = None,
):
    """Adds a sticker to the guild. (You must have emoji-council role)"""
    if not event.user.has_role(ROLE__SUPPORT__EMOJI_MANAGER):
        abort(f'You must have {ROLE__SUPPORT__EMOJI_MANAGER:m} role to invoke this command.')
    
    name_length = len(name)
    if (name_length < 2) or (name_length > 32):
        abort(f'Sticker name\'s length can be in range [2:32], got {name_length!r}, {name!r}.')
    
    emoji = parse_emoji(emoji_value)
    
    if emoji is None:
        abort(f'{emoji_value} cannot be interpreted as an emoji.')
    
    if emoji.is_custom_emoji():
        abort(f'Only unicode can be used, got {emoji}')
    
    if (description is not None):
        description_length = len(description)
        if (description_length > 100):
            abort(
                f'Sticker description\'s length can be in range [0:100], got {description_length!r}, {description!r}.'
            )
    
    file_type = file.content_type
    if (file_type is None) or (file_type != 'image/png'):
        if file_type is None:
            file_type = 'N/A'
        
        abort(f'File is not a `.png` file, got: {file_type!r}')
    
    file_size = file.size
    if file_size > 524288:
        abort(f'Max file size can be 512 kb, got {file_size//1024}kb.')
    
    file_height = file.height
    file_width = file.width
    if (file_height == 0) or (file_height > 320) or (file_width == 0) or (file_width > 320):
        abort(f'Max file dimensions: 320x320px, got {file_width}x{file_width}px')
    
    yield
    
    while True:
        try:
            image = await client.download_attachment(file)
        except ConnectionError as err:
            error_message = f'Getting image failed: {err.args[0]}'
            break
        
        except OSError as err:
            error_message = f'Getting image failed: {err.strerror}'
            break
        
        
        try:
            sticker = await client.sticker_create(event.guild, name, image, emoji, description)
        except ConnectionError:
            return
        
        except DiscordException as err:
            error_message = repr(err)
            break
        
        except ValueError as err:
            error_message = err.args[0]
            break
        
        yield 'The sticker has been successfully created'
        await client.message_create(event.channel, sticker=sticker)
        return
    
    yield error_message


def check_sticker_deleter(user, event):
    return user is event.user

STICKER_DELETE_BUTTON_CONFIRM = Button('Yes', style = ButtonStyle.red)
STICKER_DELETE_BUTTON_CANCEL = Button('No', style = ButtonStyle.gray)

STICKER_DELETE_COMPONENTS = Row(STICKER_DELETE_BUTTON_CONFIRM, STICKER_DELETE_BUTTON_CANCEL)


@STICKER_COMMANDS.interactions
async def delete_(client, event,
    sticker_name: ('str', 'The sticker\'s name to delete', 'sticker'),
):
    """Deletes the given sticker. (You must have emoji-council role)"""
    if not event.user.has_role(ROLE__SUPPORT__EMOJI_MANAGER):
        abort(f'You must have {ROLE__SUPPORT__EMOJI_MANAGER:m} role to invoke this command.')
    
    sticker = event.guild.get_sticker_like(sticker_name)
    if (sticker is None):
        abort(f'No sticker matched the given name: {sticker_name!r}.')
    
    embed = Embed('Confirmation', f'Are you sure to delete {sticker.name!r} ({sticker.id}) sticker forever?')
    
    message = yield InteractionResponse(embed = embed, components = STICKER_DELETE_COMPONENTS, allowed_mentions = None)
    
    try:
        component_interaction = await wait_for_component_interaction(message, timeout = 300.0,
            check = partial_func(check_sticker_deleter, event.user))
    
    except TimeoutError:
        embed.title = 'Timeout'
        embed.description = f'Sticker {sticker.name!r} was not deleted.'
        
        # Edit the source message with the source interaction
        yield InteractionResponse(embed = embed, components = None, allowed_mentions = None, message = message)
        return
    
    if component_interaction.interaction == STICKER_DELETE_BUTTON_CANCEL:
        embed.title = 'Cancelled'
        embed.description = f'Sticker {sticker.name!r} was not deleted.'
        
        # Edit the source message with the component interaction
        yield InteractionResponse(embed = embed, components = None, allowed_mentions = None, event = component_interaction)
        return
    
    # Acknowledge the event
    await client.interaction_component_acknowledge(component_interaction)
    
    try:
        await client.sticker_delete(sticker)
    except ConnectionError:
        # No internet, let it be
        return
    
    except DiscordException as err:
        if err.code == ERROR_CODES.unknown_sticker:
            failure = False
        else:
            failure = True
            embed.title = 'Failure'
            embed.description = repr(err)
    else:
        failure = False
    
    if not failure:
        embed.title = 'Success'
        embed.description = f'Sticker {sticker.name!r} has been deleted successfully.'
    
    # Edit the source message
    yield InteractionResponse(embed = embed, message = message, components = None)


def check_sticker_editor(user, event):
    return user is event.user

STICKER_EDIT_BUTTON_CONFIRM = Button('Yes', style = ButtonStyle.blue)
STICKER_EDIT_BUTTON_CANCEL = Button('No', style = ButtonStyle.gray)

STICKER_EDIT_COMPONENTS = Row(STICKER_EDIT_BUTTON_CONFIRM, STICKER_EDIT_BUTTON_CANCEL)


@STICKER_COMMANDS.interactions
async def edit_(client, event,
    sticker_name: ('str', 'The sticker\'s name to delete', 'sticker'),
    new_name: ('str', 'New name for the sticker',) = None,
    new_emoji_value: (str, 'Emoji representation of the sticker.', 'new_emoji') = None,
    new_description: (str, 'Description for the sticker.') = None,
):
    """Edits the given sticker. (You must have emoji-council role)"""
    if not event.user.has_role(ROLE__SUPPORT__EMOJI_MANAGER):
        abort(f'You must have {ROLE__SUPPORT__EMOJI_MANAGER:m} role to invoke this command.')
    
    sticker = event.guild.get_sticker_like(sticker_name)
    if (sticker is None):
        abort(f'No sticker matched the given name: {sticker_name!r}.')
    
    anything_to_edit = False
    
    
    if (new_name is not None):
        if (sticker.name != new_name):
            name_length = len(new_name)
            if (name_length < 2) or (name_length > 32):
                abort(f'Sticker name\'s length can be in range [2:32], got {name_length!r}, {new_name!r}.')
            
            anything_to_edit = True
        else:
            new_name = None
    
    
    if (new_emoji_value is not None):
        new_emoji = parse_emoji(new_emoji_value)
        
        if new_emoji is None:
            abort(f'{new_emoji_value} cannot be interpreted as an emoji.')
        
        if new_emoji.is_custom_emoji():
            abort(f'Only unicode can be used, got {new_emoji}')
        
        tags = sticker.tags
        if (tags is None) or (len(tags) != 1) or (next(iter(tags)) != new_emoji.name):
            anything_to_edit = True
        else:
            new_emoji = None
    else:
        new_emoji = None
    
    
    if (new_description is not None):
        description_length = len(new_description)
        if (description_length > 100):
            abort(
                f'Sticker description\'s length can be in range [0:100], got {description_length!r}, '
                f'{new_description!r}.'
            )
        
        if (sticker.description != new_description):
            anything_to_edit = True
        else:
            new_description = None
    
    if not anything_to_edit:
        abort('No differences were provided.')
    
    
    embed = Embed('Confirmation', f'Are you sure to edit {sticker.name!r} sticker?')
    
    if (new_name is not None):
        embed.add_field('Name', f'{sticker.name} -> {new_name}')
    
    if (new_emoji is not None):
        embed.add_field('Tags', f'{", ".join(sticker.tags)} -> {new_emoji.name}')
    
    if (new_description is not None):
        embed.add_field('Description', f'{sticker.description} -> {new_description}')
    
    message = yield InteractionResponse(embed = embed, components = STICKER_EDIT_COMPONENTS, allowed_mentions = None)
    
    try:
        component_interaction = await wait_for_component_interaction(message, timeout = 300.0,
            check = partial_func(check_sticker_editor, event.user))
    
    except TimeoutError:
        embed.title = 'Timeout'
        embed.description = f'Sticker {sticker.name!r} was not edited.'
        
        # Edit the source message with the source interaction
        yield InteractionResponse(embed = embed, components = None, allowed_mentions = None, message = message)
        return
    
    if component_interaction.interaction == STICKER_EDIT_BUTTON_CANCEL:
        embed.title = 'Cancelled'
        embed.description = f'Sticker {sticker.name!r} was not edited.'
        
        # Edit the source message with the component interaction
        yield InteractionResponse(embed = embed, components = None, allowed_mentions = None, event = component_interaction)
        return
    
    # Acknowledge the event
    await client.interaction_component_acknowledge(component_interaction)
    
    keyword_parameters = {}
    
    if (new_name is not None):
        keyword_parameters['name'] = new_name
    
    if (new_emoji is not None):
        keyword_parameters['tags'] = new_emoji
    
    if (new_description is not None):
        keyword_parameters['description'] = new_description
    
    try:
        await client.sticker_edit(sticker, **keyword_parameters)
    except ConnectionError:
        # No internet, let it be
        return
    
    except DiscordException as err:
        if err.code == ERROR_CODES.unknown_sticker:
            failure = False
        else:
            failure = True
            embed.title = 'Failure'
            embed.description = repr(err)
    else:
        failure = False
    
    if not failure:
        embed.title = 'Success'
        embed.description = f'Sticker {sticker.name!r} has been successfully edited.'
    
    # Edit the source message
    yield InteractionResponse(embed = embed, message = message, components = None)


def get_month_keys():
    now = datetime.utcnow()
    year = now.year
    month = now.month
    
    month_keys = [(year, month)]
    for _ in range(11):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        
        month_keys.append((year, month))
    
    month_keys.reverse()
    return month_keys


MONTHS = {
    1: 'jan',
    2: 'feb',
    3: 'mar',
    4: 'apr',
    5: 'may',
    6: 'jun',
    7: 'jul',
    8: 'aug',
    9: 'sep',
    10: 'oct',
    11: 'nov',
    12: 'dec',
}

def create_sticker_graph_line_data_set(sticker, results_by_month, month_keys):
    color = Color((sticker.id >> 22) & 0xffffff).as_html
    return {
        'label': sticker.name,
        'data': [results_by_month.get(month, 0) for month in month_keys],
        'borderColor': color,
        'backgroundColor': color,
        'fill': False,
    }


@STICKER_COMMANDS.interactions
async def user_sticker_compare(
    raw_sticker_1: ('str', 'Pick a sticker', 'sticker-1'),
    raw_sticker_2: ('str', 'Pick a sticker', 'sticker-2') = None,
    raw_sticker_3: ('str', 'Pick a sticker', 'sticker-3') = None,
    raw_sticker_4: ('str', 'Pick a sticker', 'sticker-4') = None,
    raw_sticker_5: ('str', 'Pick a sticker', 'sticker-5') = None,
    raw_sticker_6: ('str', 'Pick a sticker', 'sticker-6') = None,
    raw_sticker_7: ('str', 'Pick a sticker', 'sticker-7') = None,
    raw_sticker_8: ('str', 'Pick a sticker', 'sticker-8') = None,
    raw_sticker_9: ('str', 'Pick a sticker', 'sticker-9') = None,
    raw_sticker_10: ('str', 'Pick a sticker', 'sticker-10') = None,
):
    """Compares the two stickers or something, smh smh."""
    stickers = set()
    
    for raw_sticker in (
        raw_sticker_1, raw_sticker_2, raw_sticker_3, raw_sticker_4, raw_sticker_5, raw_sticker_6, raw_sticker_7,
        raw_sticker_8, raw_sticker_9, raw_sticker_10,
    ):
        if raw_sticker is None:
            continue
        
        sticker = GUILD__SUPPORT.get_sticker_like(raw_sticker)
        if sticker is None:
            
            # Slash command parameters have no length limit
            if len(raw_sticker) > 100:
                raw_sticker = raw_sticker[:100]
            
            abort(f'There is not sticker with name `{raw_sticker}` in the guild.')
            return # this makes the linters stop crying
        
        stickers.add(sticker)
    
    stickers = sorted(stickers)
    
    async with DB_ENGINE.connect() as connector:
        response = await connector.execute(
            select(
                [
                    sticker_counter_model.sticker_id,
                    alchemy_function.count(sticker_counter_model.sticker_id),
                    alchemy_function.date_part('year', sticker_counter_model.timestamp).label('year'),
                    alchemy_function.date_part('month', sticker_counter_model.timestamp).label('month'),
                ],
            ).where(
                and_(
                    sticker_counter_model.sticker_id.in_([sticker.id for sticker in stickers]),
                    sticker_counter_model.timestamp > datetime.utcnow() - RELATIVE_MONTH * 12,
                )
            ).group_by(
                sticker_counter_model.sticker_id,
                'month',
                'year',
            )
        )
        
        results = await response.fetchall()
    
    sticker_id_to_results_by_month = {sticker.id: {} for sticker in stickers}
    
    for sticker_id, count, year, month in results:
        sticker_id_to_results_by_month[sticker_id][(int(year), int(month))] = count
    
    month_keys = get_month_keys()
    
    data = to_json({
        'type': 'line',
        'data': {
            'labels': [f'{year} {MONTHS[month]}' for year, month in month_keys],
            'datasets': [
                create_sticker_graph_line_data_set(sticker, sticker_id_to_results_by_month[sticker.id], month_keys)
                for sticker in stickers
            ],
        },
        'options': {
            'legend': {
                'labels': {
                    'fontColor': 'white',
                },
            },
            'scales': {
                'yAxes': [
                    {
                        'ticks': {
                            'beginAtZero': 'true',
                            'fontColor': 'white',
                            'fontStyle': 'bold',
                        },
                        'gridLines': {
                            'color': 'white',
                        },
                    },
                ],
                'xAxes': [
                    {
                        'ticks': {
                            'fontColor': 'white',
                            'fontStyle': 'bold',
                        },
                        'gridLines': {
                            'color': 'white',
                        },
                    },
                ],
            },
        },
    })
    
    chart_url = f'https://quickchart.io/chart?width=500&height=300&c={quote(data)}'
    
    return Embed(
        'Sticker comparison'
    ).add_image(
        chart_url,
    )

@STICKER_COMMANDS.autocomplete('sticker_name', 'sticker')
async def autocomplete_sticker_name(value):
    if value is None:
        return sorted(
            sticker.name for sticker in GUILD__SUPPORT.stickers.values()
        )
    
    value = value.casefold()
    
    return sorted(
        sticker.name for sticker in GUILD__SUPPORT.stickers.values()
        if value in sticker.name.casefold()
    )


@user_sticker_compare.autocomplete(
    'sticker-1', 'sticker-2', 'sticker-3', 'sticker-4', 'sticker-5', 'sticker-6', 'sticker-7', 'sticker-8',
    'sticker-9', 'sticker-10'
)
async def get_autocomplete_sticker_names_except(event, actual_value):
    stickers_except = set()
    
    for value in event.interaction.get_non_focused_values().values():
        if value is not None:
            sticker = GUILD__SUPPORT.get_sticker_like(value)
            if (sticker is not None):
                stickers_except.add(sticker)
    
    guild_stickers = GUILD__SUPPORT.stickers
    
    if actual_value is None:
        return sorted(
            sticker.name for sticker in guild_stickers.values()
            if (sticker not in stickers_except)
        )
    
    
    actual_value = actual_value.casefold()
    
    return sorted(
        sticker.name for sticker in guild_stickers.values()
        if (
            (sticker not in stickers_except) and
            (actual_value in sticker.name.casefold())
        )
    )
