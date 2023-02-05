import pygame
import sys
import os
import pathlib
import hashlib
from typing import Optional, Union, Callable

import util
import config
import client

pygame.init()

clock = pygame.time.Clock()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS_CAP = 60

RUNNING = True

os.chdir(util.homedir)

screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])

base_font = pygame.font.Font(pathlib.Path("./fonts/courbd.ttf"), 32)
WHITE_COLOR = pygame.Color(255, 255, 255)
LIGHT_COLOR = pygame.Color(0, 175, 255)
DIM_COLOR = pygame.Color(157, 224, 255)
BLACK_COLOR = pygame.Color(0, 0, 0)

click_check = []
key_check = []
mouseup_check = []
update_check = []
keypress_update_check = []

ui_elements = []

tile_wh = 32

checks = [click_check, key_check, mouseup_check, update_check, keypress_update_check]

icon_surf = pygame.image.load("sprites\\icon.png").convert()
pygame.display.set_icon(icon_surf)
pygame.display.set_caption(f"SUBURB CLIENT {util.VERSION}")

def clear_elements():
    for element in ui_elements.copy():
        element.delete()

class UIElement(pygame.sprite.Sprite):
    def __init__(self): # x and y as fractions of 1 (centered position on screen)
        super(UIElement, self).__init__()
        self.rect: Union[pygame.Rect, pygame.rect.Rect] = pygame.Rect(0, 0, 0, 0)
        ui_elements.append(self)

    def mouseover(self): # returns True if mouse is over this element
        mousepos = pygame.mouse.get_pos()
        return True if self.rect.collidepoint(mousepos[0], mousepos[1]) else False

    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)

    def delete(self):
        ui_elements.remove(self)
        for list in checks:
            if self in list:
                list.remove(self)
        self.kill()

class TileMap(UIElement):
    def __init__(self, x, y, map: list[list[str]], specials: dict):
        super(TileMap, self).__init__()
        self.x = x
        self.y = y
        self.map = map
        self.specials = specials
        self.tiles = {}
        self.update_map(map)
        update_check.append(self)
        key_check.append(self)

    def update(self):
        for tile in self.tiles:
            self.tiles[tile].update()

    def update_map(self, map):
        if self.map != map or len(self.tiles) == 0:
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
        match event.key:
            case pygame.K_UP: direction = "up"
            case pygame.K_DOWN: direction = "down"
            case pygame.K_LEFT: direction = "left"
            case pygame.K_RIGHT: direction = "right"
            case _: return
        client.requestplus("move", direction)
        dic = client.requestdic("current_map")
        self.map = dic["map"]
        self.specials = dic["specials"]

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

    def update(self):
        if self.x == 0 or self.y == 0: return # don't draw the outer edges of the tilemap, but they should still tile correctly
        if self.x == len(self.TileMap.map[0]) - 1 or self.y == len(self.TileMap.map) - 1: return # ^
        image = pygame.image.load(self.image)
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
        self.surf.blit(image, (0, 0), (offsetx, offsety, tile_wh, tile_wh))
        if f"{self.x}, {self.y}" in self.specials:
            print(f"{self.x}, {self.y}: {self.specials[f'{self.x}, {self.y}']}")
            room_specials = self.specials[f"{self.x}, {self.y}"]
            specials_keys = list(room_specials.keys()) + [None]
            drawing_index = int(((pygame.time.get_ticks() / 10) % FPS_CAP) / (FPS_CAP / len(specials_keys))) # full cycle each second
            drawing_name = specials_keys[drawing_index]
            print(drawing_name)
            if drawing_name is not None: # if we're not drawing nothing (images should be flashing)
                drawing_type = room_specials[drawing_name]
                icon_image_filename = config.icons[drawing_type]
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
    def image(self): # returns path to image
        if self.tile in config.tiles:
            return config.tiles[self.tile]
        else:
            return "sprites\\tiles\\missingtile.png"


class SolidColor(UIElement):
    def __init__(self, x, y, w, h, color: pygame.Color):
        super(SolidColor, self).__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color: pygame.Color = color
        self.absolute = True
        update_check.append(self)

    def update(self):
        self.surf = pygame.Surface((self.w, self.h))
        self.surf.fill(self.color)
        self.rect = self.surf.get_rect()
        if self.absolute:
            self.rect.x = self.x
            self.rect.y = self.y
        else:
            #todo: relative positioning
            pass
        screen.blit(self.surf, ((self.rect.x, self.rect.y)))

class TextButton(UIElement):
    def __init__(self, x, y, w, h, text, onpress: Callable, hover=True):
        super(TextButton, self).__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.onpress = onpress
        self.active = False
        self.hover = hover
        self.outlinedepth = 2
        self.absolute = False
        self.fontsize = 16
        self.text = text
        self.text_color: pygame.Color = BLACK_COLOR
        self.toggle = False
        click_check.append(self)
        update_check.append(self)
        mouseup_check.append(self)

    def update(self):
        self.text_surf = self.font.render(self.text, True, self.text_color)
        self.outline_surf = pygame.Surface((self.w, self.h))
        self.outline_surf.fill(LIGHT_COLOR)
        self.surf = pygame.Surface((self.w-2*self.outlinedepth, self.h-2*self.outlinedepth))
        self.surf.fill(WHITE_COLOR)
        if self.active:
            self.hoversurf = pygame.Surface((self.w, self.h))
            self.hoversurf.fill(LIGHT_COLOR)
            self.hoversurf.set_alpha(89)
        else:
            self.hoversurf = None
        self.rect = self.outline_surf.get_rect()
        if self.absolute:
            self.rect.x = self.x
            self.rect.y = self.y
        else:
            self.rect.x = int((SCREEN_WIDTH * self.x) - (self.outline_surf.get_width() / 2))
            self.rect.y = int((SCREEN_HEIGHT * self.y) - (self.outline_surf.get_height() / 2))
        screen.blit(self.outline_surf, ((self.rect.x, self.rect.y)))
        screen.blit(self.surf, ((self.rect.x+self.outlinedepth, self.rect.y+self.outlinedepth)))
        screen.blit(self.text_surf, ((self.rect.x+(self.outline_surf.get_width()/2)-(self.text_surf.get_width()/2), self.rect.y+(self.outline_surf.get_height()/2)-(self.text_surf.get_height()/2))))
        if self.hoversurf != None:
            screen.blit(self.hoversurf, ((self.rect.x, self.rect.y)))

    def onclick(self, isclicked):
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
    def __init__(self, x, y, unpressed_img_path, pressed_img_path, onpress: Callable, alt: Optional[Callable]=None, alt_img_path=None, altclick: Optional[Callable]=None, hover=None): # x and y as fractions of 1 (centered position on screen)
        super(Button, self).__init__()
        self.unpressed_img_path = unpressed_img_path
        self.pressed_img_path = pressed_img_path
        self.x = x
        self.y = y
        self.onpress = onpress
        self.active = False
        self.alt = alt
        self.alt_img_path = alt_img_path
        self.altclick = altclick
        self.alt_alpha = 255
        self.absolute = False
        self.hover = hover
        click_check.append(self)
        update_check.append(self)
        mouseup_check.append(self)

    def update(self):
        if self.alt is not None and self.alt() and self.alt_img_path is not None: # alternative display condition
            self.surf = pygame.image.load(self.alt_img_path).convert()
            self.surf.set_alpha(self.alt_alpha)
        else:
            if self.active:
                self.surf = pygame.image.load(self.pressed_img_path).convert()
            else:
                if self.hover != None and self.collidepoint(pygame.mouse.get_pos()):
                    self.surf = pygame.image.load(self.hover).convert()
                else:
                    self.surf = pygame.image.load(self.unpressed_img_path).convert()
        self.rect = self.surf.get_rect()
        if self.absolute:
            self.rect.x = self.x
            self.rect.y = self.y
        else:
            self.rect.x = (SCREEN_WIDTH * self.x) - self.surf.get_width() / 2
            self.rect.y = (SCREEN_HEIGHT * self.y) - self.surf.get_height() / 2
        screen.blit(self.surf, ((self.rect.x, self.rect.y)))

    def onclick(self, isclicked):
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
    def __init__(self, x, y):
        super(InputTextBox, self).__init__()
        self.text = ""
        self.active = False
        self.waitframes = 0
        self.x = x
        self.y = y
        self.secure = False
        self.button = None
        click_check.append(self)
        key_check.append(self)
        keypress_update_check.append(self)

    def update(self, keys):
        if self.secure:
            t = "*" * len(self.text)
            self.text_surf = base_font.render(t, True, BLACK_COLOR)
        else:
            self.text_surf = base_font.render(self.text, True, BLACK_COLOR)
        width = max(100, self.text_surf.get_width()+10)
        height = 32
        outline = 3
        self.surf = pygame.Surface((width, height))
        if self.active:
            self.surf.fill(DIM_COLOR)
        else:
            self.surf.fill(WHITE_COLOR)

        self.outline_surf = pygame.Surface((width + (outline * 2), height + (outline  * 2)))
        self.outline_surf.fill(LIGHT_COLOR)

        self.rect = self.outline_surf.get_rect()
        self.rect.x = int((SCREEN_WIDTH * self.x) - self.outline_surf.get_width() / 2)
        self.rect.y = int((SCREEN_HEIGHT * self.y) - self.outline_surf.get_height() / 2)
        screen.blit(self.outline_surf, (self.rect.x, self.rect.y))

        surfx = (SCREEN_WIDTH * self.x) - self.surf.get_width() / 2
        surfy = (SCREEN_HEIGHT * self.y) - self.surf.get_height() / 2
        screen.blit(self.surf, (surfx, surfy))

        textx = (SCREEN_WIDTH * self.x) - self.text_surf.get_width() / 2
        texty = (SCREEN_HEIGHT * self.y) - self.text_surf.get_height() / 2
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
            # if enter is pressed and this text box has a button assigned to it, press that button
            elif event.key == pygame.K_RETURN and self.button != None:
                self.button.mouseup()
            else:
                if event.unicode.isascii() and event.unicode not in  ["\n", "\t", "\r"]: #no newline, tab or carriage return
                    self.text += event.unicode

    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)

class Image(UIElement):
    def __init__(self, x, y, path):
        super(Image, self).__init__()
        self.x = x
        self.y = y
        self.path = path
        self.absolute = False
        self.animated = False
        self.animframe = 1
        self.animframes = 1
        self.speed = 3
        self.wait = 0
        self.highlight_color: Optional[pygame.Color] = None
        update_check.append(self)

    def update(self):
        if self.animated:
            self.surf = pygame.image.load(self.path+f"-{self.animframe}.png")
            if self.wait == self.speed:
                self.animframe += 1
                if self.animframe > self.animframes:
                    self.animframe = 1
                self.wait = 0
            else:
                self.wait += 1
        else:
            self.surf = pygame.image.load(self.path).convert()
        self.rect = self.surf.get_rect()
        if self.absolute:
            self.rect.x = self.x
            self.rect.y = self.y
        else:
            self.rect.x = int((SCREEN_WIDTH * self.x) - self.surf.get_width() / 2)
            self.rect.y = int((SCREEN_HEIGHT * self.y) - self.surf.get_height() / 2)
        if self.highlight_color != None:
            self.highlight_surf = pygame.Surface((self.surf.get_width(), self.surf.get_height()))
            self.highlight_surf.fill(self.highlight_color)
            screen.blit(self.highlight_surf, (self.rect.x, self.rect.y))
        screen.blit(self.surf, (self.rect.x, self.rect.y))

class Text(UIElement):
    def __init__(self, x, y, text):
        super(Text, self).__init__()
        self.x = x
        self.y = y
        self.text = text
        self.absolute = False  # whether x and y should be exact coords
        self.color: pygame.Color = BLACK_COLOR
        self.outline_color: Optional[pygame.Color] = None
        self.outline_depth = 1
        self.fontsize = 32
        update_check.append(self)

    def update(self):
        self.text_surf = self.font.render(self.text, True, self.color)
        self.rect = self.text_surf.get_rect()
        if self.absolute:
            self.rect.x = self.x
            self.rect.y = self.y
        else:
            self.rect.x = int((SCREEN_WIDTH * self.x) - self.text_surf.get_width() / 2)
            self.rect.y = int((SCREEN_HEIGHT * self.y) - self.text_surf.get_height() / 2)
        if self.outline_color != None:
            self.outline_surf = self.font.render(self.text, True, self.outline_color)
            # screen.blit(self.outline_surf, (self.rect.x + self.outline_depth, self.rect.y + self.outline_depth)) # +y +x
            # screen.blit(self.outline_surf, (self.rect.x - self.outline_depth, self.rect.y + self.outline_depth)) # +y -x
            # screen.blit(self.outline_surf, (self.rect.x - self.outline_depth, self.rect.y - self.outline_depth)) # -y -x
            # screen.blit(self.outline_surf, (self.rect.x + self.outline_depth, self.rect.y - self.outline_depth)) # -y +x
            screen.blit(self.outline_surf, (self.rect.x, self.rect.y + self.outline_depth))
            screen.blit(self.outline_surf, (self.rect.x, self.rect.y - self.outline_depth))
            screen.blit(self.outline_surf, (self.rect.x + self.outline_depth, self.rect.y))
            screen.blit(self.outline_surf, (self.rect.x - self.outline_depth, self.rect.y))
        screen.blit(self.text_surf, (self.rect.x, self.rect.y))

    @property
    def font(self):
        return pygame.font.Font(pathlib.Path("./fonts/courbd.ttf"), self.fontsize)

def render():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

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

    screen.fill(DIM_COLOR)
    keys = pygame.key.get_pressed()

    for sprite in update_check:
        sprite.update()

    for sprite in keypress_update_check:
        sprite.update(keys)

    pygame.display.flip()

    #fps cap
    clock.tick(FPS_CAP)
    return True
