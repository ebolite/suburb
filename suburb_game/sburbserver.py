import render
import client
import themes

client_username = None

def sburb(window: "render.Window"):
    window.theme = themes.default
    if client_username is None: 
        connect(window)
        return
    ...

def connect(window: "render.Window"):
    username = client.requestdic(intent="player_info")["client_player_name"]
    if username is not None: 
        global client_username
        client_username = username
        sburb(window)
        return
    dic = client.requestdic(intent="get_client_server_chains")
    chains: list = dic["chains"]
    no_server: list = dic["no_server"]
    player_names: dict = dic["player_names"]
    server_client: dict = dic["server_client"]
    print("chains", chains)
    print("no_server", no_server)
    print("server_client", server_client)
    icon = render.Image(0.15, 0.25, "sprites/largeicon.png")
    icon.convert = False
    icon.bind_to(window.viewport)
    text = render.Text(0.5, 0.93, "Connect to a client.")
    text.color = window.theme.light
    text.outline_color = window.theme.dark
    text.bind_to(window.viewport)
    chains_text = render.Text(0.6, 0.05, "Server -> Client chains")
    chains_text.color = window.theme.light
    chains_text.outline_color = window.theme.dark
    chains_text.bind_to(window.viewport)
    if len(chains) == 0:
        no_chains_text = render.Text(0.6, 0.2, "None currently.")
        no_chains_text.bind_to(window.viewport)
    for chain_index, chain in enumerate(chains):
        y = 0.1 + 0.07*chain_index
        chain_text = render.Text(0.6, y, " -> ".join(chain))
    def get_connect_button(player_name):
        def connect_button():
            client.requestplus(intent="computer", content={"command": "connect", "client_player_username": player_name})
        return connect_button
    connect_button_y = 0.83
    for player_index, player_name in enumerate(no_server):
        connect_button_x = (1/(len(no_server)+1)) * (player_index + 1)
        nickname = player_names[player_name]
        button = render.TextButton(connect_button_x, connect_button_y, 200, 50, nickname, get_connect_button(player_name))
        button.bind_to(window.viewport)
