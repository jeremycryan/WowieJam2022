from primitives import Pose
from spice_rack import SpiceRack
import constants as c
import pygame
from pot import Pot
from image_manager import ImageManager
from bell import Bell
from customer_queue import CustomerQueue
from ingredient import Ingredient
from robot import Robot
import math

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
        self.pot = Pot(self)
        self.rack = SpiceRack((c.WINDOW_WIDTH*0.5, c.WINDOW_HEIGHT - 120), self.pot)
        self.rack.add_ingredients({
            key: 3 for key in Ingredient.ingredient_dict
        })
        self.bell = Bell((c.WINDOW_WIDTH * 0.6, c.WINDOW_HEIGHT * 0.62), self)
        super().__init__(game)

        self.item_counter = ImageManager.load("assets/images/item_counter.png")
        self.item_counter = pygame.transform.scale(self.item_counter, (c.WINDOW_WIDTH, self.item_counter.get_height() * (c.WINDOW_WIDTH/self.item_counter.get_width())))
        self.counter = ImageManager.load("assets/images/counter_back.png")
        self.counter = pygame.transform.scale(self.counter, (c.WINDOW_WIDTH, self.counter.get_height() * (c.WINDOW_WIDTH/self.counter.get_width())))
        self.queue = CustomerQueue(self)

        self.background = ImageManager.load("assets/images/background.png")

        self.hfont = pygame.font.Font("assets/fonts/corbel.ttf", 20)
        self.hsurf = self.hfont.render("SERVE", 1, (0, 0, 0))

        self.particles = []
        self.fronticles = []
        self.robot = Robot(self)

        self.since_shake = 0
        self.shake_amt = 0

    def update_shake(self, dt, events):
        self.shake_amt *= 0.005**dt
        self.shake_amt -= 15*dt
        if self.shake_amt < 0:
            self.shake_amt = 0
        self.since_shake += dt

    def get_shake_offset(self):
        x = math.cos(self.since_shake * 20) * self.shake_amt
        y = math.cos(self.since_shake * 20) * self.shake_amt /2
        return (x, y)

    def add_particle(self, particle, front=False):
        if front:
            self.fronticles.append(particle)
            return
        self.particles.append(particle)

    def draw_particles(self, surface, offset=(0, 0)):
        for particle in self.particles:
            particle.draw(surface, offset)

    def draw_fronticles(self, surface, offset=(0, 0)):
        for fronticle in self.fronticles:
            fronticle.draw(surface, offset)

    def shake(self, amt=15):
        self.since_shake = 0
        self.shake_amt = amt

    def draw(self, surface, offset=(0, 0)):
        surface.blit(self.background, offset)
        offset = self.get_shake_offset()
        self.queue.draw(surface, offset)
        surface.blit(self.counter, (0, c.WINDOW_HEIGHT - self.counter.get_height()))

        self.robot.draw_dialog(surface, offset)

        self.draw_counter(surface, offset)
        self.bell.draw(surface, offset)
        self.queue.draw_plates(surface, offset)
        self.pot.draw(surface, offset)

        self.robot.draw(surface, offset=(0, 0))
        self.rack.draw(surface, offset)
        self.draw_fronticles(surface, offset)

        #surface.blit(self.hsurf, (10, 10))

    def draw_counter(self, surface, offset=(0, 0)):

        surface.blit(self.item_counter, (0, c.WINDOW_HEIGHT - self.item_counter.get_height()))

    def update(self, dt, events):
        self.queue.update(dt, events)
        self.rack.update(dt, events)
        self.pot.update(dt, events)
        self.update_shake(dt, events)
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.rack.add_ingredients({
                    "sugar": 1,
                })
        self.bell.update(dt, events)
        for particle in self.particles[:]:
            particle.update(dt, events)
            if particle.destroyed:
                self.particles.remove(particle)
        for particle in self.fronticles[:]:
            particle.update(dt, events)
            if particle.destroyed:
                self.fronticles.remove(particle)
        self.robot.update(dt, events)

    def happiness_flare(self, happiness):
        pass
        #self.hsurf = self.hfont.render(f"HAPPINESS: {happiness}",1,(0, 0, 0))