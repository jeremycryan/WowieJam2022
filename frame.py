from spice_rack import SpiceRack
import constants as c
import pygame
from pot import Pot
from image_manager import ImageManager
from bell import Bell
from customer_queue import CustomerQueue
from ingredient import Ingredient

class Frame:
    def __init__(self, game):
        self.game = game
        self.done = False

    def load(self):
        pass

    def update(self, dt, events):
        pass

    def draw(self, surface, offset=(0, 0)):
        surface.fill((0, 0, 0))

    def next_frame(self):
        return Frame()


class GameFrame(Frame):
    def __init__(self, game):
        self.pot = Pot()
        self.rack = SpiceRack((c.WINDOW_WIDTH*0.5, c.WINDOW_HEIGHT - 120), self.pot)
        self.rack.add_ingredients({
            key: 3 for key in Ingredient.ingredient_dict
        })
        self.bell = Bell((c.WINDOW_WIDTH * 0.6, c.WINDOW_HEIGHT * 0.65), self)
        super().__init__(game)

        self.item_counter = ImageManager.load("assets/images/item_counter.png")
        self.item_counter = pygame.transform.scale(self.item_counter, (c.WINDOW_WIDTH, self.item_counter.get_height() * (c.WINDOW_WIDTH/self.item_counter.get_width())))
        self.counter = ImageManager.load("assets/images/counter_back.png")
        self.counter = pygame.transform.scale(self.counter, (c.WINDOW_WIDTH, self.counter.get_height() * (c.WINDOW_WIDTH/self.counter.get_width())))
        self.queue = CustomerQueue(self)

        self.background = ImageManager.load("assets/images/background.png")

        self.hfont = pygame.font.Font("assets/fonts/corbel.ttf", 20)
        self.hsurf = self.hfont.render("SERVE",1,(0, 0, 0))


    def draw(self, surface, offset=(0, 0)):
        surface.blit(self.background, (0, 0))
        self.queue.draw(surface, offset)
        surface.blit(self.counter, (0, c.WINDOW_HEIGHT - self.counter.get_height()))
        surface.blit(self.item_counter, (0, c.WINDOW_HEIGHT - self.item_counter.get_height()))
        self.bell.draw(surface, offset)
        self.pot.draw(surface, offset)
        self.rack.draw(surface, offset)

        surface.blit(self.hsurf, (10, 10))


    def update(self, dt, events):
        self.queue.update(dt, events)
        self.rack.update(dt, events)
        self.pot.update(dt, events)
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.rack.add_ingredients({
                    "sugar": 1,
                })
        self.bell.update(dt, events)

    def happiness_flare(self, happiness):
        self.hsurf = self.hfont.render(f"HAPPINESS: {happiness}",1,(0, 0, 0))