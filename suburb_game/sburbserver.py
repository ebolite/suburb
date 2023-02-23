from typing import Optional

import render
import client
import themes

client_username = None
current_x = None
current_y = None
viewport_dic = {}

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
    
def draw_sburb_bar(window, tilemap: Optional["render.TileMap"]=None):
    client_grist_cache = viewport_dic["client_grist_cache"]
    build_display_box = render.SolidColor(235, 50, 150, 50, window.theme.white)
    build_display_box.bind_to(window.viewport)
    build_display_box.outline_color = window.theme.dark
    build_grist_icon = render.Image(0.13, 0.6, "sprites/grists/build.png")
    build_grist_icon.scale = 0.66
    build_grist_icon.bind_to(build_display_box)
    build_grist_number = render.Text(0.6, 0.6, str(client_grist_cache["build"]))
    build_grist_number.set_fontsize_by_width(100)
    build_grist_number.color = window.theme.dark
    build_grist_number.bind_to(build_display_box)
    ui_bar = render.Image(0, 0, "sprites/computer/Sburb/sburb_ui.png")
    ui_bar.absolute = True
    ui_bar.bind_to(window.viewport)
    spirograph = render.get_spirograph(0, 0)
    spirograph.absolute = True
    spirograph.scale = 0.5
    spirograph.bind_to(ui_bar)
    def get_arrow_function(direction):
        def arrow_function():
            move_view_by_direction(direction)
            if tilemap is not None: tilemap.update_map()
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
    selectbutton = render.Button(0.27, 0.16, "sprites/computer/Sburb/select_button.png", "sprites/computer/Sburb/select_button.png", placeholder)
    selectbutton.overlay_on_click = True
    selectbutton.bind_to(ui_bar)
    selectbutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.dark)
    selectbutton_background.border_radius = 2
    selectbutton_background.bind_to(selectbutton)
    selectbutton.bring_to_top()
    revisebutton = render.Button(55, 0, "sprites/computer/Sburb/revise_button.png", None, placeholder)
    revisebutton.absolute = True
    revisebutton.overlay_on_click = True
    revisebutton.bind_to(selectbutton)
    revisebutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.dark)
    revisebutton_background.border_radius = 2
    revisebutton_background.bind_to(revisebutton)
    revisebutton.bring_to_top()
    deploybutton = render.Button(55, 0, "sprites/computer/Sburb/deploy_button.png", None, placeholder)
    deploybutton.absolute = True
    deploybutton.overlay_on_click = True
    deploybutton.bind_to(revisebutton)
    deploybutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.dark)
    deploybutton_background.border_radius = 2
    deploybutton_background.bind_to(deploybutton)
    deploybutton.bring_to_top()
    phernaliaregistrybutton = render.Button(55, 0, "sprites/computer/Sburb/phernalia_registry_button.png", None, placeholder)
    phernaliaregistrybutton.absolute = True
    phernaliaregistrybutton.overlay_on_click = True
    phernaliaregistrybutton.bind_to(deploybutton)
    phernaliaregistrybutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.dark)
    phernaliaregistrybutton_background.border_radius = 2
    phernaliaregistrybutton_background.bind_to(phernaliaregistrybutton)
    phernaliaregistrybutton.bring_to_top()
    gristcachebutton = render.Button(55, 0, "sprites/computer/Sburb/grist_cache_button.png", None, placeholder)
    gristcachebutton.absolute = True
    gristcachebutton.overlay_on_click = True
    gristcachebutton.bind_to(phernaliaregistrybutton)
    gristcachebutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.dark)
    gristcachebutton_background.border_radius = 2
    gristcachebutton_background.bind_to(gristcachebutton)
    gristcachebutton.bring_to_top()
    atheneumbutton = render.Button(55, 0, "sprites/computer/Sburb/atheneum_button.png", None, placeholder)
    atheneumbutton.absolute = True
    atheneumbutton.overlay_on_click = True
    atheneumbutton.bind_to(gristcachebutton)
    atheneumbutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.dark)
    atheneumbutton_background.border_radius = 2
    atheneumbutton_background.bind_to(atheneumbutton)
    atheneumbutton.bring_to_top()
    alchemizebutton = render.Button(55, 0, "sprites/computer/Sburb/alchemize_button.png", None, placeholder)
    alchemizebutton.absolute = True
    alchemizebutton.overlay_on_click = True
    alchemizebutton.bind_to(atheneumbutton)
    alchemizebutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.dark)
    alchemizebutton_background.border_radius = 2
    alchemizebutton_background.bind_to(alchemizebutton)
    alchemizebutton.bring_to_top()

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
    global viewport_dic
    viewport_dic = client.requestplusdic(intent="computer", content={"command": "viewport", "x":current_x, "y":current_y})
    new_map = viewport_dic["map"]
    specials = viewport_dic["specials"]
    instances = viewport_dic["instances"]
    room_name = viewport_dic["room_name"]
    item_display = render.RoomItemDisplay(20, 210, instances, server_view=True)
    tilemap = render.TileMap(0.5, 0.5, new_map, specials, room_name, item_display, server_view=True)
    draw_sburb_bar(window, tilemap)

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
