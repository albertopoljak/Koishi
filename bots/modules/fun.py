from random import random, randint, choice
from html import unescape as html_unescape
from functools import partial as partial_func

from scarletio import Lock
from hata import Client, Embed, BUILTIN_EMOJIS, KOKORO, DiscordException, ERROR_CODES, Emoji
from hata.ext.command_utils import wait_for_reaction
from hata.ext.slash import abort

from bot_utils.constants import GUILD__SUPPORT

SLASH_CLIENT : Client


TRIVIA_QUEUE = []
TRIVIA_URL = 'https://opentdb.com/api.php'
TRIVIA_REQUEST_LOCK = Lock(KOKORO)
TRIVIA_USER_LOCK = set()

async def get_trivias():
    if TRIVIA_REQUEST_LOCK.is_locked():
        await TRIVIA_REQUEST_LOCK
        return
    
    async with TRIVIA_REQUEST_LOCK:
        async with SLASH_CLIENT.http.get(TRIVIA_URL, params={'amount': 100, 'category': 31}) as response:
            json = await response.json()
        
        for trivia_data in json['results']:
            trivia = (
                html_unescape(trivia_data['question']),
                html_unescape(trivia_data['correct_answer']),
                [html_unescape(element) for element in trivia_data['incorrect_answers']],
            )
            
            TRIVIA_QUEUE.append(trivia)

async def get_trivia():
    if TRIVIA_QUEUE:
        return TRIVIA_QUEUE.pop()
    
    await get_trivias()
    
    if TRIVIA_QUEUE:
        return TRIVIA_QUEUE.pop()
    
    return None

TRIVIA_OPTIONS = (
    BUILTIN_EMOJIS['regional_indicator_a'],
    BUILTIN_EMOJIS['regional_indicator_b'],
    BUILTIN_EMOJIS['regional_indicator_c'],
    BUILTIN_EMOJIS['regional_indicator_d'],
)

def check_for_trivia_emoji(user, event):
    if event.user is not user:
        return False
    
    if event.emoji not in TRIVIA_OPTIONS:
        return False
    
    return True


@SLASH_CLIENT.interactions(is_global=True, name='trivia')
async def trivia_(client, event):
    """Asks a trivia."""
    guild = event.guild
    if guild is None:
        abort('Guild only command.')
    
    if client.get_guild_profile_for(guild) is None:
        abort('I must be in the guild to execute this command.')
    
    if not event.channel.cached_permissions_for(client).can_add_reactions:
        abort('I need add `reactions permission` to execute this command.')
    
    user = event.user
    if user.id in TRIVIA_USER_LOCK:
        abort('You are already in a trivia game.')
    
    TRIVIA_USER_LOCK.add(user.id)
    try:
        yield
        
        trivia = await get_trivia()
        if trivia is None:
            abort('No memes for now.')
            return
        
        question, correct, wrong = trivia
        possibilities = [correct, *wrong]
        correct_emoji = TRIVIA_OPTIONS[possibilities.index(correct)]
        
        description_parts = []
        for emoji, possibility in zip(TRIVIA_OPTIONS, possibilities):
            description_parts.append(emoji.as_emoji)
            description_parts.append(' ')
            description_parts.append(possibility)
            description_parts.append('\n')
        
        del description_parts[-1]
        
        description = ''.join(description_parts)
        
       
        message = yield Embed(question, description).add_author(user.avatar_url, user.full_name)
        
        for emoji in TRIVIA_OPTIONS:
            await client.reaction_add(message, emoji)
        
        try:
           reaction_add_event = await wait_for_reaction(client, message, partial_func(check_for_trivia_emoji, user), 300.)
        except TimeoutError:
            title = 'Oof'
            description = 'Timeout occurred.'
        else:
            if reaction_add_event.emoji is correct_emoji:
                title = 'Noice'
                description = f'I raised that neko.\n\n{correct_emoji.as_emoji} {correct}'
            else:
                title = 'Oof'
                description = f'The correct answer is:\n\n{correct_emoji.as_emoji} {correct}'
        
        yield Embed(title, description).add_author(user.avatar_url, user.full_name)
        
        if message.channel.cached_permissions_for(client).can_manage_messages:
            await client.reaction_clear(message)
    
    finally:
        TRIVIA_USER_LOCK.discard(user.id)


@SLASH_CLIENT.interactions(show_for_invoking_user_only=True, is_global=True)
async def message_me(client, event):
    """Messages you!"""
    yield
    
    channel = await client.channel_private_create(event.user)
    try:
        await client.message_create(channel, 'Love you!')
    except DiscordException as err:
        if err.code == ERROR_CODES.cannot_message_user:
            yield 'Pls turn on private messages from this server!'
        
        raise
    
    yield ':3'


@SLASH_CLIENT.interactions(is_global=True)
async def roll(client, event,
    dice_count: ([(str(v), v) for v in range(1, 7)], 'With how much dice do you wanna roll?') = 1,
):
    """Rolls with dices."""
    amount = 0
    for _ in range(dice_count):
        amount += round(1.+(random() * 5.))
    
    return str(amount)


@SLASH_CLIENT.interactions(is_global=True)
async def rate(client, event,
    target_user: ('user', 'Do you want me to rate someone else?') = None,
):
    """Rates someone!"""
    if target_user is None:
        target_user = event.user
    
    if isinstance(target_user, Client) or client.is_owner(target_user):
        result = 10
    else:
        result = target_user.id % 11
    
    return f'I rate {target_user.name_at(event.guild)} {result}/10'


@SLASH_CLIENT.interactions(is_global=True)
async def yuno():
    """Your personal yandere!"""
    return Embed(
        'YUKI YUKI YUKI!',
        (
            '░░░░░░░░░░░▄▄▀▀▀▀▀▀▀▀▄▄░░░░░░░░░░░░░\n'
            '░░░░░░░░▄▀▀░░░░░░░░░░░░▀▄▄░░░░░░░░░░\n'
            '░░░░░░▄▀░░░░░░░░░░░░░░░░░░▀▄░░░░░░░░\n'
            '░░░░░▌░░░░░░░░░░░░░▀▄░░░░░░░▀▀▄░░░░░\n'
            '░░░░▌░░░░░░░░░░░░░░░░▀▌░░░░░░░░▌░░░░\n'
            '░░░▐░░░░░░░░░░░░▒░░░░░▌░░░░░░░░▐░░░░\n'
            '░░░▌▐░░░░▐░░░░▐▒▒░░░░░▌░░░░░░░░░▌░░░\n'
            '░░▐░▌░░░░▌░░▐░▌▒▒▒░░░▐░░░░░▒░▌▐░▐░░░\n'
            '░░▐░▌▒░░░▌▄▄▀▀▌▌▒▒░▒░▐▀▌▀▌▄▒░▐▒▌░▌░░\n'
            '░░░▌▌░▒░░▐▀▄▌▌▐▐▒▒▒▒▐▐▐▒▐▒▌▌░▐▒▌▄▐░░\n'
            '░▄▀▄▐▒▒▒░▌▌▄▀▄▐░▌▌▒▐░▌▄▀▄░▐▒░▐▒▌░▀▄░\n'
            '▀▄▀▒▒▌▒▒▄▀░▌█▐░░▐▐▀░░░▌█▐░▀▄▐▒▌▌░░░▀\n'
            '░▀▀▄▄▐▒▀▄▀░▀▄▀░░░░░░░░▀▄▀▄▀▒▌░▐░░░░░\n'
            '░░░░▀▐▀▄▒▀▄░░░░░░░░▐░░░░░░▀▌▐░░░░░░░\n'
            '░░░░░░▌▒▌▐▒▀░░░░░░░░░░░░░░▐▒▐░░░░░░░\n'
            '░░░░░░▐░▐▒▌░░░░▄▄▀▀▀▀▄░░░░▌▒▐░░░░░░░\n'
            '░░░░░░░▌▐▒▐▄░░░▐▒▒▒▒▒▌░░▄▀▒░▐░░░░░░░\n'
            '░░░░░░▐░░▌▐▐▀▄░░▀▄▄▄▀░▄▀▐▒░░▐░░░░░░░\n'
            '░░░░░░▌▌░▌▐░▌▒▀▄▄░░░░▄▌▐░▌▒░▐░░░░░░░\n'
            '░░░░░▐▒▐░▐▐░▌▒▒▒▒▀▀▄▀▌▐░░▌▒░▌░░░░░░░\n'
            '░░░░░▌▒▒▌▐▒▌▒▒▒▒▒▒▒▒▐▀▄▌░▐▒▒▌░░░░░░░\n'
        ),
        color = 0xffafde,
        url = 'https://www.youtube.com/watch?v=TaDAn_S_4Y8',
    )


@SLASH_CLIENT.interactions(is_global=True)
async def paranoia(client, event):
    """Pa-Pa-Pa-Pa-Paranoia!!!"""
    return Embed(
        'Pa-Pa-Pa-Pa-Paranoia',
        color = 0x08963c,
        url = 'https://www.youtube.com/watch?v=wnli28pjsn4',
    ).add_image(
        'https://i.ytimg.com/vi/wnli28pjsn4/hqdefault.jpg?sqp=-oaymwEZCPYBEIoBSFXyq4qpAwsIARUAAIhCG'
        'AFwAQ==&rs=AOn4CLC27YDJ7qBQhLzq7y5iD85vlIYuHw'
    )


@SLASH_CLIENT.interactions(is_global=True)
async def random_(
    n1: ('int', 'Number limit.'),
    n2: ('int', 'Other number limit!') = 0,
):
    """Do you need some random numbers?"""
    if n1 == n2:
        result = n1
    else:
        if n2 < n1:
            n1, n2 = n2, n1
        
        result = randint(n1, n2)
    
    return str(result)


def generate_love_level():
    value = {
        'titles': (
            f'{BUILTIN_EMOJIS["blue_heart"]} There\'s no real connection between you two {BUILTIN_EMOJIS["blue_heart"]}',
        ),
        'text': (
            'The chance of this relationship working out is really low. You '
            'can get it to work, but with high costs and no guarantee of '
            'working out. Do not sit back, spend as much time together as '
            'possible, talk a lot with each other to increase the chances of '
            'this relationship\'s survival.'
        ),
    }
    
    for x in range(0, 2):
        yield value
    
    value = {
        'titles': (
            f'{BUILTIN_EMOJIS["blue_heart"]} A small acquaintance {BUILTIN_EMOJIS["blue_heart"]}',
        ),
        'text': (
            'There might be a chance of this relationship working out somewhat '
            'well, but it is not very high. With a lot of time and effort '
            'you\'ll get it to work eventually, however don\'t count on it. It '
            'might fall apart quicker than you\'d expect.'
        ),
    }
    
    for x in range(2, 6):
        yield value
    
    value = {
        'titles': (
            f'{BUILTIN_EMOJIS["purple_heart"]} You two seem like casual friends {BUILTIN_EMOJIS["purple_heart"]}',
        ),
        'text': (
            'The chance of this relationship working is not very high. You both '
            'need to put time and effort into this relationship, if you want it '
            'to work out well for both of you. Talk with each other about '
            'everything and don\'t lock yourself up. Spend time together. This '
            'will improve the chances of this relationship\'s survival by a lot.'
        ),
    }
    
    for x in range(6, 21):
        yield value
    
    value = {
        'titles': (
            f'{BUILTIN_EMOJIS["heartpulse"]} You seem like you are good friends {BUILTIN_EMOJIS["heartpulse"]}',
        ),
        'text': (
            'The chance of this relationship working is not very high, but its '
            'not that low either. If you both want this relationship to work, '
            'and put time and effort into it, meaning spending time together, '
            'talking to each other etc., than nothing shall stand in your way.'
        ),
    }
    
    for x in range(21, 31):
        yield value
    
    value = {
        'titles':(
            f'{BUILTIN_EMOJIS["cupid"]} You two are really close aren\'t you? {BUILTIN_EMOJIS["cupid"]}',
        ),
        'text': (
            'Your relationship has a reasonable amount of working out. But do '
            'not overestimate yourself there. Your relationship will suffer '
            'good and bad times. Make sure to not let the bad times destroy '
            'your relationship, so do not hesitate to talk to each other, '
            'figure problems out together etc.'
        ),
    }
    
    for x in range(31, 46):
        yield value
    
    value = {
        'titles': (
            f'{BUILTIN_EMOJIS["heart"]} So when will you two go on a date? {BUILTIN_EMOJIS["heart"]}',
        ),
        'text': (
            'Your relationship will most likely work out. It won\'t be perfect '
            'and you two need to spend a lot of time together, but if you keep '
            'on having contact, the good times in your relationship will '
            'outweigh the bad ones.'
        ),
    }
    
    for x in range(46, 61):
        yield value
    
    value = {
        'titles': (
            f'{BUILTIN_EMOJIS["two_hearts"]} Aww look you two fit so well together {BUILTIN_EMOJIS["two_hearts"]}',
        ),
        'text': (
            'Your relationship will most likely work out well. Don\'t hesitate '
            'on making contact with each other though, as your relationship '
            'might suffer from a lack of time spent together. Talking with '
            'each other and spending time together is key.'
        ),
    }

    for x in range(61, 86):
        yield value
    
    value = {
        'titles': (
            f'{BUILTIN_EMOJIS["sparkling_heart"]} Love is in the air {BUILTIN_EMOJIS["sparkling_heart"]}',
            f'{BUILTIN_EMOJIS["sparkling_heart"]} Planned your future yet? {BUILTIN_EMOJIS["sparkling_heart"]}',
        ),
        'text': (
            'Your relationship will most likely work out perfect. This '
            'doesn\'t mean thought that you don\'t need to put effort into it. '
            'Talk to each other, spend time together, and you two won\'t have '
            'a hard time.'
        ),
    }
    
    for x in range(86, 96):
        yield value
    
    value = {
        'titles': (
            f'{BUILTIN_EMOJIS["sparkling_heart"]} When will you two marry? {BUILTIN_EMOJIS["sparkling_heart"]}',
            f'{BUILTIN_EMOJIS["sparkling_heart"]} Now kiss already {BUILTIN_EMOJIS["sparkling_heart"]}',
        ),
        'text': (
            'You two will most likely have the perfect relationship. But don\'t '
            'think that this means you don\'t have to do anything for it to '
            'work. Talking to each other and spending time together is key, '
            'even in a seemingly perfect relationship.'
        ),
    }
    
    for x in range(96, 101):
        yield value

LOVE_VALUES = tuple(generate_love_level())
del generate_love_level

@SLASH_CLIENT.interactions(is_global=True)
async def love(client, event,
    user_1: ('user', 'Select your heart\'s chosen one!', 'user') = None,
    user_2: ('user', 'Check some else\'s love life?', 'with') = None,
):
    """How much you two fit together?"""
    if user_2 is None:
        source_user = event.user
        
        if user_1 is None:
            target_user = client
        else:
            target_user = user_1
    else:
        target_user = user_2
        
        if user_1 is None:
            source_user = event.user
        else:
            source_user = user_1
    
    if source_user is target_user:
        abort('huh?')
    
    percent = ((source_user.id & 0x1111111111111111111111) + (target_user.id & 0x1111111111111111111111)) % 101
    element = LOVE_VALUES[percent]
    
    return Embed(
        choice(element['titles']),
        f'{source_user:f} {BUILTIN_EMOJIS["heart"]} {target_user:f} scored {percent}%!',
        0xad1457,
    ).add_field(
        'My advice:',
        element['text'],
    )


MINE_MINE_CLEAR = (
    BUILTIN_EMOJIS['white_large_square'].as_emoji,
    BUILTIN_EMOJIS['one'].as_emoji,
    BUILTIN_EMOJIS['two'].as_emoji,
    BUILTIN_EMOJIS['three'].as_emoji,
    BUILTIN_EMOJIS['four'].as_emoji,
    BUILTIN_EMOJIS['five'].as_emoji,
    BUILTIN_EMOJIS['six'].as_emoji,
    BUILTIN_EMOJIS['seven'].as_emoji,
    BUILTIN_EMOJIS['eight'].as_emoji,
    BUILTIN_EMOJIS['bomb'].as_emoji,
)

MINE_MINE = tuple(f'||{e}||' for e in MINE_MINE_CLEAR)

MINE_X_SIZE = 9
MINE_Y_SIZE = 9
MINE_SIZE = MINE_X_SIZE * MINE_Y_SIZE

@SLASH_CLIENT.interactions(is_global=True)
async def minesweeper(
    bomb_count: ([(str(x), x) for x in range(7, 15)], 'How much bombs should be on the field?') = 10,
    raw: ('bool', 'Raw text?') = False,
):
    """Minesweeping is fun!? (not in irl)"""
    
    data = [0 for x in range(MINE_SIZE)]
    
    while bomb_count:
        x = randint(0, 8)
        y = randint(0, 8)
        position = x + y * MINE_X_SIZE
        
        value = data[position]
        if value == 9:
            continue
        
        local_count = 0

        for c_x, c_y in ((-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)):
            local_x = x + c_x
            local_y = y + c_y
            if (
                    local_x != MINE_X_SIZE and
                    local_x != -1 and
                    local_y != MINE_Y_SIZE and
                    local_y != -1 and
                    data[local_x + local_y * MINE_X_SIZE] == 9
            ):
                local_count += 1
        
        if local_count > 3:
            continue

        for c_x,c_y in ((-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)):
            local_x = x + c_x
            local_y = y + c_y
            if local_x != MINE_X_SIZE and local_x != -1 and local_y != MINE_Y_SIZE and local_y != -1:
                local_position = local_x + local_y * MINE_X_SIZE
                local_value = data[local_position]
                if local_value == 9:
                    continue
                data[local_position] = local_value + 1
        
        data[position] = 9
        
        bomb_count -= 1
    
    result = []
    if raw:
        result.append('```')
    
    result_sub = []
    y = 0
    while True:
        x = 0
        while True:
            result_sub.append(MINE_MINE[data[x + y]])
            x += 1
            if x == MINE_X_SIZE:
                break
        result.append(''.join(result_sub))
        result_sub.clear()
        y += MINE_X_SIZE
        if y == MINE_SIZE:
            break
    
    if raw:
        result.append('```')
    
    return '\n'.join(result)


EMOJI_1 = Emoji.precreate(814618830106132511, name='T90Salute')
EMOJI_2 = Emoji.precreate(588052578214871053, name='tatohaHola')


@SLASH_CLIENT.interactions(guild=GUILD__SUPPORT, show_for_invoking_user_only=True)
async def crywolf_(client, event):
    """Crywolf is a bot"""
    yield 'crywolf is a sus'
    channel = event.channel
    webhook = await client.webhook_get_own_channel(channel)
    if (webhook is None):
        webhook = await client.webhook_create(channel, 'crywolf-bot')
    
    crywolf = await client.user_get(151446521311789057)
    await client.webhook_message_create(
        webhook,
        'Good morning, how are yous?',
        name = crywolf.name,
        avatar_url = crywolf.avatar_url,
        wait = True,
    )
    
    await client.webhook_message_create(
        webhook,
        f'{EMOJI_1} {EMOJI_2}',
        name = crywolf.name,
        avatar_url = crywolf.avatar_url,
        wait = True,
    )


SEX_RESET_AFTER = 600

SEX_SPAM_LOCK = {}

class SexSpamLock:
    __slots__ = ('channel_id', 'expires_at', 'max_level')
    
    def __new__(cls, channel_id, max_level):
        self = object.__new__(cls)
        self.channel_id = channel_id
        self.max_level = max_level
        self.expires_at = 0.0
        
        KOKORO.call_later(SEX_RESET_AFTER, self)
        return self
    
    def __call__(self):
        expires_at = self.expires_at
        if expires_at:
            KOKORO.call_at(expires_at+SEX_RESET_AFTER, self)
        else:
            try:
                del SEX_SPAM_LOCK[self.channel_id]
            except KeyError:
                pass
    
    
    def set_max_level(self, level):
        max_level = self.max_level
        if level > max_level:
            level = max_level
        elif level < max_level:
            self.max_level = level
        
        return level


SEX_IMAGES = [
    'https://cdn.discordapp.com/attachments/568837922288173058/927858207764918284/no-sex-0000.gif',
    'https://cdn.discordapp.com/attachments/568837922288173058/837747879497433158/yes-sex.gif',
    'https://cdn.discordapp.com/attachments/568837922288173058/840676567180771348/yes-sex-hyper-opti.gif',
    'https://cdn.discordapp.com/attachments/568837922288173058/927858614226526228/sex_2_0.png',
]

@SLASH_CLIENT.interactions(is_global=True)
async def sex(event):
    """You horny?"""
    value = random()
    if value > 0.100:
        level = 0
    elif value > 0.012:
        level = 1
    elif value > 0.004:
        level = 2
    else:
        level = 3
    
    channel_id = event.channel_id
    try:
        spam_lock = SEX_SPAM_LOCK[channel_id]
    except KeyError:
        SEX_SPAM_LOCK[channel_id] = SexSpamLock(channel_id, level)
    else:
        level = spam_lock.set_max_level(level)
    
    
    return Embed().add_image(SEX_IMAGES[level])
