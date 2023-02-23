import render
import client
import themes

client_username = None
current_x = None
current_y = None

def placeholder(): pass

def is_tile_in_bounds(map_tiles, x: int, y: int) -> bool:
    if y < 0: return False
    if x < 0: return False
    if y >= len(map_tiles): return False
    if x >= len(map_tiles[0]): return False
    return True

def move_view_by_direction(direction:str) -> bool:
    if current_x is None or current_y is None: return False
    target_x = current_x
    target_y = current_y
    if direction == "up": target_y -= 1
    if direction == "down": target_y += 1
    if direction == "right": target_x += 1
    if direction == "left": target_x -= 1
    return move_view_to_tile(target_x, target_y)
    
def move_view_to_tile(target_x:int, target_y:int) -> bool:
    reply = client.requestplus(intent="computer", content={"command": "is_tile_in_bounds", "x":target_x, "y":target_y})
    if reply == "False": return False
    else:
        global current_x
        global current_y
        current_x = target_x
        current_y = target_y
        return True

def sburb(window: "render.Window"):
    window.theme = themes.default
    if client_username is None: 
        connect(window)
        return
    global current_x
    global current_y
    if current_x is None or current_y is None:
        coords = client.requestplusdic(intent="computer", content={"command": "starting_sburb_coords"})
        current_x = coords["x"]
        current_y = coords["y"]
    dic = client.requestplusdic(intent="computer", content={"command": "viewport", "x":current_x, "y":current_y})
    new_map = dic["map"]
    specials = dic["specials"]
    instances = dic["instances"]
    room_name = dic["room_name"]
    item_display = render.RoomItemDisplay(20, 210, instances, server_view=True)
    tile_map = render.TileMap(0.5, 0.5, new_map, specials, room_name, item_display, server_view=True)
    ui_bar = render.Image(0, 0, "sprites/computer/Sburb/sburb_ui.png")
    ui_bar.absolute = True
    ui_bar.bind_to(window.viewport)
    def get_arrow_function(direction):
        def arrow_function():
            move_view_by_direction(direction)
            tile_map.update_map()
        return arrow_function
    uparrow = render.Button(116, 56, "sprites/computer/Sburb/uparrow.png", "sprites/computer/Sburb/uparrow_pressed.png", get_arrow_function("up"))
    uparrow.absolute = True
    uparrow.bind_to(ui_bar)
    leftarrow = render.Button(94, 78, "sprites/computer/Sburb/leftarrow.png", "sprites/computer/Sburb/leftarrow_pressed.png", get_arrow_function("left"))
    leftarrow.absolute = True
    leftarrow.bind_to(ui_bar)
    rightarrow = render.Button(148, 78, "sprites/computer/Sburb/rightarrow.png", "sprites/computer/Sburb/rightarrow_pressed.png", get_arrow_function("right"))
    rightarrow.absolute = True
    rightarrow.bind_to(ui_bar)
    downarrow = render.Button(116, 110, "sprites/computer/Sburb/downarrow.png", "sprites/computer/Sburb/downarrow_pressed.png", get_arrow_function("down"))
    downarrow.absolute = True
    downarrow.bind_to(ui_bar)
    middlebutton = render.Button(122, 84, "sprites/computer/Sburb/middlebutton.png", "sprites/computer/Sburb/middlebutton_pressed.png", placeholder)
    middlebutton.absolute = True
    middlebutton.bind_to(ui_bar)

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
        y = 0.13 + 0.07*chain_index
        chain_names = [player_names[name] for name in chain]
        chain_text = render.Text(0.6, y, " -> ".join(chain_names))
        chain_text.set_fontsize_by_width(900)
        chain_text.bind_to(window.viewport)
    def get_connect_button(player_name):
        def connect_button():
            client.requestplus(intent="computer", content={"command": "connect", "client_player_username": player_name})
            window.reload()
        return connect_button
    connect_button_y = 0.83
    for player_index, player_name in enumerate(no_server):
        connect_button_x = (1/(len(no_server)+1)) * (player_index + 1)
        nickname = player_names[player_name]
        button = render.TextButton(connect_button_x, connect_button_y, 200, 50, nickname, get_connect_button(player_name))
        button.bind_to(window.viewport)
