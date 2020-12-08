import random
import string

EMOJI_NUMBER = {
    0: '0️⃣',
    1: '1️⃣',
    2: '2️⃣',
    3: '3️⃣',
    4: '4️⃣',
    5: '5️⃣',
    6: '6️⃣',
    7: '7️⃣',
    8: '8️⃣',
    9: '9️⃣',
}


def generate_random_string(n=10):
    r = ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=n
        )
    )
    return r


def chunk_list(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out


class DummyGuilds:
    def __init__(self, name, member_count):
        self.name = name
        self.member_count = member_count


def dummy_guilds(n=10):
    guilds = []
    for _ in range(n):
        guilds.append(
            DummyGuilds(
                generate_random_string(random.randint(5, 10)),
                random.randint(10, 1000)
            )
        )
    return guilds


def get_emoji_by_number(num):
    return EMOJI_NUMBER.get(num)


def get_number_by_emoji(emoji):
    for k, v in EMOJI_NUMBER.items():
        if str(emoji) == v:
            return k
    return None


def get_page(current_page, emoji):
    if str(emoji) == '⏩':
        return current_page + 1
    else:
        return current_page - 1
