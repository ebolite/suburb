from typing import Optional, Tuple, Callable
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
viewport_dic = {}

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
    gristcachebutton = render.Button(55, 0, "sprites/computer/Sburb/grist_cache_button.png", None, get_mode_change_button(None, "grist_cache"))
    gristcachebutton.absolute = True
    gristcachebutton.overlay_on_click = True
    atheneumbutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.light)
    atheneumbutton_background.border_radius = 2
    atheneumbutton = render.Button(55, 0, "sprites/computer/Sburb/atheneum_button.png", None, get_mode_change_button("deploy", "atheneum"))
    atheneumbutton.absolute = True
    atheneumbutton.overlay_on_click = True
    alchemizebutton_background = render.SolidColor(-2, -2, 49, 49, window.theme.light)
    alchemizebutton_background.border_radius = 2
    alchemizebutton = render.Button(55, 0, "sprites/computer/Sburb/alchemize_button.png", None, get_mode_change_button(None, "alchemize"))
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
            item = sylladex.Item(item_name, available_phernalia[item_name])
            box_x = padding + column_index*(box_w + padding*2)
            if current_selected_phernalia == item_name: box_color = info_window.theme.dark
            else: box_color = info_window.theme.white
            cost_label_h = box_h//5
            item_box_h = box_h-cost_label_h
            item_box = render.SolidColor(box_x, box_y, box_w, item_box_h, box_color)
            item_box.border_radius = 3
            item_box.bind_to(info_window, True)
            cost_label_box = render.SolidColor(0, item_box_h, box_w, cost_label_h, info_window.theme.white)
            cost_label_box.border_radius = 3
            cost_label_box.bind_to(item_box)
            cost_label = render.make_grist_cost_display(0, 0, cost_label_h, item.true_cost, grist_cache, cost_label_box, info_window.theme.dark)
            if current_selected_phernalia != item_name:
                box_button = render.TextButton(0, 0, box_w, item_box_h, "", get_box_button_func(item_name))
                box_button.draw_sprite = False
                box_button.absolute = True
                box_button.click_on_mouse_down = True
                box_button.bind_to(item_box)
            image_path = f"sprites/items/{item_name}.png"
            if os.path.isfile(image_path):
                card_image = render.ItemImage(0.5, 0.5, item_name)
                if card_image is not None:
                    card_image.convert = False
                    card_image.bind_to(item_box)
                    card_image.scale = item_box_h / 240
            else:
                card_image = None

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
            print(tile_char)
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

def display_atheneum(info_window: "render.SolidColor", info_text: "render.Text", page=0):
    info_window.kill_temporary_elements()
    info_window.color = info_window.theme.light
    info_text.text = "Atheneum"
    update_viewport_dic()
    atheneum_dict: dict[str, dict] = viewport_dic["atheneum"]
    padding=4
    num_columns = 3
    usable_area_w = info_window.w
    usable_area_h = info_window.h - 25
    box_w = usable_area_w//num_columns - padding*2
    box_h = box_w
    num_rows = usable_area_h // (box_h + padding*2)
    rows = []
    for instance_name in atheneum_dict:
        for row in rows:
            if len(row) != num_columns:
                row.append(instance_name)
                break
        else:
            rows.append([instance_name])
    display_rows = rows[page*num_rows:page*num_rows + num_rows]
    def get_box_button_func(instance_name: str) -> Callable:
        def button_func():
            global current_selected_atheneum
            global current_selected_phernalia
            current_selected_atheneum = instance_name
            current_selected_phernalia = None
            display_atheneum(info_window, info_text, page)
        return button_func
    def get_recycle_button_func(instance_name: str) -> Callable:
        def recycle_button_func():
            client.requestplus(intent="computer", content={"command": "recycle", "instance_name": instance_name})
            display_atheneum(info_window, info_text, page)
        return recycle_button_func
    for row_index, row in enumerate(display_rows):
        box_y = padding + row_index*(box_h + padding*2)
        for column_index, instance_name in enumerate(row):
            item = sylladex.Item(atheneum_dict[instance_name]["name"], atheneum_dict[instance_name])
            item_name = item.name
            box_x = padding + column_index*(box_w + padding*2)
            box_color = info_window.theme.white
            item_box = render.SolidColor(box_x, box_y, box_w, box_h, box_color)
            if current_selected_atheneum == instance_name: item_box.outline_color = info_window.theme.dark
            item_box.border_radius = 3
            item_box.bind_to(info_window, True)
            if current_selected_atheneum != instance_name:
                box_button = render.TextButton(0, 0, box_w, box_h, "", get_box_button_func(instance_name))
                box_button.draw_sprite = False
                box_button.absolute = True
                box_button.click_on_mouse_down = True
                box_button.bind_to(item_box)
            image_path = f"sprites/items/{item_name}.png"
            if os.path.isfile(image_path):
                card_image = render.ItemImage(0.5, 0.5, item_name)
                if card_image is not None:
                    card_image.convert = False
                    card_image.bind_to(item_box)
                    card_image.scale = box_h / 240
            else:
                card_image = None
            item_label = render.Text(0.5, 0.9, util.shorten_item_name(item_name))
            item_label.bind_to(item_box)
            item_label.fontsize = 20
            item_label.set_fontsize_by_width(box_w)
            recycle_button = render.Button(box_w-16-padding, padding, "sprites/buttons/trash.png", None, get_recycle_button_func(instance_name))
            recycle_button.bind_to(item_box)
            recycle_button.absolute = True
            tooltip = render.ToolTip(0, 0, 16, 16)
            tooltip.tooltip_offsetx = -20
            tooltip.bind_to(recycle_button)
            value_display = render.make_grist_cost_display(padding, padding, 20, item.true_cost, binding=tooltip, flipped=True)
            value_display.bind_to(tooltip)
            value_display.bring_to_top()
    def get_leftbutton_func(page_num):
        def leftbutton_func():
            display_atheneum(info_window, info_text, page_num-1)
        return leftbutton_func
    def get_rightbutton_func(page_num):
        def rightbutton_func():
            display_atheneum(info_window, info_text, page_num+1)
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



def update_info_window(info_window, info_text):
    match current_info_window:
        case "grist_cache": display_grist_cache(info_window, info_text)
        case "phernalia_registry": display_phernalia_registry(info_window, info_text)
        case "revise": display_revise(info_window, info_text)
        case "atheneum": display_atheneum(info_window, info_text)
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
    tilemap = render.TileMap(0.5, 0.55, item_display_x=40, item_display_y=250, server_view=True)
    tilemap.bind_to(window.viewport)
    info_window, info_text = draw_info_window(window)
    tilemap.info_window, tilemap.info_text = info_window, info_text
    update_info_window(info_window, info_text)
    draw_sburb_bar(window, info_window, info_text, tilemap)

def connect(window: "render.Window"):
    username = client.requestdic(intent="player_info")["client_player_name"]
    if username is not None: 
        global client_username
        client_username = username
        sburb(window)
        return True
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
    return False
