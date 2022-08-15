import constants as c
from ingredient import Ingredient
from primitives import Pose
import pygame
import math
import time
from flavor_preview import FlavorPreview
from particle import FoodParticle
from image_manager import ImageManager
from sound_manager import SoundManager

class SpiceRack:

    X_SPACING = 0
    SMALL_RECT = (90, 90)
    LARGE_RECT = (200, 200)

    def __init__(self, pos=(0, 0), pot=None):
        Ingredient.load_spices_from_yaml()
        self.position = Pose(pos)
        self.ingredients = {}
        self.entries = []
        self.initialize_entries()
        self.pot = pot

        self.click_sound = SoundManager.load("assets/sounds/item click.wav")
        self.hover_sound = SoundManager.load("assets/sounds/item hover.wav")
        self.hover_sound.set_volume(0.5)

    def hovered(self):
        for entry in self.entries:
            if entry.hovered():
                return entry.key
        return False

    def add_ingredients(self, amounts):
        for key in amounts:
            if not key in Ingredient.ingredient_dict:
                continue
            if not key in self.ingredients:
                self.ingredients[key] = 0
            self.ingredients[key] += amounts[key]
        self.initialize_entries(False)

    def get_quantity(self, key):
        if not key in self.ingredients:
            return 0
        return self.ingredients[key]

    def get_quantities(self):
        return self.ingredients.copy()

    def pop_key(self, key):
        if not self.get_quantity(key):
            return None
        self.ingredients[key] -= 1
        return Ingredient.from_key(key)

    def sorted_keys(self):
        keys = [key for key in Ingredient.ingredient_dict]
        return sorted(keys, key=lambda x: c.PRINTABLES.index(Ingredient.primary_flavor(x)[1]) * 10000 - Ingredient.primary_flavor_intensity(x))

    def update(self, dt, events):
        for entry in self.entries:
            entry.update(dt, events)
        self.set_target_positions()
        self.update_quantities()

    def draw(self, surface, offset=(0, 0)):
        offset = (0, 0)
        for entry in self.entries:
            entry.draw(surface, offset=offset)

    def update_quantities(self):
        for entry in self.entries[:]:
            if not self.get_quantity(entry.key):
                self.entries.remove(entry)

    def initialize_entries(self, snap=True):
        snap = ()
        for key in self.sorted_keys():
            if key not in [entry.key for entry in self.entries]:
                self.entries.append(SpiceEntry(key, self))
                snap += (key,)
        self.set_target_positions(snap)

    def default_width(self):
        num = len(self.entries)
        width = num * self.SMALL_RECT[0] + (num) * self.X_SPACING
        return width

    def add_to_pot(self, key):
        self.pot.add_ingredient(Ingredient.from_key(key))
        self.pot.frame.add_particle(FoodParticle(key, self.pot.frame))
        self.click_sound.play()

    def set_target_positions(self, snap=()):
        num = len(self.entries)
        width = num * self.SMALL_RECT[0] + (num - 1) * self.X_SPACING
        if self.hovered():
            width += self.LARGE_RECT[0] - self.SMALL_RECT[0]
        x = self.position.x - width//2 + self.SMALL_RECT[0]//2
        for i, item in enumerate(self.entries):
            if item.key == self.hovered():
                x += (self.LARGE_RECT[0] - self.SMALL_RECT[0])/2
            item.target_position = Pose((x, self.position.y))
            if item.key != self.hovered():
                item.target_position += Pose((math.sin(i * 0.8 + time.time() *4), math.cos(i * 0.8 + time.time() * 4))) * 0

            item.target_scale = self.SMALL_RECT[0]/self.LARGE_RECT[0]
            if item.key == self.hovered():
                item.target_scale = 1
            if item.key in snap:
                item.scale = 0
                item.position = item.target_position.copy()
            x += self.SMALL_RECT[0] + self.X_SPACING
            if item.key == self.hovered():
                x += (self.LARGE_RECT[0] - self.SMALL_RECT[0])/2



class SpiceEntry:

    QUANTITY_FONT = None
    DESCRIPTION_FONT = None

    def __init__(self, key, rack):
        self.surface = pygame.transform.scale(Ingredient.get_surf(key), rack.LARGE_RECT)
        self.rack = rack
        self.key = key
        self.position = Pose((0, 0))
        self.target_position = self.position.copy()
        self.scale = 0.5
        self.target_scale = 0.5
        if not SpiceEntry.QUANTITY_FONT:
            SpiceEntry.QUANTITY_FONT = pygame.font.Font("assets/fonts/AllTheWayToTheSun.ttf", 25)
        if not SpiceEntry.DESCRIPTION_FONT:
            SpiceEntry.DESCRIPTION_FONT = pygame.font.Font("assets/fonts/corbel.ttf", 15)
        self.squash = 0
        self.surface = pygame.transform.scale(self.surface, self.rack.LARGE_RECT)
        self.preview = FlavorPreview(Ingredient.ingredient_dict[self.key]["flavors"],self.target_position.get_position(),radius=50)
        self.was_hovered = False
        self.hover_back = ImageManager.load("assets/images/item_hover.png")
        self.hover_back.set_alpha(175)

        self.name_surf = SpiceEntry.QUANTITY_FONT.render(key.upper(), 1, (255, 255, 255))
        self.description_chars = {char:SpiceEntry.DESCRIPTION_FONT.render(char, 1, (255, 255, 255)) for char in c.PRINTABLES}

        self.taste_icon = ImageManager.load(c.FLAVOR_ICONS[Ingredient.primary_flavor(self.key)])

    def update(self, dt, events):
        self.position += (self.target_position - self.position)*dt*20
        if self.scale < self.target_scale:
            self.scale += 3*dt
            if self.scale > self.target_scale:
                self.scale = self.target_scale
        if self.scale > self.target_scale:
            self.scale -= 3*dt
            if self.scale < self.target_scale:
                self.scale = self.target_scale
        self.scale += (self.target_scale - self.scale) * dt * 15
        self.squash -= 2.5*dt
        self.squash *= 0.5**dt
        if self.squash < 0:
            self.squash = 0

        if self.hovered():
            self.preview.update(dt, events)
            if self.was_hovered:
                self.preview.set_position((self.target_position.copy() + Pose((0, -120))).get_position())
            else:
                self.rack.hover_sound.play()
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.add_to_pot()
        self.was_hovered = self.hovered()

    def add_to_pot(self):
        self.squash = 1
        #self.rack.ingredients[self.key] -= 1
        self.rack.add_to_pot(self.key)

        d = self.rack.pot.frame.ingredients_used
        if not self.key in d:
            d[self.key] = 1
        else:
            d[self.key] += 1

    def width(self):
        return self.scale * self.surface.get_width()

    def height(self):
        return self.scale * self.surface.get_height()

    def quantity(self):
        return self.rack.get_quantity(self.key)

    def draw_quantity(self, surface, offset=(0, 0)):
        surf = self.taste_icon
        scale = (self.scale*0.5 + 0.5) * 0.2
        w = surf.get_width() * scale
        h = surf.get_height() * scale
        surf = pygame.transform.scale(surf, (w, h))
        x = self.position.x + offset[0] - self.width()//2 + 5
        y = self.position.y + offset[1] + self.height()//2 - h
        surface.blit(surf, (x, y))

    def hovered(self):
        mpos = pygame.mouse.get_pos()
        if mpos[0] < self.position.x - self.width()/2:
            return False
        if mpos[0] > self.position.x + self.width()/2:
            return False
        if mpos[1] < self.position.y - self.surface.get_height()/2:
            return False
        if mpos[1] > self.position.y + self.surface.get_height()/2:
            return False
        return True

    def draw(self, surface, offset=(0, 0)):
        w = self.width() * (1 - self.squash) + self.width() * self.squash * math.sin(self.squash * math.pi * 0.85) + 1
        h = (self.width() * self.height())/w
        x = self.position.x + offset[0] - w//2
        y = self.position.y + offset[1] - h//2

        if self.hovered():
            self.draw_ingredient_preview(surface, offset=offset)

        scaled = pygame.transform.scale(self.surface, (w, h))
        surface.blit(scaled, (x, y))
        self.draw_quantity(surface, offset)

    def draw_ingredient_preview(self, surface, offset=(0, 0)):
        if self.preview.position.x == 0 or self.preview.position.y == 0:
            return
        w = self.hover_back.get_width()
        h = self.hover_back.get_height()
        x = self.preview.position.x + offset[0] - w //2
        y = self.preview.position.y + offset[1] - h//2 - 30
        surface.blit(self.hover_back, (x, y))

        offset = (Pose(offset) + Pose((-70, -35))).get_position()
        self.preview.draw(surface, offset)
        surface.blit(self.name_surf, (x + 175 - self.name_surf.get_width()//2, y + 15))
        self.draw_description(surface, offset)

    def draw_description(self, surface, offset=(0, 0)):
        w = 120
        height = 50
        spacing = 16

        offset = (Pose(offset) + self.preview.position + Pose((50, -30))).get_position()

        self.dialog = Ingredient.ingredient_dict[self.key]["description"] if "description" in Ingredient.ingredient_dict[self.key]  else "unknown ingredient"
        if self.dialog is None:
            self.dialog = "unknown ingredient"
        words = self.dialog.split(" ")
        lines = []
        current_line = ""
        line_width = 0
        for word in words:
            word_width = sum(self.description_chars[char].get_width() for char in word)
            if line_width + word_width > w:
                lines.append(current_line)
                current_line = ""
                line_width = 0

            current_line += word + " "
            line_width += word_width + self.description_chars[" "].get_width()
        if current_line:
            lines.append(current_line)

        x0 = offset[0]
        y0 = offset[1] + height / 2 + 5
        y0 -= spacing * len(lines) / 2
        for line in lines:
            line_width = sum([self.description_chars[char].get_width() for char in line])
            x = x0 - line_width // 2 + w // 2
            for i, char in enumerate(line):
                xp, yp = x, y0
                yp += math.sin(time.time() * -10 + i * 0.9) * 1
                surface.blit(self.description_chars[char], (xp, yp))
                x += self.description_chars[char].get_width()
            y0 += spacing

        #pygame.draw.rect(surface, (255, 0, 0), (x, y, w, h), 2)
