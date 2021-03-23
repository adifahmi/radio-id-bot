import math
import random
import string
import re
import yaml
import psutil
import subprocess
import platform
import tempfile
import datetime
import os

from collections import OrderedDict
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

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
NOW_PLAYING = {}  # NOW_PLAYING as a dict db, maybe in the future can switch to actual dbms
STATIONS_LIST_STATUS = {}


class Stations:
    def __init__(self):
        self.stations = STATIONS_LIST_STATUS
        self.init_station_list()

    def hot_load_stations(self):
        try:
            return yaml.load(open('stations.yaml'), Loader=yaml.FullLoader)['radio-stations']
        except FileNotFoundError:
            print("CONFIG ERROR: Please create stations.yaml")
            return None
        except KeyError:
            print("CONFIG ERROR: radio-stations not found, can see stations.yaml.example for the yaml format")
            return None

    def init_station_list(self):
        loaded_stations = self.hot_load_stations()
        if loaded_stations is None:
            self.stations = {}
            return
        for station_name, url in loaded_stations.items():
            self.stations[station_name] = {
                "url": url,
                "status": 200
            }

    def reload_station_list(self):
        loaded_stations = self.hot_load_stations()
        if loaded_stations is None:
            self.stations = {}
            return
        station_name_list = [k for k in loaded_stations.keys()]

        # handle removed station
        for station_name in list(self.stations.keys()):
            if station_name not in station_name_list:
                del self.stations[station_name]

        # handle added station
        for station_name in station_name_list:
            if station_name not in self.stations.keys():
                self.stations[station_name] = {
                    "url": loaded_stations[station_name],
                    "status": 200
                }

    def get_stations(self, is_sort=True):
        if is_sort is True:
            return OrderedDict(sorted(self.stations.items(), key=lambda t: t[0]))
        return self.stations

    def get_stations_by_name(self, station_name):
        return self.stations.get(station_name)

    def check_station_url(self, url):
        try:
            req = urlopen(url)
            stat = req.getcode()
        except HTTPError as e:
            stat = str(e)
        except URLError as e:
            stat = str(e)
        except Exception as e:
            stat = str(e)
        return stat

    def update_station_status(self):
        self.reload_station_list()
        stat_info_dict = {}

        for station_name, station_attr in self.stations.items():
            url = station_attr["url"]
            stat = self.check_station_url(url)
            print(f"status for {station_name} is {stat}")

            self.stations[station_name]["status"] = stat
            stat_info_dict[station_name] = stat

        return stat_info_dict


class Playing:
    def __init__(self):
        self.np = NOW_PLAYING

    def current_play(self, guild_id):
        return self.np.get(guild_id)

    def add_to_play(self, guild_id, guild_name, station):
        self.np[guild_id] = {"station": station, "guild_name": guild_name}

    def remove_from_play(self, guild_id):
        self.np.pop(guild_id, None)

    def get_play_count(self):
        return len(self.np)

    def get_all_play(self):
        return self.np


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
    def __init__(self, id, name, member_count):
        self.id = id
        self.name = name
        self.member_count = member_count

    def __repr__(self):
        return f"Guild(id={self.id}, name={self.name}, member_count={self.member_count})"


def dummy_guilds(n=10):
    guilds = []
    for i in range(n):
        guilds.append(
            DummyGuilds(
                i,
                generate_random_string(random.randint(5, 10)),
                random.randint(10, 1000)
            )
        )
    return guilds


def get_emoji_by_number(num):
    emoji = ""
    for snum in str(num):
        try:
            snum = int(snum)
        except ValueError:
            continue
        emoji += f"{EMOJI_NUMBER.get(snum)} "
    return emoji


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


def is_valid_url(url):
    """
        Taken from django URL validator
        https://github.com/django/django/blob/master/django/core/validators.py#L65
    """
    ul = '\u00a1-\uffff'  # Unicode letters range (must not be a raw string).

    # IP patterns
    ipv4_re = r'(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}'
    ipv6_re = r'\[[0-9a-f:.]+\]'  # (simple regex, validated later)

    # Host patterns
    hostname_re = r'[a-z' + ul + r'0-9](?:[a-z' + ul + r'0-9-]{0,61}[a-z' + ul + r'0-9])?'
    # Max length for domain name labels is 63 characters per RFC 1034 sec. 3.1
    domain_re = r'(?:\.(?!-)[a-z' + ul + r'0-9-]{1,63}(?<!-))*'
    tld_re = (
        r'\.'                                # dot
        r'(?!-)'                             # can't start with a dash
        r'(?:[a-z' + ul + '-]{2,63}'         # domain label
        r'|xn--[a-z0-9]{1,59})'              # or punycode label
        r'(?<!-)'                            # can't end with a dash
        r'\.?'                               # may have a trailing dot
    )
    host_re = '(' + hostname_re + domain_re + tld_re + '|localhost)'

    regex = re.compile(
        r'^(?:[a-z0-9.+-]*)://'  # scheme is validated separately
        r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'  # user:pass authentication
        r'(?:' + ipv4_re + '|' + ipv6_re + '|' + host_re + ')'
        r'(?::\d{2,5})?'  # port
        r'(?:[/?#][^\s]*)?'  # resource path
        r'\Z', re.IGNORECASE)
    return re.match(regex, url) is not None


def split_to_columns(text):
    lines = text.split("\n")
    max_len = len(max(lines, key=len))  # find longest text in list

    column = []
    halflen = int(math.ceil(len(lines) / 2))
    for x in range(halflen):
        left_line = lines[x]
        len_left_line = len(left_line)
        try:
            right_lane = lines[x + halflen]
        except IndexError:
            right_lane = " "
        len_right_line = len(right_lane)

        # append space to make it equal with longest line
        if len_left_line < max_len or len_right_line < max_len:
            left_line = left_line + " " * (max_len - len_left_line)
            right_lane = right_lane + " " * (max_len - len_right_line)

        per_line = "   ".join([left_line, right_lane])
        column.append(per_line)

    column_text = "\n".join(column)
    return column_text


def split_to_list(text: str, max_len: int = 1000):
    spllited_text = []
    if len(text) >= max_len:
        remain_text = text
        while True:
            split_by_new_line = remain_text.split("\n")
            app_text = ""
            for new_line_text in split_by_new_line:
                new_line_text = new_line_text + "\n"
                if len(app_text) + len(new_line_text) >= max_len:
                    break
                app_text += new_line_text

            spllited_text.append(app_text)
            remain_text = remain_text[len(app_text):]

            if remain_text == "":
                break
    else:
        spllited_text = [text]
    return spllited_text


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def run_sys_info():
    sys_name = f"{platform.system()} - {platform.release()} ({platform.dist()[0]} {platform.dist()[1]} {platform.dist()[2]})"

    total_cpu = psutil.cpu_count()
    cpu_usage_overall = psutil.cpu_percent(interval=1)
    cpu_usage_per_cpu = psutil.cpu_percent(interval=1, percpu=True)

    ram = psutil.virtual_memory()
    total_ram = convert_size(ram.total)
    ram_usage = convert_size(ram.used)
    ram_usage_percent = ram.percent

    disk = psutil.disk_usage('/')
    total_disk = convert_size(disk.total)
    disk_usage = convert_size(disk.used)
    disk_usage_percent = disk.percent

    sys_info_fmt = f"{sys_name} \n"
    sys_info_fmt += f"\nTotal CPU: {total_cpu}\n"
    sys_info_fmt += f"CPU Usage (overall): {cpu_usage_overall}%\n"
    sys_info_fmt += "CPU Usage (per CPU):\n"
    per_cpu_info = ""
    for cpu_num in range(total_cpu):
        new_line = "" if cpu_num == 0 else "\n"
        per_cpu_info += f"{new_line}{' ' * 3}- CPU {cpu_num + 1}: {cpu_usage_per_cpu[cpu_num]}%"
    per_cpu_info = split_to_columns(per_cpu_info)
    sys_info_fmt += per_cpu_info
    sys_info_fmt += f"\n\nTotal RAM: {total_ram}\n"
    sys_info_fmt += f"RAM Usage: {ram_usage} ({ram_usage_percent}%)\n"
    sys_info_fmt += f"\nTotal Disk: {total_disk}\n"
    sys_info_fmt += f"Disk Usage: {disk_usage} ({disk_usage_percent}%)\n"
    return sys_info_fmt


def run_cmd(cmd):
    print(f"Init run cmd: `{cmd}`")
    try:
        cmd_list = cmd.split(" ")
        run = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        run_err = run.stderr.decode('utf-8')
        if run_err != "":
            return False, run_err
        return True, run.stdout.decode('utf-8')
    except Exception as err:
        return False, str(err)


def run_speedtest():
    _, output = run_cmd('speedtest')
    return output


def run_ping(url, times=4):
    cmd = f"ping -c {str(times)} {url}"
    _, output = run_cmd(cmd)
    return output


def create_tempfile(data):
    fp = tempfile.TemporaryFile()
    if type(data) is str:
        data = str.encode(data)
    fp.write(data)
    fp.seek(0)
    file = fp.read()
    fp.close()
    return file


def list_to_csv(datas):
    return '|'.join(map(str, datas))


def generate_report_csv(guild_obj, params):
    total_guild = len(guild_obj)
    csv_guilds = ""
    csv_guilds_detail = ""
    total_member = 0
    num = 1
    for guild in guild_obj:
        csv_guilds += f'{num},"{guild.name}",{guild.member_count},{guild.id}\n'

        csv_guilds_detail += f'{num},"{guild.name}",{guild.member_count},{guild.id},'
        csv_guilds_detail += f'{guild.created_at},{guild.region},{guild.bitrate_limit},'
        csv_guilds_detail += f'"{guild.me.nick}","{list_to_csv([x.name for x in guild.me.roles])}",'
        csv_guilds_detail += f'{guild.preferred_locale},{guild.premium_tier},{guild.icon_url},'
        csv_guilds_detail += f'"{list_to_csv([x for x in guild.features])}",'
        csv_guilds_detail += f'"{list_to_csv([x.name for x in guild.roles])}",'
        csv_guilds_detail += f'"{list_to_csv([x.name for x in guild.text_channels])}",'
        csv_guilds_detail += f'"{list_to_csv([x.name for x in guild.voice_channels])}"\n'

        total_member += guild.member_count
        num += 1

    csv_report = f"Added by {total_guild} servers\n"
    csv_report += f"Total members: {total_member}\n\n"

    if "details" in params:
        csv_report += "ID,Name,Member Count,Guild ID,Created At (UTC),Voice Region,Bitrate Limit,Bot Nick," + \
            "Bot Roles,Preferred Locale,Premium Tier,Icon URL,Features,Roles,Text Channels,Voice Channels\n"
        csv_report += csv_guilds_detail
    else:
        csv_report += "ID,Name,Member Count,Guild ID\n"
        csv_report += csv_guilds

    now = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")
    file = create_tempfile(csv_report)
    env = os.environ.get("ENVIRONMENT")
    filename = f"{env}/RadioID_{now}.csv"
    if "details" in params:
        filename = f"{env}/RadioID_{now}_details.csv"
    return file, filename
