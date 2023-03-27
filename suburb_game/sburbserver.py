from typing import Optional, Tuple, Callable, Union
from pygame import Color
import os

import render
import sylladex
import client
import themes
import config
import util

client_username = None
current_x = None
current_y = None
current_mode = "select"
current_info_window = "grist_cache"
current_selected_phernalia = None
current_selected_atheneum = None
current_selected_tile = "."
current_alchemy_item_1: Optional["sylladex.Item"] = None
current_alchemy_item_2: Optional["sylladex.Item"] = None
current_alchemy_item_3: Optional["sylladex.Item"] = None
last_tile_map: Optional["render.TileMap"] = None
viewport_dic = {}
results_sprites: list["render.UIElement"] = []

def get_server_tiles():
    reply_dict = client.requestdic("server_tiles")
    server_tiles = reply_dict["server_tiles"]
    tile_labels = reply_dict["labels"]
    return server_tiles, tile_labels

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

def deploy_item(target_x: int, target_y: int) -> Optional[dict]:
    reply = False
    if current_info_window == "phernalia_registry":
        if current_selected_phernalia is None: return None
        reply = client.requestplusdic(intent="computer", content={
            "command": "deploy_phernalia", "x":target_x, "y":target_y, "item_name": current_selected_phernalia,
            "viewport_x": current_x, "viewport_y": current_y
            })
    elif current_info_window == "atheneum":
        if current_selected_atheneum is None: return None
        reply = client.requestplusdic(intent="computer", content={
            "command": "deploy_atheneum", "x":target_x, "y":target_y, "instance_name": current_selected_atheneum,
            "viewport_x": current_x, "viewport_y": current_y
            })
    if reply:
        return reply
    else:
        return None
        
def revise_tile(target_x: int, target_y: int) -> Optional[dict]:
    reply = client.requestplusdic(intent="computer", content={
        "command": "revise", "x": target_x, "y": target_y, "tile_char": current_selected_tile,
        "viewport_x": current_x, "viewport_y": current_y
    })
    if reply:
        return reply
    else:
        return None
    
def add_instance_to_atheneum(instance_name):
    reply = client.requestplus(intent="computer", content={
        "command": "add_to_atheneum", "viewport_x": current_x, "viewport_y": current_y, "instance_name": instance_name
    })

def update_viewport_dic(dic: Optional[dict]=None):
    global viewport_dic
    if dic is None:
        viewport_dic = client.requestplusdic(intent="computer", content={"command": "viewport", "viewport_x":current_x, "viewport_y":current_y})
    else:
        viewport_dic = dic

def make_item_box(item: Optional["sylladex.Item"], x, y, w, h, theme: "themes.Theme", button_func: Optional[Callable]=None, selected=False, label=False, dowel=False) -> "render.SolidColor":
    item_box = render.SolidColor(x, y, w, h, theme.white)
    if selected: item_box.outline_color = theme.dark
    item_box.border_radius = 3
    if button_func is not None:
        box_button = render.TextButton(0, 0, w, h, "", button_func)
        box_button.draw_sprite = False
        box_button.absolute = True
        box_button.click_on_mouse_down = True
        box_button.bind_to(item_box)
    if item is None: return item_box
    image_path = f"sprites/items/{item.name}.png"
    if os.path.isfile(image_path):
        card_image = render.Image(0.5, 0.5, image_path)
        card_image.convert = False
        card_image.bind_to(item_box)
        card_image.scale = h / 240
    else:
        card_image = None
    if dowel:
        dowel_box_w, dowel_box_h = w//3, h//3
        dowel_box = render.SolidColor(0, h-dowel_box_h, dowel_box_w, dowel_box_h, theme.white)
        dowel_box.outline_color = theme.dark
        dowel_box.bind_to(item_box)
        dowel_image = render.Dowel(0.5, 0.5, item.code, color=viewport_dic["player_color"])
        dowel_image.scale = 0.15
        dowel_image.bind_to(dowel_box)
    if label:
        item_label = render.Text(0.5, 0.1, item.display_name)
        item_label.bind_to(item_box)
        item_label.fontsize = 20
        item_label.color = theme.dark
        item_label.outline_color = theme.white
        item_label.set_fontsize_by_width(w)
    return item_box

def draw_sburb_bar(window: "render.Window", info_window: "render.SolidColor", info_text: "render.Text", tilemap: Optional["render.TileMap"]=None):
    client_grist_cache = viewport_dic["client_grist_cache"]
    build_display_box = render.SolidColor(235, 50, 150, 50, window.theme.white)
    build_display_box.outline_color = window.theme.dark
    build_grist_icon = render.Image(0.13, 0.6, "sprites/grists/build.png")
    build_grist_icon.scale = 0.66
    build_grist_icon.bind_to(build_display_box)
    build_grist_number = render.Text(0.6, 0.6, str(client_grist_cache["build"]))
    build_grist_number.set_fontsize_by_width(100)
    build_grist_number.text_func = lambda *args: viewport_dic["client_grist_cache"].get("build")
    build_grist_number.color = window.theme.dark
    build_grist_number.bind_to(build_display_box)
    ui_bar = render.Image(0, 0, "sprites/computer/Sburb/sburb_ui.png")
    ui_bar.absolute = True
    ui_bar.bind_to(window.viewport)
    build_display_box.bind_to(ui_bar)
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
    selectbutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.light)
    selectbutton_background.border_radius = 2
    selectbutton = render.Button(0.27, 0.16, "sprites/computer/Sburb/select_button.png", None, placeholder)
    selectbutton.overlay_on_click = True
    revisebutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.light)
    revisebutton_background.border_radius = 2
    revisebutton = render.Button(55, 0, "sprites/computer/Sburb/revise_button.png", None, placeholder)
    revisebutton.absolute = True
    revisebutton.overlay_on_click = True
    deploybutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.light)
    deploybutton_background.border_radius = 2
    deploybutton = render.Button(55, 0, "sprites/computer/Sburb/deploy_button.png", None, placeholder)
    deploybutton.absolute = True
    deploybutton.overlay_on_click = True
    def update_buttons():
        selectbutton_background.color = window.theme.light
        revisebutton_background.color = window.theme.light
        deploybutton_background.color = window.theme.light
        match current_mode:
            case "select": selectbutton_background.color = window.theme.dark
            case "revise": revisebutton_background.color = window.theme.dark
            case "deploy": deploybutton_background.color = window.theme.dark
    update_buttons()
    def get_mode_change_button(mode=None, new_info_window=None):
        def button_func():
            global current_mode
            global current_info_window
            if mode is not None: current_mode = mode
            if new_info_window is not None: current_info_window = new_info_window
            update_buttons()
            update_info_window(info_window, info_text)
        return button_func
    selectbutton.onpress = get_mode_change_button("select", "grist_cache")
    revisebutton.onpress = get_mode_change_button("revise", "revise")
    deploybutton.onpress = get_mode_change_button("deploy", "phernalia_registry")
    phernaliaregistrybutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.light)
    phernaliaregistrybutton_background.border_radius = 2
    phernaliaregistrybutton = render.Button(55, 0, "sprites/computer/Sburb/phernalia_registry_button.png", None, get_mode_change_button("deploy", "phernalia_registry"))
    phernaliaregistrybutton.absolute = True
    phernaliaregistrybutton.overlay_on_click = True
    gristcachebutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.light)
    gristcachebutton_background.border_radius = 2
    gristcachebutton = render.Button(55, 0, "sprites/computer/Sburb/grist_cache_button.png", None, get_mode_change_button("select", "grist_cache"))
    gristcachebutton.absolute = True
    gristcachebutton.overlay_on_click = True
    atheneumbutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.light)
    atheneumbutton_background.border_radius = 2
    atheneumbutton = render.Button(55, 0, "sprites/computer/Sburb/atheneum_button.png", None, get_mode_change_button("deploy", "atheneum"))
    atheneumbutton.absolute = True
    atheneumbutton.overlay_on_click = True
    alchemizebutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.light)
    alchemizebutton_background.border_radius = 2
    alchemizebutton = render.Button(55, 0, "sprites/computer/Sburb/alchemize_button.png", None, get_mode_change_button("select", "alchemize"))
    alchemizebutton.absolute = True
    alchemizebutton.overlay_on_click = True
    selectbutton.bind_to(ui_bar)
    selectbutton_background.bind_to(selectbutton)
    revisebutton.bind_to(selectbutton)
    revisebutton_background.bind_to(revisebutton)
    deploybutton.bind_to(revisebutton)
    deploybutton_background.bind_to(deploybutton)
    phernaliaregistrybutton.bind_to(deploybutton)
    phernaliaregistrybutton_background.bind_to(phernaliaregistrybutton)
    gristcachebutton.bind_to(phernaliaregistrybutton)
    gristcachebutton_background.bind_to(gristcachebutton)
    atheneumbutton.bind_to(gristcachebutton)
    atheneumbutton_background.bind_to(atheneumbutton)
    alchemizebutton.bind_to(atheneumbutton)
    alchemizebutton_background.bind_to(alchemizebutton)

def draw_info_window(window: "render.Window") -> Tuple["render.SolidColor", "render.Text"]:
    padding = 5
    border_radius = 3
    iw_w = 370
    iw_h = 500
    iw_outline_width = 4
    iw_x = window.viewport.w-iw_w-iw_outline_width+iw_outline_width
    iw_y = window.viewport.h-iw_h-iw_outline_width-padding
    top_pad_w = iw_w + iw_outline_width*2
    top_pad_h = 20 + iw_outline_width*2
    top_pad_x = 0 - iw_outline_width
    top_pad_y = 0 - top_pad_h + padding
    top_pad = render.SolidColor(top_pad_x, top_pad_y, top_pad_w, top_pad_h, window.theme.dark)
    top_pad.border_radius = border_radius
    header_w = 200
    header_h = 60
    header_x = top_pad_w - header_w
    header_y = 0 - header_h + padding
    header = render.SolidColor(header_x, header_y, header_w, header_h, window.theme.dark)
    header.border_radius = border_radius
    icon_path = config.header_icons[current_info_window]
    header_icon = render.Image(padding, padding, icon_path)
    header_icon.convert = False
    header_icon.absolute = True
    header_icon.path_func = lambda *args: config.header_icons[current_info_window]
    info_window = render.SolidColor(iw_x, iw_y, iw_w, iw_h, window.theme.white)
    info_window.outline_color = window.theme.dark
    info_window.outline_width = iw_outline_width
    info_window.border_radius = border_radius
    text_fontsize = top_pad_h - padding*2
    text_y = top_pad_h//2 - padding - text_fontsize//2 + 2
    text = render.Text(padding, text_y, "text")
    text.color = window.theme.light
    text.absolute = True
    text.fontsize = text_fontsize
    info_window.bind_to(window.viewport)
    top_pad.bind_to(info_window)
    header.bind_to(top_pad)
    header_icon.bind_to(header)
    text.bind_to(top_pad)
    return info_window, text

def display_grist_cache(info_window: "render.SolidColor", info_text: "render.Text", page=0):
    info_window.kill_temporary_elements()
    info_window.color = info_window.theme.light
    padding = 5
    # viewport dic needs to be up to date
    grist_cache: dict = viewport_dic["client_grist_cache"]
    grist_cache_limit = viewport_dic["client_cache_limit"]
    info_text.text = f"Cache Limit: {grist_cache_limit}"
    nonzero_grist = []
    zero_grist = []
    for grist_name, amount in grist_cache.items():
        if amount > 0: nonzero_grist.append(grist_name)
        else: zero_grist.append(grist_name)
    num_columns = 2
    num_rows = 10
    usable_area_w = info_window.w
    usable_area_h = info_window.h - 25
    grist_box_w = usable_area_w//num_columns - padding*2
    grist_box_h = (usable_area_h-padding)//num_rows - padding
    rows = []
    grist_order = nonzero_grist + zero_grist
    for grist_name in grist_order:
        for row in rows:
            if len(row) != num_columns:
                row.append(grist_name)
                break
        else:
            rows.append([grist_name])
    display_rows = rows[page*num_rows:page*num_rows + num_rows]
    for row_index, row in enumerate(display_rows):
        grist_box_y = padding + (grist_box_h+padding)*row_index
        for column_index, grist_name in enumerate(row):
            grist_box_x = padding + (grist_box_w+padding)*column_index
            box = render.make_grist_display(grist_box_x, grist_box_y, grist_box_w, grist_box_h, padding, 
                                            grist_name, grist_cache[grist_name], grist_cache_limit, 
                                            info_window.theme, info_window.theme.white, info_window.theme.dark, info_window.theme.dark,
                                            use_grist_color=True)
            box.bind_to(info_window, temporary=True)
    def get_leftbutton_func(page_num):
        def leftbutton_func():
            display_grist_cache(info_window, info_text, page_num-1)
        return leftbutton_func
    def get_rightbutton_func(page_num):
        def rightbutton_func():
            display_grist_cache(info_window, info_text, page_num+1)
        return rightbutton_func
    page_button_w = info_window.w//2-padding*2
    page_button_h = 20
    page_button_y = info_window.h-page_button_h-padding
    if page != 0:
        left_button = render.TextButton(padding, page_button_y, page_button_w, page_button_h, "<-", get_leftbutton_func(page))
        left_button.absolute = True
        left_button.bind_to(info_window, temporary=True)
    if rows[(page+1)*num_rows:(page+1)*num_rows + num_rows] != []:
        right_button = render.TextButton(padding*2+page_button_w, page_button_y, page_button_w, page_button_h, "->", get_rightbutton_func(page))
        right_button.absolute = True
        right_button.bind_to(info_window, temporary=True)

def display_phernalia_registry(info_window: "render.SolidColor", info_text: "render.Text"):
    info_window.kill_temporary_elements()
    info_window.color = info_window.theme.light
    padding = 4
    # viewport dic needs to be up to date
    available_phernalia: dict = viewport_dic["client_available_phernalia"]
    grist_cache: dict = viewport_dic["client_grist_cache"]
    info_text.text = f"Phernalia Registry"
    num_columns = 3
    usable_area_w = info_window.w
    usable_area_h = info_window.h - 25
    box_w = usable_area_w//num_columns - padding*2
    box_h = box_w
    num_rows = usable_area_h // (box_h + padding*2)
    rows = []
    for item_name in available_phernalia:
        for row in rows:
            if len(row) != num_columns:
                row.append(item_name)
                break
        else:
            rows.append([item_name])
    def get_box_button_func(item_name: str) -> Callable:
        def button_func():
            global current_selected_phernalia
            global current_selected_atheneum
            current_selected_phernalia = item_name
            current_selected_atheneum = None
            display_phernalia_registry(info_window, info_text)
        return button_func
    for row_index, row in enumerate(rows):
        box_y = padding + row_index*(box_h + padding*2)
        for column_index, item_name in enumerate(row):
            box_x = padding + column_index*(box_w + padding*2)
            item = sylladex.Item(item_name, available_phernalia[item_name])
            if current_selected_phernalia == item_name: selected = True
            else: selected = False
            cost_label_h = box_h//5
            item_box_h = box_h-cost_label_h
            item_box = make_item_box(item, box_x, box_y, box_w, item_box_h, info_window.theme, get_box_button_func(item_name), selected=selected)
            item_box.bind_to(info_window, True)
            cost_label_box = render.SolidColor(0, item_box_h, box_w, cost_label_h, info_window.theme.white)
            cost_label_box.border_radius = 3
            cost_label_box.bind_to(item_box)
            if selected: cost_label_box.outline_color = info_window.theme.dark
            cost_label = render.make_grist_cost_display(0, 0, cost_label_h, item.true_cost, grist_cache, cost_label_box, info_window.theme.dark)
            cost_label.bind_to(cost_label_box)

def display_revise(info_window: "render.SolidColor", info_text: "render.Text", page=0):
    info_window.kill_temporary_elements()
    info_window.color = info_window.theme.white
    info_text.text = "Available Tiles"
    padding = 4
    border_width = 2
    cost_label_h = 16
    grist_cache: dict = viewport_dic["client_grist_cache"]
    server_tiles, tile_labels = get_server_tiles()
    tile_scale = 2
    tile_wh = int(render.tile_wh * tile_scale)
    num_rows = info_window.h // (tile_wh + cost_label_h + border_width*2 + padding*2 )
    num_columns = info_window.w // (tile_wh + border_width*2 + padding)
    x_offset = (info_window.w%(tile_wh + border_width*2 + padding))
    rows = []
    def get_tile_button_func(tile_char):
        def func():
            global current_selected_tile
            current_selected_tile = tile_char
            display_revise(info_window, info_text, page)
        return func
    for tile_char in server_tiles:
        for row in rows:
            if len(row) != num_columns:
                row.append(tile_char)
                break
        else:
            rows.append([tile_char])
    display_rows = rows[page*num_rows:page*num_rows + num_rows]
    for row_index, row in enumerate(display_rows):
        tile_y = padding + row_index*(tile_wh+cost_label_h + border_width*2 + padding*2)
        for column_index, tile_char in enumerate(row):
            tile_x = x_offset + column_index*(tile_wh + border_width*2 + padding)
            if current_selected_tile == tile_char:
                border_color = info_window.theme.dark
                border = render.SolidColor(tile_x-border_width, tile_y-border_width, tile_wh + border_width*2, tile_wh + border_width*2, border_color)
                border.border_radius = 2
                border.bind_to(info_window, True)
            tile = render.TileDisplay(tile_x, tile_y, tile_char)
            tile.absolute = True
            tile.scale = tile_scale
            tile.tooltip = tile_labels[tile_char]
            tile.bind_to(info_window, True)
            tile_button = render.TextButton(0, 0, tile_wh, tile_wh, "", get_tile_button_func(tile_char))
            tile_button.absolute = True
            tile_button.draw_sprite = False
            tile_button.bind_to(tile)
            cost_label = render.make_grist_cost_display(0, tile_wh+padding, cost_label_h, 
                                                        {"build": server_tiles[tile_char]}, grist_cache, tile,
                                                        info_window.theme.dark, scale_mult=1)
    def get_leftbutton_func(page_num):
        def leftbutton_func():
            display_revise(info_window, info_text, page_num-1)
        return leftbutton_func
    def get_rightbutton_func(page_num):
        def rightbutton_func():
            display_revise(info_window, info_text, page_num+1)
        return rightbutton_func
    page_button_w = info_window.w//2-padding*2
    page_button_h = 20
    page_button_y = info_window.h-page_button_h-padding
    if page != 0:
        left_button = render.TextButton(padding, page_button_y, page_button_w, page_button_h, "<-", get_leftbutton_func(page))
        left_button.absolute = True
        left_button.bind_to(info_window, temporary=True)
    if rows[(page+1)*num_rows:(page+1)*num_rows + num_rows] != []:
        right_button = render.TextButton(padding*2+page_button_w, page_button_y, page_button_w, page_button_h, "->", get_rightbutton_func(page))
        right_button.absolute = True
        right_button.bind_to(info_window, temporary=True)

def display_atheneum(info_window: "render.SolidColor", info_text: "render.Text", page=0, search:Optional[str]=None):
    info_window.kill_temporary_elements()
    info_window.color = info_window.theme.light
    info_text.text = "Atheneum"
    update_viewport_dic()
    def filter_func(instance: "sylladex.Instance", search_text):
        assert search_text is not None
        if search_text in instance.name or search_text in instance.display_name() or search_text in instance.item.display_name:
            return True
        else:
            return False
    def make_results(search_text: Optional[str]):
        def get_button_func(instance_name: str):
            def button_func():
                global current_selected_atheneum
                global current_selected_phernalia
                current_selected_atheneum = instance_name
                current_selected_phernalia = None
                display_atheneum(info_window, info_text, page, search)
            return button_func
        def get_recycle_button_func(instance_name: str) -> Callable:
            def recycle_button_func():
                client.requestplus(intent="computer", content={"command": "recycle", "instance_name": instance_name})
                display_atheneum(info_window, info_text, page, search)
            return recycle_button_func
        results_sprites = []
        atheneum_dict: dict[str, dict] = viewport_dic["atheneum"]
        atheneum_instances = [sylladex.Instance(instance_name, atheneum_dict[instance_name]) for instance_name in atheneum_dict]
        if search_text is not None:
            atheneum_instances = [instance for instance in atheneum_instances if filter_func(instance, search_text)]
        padding = 4
        num_columns = 3
        usable_area_w = info_window.w
        usable_area_h = info_window.h - 25
        box_w = usable_area_w//num_columns - padding*2
        box_h = box_w
        num_rows = usable_area_h // (box_h + padding*2)
        rows = []
        for item in atheneum_instances:
            for row in rows:
                if len(row) != num_columns:
                    row.append(item)
                    break
            else:
                rows.append([item])
        display_rows = rows[page*num_rows:page*num_rows + num_rows]
        for row_index, row in enumerate(display_rows):
            box_y = padding + row_index*(box_h + padding*2)
            for column_index, instance in enumerate(row):
                box_x = padding + column_index*(box_w + padding*2)
                if current_selected_atheneum == instance.name: selected = True
                else: selected = False
                item_box = make_item_box(instance.item, box_x, box_y, box_w, box_h, info_window.theme, get_button_func(instance.name), selected=selected, label=True)
                item_box.bind_to(info_window, True)
                results_sprites.append(item_box)
                recycle_button = render.Button(box_w-16-padding, box_h-16-padding, "sprites/buttons/trash.png", None, get_recycle_button_func(instance.name))
                recycle_button.bind_to(item_box)
                recycle_button.absolute = True
                tooltip = render.ToolTip(0, 0, 16, 16)
                tooltip.tooltip_offsetx = -20
                tooltip.bind_to(recycle_button)
                value_display = render.make_grist_cost_display(padding, padding, 20, instance.item.true_cost, binding=tooltip, flipped=True)
                value_display.bind_to(tooltip)
                value_display.bring_to_top()
                results_sprites.append(recycle_button)
        def get_leftbutton_func(page_num):
            def leftbutton_func():
                choose_alchemy_item(info_window, info_text, page_num-1, search=search)
            return leftbutton_func
        def get_rightbutton_func(page_num):
            def rightbutton_func():
                choose_alchemy_item(info_window, info_text, page_num+1, search=search)
            return rightbutton_func
        page_button_w = info_window.w//2-padding*2
        page_button_h = 20
        page_button_y = info_window.h-page_button_h-padding
        if page != 0:
            left_button = render.TextButton(padding, page_button_y, page_button_w, page_button_h, "<-", get_leftbutton_func(page))
            left_button.absolute = True
            left_button.bind_to(info_window, temporary=True)
            results_sprites.append(left_button)
        if rows[(page+1)*num_rows:(page+1)*num_rows + num_rows] != []:
            right_button = render.TextButton(padding*2+page_button_w, page_button_y, page_button_w, page_button_h, "->", get_rightbutton_func(page))
            right_button.absolute = True
            right_button.bind_to(info_window, temporary=True)
            results_sprites.append(right_button)
        return results_sprites

    search_bar = render.InputTextBox(0.5, 0.8, 256, 32)
    search_init_time = render.clock.get_time()
    global results_sprites
    results_sprites = make_results(search)
    def key_press_func():
        if render.clock.get_time() == search_init_time: return
        global results_sprites
        for sprite in results_sprites: 
            sprite.delete()
        results_sprites = []
        results_sprites = make_results(search_bar.text)
    if search is not None: 
        search_bar.text = search
        search_bar.active = True
    search_bar.bind_to(info_window, True)
    search_bar.key_press_func = key_press_func
    if last_tile_map is not None:
        last_tile_map.input_text_box = search_bar

def display_alchemy(info_window: "render.SolidColor", info_text: "render.Text", operation: Optional[str]="&&"):
    target_item = current_alchemy_item_3
    info_window.kill_temporary_elements()
    info_window.color = info_window.theme.light
    info_text.text = "Alchemy"
    update_viewport_dic()
    reply = client.requestplusdic(intent="computer", content={"command": "get_alchemiter_location"})
    alchemiter_location = reply["alchemiter_location"]
    if alchemiter_location is None:
        text_box = render.Text(0.5, 0.5, "You must deploy an alchemiter before doing alchemy!")
        text_box.set_fontsize_by_width(info_window.w)
        text_box.color = info_window.theme.dark
        text_box.bind_to(info_window, True)
        return
    box_w, box_h = 100, 100
    if target_item is None:
        item_1: Optional[sylladex.Item] = current_alchemy_item_1
        item_2: Optional[sylladex.Item]  = current_alchemy_item_2
    else:
        item_1, item_2 = None, None
    def box_1_func():
        choose_alchemy_item(info_window, info_text, 1)
    item_1_box = make_item_box(item_1, 0.25, 0.15, box_w, box_h, info_window.theme, box_1_func)
    item_1_box.absolute = False
    item_1_box.outline_color = info_window.theme.dark
    item_1_box.bind_to(info_window, True)
    if target_item is not None: item_1_label_text = "(...)"
    elif item_1 is None: item_1_label_text = "(choose item 1)"
    else: item_1_label_text = item_1.display_name
    item_1_label = render.Text(0.7, 0.15, item_1_label_text)
    item_1_label.color = info_window.theme.dark
    item_1_label.set_fontsize_by_width(200)
    item_1_label.bind_to(info_window, True)
    if operation is not None:
        operation_box = render.TextButton(0.25, 0.35, 50, 50, operation, placeholder)
        operation_box.bind_to(info_window, True)
        def operation_box_button():
            if operation == "&&":
                display_alchemy(info_window, info_text, operation="||")
            else:
                display_alchemy(info_window, info_text, operation="&&")
        operation_box.onpress = operation_box_button
    def box_2_func():
        choose_alchemy_item(info_window, info_text, 2)
    item_2_box = make_item_box(item_2, 0.25, 0.55, box_w, box_h, info_window.theme, box_2_func)
    item_2_box.absolute = False
    item_2_box.outline_color = info_window.theme.dark
    item_2_box.bind_to(info_window, True)
    if target_item is not None: item_2_label_text = "(...)"
    elif item_2 is None: item_2_label_text = "(choose item 2)"
    else: item_2_label_text = item_2.display_name
    item_2_label = render.Text(0.7, 0.55, item_2_label_text)
    item_2_label.color = info_window.theme.dark
    item_2_label.set_fontsize_by_width(200)
    item_2_label.bind_to(info_window, True)
    equals_line = render.SolidColor(0.5, 0.7, info_window.w-50, 3, info_window.theme.dark)
    equals_line.absolute = False
    equals_line.bind_to(info_window, True)
    if item_1 is not None and item_2 is not None:
        resulting_item_dict = client.requestplusdic(intent="get_resulting_alchemy", content={"code_1": item_1.code, "code_2": item_2.code, "operation": operation})
        resulting_item_name = resulting_item_dict["name"]
        resulting_item = sylladex.Item(resulting_item_name, resulting_item_dict)
    elif target_item is not None: resulting_item = target_item
    else: resulting_item = None
    def box_3_func(): choose_alchemy_item(info_window, info_text, item_num=3)
    item_3_box = make_item_box(resulting_item, 0.25, 0.85, box_w, box_h, info_window.theme, dowel=True, button_func=box_3_func)
    item_3_box.absolute = False
    item_3_box.outline_color = info_window.theme.dark
    item_3_box.bind_to(info_window, True)
    if resulting_item is not None:
        grist_cache = viewport_dic["client_grist_cache"]
        for grist_type, value in resulting_item.true_cost.items():
            if grist_type not in grist_cache:
                can_make = False
                break
            if grist_cache[grist_type] < value:
                can_make = False
                break
        else:
            can_make = True
        if can_make:
            def button_func():
                reply = client.requestplus(intent="computer", content={"command": "server_alchemy", "code": resulting_item.code})
                global current_x
                global current_y
                current_x, current_y = alchemiter_location
                if last_tile_map is not None:
                    last_tile_map.update_map(update_info_window=True)
                update_viewport_dic()
            alchemize_button = render.TextButton(0.7, 0.95, 196, 32, ">ALCHEMIZE", button_func, theme=info_window.theme)
            alchemize_button.text_color = info_window.theme.dark
            alchemize_button.bind_to(info_window, True) 
        item_3_label = render.Text(0.7, 0.85, resulting_item.display_name)
        item_3_label.color = info_window.theme.dark
        item_3_label.set_fontsize_by_width(200)
        item_3_label.bind_to(info_window, True)
        power_label = render.Text(0.5, 1.3, f"POWER: {resulting_item.power}")
        power_label.bind_to(item_3_label)
        power_label.color = info_window.theme.dark
        power_label.set_fontsize_by_width(75)
        tooltip = render.ToolTip(0, 0, box_w, box_h)
        tooltip.bind_to(item_3_box)
        tooltip.tooltip_offsety = -25
        cost_label = render.make_grist_cost_display(0, 0, 20, resulting_item.true_cost, 
                                                    grist_cache, tooltip, text_color=info_window.theme.dark,
                                                    flipped=True)

def choose_alchemy_item(info_window: "render.SolidColor", info_text: "render.Text", item_num: int, page=0, search: Optional[str]=None):
    info_window.kill_temporary_elements()
    info_window.color = info_window.theme.light
    info_text.text = "Alchemy Excursus"
    update_viewport_dic()
    def filter_func(item: "sylladex.Item", search_text):
        assert search_text is not None
        if search_text in item.name or search_text in item.display_name:
            return True
        else:
            return False
    def make_results(search_text: Optional[str]):
        def get_button_func(item: "sylladex.Item"):
            def button_func():
                global current_alchemy_item_3
                if item_num == 1:
                    global current_alchemy_item_1
                    current_alchemy_item_1 = item
                    current_alchemy_item_3 = None
                elif item_num == 2:
                    global current_alchemy_item_2
                    current_alchemy_item_2 = item
                    current_alchemy_item_3 = None
                else:
                    current_alchemy_item_3 = item
                display_alchemy(info_window, info_text)
            return button_func
        results_sprites = []
        excursus: dict[str, dict] = viewport_dic["excursus"]
        all_excursus_items = [sylladex.Item(item_name, excursus[item_name]) for item_name in excursus]
        excursus_items = [item for item in all_excursus_items if not item.forbiddencode]
        if search_text is not None:
            excursus_items = [item for item in excursus_items if filter_func(item, search_text)]
        padding=4
        num_columns = 3
        usable_area_w = info_window.w
        usable_area_h = info_window.h - 25
        box_w = usable_area_w//num_columns - padding*2
        box_h = box_w
        num_rows = usable_area_h // (box_h + padding*2)
        rows = []
        for item in excursus_items:
            for row in rows:
                if len(row) != num_columns:
                    row.append(item)
                    break
            else:
                rows.append([item])
        display_rows = rows[page*num_rows:page*num_rows + num_rows]
        for row_index, row in enumerate(display_rows):
            box_y = padding + row_index*(box_h + padding*2)
            for column_index, item in enumerate(row):
                box_x = padding + column_index*(box_w + padding*2)
                item_box = make_item_box(item, box_x, box_y, box_w, box_h, info_window.theme, get_button_func(item), selected=True, label=True, dowel=True)
                item_box.bind_to(info_window, True)
                results_sprites.append(item_box)
        def get_leftbutton_func(page_num):
            def leftbutton_func():
                choose_alchemy_item(info_window, info_text, item_num, page_num-1, search=search)
            return leftbutton_func
        def get_rightbutton_func(page_num):
            def rightbutton_func():
                choose_alchemy_item(info_window, info_text, item_num, page_num+1, search=search)
            return rightbutton_func
        page_button_w = info_window.w//2-padding*2
        page_button_h = 20
        page_button_y = info_window.h-page_button_h-padding
        if page != 0:
            left_button = render.TextButton(padding, page_button_y, page_button_w, page_button_h, "<-", get_leftbutton_func(page))
            left_button.absolute = True
            left_button.bind_to(info_window, temporary=True)
            results_sprites.append(left_button)
        if rows[(page+1)*num_rows:(page+1)*num_rows + num_rows] != []:
            right_button = render.TextButton(padding*2+page_button_w, page_button_y, page_button_w, page_button_h, "->", get_rightbutton_func(page))
            right_button.absolute = True
            right_button.bind_to(info_window, temporary=True)
            results_sprites.append(right_button)
        return results_sprites

    search_bar = render.InputTextBox(0.5, 0.8, 256, 32)
    search_init_time = render.clock.get_time()
    def back():
        display_alchemy(info_window, info_text)
    backbutton = render.TextButton(0.5, 0.9, 128, 32, "BACK", back, theme=info_window.theme)
    backbutton.bind_to(info_window, True)
    global results_sprites
    results_sprites = make_results(search)
    def key_press_func():
        if render.clock.get_time() == search_init_time: return
        global results_sprites
        for sprite in results_sprites: 
            sprite.delete()
        results_sprites = []
        results_sprites = make_results(search_bar.text)
    if search is not None: 
        search_bar.text = search
        search_bar.active = True
    search_bar.bind_to(info_window, True)
    search_bar.key_press_func = key_press_func
    if last_tile_map is not None:
        last_tile_map.input_text_box = search_bar

def update_info_window(info_window, info_text):
    match current_info_window:
        case "grist_cache": display_grist_cache(info_window, info_text)
        case "phernalia_registry": display_phernalia_registry(info_window, info_text)
        case "revise": display_revise(info_window, info_text)
        case "atheneum": display_atheneum(info_window, info_text)
        case "alchemize": display_alchemy(info_window, info_text)
        case _: ...

def sburb(window: "render.Window"):
    window.theme = themes.default
    window.viewport.color = window.theme.light
    window.color = window.theme.dark
    window.xbutton.fill_color = window.theme.dark
    window.xbutton.outline_color = window.theme.dark
    if not connect(window): return
    global current_x
    global current_y
    if current_x is None or current_y is None:
        coords = client.requestplusdic(intent="computer", content={"command": "starting_sburb_coords"})
        current_x = coords["x"]
        current_y = coords["y"]
    update_viewport_dic()
    global last_tile_map
    last_tile_map = render.TileMap(0.5, 0.55, item_display_x=40, item_display_y=250, server_view=True)
    last_tile_map.bind_to(window.viewport)
    info_window, info_text = draw_info_window(window)
    last_tile_map.info_window, last_tile_map.info_text = info_window, info_text
    update_info_window(info_window, info_text)
    draw_sburb_bar(window, info_window, info_text, last_tile_map)

def connect(window: "render.Window"):
    username = client.requestdic(intent="player_info")["client_player_name"]
    if username is not None: 
        global client_username
        client_username = username
        return True
    dic = client.requestdic(intent="get_client_server_chains")
    chains: list = dic["chains"]
    no_server: list = dic["no_server"]
    player_names: dict = dic["player_names"]
    server_client: dict = dic["server_client"]
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
    return False
