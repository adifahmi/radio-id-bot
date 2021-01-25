import unittest

from urllib.request import urlopen
from urllib.error import HTTPError, URLError

try:
    from .static import RADIO_STATIONS
except ModuleNotFoundError:
    from static import RADIO_STATIONS


def check_stream_url():
    stat_msgs = []
    stats = []
    for station, url in RADIO_STATIONS.items():
        try:
            req = urlopen(url)
            stat = req.getcode()
        except HTTPError as e:
            print(f"Error for {station} | {e}")
            stat = "not_200"
        except URLError as e:
            print(f"Error for {station} | {e}")
            stat = "urlerror"
        except Exception as e:
            print(f"Error for {station} | {e}")
            stat = "other_error"

        msg = f"• Status for {station} is {stat}"
        stat_msgs.append(msg)
        stats.append(stat)
    return stat_msgs, stats


class TestStreamUrl(unittest.TestCase):

    def test_main(self):
        _, stats = check_stream_url()
        for stat in stats:
            self.assertEqual(stat, 200)


if __name__ == '__main__':
    unittest.main()
