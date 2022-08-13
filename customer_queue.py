import random
import constants as c
from primitives import Pose
from image_manager import ImageManager
import pygame
import math
import time


class CustomerQueue:

    def __init__(self, frame):
        self.customers = []
        self.served_customers = []
        self.frame = frame

    def has_customers(self):
        return len(self.customers) > 0

    def front_customer(self):
        return self.customers[0]

    def serve_customer(self, flavor):
        served_customer = self.customers.pop(0)
        served_customer.serve(flavor)
        self.served_customers.append(served_customer)

    def update(self, dt, events):
        for customer in self.customers + self.served_customers:
            customer.update(dt, events)
            if customer.position.x > c.WINDOW_WIDTH + 500 or customer.position.x < -500:
                if customer in self.served_customers:
                    self.served_customers.remove(customer)
        self.queue_customers()
        self.update_target_positions()

        if self.front_customer().at_target() and self.front_customer().state == c.QUEUED:
            self.front_customer().speak()
            self.frame.pot.preview.target_flavor_spread = self.front_customer().tolerance
            self.frame.pot.preview.update_goal_flavor(self.front_customer().desired_flavor)

    def draw(self, surface, offset=(0, 0)):
        for customer in self.customers[::-1] + self.served_customers:
            customer.draw(surface, offset)

    def update_target_positions(self):
        x = c.WINDOW_WIDTH * 0.8
        y = c.WINDOW_HEIGHT//2
        for customer in self.customers:
            customer.target_position = Pose((x, y))
            x += 100

    def queue_customers(self):
        while len(self.customers) < 3:
            tolerance = random.random() * 0.5 + 0.3
            self.customers.append(Customer((c.WINDOW_WIDTH + 100, c.WINDOW_HEIGHT//2), self, tolerance, None))

class Customer:

    SPEAK_FONT = None
    CHARS = {}

    def __init__(self, position, queue, tolerance=1.0, desired_flavor = None):
        if not self.SPEAK_FONT:
            Customer.SPEAK_FONT = pygame.font.Font("assets/fonts/corbel.ttf", 24)
            Customer.CHARS = {char:Customer.SPEAK_FONT.render(char, 1, (0, 0, 0)) for char in c.PRINTABLES}

        self.queue = queue
        self.position = Pose(position)
        self.target_position = Pose(position)
        self.tolerance = tolerance
        self.desired_flavor = desired_flavor if desired_flavor else self.random_flavor()

        self.queue_surf = ImageManager.load("assets/images/customer_waiting.png")
        self.talk_surf = ImageManager.load("assets/images/customer_speaking.png")
        self.wait_surf = ImageManager.load("assets/images/customer_waiting.png")
        self.happy_surf = ImageManager.load("assets/images/customer_served_happy.png")
        self.serve_surf = self.happy_surf

        self.state = c.QUEUED
        self.since_spoken = 0

        self.velocity = Pose((-200, 0))

        self.window = ImageManager.load("assets/images/window.png")
        self.window_alpha = 0
        self.window_target_alpha = 255

        self.dialog = self.get_dialog()

        self.happiness = None

    def get_dialog(self):
        return "Could I get something that tastes like dirt?"

    def speak(self):
        self.state = c.SPEAKING
        self.since_spoken = 0
        self.window_target_alpha = 255

    def stop_speaking(self):
        self.state = c.WAITING

    @staticmethod
    def random_flavor():
        total = 100
        flavor = {}
        most = random.random() * total
        middle = random.random() * (total - most)
        least = total - most - middle
        flavors = c.FLAVORS.copy()
        random.shuffle(flavors)
        flavor[flavors[0]] = most
        flavor[flavors[1]] = middle
        flavor[flavors[2]] = least
        return flavor

    def serve(self, flavor):
        self.state = c.SERVED
        self.serve_surf = self.happy_surf
        self.happiness = self.queue.frame.pot.preview.flavor_in_range(flavor)
        self.queue.frame.happiness_flare(self.happiness)

    def at_target(self):
        return (self.target_position - self.position).magnitude() < 5

    def update(self, dt, events):
        self.since_spoken += dt
        if self.since_spoken > 3 and self.state == c.SPEAKING:
            pass#self.stop_speaking()
        if self.state == c.SERVED:
            self.target_position += self.velocity*dt
            self.velocity += Pose((5000, 0))*dt

        d = self.target_position - self.position
        self.position += d * dt * 5
        if not self.state == c.SPEAKING:
            self.window_target_alpha = 0

        if self.window_alpha < self.window_target_alpha:
            self.window_alpha += 1000*dt
            if self.window_alpha > self.window_target_alpha:
                self.window_alpha = self.window_target_alpha
        elif self.window_alpha > self.window_target_alpha:
            self.window_alpha -= 2500*dt
            if self.window_alpha < self.window_target_alpha:
                self.window_alpha = self.window_target_alpha

    def draw(self, surface, offset=(0, 0)):
        surf = None
        if self.state == c.QUEUED:
            surf = self.queue_surf
        if self.state == c.SPEAKING:
            surf = self.talk_surf
        if self.state == c.WAITING:
            surf = self.wait_surf
        if self.state == c.SERVED:
            surf = self.serve_surf

        w = surf.get_width()
        h = surf.get_height()
        x = self.position.x + offset[0] - w//2
        y = self.position.y + offset[1] - h//2
        surface.blit(surf, (x, y))

        if self.window_alpha > 0:
            self.draw_dialog(surface, offset)

    def draw_dialog(self, surface, offset=(0, 0)):
        self.window.set_alpha(self.window_alpha)
        surface.blit(self.window, (c.WINDOW_WIDTH - self.window.get_width(), 0))

        x = c.WINDOW_WIDTH - 350
        y = 18
        w = 320
        h = 80
        spacing = 30
        words = self.dialog.split(" ")
        lines = []
        current_line = ""
        line_width = 0
        for word in words:
            word_width = sum(Customer.CHARS[char].get_width() for char in word)
            if line_width + word_width > w:
                lines.append(current_line)
                current_line = ""
                line_width = 0

            current_line += word + " "
            line_width += word_width + Customer.CHARS[" "].get_width()
        if current_line:
            lines.append(current_line)

        x0 = x
        y0 = y + h/2
        y0 -= spacing*len(lines)/2
        for line in lines:
            line_width = sum([Customer.CHARS[char].get_width() for char in line])
            x = x0 - line_width//2 + w//2
            for i, char in enumerate(line):
                xp, yp = x, y0
                yp += math.sin(time.time()*-20 + i*2.6)*1
                surface.blit(Customer.CHARS[char], (xp, yp))
                x += Customer.CHARS[char].get_width()
            y0 += spacing