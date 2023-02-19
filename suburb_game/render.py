import pygame
import sys
import os
import pathlib
import hashlib
import numpy as np
from typing import Optional, Union, Callable

import util
import config
import client
import suburb
import themes
import binaryoperations
from sylladex import Instance, Sylladex

pygame.init()

clock = pygame.time.Clock()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS_CAP = 60

RUNNING = True

os.chdir(util.homedir)

screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])

base_font = pygame.font.Font(pathlib.Path("./fonts/courbd.ttf"), 32)

click_check = []
key_check = []
mouseup_check = []
update_check = []
keypress_update_check = []
scroll_check = []
move_to_top = []

ui_elements = []

tile_wh = 32

checks = [click_check, key_check, mouseup_check, update_check, keypress_update_check, scroll_check]

icon_surf = pygame.image.load("sprites\\icon.png").convert()
pygame.display.set_icon(icon_surf)
pygame.display.set_caption(f"SUBURB CLIENT {util.VERSION}")

def clear_elements():
    for element in ui_elements.copy():
        element.delete()

def palette_swap(surf: Union[pygame.Surface, pygame.surface.Surface], old_color: pygame.Color, new_color: pygame.Color):
    new_surf = pygame.Surface(surf.get_size())
    new_surf.fill(new_color)
    surf.set_colorkey(old_color)
    new_surf.blit(surf, (0, 0))
    return new_surf

class UIElement(pygame.sprite.Sprite):
    def __init__(self): # x and y as fractions of 1 (centered position on screen)
        super(UIElement, self).__init__()
        self.rect: Union[pygame.Rect, pygame.rect.Rect] = pygame.Rect(0, 0, 0, 0)
        self.relative_binding: Optional[UIElement] = None
        self.absolute = False
        self.x = 0
        self.y = 0
        self.theme: themes.Theme = suburb.current_theme()
        self.bound_elements = []
        ui_elements.append(self)

    def mouseover(self): # returns True if mouse is over this element
        mousepos = pygame.mouse.get_pos()
        return True if self.rect.collidepoint(mousepos[0], mousepos[1]) else False

    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)
    
    def is_mouseover(self):
        return self.collidepoint(pygame.mouse.get_pos())

    def bind_to(self, element: "UIElement"):
        self.relative_binding = element
        element.bound_elements.append(self)

    def delete(self):
        if self in ui_elements:
            ui_elements.remove(self)
        for list in checks:
            if self in list:
                list.remove(self)
        self.kill()

    def convert_to_theme(self, surf: Union[pygame.Surface, pygame.surface.Surface]) -> pygame.Surface:
        default_theme = themes.default
        surf = palette_swap(surf, default_theme.white, self.theme.white)
        surf = palette_swap(surf, default_theme.light, self.theme.light)
        surf = palette_swap(surf, default_theme.dark, self.theme.dark)
        surf = palette_swap(surf, default_theme.black, self.theme.black)
        return surf

    def get_rect_xy(self, secondary_surf:Union[pygame.Surface, pygame.surface.Surface, None] = None) -> tuple[int, int]:
        rect_x: int = 0
        rect_y: int = 0
        if secondary_surf is not None:
            secondary_surf_width = secondary_surf.get_width()
            secondary_surf_height = secondary_surf.get_height()
        else:
            secondary_surf_width = 0
            secondary_surf_height = 0
        if self.absolute:
            rect_x = self.x
            rect_y = self.y
            if self.relative_binding is not None:
                rect_x += self.relative_binding.rect.x
                rect_y += self.relative_binding.rect.y
        else:
            if self.relative_binding is None:
                rect_x = int((SCREEN_WIDTH * self.x) - secondary_surf_width/2)
                rect_y = int((SCREEN_HEIGHT * self.y) - secondary_surf_height/2)
            else:
                rect_x = int(self.relative_binding.rect.x - secondary_surf_width/2) + self.x*self.relative_binding.rect.w
                rect_y = int(self.relative_binding.rect.y - secondary_surf_height/2) + self.y*self.relative_binding.rect.h
        return rect_x, rect_y

class SolidColor(UIElement):
    def __init__(self, x, y, w, h, color: pygame.Color):
        super(SolidColor, self).__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color: pygame.Color = color
        self.outline_color: Optional[pygame.Color] = None
        self.outline_width = 2
        self.absolute = True
        update_check.append(self)

    def update(self):
        self.surf = pygame.Surface((self.w, self.h))
        self.surf.fill(self.color)
        if self.outline_color is not None:
            self.outline_surf = pygame.Surface((self.w + self.outline_width*2, self.h + self.outline_width*2))
            self.outline_surf.fill(self.outline_color)
        self.rect = self.surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy()
        if self.outline_color is not None: screen.blit(self.outline_surf, ((self.rect.x-self.outline_width, self.rect.y-self.outline_width)))
        screen.blit(self.surf, ((self.rect.x, self.rect.y)))

class Div(SolidColor):
    def __init__(self, x, y, w, h):
        super(SolidColor, self).__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.absolute = False
        update_check.append(self)

    def update(self):
        self.surf = pygame.Surface((self.w, self.h))
        self.rect = self.surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy()

class TextButton(UIElement):
    def __init__(self, x, y, w, h, text, onpress: Callable, hover=True, truncate_text=False):
        super(TextButton, self).__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.onpress = onpress
        self.active = False
        self.hover = hover
        self.truncate_text = truncate_text
        self.truncated = False
        self.outline_width = 2
        self.absolute = False
        self.fontsize = 16
        self.text = text
        self.text_color: pygame.Color = self.theme.black
        self.outline_color: pygame.Color = self.theme.dark
        self.fill_color: pygame.Color = self.theme.white
        self.hover_color: pygame.Color = self.theme.dark
        self.toggle = False
        click_check.append(self)
        update_check.append(self)
        mouseup_check.append(self)

    def update(self):
        if self.truncated == True:
            self.text_surf = self.font.render(self.text+"...", True, self.text_color)
        else:
            self.text_surf = self.font.render(self.text, True, self.text_color)
        while self.truncate_text and self.text_surf.get_width() > self.w:
            self.truncated = True
            self.text = self.text[:-1]
            if self.text[-1] == " ": self.text = self.text[:-1]
            self.text_surf = self.font.render(self.text+"...", True, self.text_color)
        self.outline_surf = pygame.Surface((self.w, self.h))
        self.outline_surf.fill(self.outline_color)
        self.surf = pygame.Surface((self.w-2*self.outline_width, self.h-2*self.outline_width))
        self.surf.fill(self.fill_color)
        if self.active:
            self.hoversurf = pygame.Surface((self.w, self.h))
            self.hoversurf.fill(self.hover_color)
            self.hoversurf.set_alpha(89)
        else:
            self.hoversurf = None
        self.rect = self.outline_surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy(self.outline_surf)
        screen.blit(self.outline_surf, ((self.rect.x, self.rect.y)))
        screen.blit(self.surf, ((self.rect.x+self.outline_width, self.rect.y+self.outline_width)))
        screen.blit(self.text_surf, ((self.rect.x+(self.outline_surf.get_width()/2)-(self.text_surf.get_width()/2), self.rect.y+(self.outline_surf.get_height()/2)-(self.text_surf.get_height()/2))))
        if self.hoversurf != None:
            screen.blit(self.hoversurf, ((self.rect.x, self.rect.y)))

    def onclick(self, isclicked):
        if self not in click_check: return
        if isclicked:
            if not self.toggle:
                self.active = True


    def mouseup(self, isclicked):
        if not self.toggle:
            self.active = False
        if isclicked:
            if self.toggle:
                if self.active:
                    self.active = False
                else:
                    self.active = True
            self.onpress()

    @property
    def font(self):
        return pygame.font.Font(pathlib.Path("./fonts/courbd.ttf"), self.fontsize)


class Button(UIElement):
    def __init__(self, x, y, unpressed_img_path:str, pressed_img_path:str, onpress:Callable, alt:Optional[Callable]=None, alt_img_path=None, altclick:Optional[Callable]=None, hover=None, theme:themes.Theme=suburb.current_theme()): # x and y as fractions of 1 (centered position on screen)
        super(Button, self).__init__()
        self.unpressed_img_path = unpressed_img_path
        self.pressed_img_path = pressed_img_path
        self.x = x
        self.y = y
        self.onpress = onpress
        self.active = False
        self.alpha = 255
        self.alt = alt
        self.alt_img_path = alt_img_path
        self.altclick = altclick
        self.alt_alpha = 255
        self.absolute = False
        self.convert = True
        self.hover = hover
        self.theme = theme
        self.scale: float = 1.0
        click_check.append(self)
        update_check.append(self)
        mouseup_check.append(self)

    def update(self):
        if self.alt is not None and self.alt() and self.alt_img_path is not None: # alternative display condition
            self.surf = pygame.image.load(self.alt_img_path)
            self.surf.set_alpha(self.alt_alpha)
        else:
            if self.active:
                self.surf = pygame.image.load(self.pressed_img_path)
            else:
                if self.hover != None and self.collidepoint(pygame.mouse.get_pos()):
                    self.surf = pygame.image.load(self.hover)
                else:
                    self.surf = pygame.image.load(self.unpressed_img_path)
        if self.convert: 
            self.surf = self.surf.convert()
            self.surf = self.convert_to_theme(self.surf)
            self.surf.set_colorkey(pygame.Color(0, 0, 0))
        if self.alpha != 255: self.surf.set_alpha(self.alpha)
        if self.scale != 1:
            w = self.surf.get_width()
            h = self.surf.get_height()
            self.surf = pygame.transform.scale(self.surf, (int(w*self.scale), int(h*self.scale)))
            self.scaled = True
        self.rect = self.surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy(self.surf)
        screen.blit(self.surf, ((self.rect.x, self.rect.y)))

    def onclick(self, isclicked):
        if self not in click_check: return
        if isclicked:
            self.active = True

    def mouseup(self, isclicked):
        self.active = False
        if isclicked:
            print("clicked")
            if self.alt != None and self.alt():
                if self.altclick != None:
                    self.altclick()
            else:
                self.onpress()

class InputTextBox(UIElement):
    def __init__(self, x, y, w=None, h=None):
        super(InputTextBox, self).__init__()
        self.text = ""
        self.active = False
        self.waitframes = 0
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text_color = self.theme.black
        self.inactive_color = self.theme.white
        self.active_color = self.theme.light
        self.outline_color: Optional[pygame.Color] = self.theme.dark
        self.fontsize = 32
        self.suffix = ""
        self.secure = False
        self.button: Union[Button, TextButton, None] = None
        self.enter_func: Optional[Callable] = None
        click_check.append(self)
        key_check.append(self)
        keypress_update_check.append(self)

    def update(self, keys):
        if self.secure:
            t = self.suffix + ("*" * len(self.text))
            self.text_surf = self.font.render(t, True, self.text_color)
        else:
            self.text_surf = self.font.render(self.suffix+self.text, True, self.text_color)
        width = self.w or max(100, self.text_surf.get_width()+10)
        height = self.h or 32
        outline = 3
        self.surf = pygame.Surface((width, height))
        if self.active:
            self.surf.fill(self.active_color)
        else:
            self.surf.fill(self.inactive_color)

        if self.outline_color is not None:
            self.outline_surf = pygame.Surface((width + (outline * 2), height + (outline  * 2)))
            self.outline_surf.fill(self.outline_color)
            rect_surf = self.outline_surf
        else:
            rect_surf = self.surf

        self.rect = rect_surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy(rect_surf)

        if self.outline_color is not None:
            screen.blit(self.outline_surf, (self.rect.x, self.rect.y))

        surfx, surfy = self.get_rect_xy(self.surf)
        screen.blit(self.surf, (surfx, surfy))

        textx, texty = self.get_rect_xy(self.text_surf)
        screen.blit(self.text_surf, (textx, texty))

        if self.active and keys[pygame.K_BACKSPACE]:
            if self.waitframes > 15:
                if self.waitframes % 3 == 0:
                    self.text = self.text[:-1]
            self.waitframes += 1
        else:
            self.waitframes = 0

    def onclick(self, isclicked):
        if isclicked:
            self.active = True
        else:
            self.active = False

    def keypress(self, event):
        if self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN and self.enter_func != None:
                self.enter_func(self)
            # if enter is pressed and this text box has a button assigned to it, press that button
            elif event.key == pygame.K_RETURN and self.button != None:
                self.button.mouseup(True)
            else:
                if event.unicode.isascii() and event.unicode not in  ["\n", "\t", "\r"]: #no newline, tab or carriage return
                    self.text += event.unicode

    @property
    def font(self):
        return pygame.font.Font(pathlib.Path("./fonts/courbd.ttf"), int(self.fontsize))

class Image(UIElement):
    def __init__(self, x, y, path, theme=suburb.current_theme(), convert=True):
        super(Image, self).__init__()
        self.x = x
        self.y = y
        self.path = path
        self.theme = theme
        self.convert = convert
        self.absolute = False
        self.animated = False
        self.hover_to_top = False
        self.animframe = 1
        self.animframes = 1
        self.speed = 3
        self.wait = 0
        self.alpha = 255
        self.scale: float = 1
        self.scaled = False
        self.highlight_color: Optional[pygame.Color] = None
        update_check.append(self)

    def update(self):
        if self.animated:
            self.surf = pygame.image.load(self.path+f"-{self.animframe}.png").convert()
            if self.wait == self.speed:
                self.animframe += 1
                if self.animframe > self.animframes:
                    self.animframe = 1
                self.wait = 0
            else:
                self.wait += 1
        else:
            try: self.surf
            except AttributeError: 
                self.surf = pygame.image.load(self.path)
                if self.convert:
                    self.surf = self.surf.convert()
                    self.surf = self.convert_to_theme(self.surf)
                    self.surf.set_colorkey(pygame.Color(0, 0, 0))
        if self.alpha != 255: self.surf.set_alpha(self.alpha)
        if self.scale != 1 and not self.scaled: 
            w = self.surf.get_width()
            h = self.surf.get_height()
            self.surf = pygame.transform.scale(self.surf, (int(w*self.scale), int(h*self.scale)))
            self.scaled = True
        self.rect = self.surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy(self.surf)
        if self.highlight_color != None:
            self.highlight_surf = pygame.Surface((self.surf.get_width(), self.surf.get_height()))
            self.highlight_surf.fill(self.highlight_color)
            screen.blit(self.highlight_surf, (self.rect.x, self.rect.y))
        if self.hover_to_top and self.is_mouseover():
            for ui_element in update_check:
                if not ui_element.is_mouseover(): continue
                # we want to bring this to the top of drawing only if it's not behind anything
                if update_check.index(self) < update_check.index(ui_element): break
            else:
                # move to top (last in update_check list)
                move_to_top.append(self)
                # move our bound elements to the top
                for ui_element in self.bound_elements:
                    move_to_top.append(ui_element)
        screen.blit(self.surf, (self.rect.x, self.rect.y))

class Text(UIElement):
    def __init__(self, x, y, text: str):
        super(Text, self).__init__()
        self.x = x
        self.y = y
        self.text = text
        self.absolute = False  # whether x and y should be exact coords
        self.color: pygame.Color = self.theme.black
        self.outline_color: Optional[pygame.Color] = None
        self.outline_depth = 1
        self.highlight_color: Optional[pygame.Color] = None
        self.fontsize: int = 32
        self.scale: float = 1
        self.alpha = 255
        update_check.append(self)

    def set_fontsize_by_width(self, width):
        text_surf = self.font.render(self.text, True, self.color)
        while text_surf.get_width() > width:
            self.fontsize -= 1
            text_surf = self.font.render(self.text, True, self.color)

    def update(self):
        self.text_surf = self.font.render(self.text, True, self.color)
        self.rect = self.text_surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy(self.text_surf)
        if self.highlight_color is not None:
            self.highlight_surf = pygame.Surface((self.rect.w, self.rect.h))
            self.highlight_surf.fill(self.highlight_color)
            screen.blit(self.highlight_surf, (self.rect.x, self.rect.y))
        if self.outline_color != None:
            self.outline_surf = self.font.render(self.text, True, self.outline_color)
            if self.alpha != 255: self.outline_surf.set_alpha(self.alpha)
            # screen.blit(self.outline_surf, (self.rect.x + self.outline_depth, self.rect.y + self.outline_depth)) # +y +x
            # screen.blit(self.outline_surf, (self.rect.x - self.outline_depth, self.rect.y + self.outline_depth)) # +y -x
            # screen.blit(self.outline_surf, (self.rect.x - self.outline_depth, self.rect.y - self.outline_depth)) # -y -x
            # screen.blit(self.outline_surf, (self.rect.x + self.outline_depth, self.rect.y - self.outline_depth)) # -y +x
            screen.blit(self.outline_surf, (self.rect.x, self.rect.y + self.outline_depth))
            screen.blit(self.outline_surf, (self.rect.x, self.rect.y - self.outline_depth))
            screen.blit(self.outline_surf, (self.rect.x + self.outline_depth, self.rect.y))
            screen.blit(self.outline_surf, (self.rect.x - self.outline_depth, self.rect.y))
        if self.alpha != 255: self.text_surf.set_alpha(self.alpha)
        screen.blit(self.text_surf, (self.rect.x, self.rect.y))

    @property
    def font(self):
        return pygame.font.Font(pathlib.Path("./fonts/courbd.ttf"), int(self.fontsize*self.scale))

class TileMap(UIElement):
    def __init__(self, x, y, map: list[list[str]], specials: dict, room_name: str, item_display:"RoomItemDisplay"):
        super(TileMap, self).__init__()
        self.x = x
        self.y = y
        self.map = map
        self.specials = specials
        self.tiles = {}
        self.room_name = room_name
        self.item_display = item_display
        self.label = Text(0.5, 0, room_name)
        self.label.bind_to(self)
        self.input_text_box: Optional[InputTextBox] = None
        self.update_map(map)
        update_check.append(self)
        key_check.append(self)

    def update(self):
        for tile in self.tiles:
            self.tiles[tile].update()

    def update_map(self, map):
        if self.map != map or len(self.tiles) == 0:
            self.map = map
            self.rect = pygame.Rect(0, 0, len(map[0])*tile_wh, len(map)*tile_wh)
            self.rect.x = int((SCREEN_WIDTH * self.x) - (self.rect.w / 2))
            self.rect.y = int((SCREEN_HEIGHT * self.y) - (self.rect.h / 2))
            for tile in self.tiles:
                self.tiles[tile].delete()
            self.tiles = {}
            for y, line in enumerate(map):
                for x, char in enumerate(line):
                    self.tiles[f"{x}, {y}"] = Tile(x, y, self, self.specials)

    def keypress(self, event):
        if self.input_text_box is not None and self.input_text_box.active: return
        match event.key:
            case pygame.K_UP: direction = "up"
            case pygame.K_w: direction = "up"
            case pygame.K_DOWN: direction = "down"
            case pygame.K_s: direction = "down"
            case pygame.K_LEFT: direction = "left"
            case pygame.K_a: direction = "left"
            case pygame.K_RIGHT: direction = "right"
            case pygame.K_d: direction = "right"
            case _: return
        client.requestplus("move", direction)
        dic = client.requestdic("current_map")
        self.map = dic["map"]
        self.specials = dic["specials"]
        self.instances = dic["instances"]
        self.room_name = dic["room_name"]
        self.item_display.update_instances(self.instances)
        self.label.text = self.room_name

    def delete(self):
        for tile in self.tiles:
            self.tiles[tile].delete()
        super(TileMap, self).delete()

allowedtiles = {
"#": ["|", "=", "+"],
"|": ["#", "\\", "/", "^", "=", "+"],
"\\": ["#", "/", "X", "|", "=", "+"],
"/": ["#", "\\", "X", "|", "=", "+"],
"=": ["#", "\\", "/", "^", "|", "+"],
"+": ["#", "\\", "/", "^", "|", "="]
} # tiles allowed for tiling

nonselftiles = ["/", "\\"] # tiles that don't tile with themselves

directiontiles = { # tiles that only tile from certain directions
"/": ["right", "down"],
"\\": ["left", "down"],
"X": ["left", "right", "down"],
}

def dircheck(tile, direction):
    if tile in directiontiles:
        if direction in directiontiles[tile]:
            return True
        else:
            return False
    else:
        return True

class Tile(UIElement):
    def __init__(self, x, y, TileMap: TileMap, specials: dict):
        super(Tile, self).__init__()
        self.x = x
        self.y = y
        self.TileMap = TileMap
        self.specials = specials
        self.last_tile = self.tile

    def update_image(self):
        try: self.image
        except AttributeError: self.image: pygame.surface.Surface = pygame.image.load(self.image_path)
        if self.last_tile != self.tile: 
            self.image: pygame.surface.Surface = pygame.image.load(self.image_path)
            self.last_tile = self.tile

    def update(self):
        if self.x == 0 or self.y == 0: return # don't draw the outer edges of the tilemap, but they should still tile correctly
        if self.x == len(self.TileMap.map[0]) - 1 or self.y == len(self.TileMap.map) - 1: return # ^
        self.update_image()
        self.surf = pygame.Surface((tile_wh, tile_wh))
        offsety = 0
        offsetx = 0
        if (len(self.TileMap.map) > self.y + 1 and 
            self.TileMap.map[self.y+1][self.x] in self.allowedtiles and 
            dircheck(self.TileMap.map[self.y+1][self.x], "up")): # tile below is the same
            offsety += tile_wh
            if (self.y != 0 and 
                self.TileMap.map[self.y-1][self.x] in self.allowedtiles and 
                dircheck(self.TileMap.map[self.y-1][self.x], "down")): # tile above is the same
                offsety += tile_wh
        elif (self.y != 0 and 
              self.TileMap.map[self.y-1][self.x] in self.allowedtiles and 
              dircheck(self.TileMap.map[self.y-1][self.x], "down")): # tile above is the same but not tile below
            offsety += tile_wh * 3
        if (len(self.TileMap.map[0]) > self.x + 1 and 
            self.TileMap.map[self.y][self.x+1] in self.allowedtiles and 
            dircheck(self.TileMap.map[self.y][self.x+1], "left")): # tile right is the same
            offsetx += tile_wh
            if (self.x != 0 and 
                self.TileMap.map[self.y][self.x-1] in self.allowedtiles and 
                dircheck(self.TileMap.map[self.y][self.x-1], "right")): # tile left is also the same
                offsetx += tile_wh
        elif (self.x != 0 and 
              self.TileMap.map[self.y][self.x-1] in self.allowedtiles and 
              dircheck(self.TileMap.map[self.y][self.x-1], "right")): # tile left is the same but not right
            offsetx += tile_wh * 3
        self.rect = self.surf.get_rect()
        self.rect.x = (self.x * tile_wh) + self.TileMap.rect.x
        self.rect.y = (self.y * tile_wh) + self.TileMap.rect.y
        self.surf.blit(self.image, (0, 0), (offsetx, offsety, tile_wh, tile_wh))
        if f"{self.x}, {self.y}" in self.TileMap.specials:
            room_specials = self.TileMap.specials[f"{self.x}, {self.y}"]
            specials_keys = list(room_specials.keys()) + [None for i in range(len(room_specials.keys()))]
            drawing_index = int(((pygame.time.get_ticks() / 15) % FPS_CAP) / (FPS_CAP / len(specials_keys))) # full cycle each second
            drawing_name = specials_keys[drawing_index]
            if drawing_name is not None: # if we're not drawing nothing (images should be flashing)
                drawing_type = room_specials[drawing_name]
                if drawing_type in config.icons: icon_image_filename = config.icons[drawing_type]
                else: icon_image_filename = config.icons["no_icon"]
                icon_image = pygame.image.load(icon_image_filename)
                self.surf.blit(icon_image, (0, 0), (0, 0, tile_wh, tile_wh))
        screen.blit(self.surf, ((self.rect.x, self.rect.y)))

    @property
    def allowedtiles(self):
        allowed = []
        if self.tile in allowedtiles:
            allowed = allowedtiles[self.tile]
            if self.tile not in nonselftiles:
                allowed = allowed + [self.tile]
        else:
            if self.tile not in nonselftiles:
                allowed = [self.tile]
        return allowed

    @property
    def tile(self):
        return self.TileMap.map[self.y][self.x]

    @property
    def image_path(self): # returns path to image
        if self.tile in config.tiles:
            return config.tiles[self.tile]
        else:
            return "sprites\\tiles\\missingtile.png"

class RoomItemDisplay(UIElement):
    def __init__(self, x, y, instances: dict):
        self.x = x
        self.y = y
        self.w = 330
        self.h = 30
        self.instances = instances
        self.absolute = True
        self.text = Text(x, y, f"You see here:")
        self.text.absolute = True
        self.buttons = []
        self.update_instances(instances)

    def update_instances(self, instances):
        def get_button_func(button_instance_name):
            def output_func():
                suburb.display_item(Instance(button_instance_name, instances[button_instance_name]), suburb.map)
            return output_func
        for button in self.buttons:
            button.delete()
        for index, instance_name in enumerate(instances):
            y = self.y + self.h*(index+1)
            instance = Instance(instance_name, instances[instance_name])
            display_name = instance.display_name()
            captcha_button = CaptchalogueButton(self.x, y, instance_name, instances)
            captcha_button.absolute = True
            use_buttons = 0
            for i, action_name in enumerate(reversed(instance.use)):
                use_buttons += 1
                path = f"sprites/item_actions/{action_name}.png"
                pressed_path = f"sprites/item_actions/{action_name}_pressed.png"
                if not os.path.isfile(path): path = "sprites/item_actions/generic_action.png"
                if not os.path.isfile(pressed_path): pressed_path = "sprites/item_actions/generic_action_pressed.png"
                use_button = Button(self.x+(self.w-(30*(i+1))), y, path, pressed_path, instance.get_action_button_func(action_name, suburb.map))
                use_button.absolute = True
                self.buttons.append(use_button)
            main_button_width = self.w-30
            main_button_width -= 30*use_buttons
            new_button = TextButton(self.x+30, y, main_button_width, self.h, util.filter_item_name(display_name), get_button_func(instance_name), truncate_text=True)
            new_button.absolute = True 
            self.buttons.append(new_button)
            self.buttons.append(captcha_button)

class CaptchalogueButton(Button):
    def __init__(self, x, y, instance_name: str, instances: dict):
        self.instances = instances
        self.instance_name = instance_name
        self.instance_dict = instances[instance_name]
        def empty(): pass
        syl = Sylladex.current_sylladex()
        if syl.can_captchalogue(Instance(self.instance_name, self.instance_dict)):
            super().__init__(x, y, "sprites/buttons/captchalogue_symbol.png", "sprites/buttons/captchalogue_symbol_pressed.png", self.get_captchalogue_function())
        else:
            super().__init__(x, y, "sprites/buttons/captchalogue_symbol_pressed.png", "sprites/buttons/captchalogue_symbol_pressed.png", empty)

    def get_captchalogue_function(self):
        instance = Instance(self.instance_name, self.instance_dict)
        def output_func():
            syl = Sylladex.current_sylladex()
            if syl.captchalogue(instance):
                suburb.map()
            else:
                ...
        return output_func

class LogWindow(UIElement):
    def __init__(self, last_scene: Callable, tilemap: Optional[TileMap]=None, draw_console=False, x=int(SCREEN_WIDTH*0.5), y=0, width=500, lines_to_display=4, fontsize=16):
        super().__init__()
        self.last_scene = last_scene
        self.x = x
        self.y = y
        self.width = width
        self.lines_to_display = lines_to_display
        self.fontsize = fontsize
        self.padding = 4
        self.tilemap = tilemap
        self.draw_console = draw_console
        util.log_window = self
        self.scroll_offset = 0
        self.background: Optional[UIElement] = None
        self.console: Optional[InputTextBox] = None
        self.elements: list[UIElement] = []
        self.spawn_logger_lines()
        scroll_check.append(self)

    def delete(self):
        if util.log_window == self: util.log_window = None
        super().delete()
    
    def update_logs(self):
        for element in self.elements: element.delete()
        if self.background is not None:
            self.background.delete()
            self.background = None
        if self.console is not None:
            self.console.delete()
            self.console = None
            if self.tilemap is not None: self.tilemap.input_text_box = None
        self.spawn_logger_lines()

    def spawn_logger_lines(self):
        x = self.x - int(self.width/2)
        self.background = SolidColor(x, self.y, self.width, self.fontsize*self.lines_to_display + self.padding*self.lines_to_display, self.theme.black)
        for loop_index, position_index in enumerate(reversed(range(self.lines_to_display))):
            y = self.y + position_index*self.fontsize + position_index*self.padding
            try:
                line = util.current_log()[-loop_index - 1 - self.scroll_offset]
                text = Text(x, y, line)
                text.fontsize = self.fontsize
                text.color = self.theme.light
                text.absolute = True
                text.set_fontsize_by_width(self.width)
                self.elements.append(text)
            except IndexError:
                pass
        def console_enter_func(textbox: InputTextBox):
            util.log(">"+textbox.text)
            reply = client.requestplus(intent="console_command", content=textbox.text)
            if reply != "None": util.log(reply)
            textbox.text = ""
            self.last_scene()
        if not self.draw_console: return
        console_y = self.y + (self.lines_to_display)*self.fontsize + (self.lines_to_display)*self.padding
        self.console = InputTextBox(x, console_y, self.width, self.fontsize+self.padding)
        self.console.absolute = True
        self.console.enter_func = console_enter_func
        self.console.inactive_color = self.theme.black
        self.console.active_color = self.theme.dark
        self.console.outline_color = None
        self.console.text_color = self.theme.white
        self.console.fontsize = self.fontsize
        self.console.suffix = ">"
        if self.tilemap is not None: self.tilemap.input_text_box = self.console

    def scroll(self, y: int):
        if self.background is None: return
        if not self.background.is_mouseover(): return
        max_offset = len(util.current_log()) - self.lines_to_display
        self.scroll_offset += y
        if self.scroll_offset < 0: self.scroll_offset = 0
        if self.scroll_offset > max_offset: self.scroll_offset = max_offset
        self.update_logs()

class ItemImage():
    def __new__(cls, x, y, item_name: str):
        image_path = f"sprites\\items\\{item_name}.png"
        if os.path.isfile(image_path):
            return Image(x, y, image_path)
        return Text(x, y, item_name)


def spawn_punches(bound_element: UIElement, code: str, base_x, base_y, flipped=False, w=172, h=240):
    padding = 1
    bin_rows = binaryoperations.captcha_code_to_bin_rows(code)
    if flipped:
        copy = bin_rows.copy()
        bin_rows = []
        for row in copy:
            bin_rows.append(row[::-1])
    for row_index, row in enumerate(bin_rows):
        y = (int(h/12)*row_index)
        for char_index, char in enumerate(row):
            x = (int(w/4)*char_index)
            if char == "1":
                punch_x = base_x+x + padding
                punch_y = base_y+y + padding
                punch_w = int(w/4) - padding*2
                punch_h = int(h/12) - padding*2
                punch = SolidColor(punch_x, punch_y, punch_w, punch_h, suburb.current_theme().black)
                punch.bind_to(bound_element)
                punch_middle = SolidColor(punch_x+padding, punch_y+padding, punch_w - padding*2, punch_h - padding*2, suburb.current_theme().white)
                punch_middle.bind_to(bound_element)

class FpsCounter(Text):
    def __init__(self, x, y):
        super().__init__(x, y, "")

    def update(self):
        self.text = f"FPS: {round(clock.get_fps(), 2)}"
        super().update()

class TaskBar(UIElement):
    def __init__(self):
        super().__init__()
        self.w = SCREEN_WIDTH
        self.h = 40
        self.padding = 3
        self.background = SolidColor(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.theme.white)
        self.task_bar = SolidColor(0, SCREEN_HEIGHT-self.h, SCREEN_WIDTH, self.h, self.theme.dark)
        self.task_bar.outline_color = self.theme.light
        self.task_bar.outline_width = self.padding
        actuate_button_box = SolidColor(0, SCREEN_HEIGHT-self.h, 120 + self.padding*2, self.h, self.theme.dark)
        actuate_button_box.outline_color = self.theme.light
        actuate_button_box.outline_width = self.padding
        actuate_button = TextButton(self.padding, SCREEN_HEIGHT-self.h+self.padding, 120, self.h - self.padding*2, " ACTUATE", suburb.map)
        actuate_button.absolute = True
        actuate_button.outline_color = self.theme.black
        actuate_button.fill_color = self.theme.dark
        actuate_button.hover_color = self.theme.light
        actuate_button.text_color = self.theme.white
        actuate_button.outline_width = 3
        actuate_button_image = Image(0.15, 0.5, "sprites/computer/little_green_circle.png")
        actuate_button_image.bind_to(actuate_button)
        # todo: time on bottom right
        self.apps = [actuate_button]

class AppIcon(Button):
    def __init__(self, x, y, app_name: str):
        path = f"sprites/computer/apps/{app_name}.png"
        super().__init__(x, y, path, path, lambda *args: None)
        self.convert = False
        app_label = Text(0.5, 1.2, app_name)
        app_label.color = self.theme.white
        app_label.highlight_color = self.theme.dark
        app_label.bind_to(self)

def render():
    for ui_element in move_to_top.copy():
        update_check.remove(ui_element)
        update_check.append(ui_element)
        move_to_top.remove(ui_element)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.MOUSEWHEEL:
            # 1 is up, -1 is down
            for sprite in scroll_check:
                sprite.scroll(event.y)

        if event.type == pygame.MOUSEBUTTONDOWN:
            for sprite in click_check:
                #sprites with click events will know if the click is on them or not
                sprite.onclick(sprite.collidepoint(event.pos))

        if event.type == pygame.MOUSEBUTTONUP:
            for sprite in mouseup_check:
                sprite.mouseup(sprite.collidepoint(event.pos))

        if event.type == pygame.KEYDOWN:
            for sprite in key_check:
                sprite.keypress(event)

    screen.fill(suburb.current_theme().light)
    keys = pygame.key.get_pressed()

    for sprite in update_check:
        sprite.update()

    for sprite in keypress_update_check:
        sprite.update(keys)

    pygame.display.flip()

    #fps cap
    clock.tick(FPS_CAP)
    return True
