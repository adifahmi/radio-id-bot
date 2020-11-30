import unittest

from urllib.request import urlopen
from urllib.error import HTTPError, URLError

from static import RADIO_STATIONS

class TestStringMethods(unittest.TestCase):

    def test_stream_url(self):
        for station, url in RADIO_STATIONS.items():
            try:
                req = urlopen(url)
                stats = req.getcode()
            except HTTPError as e:
                print(f"Error for {station} | {e}")
                stats = "not_200"
            except URLError as e:
                print(f"Error for {station} | {e}")
                stats = "urlerror"
            except Exception as e:
                print(f"Error for {station} | {e}")
                stats = "other_error"

            print(f"Status for {station} is {stats}")

            self.assertEqual(stats, 200)


if __name__ == '__main__':
    unittest.main()
