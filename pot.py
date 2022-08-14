from ingredient import Ingredient
from flavor_preview import FlavorPreview
from image_manager import ImageManager
import pygame

import constants as c
from particle import PanPoof

class Pot:
    def __init__(self, frame):
        self.flavors = {key: 100/3 for key in c.FLAVORS}
        self.ingredient_count = 0
        self.preview = FlavorPreview(self.flavors, (350, 250),radius=180)
        self.frame = frame

        self.bowl_front = ImageManager.load("assets/images/bowl_front.png")
        self.bowl_front = pygame.transform.scale(self.bowl_front, (self.bowl_front.get_width() * c.WINDOW_WIDTH/1920 * 1.3, self.bowl_front.get_height() * c.WINDOW_HEIGHT/1280 * 1.3))
        self.bowl_back = ImageManager.load("assets/images/bowl_back.png")
        self.bowl_back = pygame.transform.scale(self.bowl_back, (self.bowl_back.get_width() * c.WINDOW_WIDTH/1920 * 1.3, self.bowl_back.get_height() * c.WINDOW_HEIGHT/1280 * 1.3))

    def add_ingredient(self, ingredient):
        for flavor in self.flavors:
            if flavor not in ingredient.flavors:
                continue
            self.flavors[flavor] = self.flavors[flavor] + ingredient.flavors[flavor] - 100/3
        self.ingredient_count += 1
        self.normalize_flavors()
        self.preview.update_flavors(self.flavors)

    def normalize_flavors(self):
        for flavor in self.flavors:
            if self.flavors[flavor] < 0:
                self.flavors[flavor] = 0
        total = 0
        for flavor in self.flavors:
            total += self.flavors[flavor]
        for flavor in self.flavors:
            self.flavors[flavor] *= 100/total

    def empty(self):
        self.flavors = {key: 100 / 3 for key in c.FLAVORS}
        self.ingredient_count = 0
        self.preview.update_flavors(self.flavors)
        for particle in self.frame.particles[:]:
            particle.destroy()
            if particle.food:
                for i in range(10):
                    self.frame.particles.append(PanPoof(particle.position.get_position(),color=128))
        self.frame.robot.pop_up()
        self.preview.clear_goal_vis()

    def update(self, dt, events):
        self.preview.update(dt, events)

    def draw(self, surface, offset=(0, 0)):
        self.preview.draw(surface, offset)

        surface.blit(self.bowl_back, (63 + offset[0], 415 + offset[1]))

        self.frame.draw_particles(surface, offset)

        surface.blit(self.bowl_front, (60 + offset[0], 430 + offset[1]))