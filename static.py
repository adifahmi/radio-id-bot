import yaml

try:
    RADIO_STATIONS = yaml.load(open('stations.yaml'), Loader=yaml.FullLoader)['radio-stations']
except FileNotFoundError:
    print("CONFIG ERROR: Please create stations.yaml")
    exit()
except KeyError:
    print("CONFIG ERROR: radio-stations not found, can see stations.yaml.example for the yaml format")
    exit()


def get_radio_stream(radio):
    return RADIO_STATIONS.get(radio)


def get_radio_list():
    if RADIO_STATIONS is None:
        return []
    return [k for k in RADIO_STATIONS.keys()]
