import pygame
from pygame import Color
import sys
import os
import pathlib
import hashlib
import time
import numpy as np
import random
from copy import deepcopy
from typing import Optional, Union, Callable

import util
import config
import client
import suburb
import themes
import binaryoperations
import sburbserver
from strife import Npc, Griefer, Strife
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
always_on_top_check = []
keypress_update_check = []
scroll_check = []
move_to_top = []

ui_elements = []

tile_wh = 32

checks = [click_check, key_check, mouseup_check, update_check, always_on_top_check, keypress_update_check, scroll_check]

icon_surf = pygame.image.load("sprites\\icon.png").convert()
pygame.display.set_icon(icon_surf)
pygame.display.set_caption(f"SUBURB CLIENT {util.VERSION}")

def clear_elements():
    for element in ui_elements.copy():
        element.delete()
    for check_list in checks:
        check_list = []

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
        self.rect_x_offset = 0
        self.rect_y_offset = 0
        self.theme: themes.Theme = suburb.current_theme()
        self.bound_elements: list[UIElement] = []
        # temporary elements are meant to be disposed of
        self.temporary_elements: list[UIElement] = []
        self.blit_surf = screen
        ui_elements.append(self)

    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)
    
    def is_mouseover(self):
        return self.collidepoint(pygame.mouse.get_pos())

    def bind_to(self, element: "UIElement", temporary=False):
        self.relative_binding = element
        if temporary:
            element.temporary_elements.append(self)
        else:
            element.bound_elements.append(self)

    def delete(self):
        for element in self.bound_elements + self.temporary_elements:
            element.delete()
        if self in ui_elements:
            ui_elements.remove(self)
        if self.relative_binding is not None:
            if self in self.relative_binding.bound_elements: self.relative_binding.bound_elements.remove(self)
            if self in self.relative_binding.temporary_elements: self.relative_binding.temporary_elements.remove(self)
        for list in checks:
            if self in list:
                list.remove(self)
        self.kill()

    def kill_bound_elements(self):
        for element in self.bound_elements.copy():
            element.delete()
        for element in self.temporary_elements.copy():
            element.delete()
    
    def kill_temporary_elements(self):
        for element in self.temporary_elements.copy():
            element.delete()

    def bring_to_top(self):
        move_to_top.append(self)

    def convert_to_theme(self, surf: Union[pygame.Surface, pygame.surface.Surface], theme: Optional["themes.Theme"]=None) -> pygame.Surface:
        if theme is not None: new_theme = theme
        else: new_theme = self.theme
        default_theme = themes.default
        surf = palette_swap(surf, default_theme.white, new_theme.white)
        surf = palette_swap(surf, default_theme.light, new_theme.light)
        surf = palette_swap(surf, default_theme.dark, new_theme.dark)
        surf = palette_swap(surf, default_theme.black, new_theme.black)
        return surf

    def get_rect_xy(self, secondary_surf:Union[pygame.Surface, pygame.surface.Surface, None] = None, absolute: Optional[bool]=None) -> tuple[int, int]:
        rect_x: int = 0
        rect_y: int = 0
        if absolute is None: absolute = self.absolute
        if secondary_surf is not None:
            secondary_surf_width = secondary_surf.get_width()
            secondary_surf_height = secondary_surf.get_height()
        else:
            secondary_surf_width = 0
            secondary_surf_height = 0
        if absolute:
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
        return rect_x+self.rect_x_offset, rect_y+self.rect_y_offset

class SolidColor(UIElement):
    def __init__(self, x, y, w, h, color: pygame.Color, binding:Optional[UIElement]=None):
        super(SolidColor, self).__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color: Union[pygame.Color, list[pygame.Color]] = color
        self.color_func: Optional[Callable] = None
        self.outline_color: Optional[pygame.Color] = None
        self.alpha = 255
        self.animframe = 0
        self.outline_width = 2
        self.border_radius: int = 0
        self.absolute = True
        self.draw_sprite = True
        self.follow_mouse = False
        if binding:
            self.bind_to(binding)
        update_check.append(self)

    def get_color(self) -> Union[pygame.Color, list]:
        if self.color_func is None: return self.color
        else: return self.color_func()

    def update(self):
        if self.absolute and self.follow_mouse:
            self.x, self.y = pygame.mouse.get_pos()
        self.surf = pygame.Surface((self.w, self.h))
        if isinstance(self.get_color(), pygame.Color):
            fill_color = self.get_color()
        else:
            # list of colors to flip between
            index = self.animframe % len(self.color)
            fill_color = self.color[index]
            self.animframe += 1
        if self.outline_color is not None:
            self.outline_surf = pygame.Surface((self.w + self.outline_width*2, self.h + self.outline_width*2))
        self.rect = self.surf.get_rect()
        if self.absolute:
            self.rect.x, self.rect.y = self.get_rect_xy()
        else:
            if self.relative_binding is not None:
                width = self.relative_binding.rect.w
                height = self.relative_binding.rect.h
            else:
                width = SCREEN_WIDTH
                height = SCREEN_HEIGHT
            self.rect.x = int(width * self.x) - (self.w//2) + self.rect_x_offset
            self.rect.y = int(height * self.y) - (self.h//2) + self.rect_y_offset
            if self.relative_binding is not None:
                self.rect.x += self.relative_binding.rect.x
                self.rect.y += self.relative_binding.rect.y
        if not self.draw_sprite: return
        if self.outline_color is not None: 
            self.outline_rect = self.outline_surf.get_rect()
            self.outline_rect.x, self.outline_rect.y = self.rect.x-self.outline_width, self.rect.y-self.outline_width
            pygame.draw.rect(self.blit_surf, self.outline_color, self.outline_rect, border_radius = self.border_radius+self.outline_width)
        pygame.draw.rect(self.blit_surf, fill_color, self.rect, border_radius = self.border_radius)

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
    def __init__(self, x, y, w, h, text, onpress: Optional[Callable], hover=True, truncate_text=False, theme: Optional["themes.Theme"]=None):
        super(TextButton, self).__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        if onpress is None: self.onpress = lambda *args: None
        else: self.onpress = onpress
        self.active = False
        self.hover = hover
        self.truncate_text = truncate_text
        self.truncated = False
        if theme: self.theme = theme
        self.outline_width = 2
        self.absolute = False
        self.fontsize = 16
        self.text = text
        self.text_color: pygame.Color = self.theme.black
        self.outline_color: pygame.Color = self.theme.dark
        self.fill_color: pygame.Color = self.theme.white
        self.hover_color: pygame.Color = self.theme.dark
        self.draw_condition: Optional[Callable] = None
        self.inactive_condition: Optional[Callable] = None
        self.draw_sprite = True
        self.toggle = False
        self.click_on_mouse_down = False
        click_check.append(self)
        update_check.append(self)
        mouseup_check.append(self)

    def update(self):
        if self.draw_condition is not None:
            if not self.draw_condition(): return
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
        if self.inactive_condition is not None and self.inactive_condition():
            self.hoversurf = pygame.Surface((self.w, self.h))
            self.hoversurf.fill(self.hover_color)
            self.hoversurf.set_alpha(150)
        elif self.active:
            self.hoversurf = pygame.Surface((self.w, self.h))
            self.hoversurf.fill(self.hover_color)
            self.hoversurf.set_alpha(89)
        else:
            self.hoversurf = None
        self.rect = self.outline_surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy(self.outline_surf)
        if self.draw_sprite:
            self.blit_surf.blit(self.outline_surf, ((self.rect.x, self.rect.y)))
            self.blit_surf.blit(self.surf, ((self.rect.x+self.outline_width, self.rect.y+self.outline_width)))
            self.blit_surf.blit(self.text_surf, ((self.rect.x+(self.outline_surf.get_width()/2)-(self.text_surf.get_width()/2), self.rect.y+(self.outline_surf.get_height()/2)-(self.text_surf.get_height()/2))))
            if self.hoversurf != None:
                self.blit_surf.blit(self.hoversurf, ((self.rect.x, self.rect.y)))

    def onclick(self, isclicked):
        if self.inactive_condition is not None and self.inactive_condition(): return
        if self not in click_check: return
        if isclicked:
            if self.click_on_mouse_down: self.onpress()
            elif not self.toggle:
                self.active = True


    def mouseup(self, isclicked):
        if self.click_on_mouse_down: return
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
    def __init__(self, x, y, unpressed_img_path:str, pressed_img_path:Optional[str], onpress:Callable, alt:Optional[Callable]=None, alt_img_path=None, altclick:Optional[Callable]=None, hover=None, theme:themes.Theme=suburb.current_theme()): # x and y as fractions of 1 (centered position on screen)
        super(Button, self).__init__()
        self.unpressed_img_path = unpressed_img_path
        if pressed_img_path is None: self.pressed_img_path = self.unpressed_img_path
        else: self.pressed_img_path = pressed_img_path
        self.x = x
        self.y = y
        self.onpress = onpress
        self.alt_img_path = alt_img_path
        self.altclick = altclick
        self.hover = hover
        self.hover_to_top = False
        self.active = False
        self.alpha = 255
        self.alt = alt
        self.alt_alpha = 255
        self.absolute = False
        self.convert = True
        self.theme = theme
        self.scale: float = 1.0
        self.double_click = False
        self.last_clicked = 0
        self.invert_on_click = False
        self.overlay_on_click = False
        self.overlay_intensity = 30
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
                if self.invert_on_click:
                    inverted = pygame.Surface(self.surf.get_rect().size, pygame.SRCALPHA)
                    inverted.fill((255, 255, 255, 255))
                    inverted.blit(self.surf, (0, 0), None, pygame.BLEND_RGB_SUB)
                    self.surf = inverted
                if self.overlay_on_click:
                    self.surf.fill((self.overlay_intensity, self.overlay_intensity, self.overlay_intensity), None, pygame.BLEND_ADD)
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
        if self.hover_to_top and self.is_mouseover():
            for ui_element in update_check:
                if not ui_element.is_mouseover(): continue
                # we want to bring this to the top of drawing only if it's not behind anything
                if update_check.index(self) < update_check.index(ui_element): break
            else:
                # move to top (last in update_check list)
                move_to_top.append(self)
                # move our bound elements to the top
                for ui_element in self.bound_elements + self.temporary_elements:
                    move_to_top.append(ui_element)
        self.blit_surf.blit(self.surf, ((self.rect.x, self.rect.y)))

    def onclick(self, isclicked):
        if self not in click_check: return
        if isclicked:
            self.active = True

    def mouseup(self, isclicked):
        self.active = False
        if isclicked:
            if self.double_click and time.time() - self.last_clicked > 0.5: # 500 ms allowance
                self.last_clicked = time.time()
                return
            if self.alt != None and self.alt():
                if self.altclick != None:
                    self.altclick()
            else:
                self.onpress()

class InputTextBox(UIElement):
    def __init__(self, x, y, w=None, h=None, theme=themes.default):
        super(InputTextBox, self).__init__()
        self.text = ""
        self.active = False
        self.waitframes = 0
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.theme = theme
        self.text_color = self.theme.black
        self.inactive_color = self.theme.white
        self.active_color = self.theme.light
        self.outline_color: Optional[pygame.Color] = self.theme.dark
        self.fontsize = 32
        self.max_characters = 0
        self.numbers_only = False
        self.maximum_value = 0
        self.absolute_text = True
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
        outline_width = 3
        self.surf = pygame.Surface((width, height))
        if self.active:
            self.surf.fill(self.active_color)
        else:
            self.surf.fill(self.inactive_color)

        if self.outline_color is not None:
            self.outline_surf = pygame.Surface((width + (outline_width * 2), height + (outline_width * 2)))
            self.outline_surf.fill(self.outline_color)

        self.rect = self.surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy(self.surf)

        if self.outline_color is not None:
            self.blit_surf.blit(self.outline_surf, (self.rect.x-outline_width, self.rect.y-outline_width))

        surfx, surfy = self.get_rect_xy(self.surf)
        self.blit_surf.blit(self.surf, (surfx, surfy))

        if self.absolute_text:
            textx, texty = self.get_rect_xy(self.text_surf)
        else:
            textx = (self.rect.x + (self.rect.w//2)) - (self.text_surf.get_width()//2)
            texty = (self.rect.y + (self.rect.h//2)) - (self.fontsize//2)
        self.blit_surf.blit(self.text_surf, (textx, texty))

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
        if not self.active: return
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            if self.numbers_only and self.text == "": self.text = "0"
        elif event.key == pygame.K_RETURN and self.enter_func != None:
            self.enter_func(self)
        # if enter is pressed and this text box has a button assigned to it, press that button
        elif event.key == pygame.K_RETURN and self.button != None:
            self.button.mouseup(True)
        else:
            if self.max_characters != 0 and len(self.text)+1 > self.max_characters: return
            if event.unicode.isascii() and event.unicode not in  ["\n", "\t", "\r"]: #no newline, tab or carriage return
                if self.numbers_only:
                    try: int(event.unicode)
                    except ValueError: return
                self.text += event.unicode
                if self.numbers_only: 
                    number = int(self.text)
                    if self.maximum_value != 0:
                        number = min(number, self.maximum_value)
                    self.text = str(number)

    @property
    def font(self):
        return pygame.font.Font(pathlib.Path("./fonts/courbd.ttf"), int(self.fontsize))

class Image(UIElement):
    def __init__(self, x, y, path, theme=suburb.current_theme(), convert=True):
        super(Image, self).__init__()
        self.x = x
        self.y = y
        self.path = path
        self.path_func: Optional[Callable] = None
        self.theme = theme
        self.convert = convert
        self.absolute = False
        self.animated = False
        self.hover_to_top = False
        self.crop: Optional[tuple[int, int, int, int]] = None
        self.animframe = 1
        self.animframes = 1
        self.speed = 3
        self.wait = 0
        self.alpha = 255
        self.scale: float = 1
        self.scaled = False
        self.highlight_color: Optional[pygame.Color] = None
        self.convert_colors: list[tuple[pygame.Color, pygame.Color]] = []
        update_check.append(self)

    def get_width(self):
        self.update()
        return self.surf.get_width()
    
    def get_height(self):
        self.update()
        return self.surf.get_height()

    def load_image(self, path: str):
        return pygame.image.load(path)

    def update(self):
        if self.path_func is not None and self.path != self.path_func():
            self.path = self.path_func()
            delattr(self, "surf")
        if self.animated:
            self.surf = self.load_image(self.path+f"-{self.animframe}.png").convert()
            self.scaled = False
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
                self.surf = self.load_image(self.path)
                if self.convert:
                    self.surf = self.surf.convert()
                    self.surf = self.convert_to_theme(self.surf)
                    for initial_color, converted_color in self.convert_colors:
                        print(initial_color, converted_color)
                        self.surf = palette_swap(self.surf, initial_color, converted_color)
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
            self.blit_surf.blit(self.highlight_surf, (self.rect.x, self.rect.y))
        if self.hover_to_top and self.is_mouseover():
            for ui_element in update_check:
                if not ui_element.is_mouseover(): continue
                # we want to bring this to the top of drawing only if it's not behind anything
                if update_check.index(self) < update_check.index(ui_element): break
            else:
                # move to top (last in update_check list)
                move_to_top.append(self)
                # move our bound elements to the top
                for ui_element in self.bound_elements + self.temporary_elements:
                    move_to_top.append(ui_element)
        self.blit_surf.blit(self.surf, (self.rect.x, self.rect.y))

class Text(UIElement):
    def __init__(self, x, y, text: str):
        super(Text, self).__init__()
        self.x = x
        self.y = y
        self.text = text
        self.text_func: Optional[Callable] = None
        self.absolute = False  # whether x and y should be exact coords
        self.color: pygame.Color = self.theme.black
        self.outline_color: Optional[pygame.Color] = None
        self.outline_depth = 1
        self.highlight_color: Optional[pygame.Color] = None
        self.fontsize: int = 32
        self.scale: float = 1
        self.alpha = 255
        update_check.append(self)

    def get_width(self):
        text_surf = self.font.render(self.get_text(), True, self.color)
        return text_surf.get_width()

    def get_text(self):
        if self.text_func is not None:
            return str(self.text_func())
        else: return self.text

    def set_fontsize_by_width(self, width):
        text_surf = self.font.render(self.get_text(), True, self.color)
        while text_surf.get_width() > width:
            self.fontsize -= 1
            text_surf = self.font.render(self.get_text(), True, self.color)

    def update(self):
        self.text_surf = self.font.render(self.get_text(), True, self.color)
        self.rect = self.text_surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy(self.text_surf)
        if self.highlight_color is not None:
            self.highlight_surf = pygame.Surface((self.rect.w, self.rect.h))
            self.highlight_surf.fill(self.highlight_color)
            self.blit_surf.blit(self.highlight_surf, (self.rect.x, self.rect.y))
        if self.outline_color != None:
            self.outline_surf = self.font.render(self.get_text(), True, self.outline_color)
            if self.alpha != 255: self.outline_surf.set_alpha(self.alpha)
            # self.blit_surf.blit(self.outline_surf, (self.rect.x + self.outline_depth, self.rect.y + self.outline_depth)) # +y +x
            # self.blit_surf.blit(self.outline_surf, (self.rect.x - self.outline_depth, self.rect.y + self.outline_depth)) # +y -x
            # self.blit_surf.blit(self.outline_surf, (self.rect.x - self.outline_depth, self.rect.y - self.outline_depth)) # -y -x
            # self.blit_surf.blit(self.outline_surf, (self.rect.x + self.outline_depth, self.rect.y - self.outline_depth)) # -y +x
            self.blit_surf.blit(self.outline_surf, (self.rect.x, self.rect.y + self.outline_depth))
            self.blit_surf.blit(self.outline_surf, (self.rect.x, self.rect.y - self.outline_depth))
            self.blit_surf.blit(self.outline_surf, (self.rect.x + self.outline_depth, self.rect.y))
            self.blit_surf.blit(self.outline_surf, (self.rect.x - self.outline_depth, self.rect.y))
        if self.alpha != 255: self.text_surf.set_alpha(self.alpha)
        self.blit_surf.blit(self.text_surf, (self.rect.x, self.rect.y))

    @property
    def font(self):
        return pygame.font.Font(pathlib.Path("./fonts/courbd.ttf"), int(self.fontsize*self.scale))

def get_spirograph(x, y, thick=True) -> Image:
    if thick: path = "sprites/spirograph/thick/suburbspirograph"
    else: path = "sprites/spirograph/thin/suburbspirograph"
    spirograph = Image(x, y, path)
    spirograph.animated = True
    spirograph.animframes = 164
    return spirograph

def make_grist_cost_display(x, y, h, true_cost: dict, grist_cache: dict, binding: Optional[UIElement], text_color: pygame.Color, temporary=True, absolute=True, scale_mult=1.0) -> UIElement:
    elements: list[Union[Image, Text]] = []
    padding = 5
    scale = (h / 45) * scale_mult
    fontsize = int(h * scale_mult)
    for grist_name, grist_cost in true_cost.items():
        icon_path = config.grists[grist_name]["image"]
        if len(elements) != 0:
            icon_x = padding+elements[-1].get_width()
            icon_y = 0
        else:
            icon_x = x
            icon_y = y
        icon = Image(icon_x, icon_y, icon_path)
        icon.convert = False
        icon.scale = scale
        icon.absolute = True
        if len(elements) == 0:
            elements.append(icon)
            if binding is not None: icon.bind_to(binding, temporary)
        else:
            icon.bind_to(elements[-1])
            elements.append(icon)
        label_x = padding + int(45*scale)
        label = Text(label_x, 0, str(grist_cost))
        if grist_cost <= grist_cache[grist_name]:
            label.color = text_color
        else:
            label.color = pygame.Color(255, 0, 0)
        label.fontsize = fontsize
        label.bind_to(elements[-1])
        label.absolute = True
        elements.append(label)
    if not absolute:
        if binding is None:
            binding_w = SCREEN_WIDTH
            binding_h = SCREEN_HEIGHT
        else:
            binding_w = binding.rect.w
            binding_h = binding.rect.h
        total_element_w = 0
        for element in elements:
            total_element_w += element.get_width()
        elements[0].x = int(binding_w*x - total_element_w//2)
        elements[0].y = int(binding_h*y - h//2)
    return elements[0]

class TileMap(UIElement):
    def __init__(self, x, y, server_view=False, item_display_x=70, item_display_y=190):
        super(TileMap, self).__init__()
        self.x = x
        self.y = y
        self.tiles: dict[str, "Tile"] = {}
        self.server_view = server_view
        if not self.server_view:
            self.label = Text(0.5, 0, "")
            self.label.bind_to(self)
        else:
            self.label = None
        self.input_text_box: Optional[InputTextBox] = None
        self.info_window: Optional[UIElement] = None
        self.info_text: Optional[UIElement] = None
        self.item_display = RoomItemDisplay(item_display_x, item_display_y, self, server_view)
        self.update_map()
        self.w = (len(self.map)-2)*32
        self.h = (len(self.map[0])-2)*32
        outline_width = 6
        self.background = SolidColor(32-outline_width, 32-outline_width, self.w + outline_width*2, self.h + outline_width*2, self.theme.dark)
        self.background.border_radius = 3
        self.background.bind_to(self)
        self.initialize_map(self.map)
        self.item_display.update_instances()
        update_check.append(self)
        key_check.append(self)

    def bind_to(self, element, temporary=False):
        super().bind_to(element, temporary)
        self.item_display.bind_to(element, temporary)

    def update(self):
        if time.time() - self.last_update > 2:
            self.update_map()
        for tile in self.tiles:
            self.tiles[tile].update()

    def initialize_map(self, map):
        if self.map != map or len(self.tiles) == 0:
            self.map: list[list[str]] = map
            self.rect = pygame.Rect(0, 0, len(map[0])*tile_wh, len(map)*tile_wh)
            self.rect.x = int((SCREEN_WIDTH * self.x) - (self.rect.w / 2))
            self.rect.y = int((SCREEN_HEIGHT * self.y) - (self.rect.h / 2))
            for tile in self.tiles:
                self.tiles[tile].delete()
            for y, line in enumerate(map):
                for x, char in enumerate(line):
                    self.tiles[f"{x}, {y}"] = Tile(x, y, self, self.specials, self.server_view)

    def update_map(self, map_dict: Optional[dict]=None, update_info_window=False):
        if map_dict is None:
            if self.server_view:
                sburbserver.update_viewport_dic()
                map_dict = sburbserver.viewport_dic
            else:
                map_dict = client.requestdic("current_map")
        self.map = map_dict["map"]
        self.specials = map_dict["specials"]
        self.instances: dict[str, dict] = map_dict["instances"]
        self.npcs: dict[str, dict] = map_dict["npcs"]
        self.room_name: str = map_dict["room_name"]
        self.theme = themes.themes[map_dict["theme"]]
        self.item_display.update_instances()
        for tile in self.tiles.values():
            tile.known_invalid_tiles = []
        if self.label is not None: self.label.text = self.room_name
        if update_info_window: self.update_info_window()
        self.last_update = time.time()

    def update_info_window(self):
        if self.info_window is not None and self.info_text is not None:
            sburbserver.update_info_window(self.info_window, self.info_text)

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
        if self.server_view:
            sburbserver.move_view_by_direction(direction)
        else:
            client.requestplus("move", direction)
        self.update_map()
        

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
    def __init__(self, x, y, tile_map: TileMap, specials: dict, server_view=False):
        super(Tile, self).__init__()
        self.x = x
        self.y = y
        self.tile_map = tile_map
        self.specials = specials
        self.server_view = server_view
        self.last_tile = self.tile
        self.known_invalid_tiles: list[str] = []
        if server_view:
            click_check.append(self)

    def load_image(self):
        self.theme = self.tile_map.theme
        self.image: pygame.surface.Surface = pygame.image.load(self.image_path)
        self.image = self.convert_to_theme(self.image)
        self.image.set_colorkey(pygame.Color(0, 0, 0))

    def update_image(self):
        try: self.image
        except AttributeError: self.load_image()
        if self.last_tile != self.tile: 
            self.load_image()
            self.last_tile = self.tile

    def onclick(self, isclicked: bool):
        if isclicked:
            center_tile_x = len(self.tile_map.map)//2
            center_tile_y = len(self.tile_map.map)//2
            x_diff = self.x - center_tile_x
            y_diff = self.y - center_tile_y
            target_x = sburbserver.current_x+x_diff
            target_y = sburbserver.current_y+y_diff
            match sburbserver.current_mode:
                case "deploy":
                    viewport_dict = sburbserver.deploy_item(target_x, target_y)
                    if viewport_dict is not None:
                        sburbserver.update_viewport_dic(viewport_dict)
                        self.tile_map.update_map(viewport_dict, True)
                case "revise":
                    if self.tile == sburbserver.current_selected_tile: return
                    if sburbserver.current_selected_tile in self.known_invalid_tiles: return 
                    viewport_dict = sburbserver.revise_tile(target_x, target_y)
                    if viewport_dict is None: self.known_invalid_tiles.append(sburbserver.current_selected_tile)
                    else:
                        sburbserver.update_viewport_dic(viewport_dict)
                        self.tile_map.update_map(viewport_dict)
                case _:
                    if x_diff == 0 and y_diff == 0: return
                    sburbserver.move_view_to_tile(target_x, target_y)
                    self.tile_map.update_map()

    def update(self):
        if self.x == 0 or self.y == 0: return # don't draw the outer edges of the tilemap, but they should still tile correctly
        if self.x == len(self.tile_map.map[0]) - 1 or self.y == len(self.tile_map.map) - 1: return # ^
        if self.server_view and sburbserver.current_mode == "revise" and self.is_mouseover() and pygame.mouse.get_pressed()[0]:
            self.onclick(True)
        self.update_image()
        self.surf = pygame.Surface((tile_wh, tile_wh))
        offsety = 0
        offsetx = 0
        if (len(self.tile_map.map) > self.y + 1 and 
            self.tile_map.map[self.y+1][self.x] in self.allowedtiles and 
            dircheck(self.tile_map.map[self.y+1][self.x], "up")): # tile below is the same
            offsety += tile_wh
            if (self.y != 0 and 
                self.tile_map.map[self.y-1][self.x] in self.allowedtiles and 
                dircheck(self.tile_map.map[self.y-1][self.x], "down")): # tile above is the same
                offsety += tile_wh
        elif (self.y != 0 and 
              self.tile_map.map[self.y-1][self.x] in self.allowedtiles and 
              dircheck(self.tile_map.map[self.y-1][self.x], "down")): # tile above is the same but not tile below
            offsety += tile_wh * 3
        if (len(self.tile_map.map[0]) > self.x + 1 and 
            self.tile_map.map[self.y][self.x+1] in self.allowedtiles and 
            dircheck(self.tile_map.map[self.y][self.x+1], "left")): # tile right is the same
            offsetx += tile_wh
            if (self.x != 0 and 
                self.tile_map.map[self.y][self.x-1] in self.allowedtiles and 
                dircheck(self.tile_map.map[self.y][self.x-1], "right")): # tile left is also the same
                offsetx += tile_wh
        elif (self.x != 0 and 
              self.tile_map.map[self.y][self.x-1] in self.allowedtiles and 
              dircheck(self.tile_map.map[self.y][self.x-1], "right")): # tile left is the same but not right
            offsetx += tile_wh * 3
        self.rect = self.surf.get_rect()
        self.rect.x = (self.x * tile_wh) + self.tile_map.rect.x
        self.rect.y = (self.y * tile_wh) + self.tile_map.rect.y
        self.surf.blit(self.image, (0, 0), (offsetx, offsety, tile_wh, tile_wh))
        if f"{self.x}, {self.y}" in self.tile_map.specials:
            room_specials = self.tile_map.specials[f"{self.x}, {self.y}"]
            specials_keys = list(room_specials.keys()) + [None for i in range(len(room_specials.keys()))]
            drawing_index = int(((pygame.time.get_ticks() / 15) % FPS_CAP) / (FPS_CAP / len(specials_keys))) # full cycle each second
            drawing_name = specials_keys[drawing_index]
            if drawing_name is not None: # if we're not drawing nothing (images should be flashing)
                drawing_type = room_specials[drawing_name]
                if drawing_type in config.icons: icon_image_filename = config.icons[drawing_type]
                else: icon_image_filename = config.icons["no_icon"]
                icon_image = pygame.image.load(icon_image_filename)
                icon_image = self.convert_to_theme(icon_image)
                icon_image.set_colorkey(pygame.Color(0, 0, 0))
                self.surf.blit(icon_image, (0, 0), (0, 0, tile_wh, tile_wh))
        if self.server_view and self.is_mouseover():
            if sburbserver.current_mode == "deploy":
                cursor_image_path = config.icons["deploy"]
            elif sburbserver.current_mode == "revise":
                cursor_image_path = config.tiles[sburbserver.current_selected_tile]
            else:
                cursor_image_path = config.icons["select"]
            cursor_image = pygame.image.load(cursor_image_path)
            if sburbserver.current_mode == "revise":
                cursor_image = self.convert_to_theme(cursor_image)
            cursor_image.set_colorkey(pygame.Color(0, 0, 0))
            self.surf.blit(cursor_image, (0, 0), (0, 0, tile_wh, tile_wh))
        if self.server_view and self.x == len(self.tile_map.map)//2 and self.y == len(self.tile_map.map)//2:
            center_path = config.icons["center"]
            center_image = pygame.image.load(center_path)
            center_image = self.convert_to_theme(center_image, suburb.current_theme())
            center_image.set_colorkey(pygame.Color(0, 0, 0))
            self.surf.blit(center_image, (0, 0), (0, 0, tile_wh, tile_wh))
        self.blit_surf.blit(self.surf, ((self.rect.x, self.rect.y)))

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
        return self.tile_map.map[self.y][self.x]

    @property
    def image_path(self): # returns path to image
        if self.tile in config.tiles:
            return config.tiles[self.tile]
        else:
            return "sprites\\tiles\\missingtile.png"

class TileDisplay(UIElement):
    def __init__(self, x, y, tile_char):
        super().__init__()
        self.x = x
        self.y = y
        self.tile = tile_char
        self.offsetx, self.offsety = 0, 0
        self.scale = 1
        self.click_func: Optional[Callable] = None
        update_check.append(self)
        click_check.append(self)

    def onclick(self, isclicked):
        if isclicked:
            if self.click_func is not None:
                self.click_func()

    def update_image(self):
        try: self.image
        except AttributeError: self.image: pygame.surface.Surface = pygame.image.load(self.image_path)

    @property
    def image_path(self): # returns path to image
        if self.tile in config.tiles:
            return config.tiles[self.tile]
        else:
            return "sprites\\tiles\\missingtile.png"

    def update(self):
        self.update_image()
        self.surf = pygame.Surface((tile_wh, tile_wh))
        self.rect = self.surf.get_rect()
        self.rect.x, self.rect.y = self.get_rect_xy()
        self.surf.blit(self.image, (0, 0), (self.offsetx, self.offsety, tile_wh, tile_wh))
        if self.scale != 1: 
            w = self.surf.get_width()
            h = self.surf.get_height()
            self.surf = pygame.transform.scale(self.surf, (int(w*self.scale), int(h*self.scale)))
        self.blit_surf.blit(self.surf, ((self.rect.x, self.rect.y)))

class RoomItemDisplay(UIElement):
    def __init__(self, x, y, tile_map: TileMap, server_view=False):
        super().__init__()
        self.x = x
        self.y = y
        self.w = 330
        self.h = 30
        self.page = 0
        self.rows = 10
        self.tile_map = tile_map
        self.server_view=server_view
        self.absolute = True
        self.buttons = []
        self.outline = None
        self.outline_width = 5

    def delete(self):
        for button in self.buttons:
            button.delete()

    def update_instances(self):
        def get_button_func(button_instance_name):
            if self.server_view:
                def output_func(): pass
            else:
                def output_func():
                    if button_instance_name in self.tile_map.instances:
                        suburb.display_item(Instance(button_instance_name, self.tile_map.instances[button_instance_name]), suburb.map_scene)
                    else: # this is an npc
                        client.request(intent="start_strife")
                        suburb.map_scene()
            return output_func
        for button in self.buttons:
            button.delete()
        # instances and npcs are a dict so we need to convert to list to slice
        all_items = list(self.tile_map.npcs.keys()) + list(self.tile_map.instances.keys())
        display_items = list(all_items)[self.page*self.rows:self.page*self.rows + self.rows]
        if self.outline is not None:
            self.outline.delete()
            self.outline = None
        if len(all_items) > 0:
            outline_element_w = self.w + self.outline_width*2
            outline_element_h = self.h*(len(display_items) + 1) + self.outline_width*2
            self.outline = SolidColor(self.x-self.outline_width, self.y-self.outline_width, outline_element_w, outline_element_h, self.theme.dark)
            self.outline.border_radius = 3
            page_buttons_y = self.y
            def left_button_func():
                self.page -= 1
                self.update_instances()
            def right_button_func():
                self.page += 1
                self.update_instances()
            if self.page != 0:
                left_button = TextButton(self.x, page_buttons_y, self.w//2, self.h, "<-", left_button_func)
                left_button.absolute = True
            else:
                left_button = SolidColor(self.x, page_buttons_y, self.w//2, self.h, self.theme.dark)
            if list(self.tile_map.instances.keys())[(self.page+1)*self.rows:(self.page+1)*self.rows + self.rows] != []:
                right_button = TextButton(self.x+left_button.w, page_buttons_y, self.w-left_button.w, self.h, "->", right_button_func)
                right_button.absolute = True
            else:
                right_button = SolidColor(self.x+left_button.w, page_buttons_y, self.w-left_button.w, self.h, self.theme.dark)
            self.buttons.append(left_button)
            self.buttons.append(right_button)
        for index, item_name in enumerate(display_items):
            y = self.y + self.h*(index+1)
            if item_name in self.tile_map.instances: # this is an instance
                instance = Instance(item_name, self.tile_map.instances[item_name])
                display_name = instance.display_name()
                if not self.server_view:
                    captcha_button = CaptchalogueButton(self.x, y, instance.name, self.tile_map.instances)
                    captcha_button.absolute = True
                else:
                    captcha_button = None
                use_buttons = 0
                if not self.server_view:
                    for i, action_name in enumerate(reversed(instance.item.use)):
                        use_buttons += 1
                        path = f"sprites/item_actions/{action_name}.png"
                        pressed_path = f"sprites/item_actions/{action_name}_pressed.png"
                        if not os.path.isfile(path): path = "sprites/item_actions/generic_action.png"
                        if not os.path.isfile(pressed_path): pressed_path = "sprites/item_actions/generic_action_pressed.png"
                        use_button = Button(self.x+(self.w-(30*(i+1))), y, path, pressed_path, instance.get_action_button_func(action_name, suburb.map_scene))
                        use_button.absolute = True
                        self.buttons.append(use_button)
                main_button_width = self.w
                if captcha_button is not None: main_button_width -= 30
                main_button_width -= 30*use_buttons
                main_button_x = self.x
                if captcha_button is not None: main_button_x += 30
                new_button = TextButton(main_button_x, y, main_button_width, self.h, util.filter_item_name(display_name), get_button_func(instance.name), truncate_text=True)
                new_button.absolute = True 
                self.buttons.append(new_button)
                if captcha_button is not None: self.buttons.append(captcha_button)
            elif item_name in self.tile_map.npcs:
                npc = Npc(item_name, self.tile_map.npcs[item_name])
                display_name = npc.nickname
                new_button = TextButton(self.x, y, self.w, self.h, display_name, get_button_func(npc.name), truncate_text=True)
                new_button.absolute = True
                self.buttons.append(new_button)

class Overmap(UIElement):
    def __init__(self, x, y, map_tiles:list[list[str]], theme=themes.default):
        super().__init__()
        self.x = x
        self.y = y
        self.theme = theme
        self.map_tiles = map_tiles
        self.rotation_surfs = {}
        self.rotation = 0
        self.extra_height = 32 * 9
        self.offsetx = 0
        self.offsety = -self.extra_height
        self.last_mouse_pos: Optional[tuple[int, int]] = None
        self.block_image = pygame.image.load("sprites/overmap/block.png").convert()
        self.block_image = self.convert_to_theme(self.block_image)
        self.block_image.set_colorkey(pygame.Color(0, 0, 0))
        self.water_image = pygame.image.load("sprites/overmap/water.png").convert()
        self.water_image = self.convert_to_theme(self.water_image)
        self.water_image.set_colorkey(pygame.Color(0, 0, 0))
        # self.water_image = self.convert_to_theme(self.water_image)
        self.w = (len(self.map_tiles[0]) + len(self.map_tiles))*16
        self.h = (len(self.map_tiles[0]) + len(self.map_tiles))*8
        self.h += self.extra_height # extra tile height
        self.initialize_map(0)
        update_check.append(self)
        key_check.append(self)

    def initialize_map(self, rotation):
        self.rect = pygame.Rect(0, 0, self.w, self.h)
        self.rect.x = int((SCREEN_WIDTH * self.x) - (self.rect.w / 2))
        self.rect.y = int((SCREEN_HEIGHT * self.y) - (self.rect.h / 2))
        self.rotation_surfs[rotation] = pygame.Surface((self.w, self.h))
        self.rotation_surfs[rotation].fill(self.theme.black)
        match rotation:
            case 90:
                draw_tiles = np.rot90(self.map_tiles, 1, axes=(0, 1))
            case 180:
                draw_tiles = np.rot90(self.map_tiles, 2, axes=(0, 1))
            case 270:
                draw_tiles = np.rot90(self.map_tiles, 3, axes=(0, 1))
            case _:
                draw_tiles = self.map_tiles
        for y, line in enumerate(draw_tiles):
            for x, char in enumerate(reversed(line)):
                overmap_tile = OvermapTile(x, y, int(char), self)
                overmap_tile.blit_surf = self.rotation_surfs[rotation]
                overmap_tile.draw_to_surface()

    def update(self):
        if pygame.mouse.get_pressed()[0]:
            if self.last_mouse_pos is None:
                self.last_mouse_pos = pygame.mouse.get_pos()
            else:
                last_x, last_y = self.last_mouse_pos
                self.last_mouse_pos = pygame.mouse.get_pos()
                current_x, current_y = self.last_mouse_pos
                self.offsetx += current_x - last_x
                self.offsety += current_y - last_y
        else:
            self.last_mouse_pos = None
        try: self.rotation_surfs[self.rotation]
        except KeyError: self.initialize_map(self.rotation)
        screen.blit(self.rotation_surfs[self.rotation],(self.rect.x+self.offsetx, self.rect.y+self.offsety))

    def keypress(self, event):
        match event.key:
            case pygame.K_q: 
                self.rotation -= 90
                if self.rotation < 0: self.rotation = 270
            case pygame.K_e:
                self.rotation += 90
                if self.rotation == 360: self.rotation = 0
            case _: return

class OvermapTile(UIElement):
    def __init__(self, x, y, height:int, overmap: Overmap):
        self.x = x
        self.y = y
        self.height = height
        self.overmap = overmap

    def draw_to_surface(self):
        # each block starts 16 left and 8 down from the last
        # basically It Just Works(TM) don't fucking ask questions
        draw_x = -16
        draw_x += self.overmap.rect.w//2
        draw_x += (len(self.overmap.map_tiles) - len(self.overmap.map_tiles[0])) * -8
        draw_x += self.y * 16
        draw_x -= self.x * 16
        draw_y = self.overmap.extra_height - 16
        draw_y += self.y * 8
        draw_y += self.x * 8
        if self.height == 0:
            self.blit_surf.blit(self.overmap.water_image, ((draw_x, draw_y)))
        else:
            for i in range(self.height):
                self.blit_surf.blit(self.overmap.block_image, ((draw_x, draw_y)))
                draw_y -= 16

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
                suburb.map_scene()
            else:
                ...
        return output_func

class LogWindow(UIElement):
    def __init__(self, last_scene: Optional[Callable], tilemap: Optional[TileMap]=None, draw_console=False, 
                 x=int(SCREEN_WIDTH*0.5), y=0, width=500, lines_to_display=4, fontsize=16, log_list: Optional[list[str]]=None):
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
        if log_list is None:
            util.log_window = self
            self.log_list = None
        else: self.log_list = log_list
        self.scroll_offset = 0
        self.background: Optional[UIElement] = None
        self.console: Optional[InputTextBox] = None
        self.elements: list[UIElement] = []
        self.background_color: Color = self.theme.black
        self.text_color: Color = self.theme.light
        self.active_color: Color = self.theme.light
        self.active_text_color: Color = self.theme.white
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
        self.background = SolidColor(x, self.y, self.width, self.fontsize*self.lines_to_display + self.padding*self.lines_to_display, self.background_color)
        for loop_index, position_index in enumerate(reversed(range(self.lines_to_display))):
            y = self.y + position_index*self.fontsize + position_index*self.padding
            try:
                line = self.log[-loop_index - 1 - self.scroll_offset]
                text = Text(x, y, line)
                text.fontsize = self.fontsize
                text.color = self.text_color
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
            if self.last_scene: self.last_scene()
        if not self.draw_console: return
        console_y = self.y + (self.lines_to_display)*self.fontsize + (self.lines_to_display)*self.padding
        self.console = InputTextBox(x, console_y, self.width, self.fontsize+self.padding)
        self.console.absolute = True
        self.console.enter_func = console_enter_func
        self.console.inactive_color = self.background_color
        self.console.active_color = self.active_color
        self.console.outline_color = None
        self.console.text_color = self.active_text_color
        self.console.fontsize = self.fontsize
        self.console.suffix = ">"
        if self.tilemap is not None: self.tilemap.input_text_box = self.console

    def scroll(self, y: int):
        if self.background is None: return
        if not self.background.is_mouseover(): return
        max_offset = max(len(self.log) - self.lines_to_display, 0)
        self.scroll_offset += y
        if self.scroll_offset < 0: self.scroll_offset = 0
        if self.scroll_offset > max_offset: self.scroll_offset = max_offset
        self.update_logs()

    @property
    def log(self) -> list[str]:
        if self.log_list is None:
            return util.current_log()
        else: return self.log_list

class ItemImage():
    def __new__(cls, x, y, item_name: str):
        image_path = f"sprites\\items\\{item_name}.png"
        if os.path.isfile(image_path):
            return Image(x, y, image_path)
        return None


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
        self.actuate_button_box = SolidColor(0, SCREEN_HEIGHT-self.h, 120 + self.padding*2, self.h, self.theme.dark)
        self.actuate_button_box.outline_color = self.theme.light
        self.actuate_button_box.outline_width = self.padding
        self.actuate_button = TextButton(self.padding, SCREEN_HEIGHT-self.h+self.padding, 120, self.h - self.padding*2, " ACTUATE", suburb.map_scene)
        self.actuate_button.absolute = True
        self.actuate_button.outline_color = self.theme.black
        self.actuate_button.fill_color = self.theme.dark
        self.actuate_button.hover_color = self.theme.light
        self.actuate_button.text_color = self.theme.white
        self.actuate_button.outline_width = self.padding
        self.actuate_button_image = Image(0.15, 0.5, "sprites/computer/little_green_circle.png")
        self.actuate_button_image.bind_to(self.actuate_button)
        # todo: time on bottom right
        self.apps = [self.actuate_button]
        self.open_windows = []

    def bring_to_top(self):
        self.task_bar.bring_to_top()
        self.actuate_button_box.bring_to_top()
        self.actuate_button.bring_to_top()
        self.actuate_button_image.bring_to_top()

class AppIcon(Button):
    def __init__(self, x, y, app_name: str, task_bar: TaskBar):
        self.x = x
        self.y = y
        self.app_name = app_name
        self.task_bar = task_bar
        self.path = f"sprites/computer/apps/{app_name}.png"
        self.window: Optional[Window] = None
        def open_window():
            if len(self.task_bar.open_windows) > 0: return
            if self.window is None:
                self.window = Window(app_name, task_bar, self)
        super().__init__(x, y, self.path, self.path, open_window)
        self.convert = False
        self.invert_on_click = True
        self.double_click = True
        app_label = Text(0.5, 1.2, app_name)
        app_label.color = self.theme.white
        app_label.highlight_color = self.theme.dark
        app_label.bind_to(self)

class Window(SolidColor):
    def __init__(self, app_name: str, task_bar: TaskBar, app_icon: AppIcon):
        self.app_name = app_name
        self.task_bar = task_bar
        self.app_icon = app_icon
        if self not in self.task_bar.open_windows: self.task_bar.open_windows.append(self)
        self.padding = 3
        self.head_height = 40
        self.height = SCREEN_HEIGHT-task_bar.h
        self.width = SCREEN_WIDTH
        self.x = 0
        self.y = 0
        super().__init__(self.x, self.y, self.width, self.height, suburb.current_theme().light)
        self.viewport = SolidColor(self.padding, self.head_height, self.width - self.padding*2, self.height - (self.padding+self.head_height), self.theme.white)
        self.icon_path = f"sprites/computer/apps/{app_name}.png"
        self.icon = Image(self.x+self.padding, self.y+self.padding, self.icon_path, convert=False)
        self.icon.absolute = True
        self.icon.scale = 0.25
        self.label = Text(self.x + 32 + self.padding*2, self.y+self.padding, app_name)
        self.label.absolute = True
        self.label.color = self.theme.white
        self.label.outline_color = self.theme.black
        self.label.fontsize = 28
        self.xbutton = TextButton(self.width-self.head_height-self.padding, self.padding, self.head_height - self.padding*2, self.head_height - self.padding*2, "x", self.delete)
        self.xbutton.absolute = True
        self.xbutton.outline_color = self.theme.light
        self.xbutton.fill_color = self.theme.light
        self.xbutton.text_color = self.theme.white
        self.xbutton.fontsize = 24
        self.initialize_viewport()
        self.task_bar.bring_to_top()

    def initialize_viewport(self):
        for element in self.viewport.bound_elements.copy():
            element.delete()
        match self.app_name:
            case "gristTorrent":
                suburb.gristtorrent(self)
            case "Sburb":
                sburbserver.sburb(self)

    def reload(self):
        app_name = self.app_name
        task_bar = self.task_bar
        app_icon = self.app_icon
        self.delete()
        self.__init__(app_name, task_bar, app_icon)

    def delete(self):
        self.app_icon.window = None
        self.viewport.delete()
        self.icon.delete()
        self.label.delete()
        self.xbutton.delete()
        if self in self.task_bar.open_windows: self.task_bar.open_windows.remove(self)
        super().delete()

class Vial(SolidColor):
    def __init__(self, x, y, w: int, griefer: Griefer, vial_type: str):
        self.x = x
        self.y = y
        self.w = w
        self.griefer = griefer
        self.h = 8
        self.vial_y_offset = 0
        self.vial_type = vial_type
        super().__init__(x, y, w, self.h, themes.default.white)
        self.padding = 1
        self.border_radius = 2
        self.outline_width = 3
        self.outline_color = themes.default.black
        self.name = config.vials[self.vial_type]["name"]
        self.gel_vial: bool = config.vials[self.vial_type]["gel_vial"]
        self.segmented_vial: bool = config.vials[self.vial_type]["segmented_vial"]
        self.fill_color: Color = config.vials[self.vial_type]["fill_color"]
        self.shade_color: Color = config.vials[self.vial_type]["shade_color"]
        self.middle_color: Optional[Color] = config.vials[self.vial_type]["middle_color"]
        self.make_fill_surf()
        self.label = Text(0.5, 2, self.name)
        self.label.bind_to(self)
        self.label.color = self.fill_color
        self.label.fontsize = 8

    def make_fill_surf(self):
        fill_width = self.w-self.padding*4
        fill_height = self.h-self.padding*2
        shade_surf = pygame.Surface((fill_width, fill_height))
        shade_surf.fill(self.shade_color)
        fill_surf = pygame.Surface((fill_width, fill_height - 1))
        fill_surf.fill(self.fill_color)
        shade_surf.blit(fill_surf, (0, 0))
        self.fill_surf = shade_surf
        if self.middle_color is not None:
            middle_surf = pygame.Surface((fill_width, 1))
            middle_surf.fill(self.middle_color)
            self.fill_surf.blit(middle_surf, (0, 2))
        if self.segmented_vial:
            segments = 20
            segmented_surf = pygame.Surface((2, fill_height))
            segmented_surf.fill(Color(0, 0, 0))
            midpoint_x = fill_height//2 - round(fill_width/segments/2)
            for i in range(segments):
                print(i)
                xdiff = (i+1) * round(fill_width/segments)
                self.fill_surf.blit(segmented_surf, (midpoint_x+xdiff, 0))
                self.fill_surf.blit(segmented_surf, (midpoint_x-xdiff, 0))
            self.fill_surf = self.fill_surf.convert()
            self.fill_surf.set_colorkey(Color(0, 0, 0))

    def update(self):
        if self.gel_vial: 
            self.rect_x_offset = -int((1 - self.filled_percent) * self.w)
            self.label.rect_x_offset = -self.rect_x_offset
        super().update()
        # unusuable vial fill
        unusable_fill_width = int(self.fill_surf.get_width() * self.filled_percent)
        unusable_fill_rect = pygame.Rect(0, 0, unusable_fill_width, self.fill_surf.get_height())
        unusable_fill_surf = pygame.Surface((unusable_fill_width, self.fill_surf.get_height()))
        unusable_fill_surf.fill(Color(255, 0, 0))
        # usable vial fill
        fill_width = int(self.fill_surf.get_width() * self.usable_filled_percent)
        fill_rect = pygame.Rect(0, 0, fill_width, self.fill_surf.get_height())
        # blit coords
        # offset by unusable fill width because vial hasn't changed yet
        if self.gel_vial: x_offset = self.fill_surf.get_width() - unusable_fill_width
        else: x_offset = 0
        blit_x = self.rect.x+self.padding*2+x_offset
        blit_y = self.rect.y+self.padding
        self.blit_surf.blit(unusable_fill_surf, (blit_x, blit_y), unusable_fill_rect)
        self.blit_surf.blit(self.fill_surf, (blit_x, blit_y), fill_rect)

    @property
    def usable_filled_percent(self) -> float:
        return min(self.griefer.get_usable_vial(self.vial_type) / self.griefer.get_maximum_vial(self.vial_type), 1)

    @property
    def filled_percent(self) -> float:
        return self.griefer.get_vial(self.vial_type) / self.griefer.get_maximum_vial(self.vial_type)   

class Symbol(Image):
    player_image_crop = (144, 98, 114, 196)

    def __init__(self, x, y, parts: dict):
       self.parts = parts
       self.base = parts["base"]
       self.shoes = parts["shoes"]
       self.pants = parts["pants"]
       self.shirt = parts["shirt"]
       self.coat = parts["coat"]
       self.mouth = parts["mouth"]
       self.eyes = parts["eyes"]
       self.hair = parts["hair"]
       self.horns = parts["horns"]
       self.color = parts["color"]
       self.style_dict = parts["style_dict"]
       super().__init__(x, y, "")
       self.load_image("")

    @property
    def light(self):
        r, g, b = self.color[0], self.color[1], self.color[2]
        return pygame.Color(r, g, b)
    
    @property
    def dark(self):
        sub = 30
        for color in self.color:
            if color < 20: sub+= 20
        r, g, b = self.color[0]-sub, self.color[1]-sub, self.color[2]-sub
        r, g, b = max(r, 0), max(g, 0), max(b, 0)
        return pygame.Color(r, g, b)

    def get_image_path(self, part, item_name):
        style = self.style_dict[part]
        if style == "standard":
            return f"sprites/symbol/{part}/{item_name}.png"
        else:
            return f"sprites/symbol/{part}/{item_name}-{style}.png"

    def load_image(self, path: str):
        base = pygame.image.load(self.get_image_path("base", self.base)).convert_alpha()
        shoes = pygame.image.load(self.get_image_path("shoes", self.shoes)).convert_alpha()
        pants = pygame.image.load(self.get_image_path("pants", self.pants)).convert_alpha()
        shirt = pygame.image.load(self.get_image_path("shirt", self.shirt)).convert_alpha()
        coat = pygame.image.load(self.get_image_path("coat", self.coat)).convert_alpha()
        mouth = pygame.image.load(self.get_image_path("mouth", self.mouth)).convert_alpha()
        eyes = pygame.image.load(self.get_image_path("eyes", self.eyes)).convert_alpha()
        hair = pygame.image.load(self.get_image_path("hair", self.hair)).convert_alpha()
        horns = pygame.image.load(self.get_image_path("horns", self.horns)).convert_alpha()
        if self.base == "kid":
            eyes = pygame.PixelArray(eyes)
            eyes.replace(pygame.Color(255, 186, 41), pygame.Color(255, 255, 255))
            eyes = eyes.make_surface()
        elif self.base == "troll":
            eyes = pygame.PixelArray(eyes)
            eyes.replace(pygame.Color(255, 255, 255), pygame.Color(255, 186, 41))
            eyes = eyes.make_surface()
            hair = pygame.PixelArray(hair)
            hair.replace(pygame.Color(255, 255, 255), pygame.Color(1, 1, 1))
            hair = hair.make_surface()
        coat_back_path = f"sprites/symbol/coat-backs/{self.coat}-{self.style_dict['coat']}.png"
        if os.path.isfile(coat_back_path):
            coatback = pygame.image.load(coat_back_path).convert_alpha()
            coatback.blit(base, (0, 0))
            base = coatback
        base.blit(shoes, (0, 0))
        base.blit(pants, (0, 0))
        base.blit(shirt, (0, 0))
        base.blit(hair, (0, 0))
        base.blit(coat, (0, 0))
        base.blit(horns, (0, 0))
        base.blit(mouth, (0, 0))
        base.blit(eyes, (0, 0))
        base = pygame.PixelArray(base)
        base.replace(themes.default.light, self.light)
        base.replace(themes.default.dark, self.dark)
        base.replace(pygame.Color(0, 0, 0), pygame.Color(1, 1, 1))
        base = base.make_surface()
        return base
    
    def collidepoint(self, pos):
        x, y, w, h = self.player_image_crop
        x += self.rect.x
        y += self.rect.y
        hitbox_rect = pygame.Rect(x, y, w, h)
        return hitbox_rect.collidepoint(pos)

class StateIcon(Image):
    tooltip_padding = 5
    def __init__(self, x, y, griefer: "Griefer", state_name: str):
        path = f"sprites/strife/states/{state_name}.png"
        if not os.path.isfile(path):
            path = "sprites/strife/states/unknown_state.png"
        super().__init__(x, y, path)
        self.griefer = griefer
        self.state_name = state_name
        self.popup: Optional[SolidColor] = None
    
    def update(self):
        super().update()
        if not self.is_mouseover() and self.popup is not None: 
            self.popup.delete()
            self.popup = None
        if self.is_mouseover() and self.popup is None:
            x, y = pygame.mouse.get_pos()
            tooltip = self.griefer.get_state_tooltip(self.state_name)
            popup_text = Text(0.5, 0.5, f"{self.state_name.upper()} ({round(self.griefer.get_state_potency(self.state_name), 1)}): {tooltip}")
            popup_text.fontsize = 14
            popup_text.color = self.theme.dark
            self.popup = SolidColor(x, y, popup_text.get_width()+self.tooltip_padding*2, popup_text.fontsize+self.tooltip_padding*2, self.theme.white)
            self.popup.outline_color = self.theme.dark
            self.popup.follow_mouse = True
            self.popup.rect_x_offset = 10
            popup_text.bring_to_top()
            popup_text.bind_to(self.popup)

class GrieferElement(UIElement):
    griefer: Griefer
    vials: dict[str, Vial]
    state_icons: list[StateIcon]
    surf: Union[pygame.Surface, pygame.surface.Surface]
    hover_intensity = 30

    def onclick(self, clicked:bool):
        if clicked:
            self.griefer.strife.click_griefer(self.griefer)

    def add_vial(self, vial_type):
        if vial_type not in self.vials:
            new_vial = Vial(0.5, 0, 150, self.griefer, vial_type)
            new_vial.absolute = False
            if isinstance(self, Enemy):
                new_vial.rect_y_offset = -25
            else:
                new_vial.rect_y_offset = 50
            new_vial.rect_y_offset -= len(self.vials) * 30
            new_vial.bind_to(self)
            self.vials[vial_type] = new_vial

    def make_labels(self):
        if isinstance(self, Enemy):
            x, y = 0.5, 1
        else:
            x, y = 0.47, 0.7
        self.name_label = Text(x, y, self.griefer.nickname)
        self.name_label.color = self.theme.dark
        self.name_label.fontsize = 20
        self.name_label.rect_y_offset = 30
        self.name_label.bind_to(self)
        self.power_label = Text(x, y, f"POWER: {self.griefer.power}")
        self.power_label.color = self.theme.dark
        self.power_label.fontsize = 10
        self.power_label.rect_y_offset = 44
        self.power_label.bind_to(self)

    def get_duration_label_func(self, state_name):
        def label_func():
            if state_name not in self.griefer.states: return ""
            else: return f"{self.griefer.get_state_duration(state_name)}"
        return label_func

    def make_state_boxes(self):
        for state_icon in self.state_icons.copy():
            self.state_icons.remove(state_icon)
            state_icon.delete()
        if len(self.griefer.states) == 0: return
        for state_name in self.griefer.states:
            if len(self.state_icons) > 0:
                x, y = 24, 0
                absolute = True
                binding = self.state_icons[-1]
            else:
                if isinstance(self, Enemy):
                    x, y = 0.5, 1
                else:
                    x, y = 0.47, 0.7
                absolute = False
                binding = self
            new_state_icon = StateIcon(x, y, self.griefer, state_name)
            new_state_icon.absolute = absolute
            new_state_icon.bind_to(binding)
            duration_label = Text(0.5, 1.5, "")
            duration_label.text_func = self.get_duration_label_func(state_name)
            duration_label.color = self.theme.dark
            duration_label.fontsize = 14
            duration_label.bind_to(new_state_icon)
            self.state_icons.append(new_state_icon)
        first_element = self.state_icons[0]
        first_element.rect_y_offset = 60
        first_element.rect_x_offset = (len(self.state_icons) - 1) * -12

    def update(self):
        super().update()
        if self.is_mouseover() and self.griefer.strife.selected_skill is not None:
            hover_surf = self.surf.copy()
            hover_surf.fill((self.hover_intensity, self.hover_intensity, self.hover_intensity), None, pygame.BLEND_ADD)
            hover_surf.set_colorkey((self.hover_intensity, self.hover_intensity, self.hover_intensity))
            self.blit_surf.blit(hover_surf, (self.rect.x, self.rect.y))
        for state_icon in self.state_icons.copy():
            if not self.griefer.is_state_affected(state_icon.state_name):
                self.state_icons.remove(state_icon)
                state_icon.delete()
        if len(self.griefer.states) != len(self.state_icons): self.make_state_boxes()

class Enemy(GrieferElement, Image):
    def __init__(self, x, y, griefer: Griefer):
        self.vials: dict[str, Vial] = {}
        self.state_icons: list[StateIcon] = []
        self.griefer = griefer
        path = f"sprites/strife/{griefer.type}.png"
        super().__init__(x, y, path)
        grist_type = griefer.grist_type or "build"
        new_color = config.gristcolors[grist_type]
        self.convert_colors.append((themes.default.dark, new_color)) 
        self.add_vial("vim")
        self.add_vial("hp")
        self.make_labels()
        click_check.append(self)

class PlayerGriefer(GrieferElement, Symbol):
    def __init__(self, x, y, griefer: Griefer):
        super().__init__(x, y, griefer.symbol_dict)
        self.vials: dict[str, Vial] = {}
        self.state_icons: list[StateIcon] = []
        self.griefer = griefer
        self.add_vial("hp")
        self.make_labels()
        click_check.append(self)

def make_grist_display(x, y, w: int, h: int, padding: int, 
                       grist_name: str, grist_amount: int, 
                       cache_limit: int, theme: themes.Theme, 
                       box_color: Optional[pygame.Color]=None, 
                       filled_color: Optional[pygame.Color]=None,
                       label_color: Optional[pygame.Color]=None,
                       use_grist_color=False) -> SolidColor:
    box_color = box_color or theme.dark
    if use_grist_color: filled_color = config.gristcolors[grist_name]
    filled_color = filled_color or theme.light
    label_color = label_color or theme.light
    grist_box = SolidColor(x,  y, w, h, box_color)
    grist_box.border_radius = 2
    grist_image_path = f"sprites/grists/{grist_name}.png"
    anim_grist_image_path = f"sprites/grists/{grist_name}-1.png"
    if os.path.isfile(grist_image_path) or os.path.isfile(anim_grist_image_path):
        x = 0.1
        y = 0.5
        # grist images are 48x48, we wanna make sure they are scaled to the box plus some padding
        grist_image_scale = min(h, w//6)/(48+padding)
        if os.path.isfile(anim_grist_image_path):
            grist_image = Image(x, y, f"sprites/grists/{grist_name}")
            grist_image.animated = True
            grist_image.animframes = 4
        else:
            grist_image = Image(x, y, grist_image_path)
        grist_image.scale = grist_image_scale
        grist_image.bind_to(grist_box)
    bar_background = SolidColor(0.2, 0.25, w//1.3, h//3.5, box_color)
    bar_background.border_radius = 2
    bar_background.outline_color = theme.black
    bar_background.absolute = False
    bar_background.bind_to(grist_box)
    filled_bar_width = int((w//1.3 - 4) * min(grist_amount, cache_limit)/cache_limit)
    bar_filled = SolidColor(2, 2, filled_bar_width, h//3.5 - 4, filled_color)
    bar_filled.bind_to(bar_background)
    bar_label = Text(0.5, 2.2, str(grist_amount))
    bar_label.color = label_color
    bar_label.fontsize = 12
    bar_label.bind_to(bar_background)
    return grist_box

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

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for sprite in click_check:
                #sprites with click events will know if the click is on them or not
                sprite.onclick(sprite.collidepoint(event.pos))

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
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

    for sprite in always_on_top_check:
        sprite.update()

    pygame.display.flip()

    #fps cap
    clock.tick(FPS_CAP)
    return True
