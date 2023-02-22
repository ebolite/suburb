import render
import client

client_username = None

def sburb(window: "render.Window"):
    if client_username is None: connect(window)

def connect(window: "render.Window"):
    username = client.requestdic(intent="player_info")["client_player_name"]
    if username is not None: 
        client_username = username
        sburb(window)
        return
    ...