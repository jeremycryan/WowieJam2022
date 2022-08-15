from particle import TintParticle, LifeParticle
from primitives import Pose
from spice_rack import SpiceRack
import constants as c
import pygame
from pot import Pot
from image_manager import ImageManager
from bell import Bell
from customer_queue import CustomerQueue, Customer
from ingredient import Ingredient
from robot import Robot
import math
import time

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

        self.lives = 3

        self.fronticles.append(TintParticle(color=(0, 0, 0)))

        self.shade = pygame.Surface((c.WINDOW_WIDTH, c.WINDOW_HEIGHT))
        self.shade.fill((0, 0, 0))
        self.shade_alpha = 0

        Customer.COUNT = -2

        self.num_served = 0
        self.total_rating = 0
        self.total_time_save = 0

        self.ingredients_used = {}

    def lose_life(self):
        self.lives -= 1
        self.fronticles.append(LifeParticle(lives=self.lives))
        print(self.lives)

    def bad_serve(self):
        self.fronticles.append(TintParticle(color=(255, 0, 0), opacity=100, duration=0.3))
        self.lose_life()

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

        if self.shade_alpha > 0:
            self.shade.set_alpha(self.shade_alpha)
            surface.blit(self.shade, (0, 0))

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

        if self.lives < 0:
            self.shade_alpha += 255*dt
            if self.shade_alpha >= 255:
                self.done = True


    def next_frame(self):
        qsb = int((self.total_time_save/self.num_served * 2000)//100 * 100)
        rm = round(self.total_rating/self.num_served, 1)
        score = self.num_served*100*rm + qsb
        ingredients_used = [(key, self.ingredients_used[key]) for key in self.ingredients_used]
        if not ingredients_used:
            favorite = "???"
        else:
            ingredients_used = sorted(ingredients_used, key=lambda x: -x[1])
            favorite = ingredients_used[0][0]

        self.game.lvs = [
            ("CUSTOMERS SERVED", self.num_served),
             ("RAW SCORE", self.num_served * 100),
              ("RATINGS (MULTIPLIER)", f"{rm}/5"),
               ("QUICK SERVER BONUS", f"{qsb}"),
            ("FAVORITE INGREDIENT", favorite.upper()),
                ("FINAL SCORE", f"{int(score)}"),
        ]
        return Stats(self.game)

    def happiness_flare(self, happiness):
        pass
        #self.hsurf = self.hfont.render(f"HAPPINESS: {happiness}",1,(0, 0, 0))


class Stats(Frame):
    def __init__(self, game):
        super().__init__(game)

        self.shadows = [
            ImageManager.load("assets/images/spicy_shadow.png"),
            ImageManager.load("assets/images/savory_shadow.png"),
            ImageManager.load("assets/images/sweet_shadow.png"),
        ]
        for i, shadow in enumerate(self.shadows):
            self.shadows[i] = pygame.transform.scale(shadow, (32, 32))
            #self.shadows[i].set_alpha(100)

        width = 160
        height = width//3
        self.tile = pygame.Surface((width, height))
        self.tile.fill((255, 0, 255))
        self.tile.set_colorkey((255, 0, 255))
        x = width//6
        for i, item in enumerate(self.shadows):
            xf = x - item.get_width()//2
            yf = height//2 - item.get_height()//2
            self.tile.blit(item, (xf, yf))
            x += width//3
        self.tile.set_alpha(50)

        self.shade = pygame.Surface((c.WINDOW_WIDTH, c.WINDOW_HEIGHT))
        self.shade.fill((0, 0, 0))
        self.shade_alpha = 255
        self.shade_target = 0

        title_font = pygame.font.Font("assets/fonts/AllTheWayToTheSun.ttf", 80)
        title = title_font.render("RESULTS", 1, (255, 255, 255))
        self.title = title

        self.label_font = pygame.font.Font("assets/fonts/AllTheWayToTheSun.ttf", 30)
        self.value_font = pygame.font.Font("assets/fonts/AllTheWayToTheSun.ttf", 30)

        self.labels_values = self.game.lvs

        self.enter_font = pygame.font.Font("assets/fonts/AllTheWayToTheSun.ttf", 20)
        self.enter = self.enter_font.render("Press Enter to try again", 1, (255, 255, 255))
        self.enter.set_alpha(128)



    def add_label_value(self, label, value):
        self.labels_values.append((label, value))

    def draw_label_value(self, surface, lv, y):
        label = self.label_font.render(lv[0] + ": ",1, (255, 255, 255))
        label.set_alpha(128)
        value = self.value_font.render(f"{lv[1]}", 1, (255, 255, 255))
        x = c.WINDOW_WIDTH//2 + 90
        if lv[0] == "FINAL SCORE":
            x = c.WINDOW_WIDTH//2 + 50
        y = y
        surface.blit(label, (x - label.get_width(), y))
        surface.blit(value, (x, y))


    def update(self, dt, events):
        if self.shade_target < self.shade_alpha:
            self.shade_alpha -= 500*dt
            if self.shade_alpha < 0:
                self.shade_alpha = 0
        if self.shade_target > self.shade_alpha:
            self.shade_alpha += 1000*dt
            if self.shade_alpha > self.shade_target:
                self.shade_alpha = 255
        pass
        if self.shade_alpha == 255 and self.shade_target == 255:
            self.done = True

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.shade_target = 255

    def draw(self, surface, offset=(0, 0)):

        yoff = 30
        surface.fill((0, 60, 80))
        interval = 2
        t = time.time()
        x = -2*self.tile.get_width() + ((t*20)%self.tile.get_width())
        y = -7*self.tile.get_height() + ((t*10)%(6*self.tile.get_height()))
        x0 = x
        y0 = y
        while y < c.WINDOW_HEIGHT + 50:
            x0 += self.tile.get_width()//6
            x0 %= self.tile.get_width()
            x0 -= self.tile.get_width()
            x = x0
            while x < c.WINDOW_WIDTH + 50:
                surface.blit(self.tile, (x, y))
                x += self.tile.get_width()
            y += self.tile.get_height()

        surface.blit(self.title, (c.WINDOW_WIDTH//2 - self.title.get_width()//2, 80 + yoff))

        y = 200 + yoff
        for lv in self.labels_values:
            if lv[0] == "FINAL SCORE":
                y += 40
            self.draw_label_value(surface, lv, y)
            y += 40

        if time.time()%1 < 0.7:
            surface.blit(self.enter, (c.WINDOW_WIDTH//2 - self.enter.get_width()//2, c.WINDOW_HEIGHT - 70))

        if self.shade_alpha > 0:
            self.shade.set_alpha(self.shade_alpha)
            surface.blit(self.shade, (0, 0))

    def next_frame(self):
        return GameFrame(self.game)


class Title(Frame):
    def __init__(self, game):
        super().__init__(game)

        self.shadows = [
            ImageManager.load("assets/images/spicy_shadow.png"),
            ImageManager.load("assets/images/savory_shadow.png"),
            ImageManager.load("assets/images/sweet_shadow.png"),
        ]
        for i, shadow in enumerate(self.shadows):
            self.shadows[i] = pygame.transform.scale(shadow, (32, 32))
            #self.shadows[i].set_alpha(100)

        width = 160
        height = width//3
        self.tile = pygame.Surface((width, height))
        self.tile.fill((255, 0, 255))
        self.tile.set_colorkey((255, 0, 255))
        x = width//6
        for i, item in enumerate(self.shadows):
            xf = x - item.get_width()//2
            yf = height//2 - item.get_height()//2
            self.tile.blit(item, (xf, yf))
            x += width//3
        self.tile.set_alpha(50)

        self.shade = pygame.Surface((c.WINDOW_WIDTH, c.WINDOW_HEIGHT))
        self.shade.fill((0, 0, 0))
        self.shade_alpha = 255
        self.shade_target = 0

        self.enter_font = pygame.font.Font("assets/fonts/AllTheWayToTheSun.ttf", 20)
        self.enter = self.enter_font.render("Press Enter to play", 1, (255, 255, 255))
        self.enter.set_alpha(128)

        title_font = pygame.font.Font("assets/fonts/AllTheWayToTheSun.ttf", 102)
        title = title_font.render("BOT APPETIT", 1, (255, 255, 255))
        self.title = title

    def update(self, dt, events):
        if self.shade_target < self.shade_alpha:
            self.shade_alpha -= 500*dt
            if self.shade_alpha < 0:
                self.shade_alpha = 0
        if self.shade_target > self.shade_alpha:
            self.shade_alpha += 1000*dt
            if self.shade_alpha > self.shade_target:
                self.shade_alpha = 255
        pass
        if self.shade_alpha == 255 and self.shade_target == 255:
            self.done = True

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.shade_target = 255



    def draw(self, surface, offset=(0, 0)):

        surface.fill((0, 60, 80))
        interval = 2
        t = time.time()
        x = -2*self.tile.get_width() + ((t*20)%self.tile.get_width())
        y = -7*self.tile.get_height() + ((t*10)%(6*self.tile.get_height()))
        x0 = x
        y0 = y
        while y < c.WINDOW_HEIGHT + 50:
            x0 += self.tile.get_width()//6
            x0 %= self.tile.get_width()
            x0 -= self.tile.get_width()
            x = x0
            while x < c.WINDOW_WIDTH + 50:
                surface.blit(self.tile, (x, y))
                x += self.tile.get_width()
            y += self.tile.get_height()

        if time.time()%1 < 0.7:
            surface.blit(self.enter, (c.WINDOW_WIDTH//2 - self.enter.get_width()//2, c.WINDOW_HEIGHT - 70))
        surface.blit(self.title, (c.WINDOW_WIDTH//2 - self.title.get_width()//2, c.WINDOW_HEIGHT//2 - self.title.get_height()//2))

        if self.shade_alpha > 0:
            self.shade.set_alpha(self.shade_alpha)
            surface.blit(self.shade, (0, 0))

    def next_frame(self):
        return GameFrame(self.game)