# Radio-Id Bot (Discord Voice Bot)

> Radio-id-bot is a simple Discord Music Bot built with discord.py to play a radio from some Indonesian radio-station

## Getting Started

Invite this bot to your server with this [link 🔗](https://discord.com/api/oauth2/authorize?client_id=777757482687922198&permissions=8&scope=bot)

## Commands

Note: The default prefix is `!radio`

* `!radioid help`
List all available commands

* `!radioid ping`
Check bot discord latency

* `!radioid join <channel-name>`
Join to desired channel, if empty default to Author voice channel

* `!radioid list `
List all available radio stations

* `!radioid play <radio-station>`
Join/move to author voice channel and start playing the radio

* `!radioid stop`
Stop the radio

* `!radioid leave`
Leave voice channel

* `!radioid about`
About this bot

## References
* https://discordpy.readthedocs.io/en/latest/
* https://stackoverflow.com/a/62495928/4844294
* https://realpython.com/how-to-make-a-discord-bot-python/

## Prerequisite to run/host this bot:
* Python 3.5+
* [FFMPEG](https://ffmpeg.org/download.html)

## Example how to run
* on Ubuntu:

    sudo apt install ffmpeg
    virtualenv -p python3.6 venv
    . venv/bin/activate
    pip install -r requirements.txt

* Create .env file and put your discord bot token on it
* Create stations.yaml file (follow the example) and store your radio stations list there

* Run the python

    python main.py
    
## About

* Contact me on [twitter](https://twitter.com/adifahmii)
