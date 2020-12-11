import yaml

try:
    RADIO_STATIONS = yaml.load(open('stations.yaml'), Loader=yaml.FullLoader)['radio-stations']
except FileNotFoundError:
    print("CONFIG ERROR: Please create stations.yaml")
    exit()
except KeyError:
    print("CONFIG ERROR: radio-stations not found, can see stations.yaml.example for the yaml format")
    exit()


def hot_load_stations():
    return yaml.load(open('stations.yaml'), Loader=yaml.FullLoader)['radio-stations']


def get_radio_stream(radio):
    return hot_load_stations().get(radio)


def get_radio_list():
    stations = hot_load_stations()
    if stations is None:
        return []
    stations_name = [k for k in stations.keys()]
    return sorted(stations_name, key=str.lower)
