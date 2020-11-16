RADIO_LIST = {
    "hardrock-jakarta": "https://ample-08.radiojar.com/7csmg90fuqruv.mp3",
    "prambors-jakarta": "https://masima.rastream.com/masima-pramborsjakarta",
    "trax-jakarta": "https://stream.radiojar.com/rrqf78p3bnzuv"
}

def get_radio_stream(radio):
    return RADIO_LIST.get(radio)

def get_radio_list():
    return [k for k in RADIO_LIST.keys()]
