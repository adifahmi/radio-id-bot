RADIO_LIST = {
    "hardrock-jakarta": "https://ample-08.radiojar.com/7csmg90fuqruv.mp3?1605508526=&rj-tok=AAABdc_NLSsAXMLmziO7tWWweQ&rj-ttl=5",
    "prambors-jakarta": "https://masima.rastream.com/masima-pramborsjakarta"
}

def get_radio_stream(radio):
    return RADIO_LIST.get(radio)

def get_radio_list():
    return [k for k in RADIO_LIST.keys()]
