import random
import constants as c
from primitives import Pose
from image_manager import ImageManager
import pygame
import math
import time
from particle import PoofParticle, PanPoof, ReactionParticle, TintParticle
from sound_manager import SoundManager


class CustomerQueue:

    def __init__(self, frame):
        self.customers = []
        self.served_customers = []
        self.frame = frame

        self.perfect_sounds = [SoundManager.load(f"assets/sounds/grade_PERFECT(0)_{x}.wav") for x in range(1, 2)]
        for sound in self.perfect_sounds:
            sound.set_volume(0.6)
        self.ok_sounds = [SoundManager.load(f"assets/sounds/grade_OK_{x}.wav") for x in range(1, 4)]
        self.eww_sounds = [SoundManager.load(f"assets/sounds/grade_EW_{x}.wav") for x in range(1, 5)]
        for sound in self.eww_sounds:
            sound.set_volume(0.5)
        self.reaction_sound_dict = {2: self.perfect_sounds, 1: self.ok_sounds, 0: self.eww_sounds}
        self.sounds = [SoundManager.load(f"assets/sounds/customer voice_{x}.wav") for x in range(1, 11)]
        for i, sound in enumerate(self.sounds):
            num = i+1
            if num == 1:
                sound.set_volume(1)
                continue
            if num==2:
                sound.set_volume(0.5)
                continue
            if num==3:
                sound.set_volume(0.15)
                continue
            if num==4:
                sound.set_volume(0.5)
                continue
            if num ==5:
                sound.set_volume(1.0)
                continue
            if num==7:
                sound.set_volume(0.4)
                continue
            if num==6:
                sound.set_volume(0.15)
            sound.set_volume(0.25)
        self.sounds = self.sounds[:7] + [self.sounds[-1]]

    def has_customers(self):
        return len(self.customers) > 0

    def front_customer(self):
        return self.customers[0]

    def serve_customer(self, flavor):
        served_customer = self.customers.pop(0)
        served_customer.serve(self.frame, flavor)
        self.served_customers.append(served_customer)
        served_customer.plate_appear(self.frame)
        self.frame.particles.append(ReactionParticle((served_customer.position + Pose((-150, -100))).get_position(), served_customer.happiness))
        random.choice(self.reaction_sound_dict[served_customer.happiness]).play()
        if served_customer.happiness > 0:
            self.frame.fronticles.append(TintParticle(color=(255, 255, 255), opacity=128, duration=0.25))
        else:
            self.frame.bad_serve()
        self.frame.num_served += 1
        if served_customer.happiness == 0:
            rate = 1
        elif served_customer.happiness == 1:
            rate = 3
        elif served_customer.happiness == 2:
            rate = 5
        self.frame.total_rating += rate
        self.frame.total_time_save += served_customer.time_left

    def check_time(self):
        if self.front_customer().state not in [c.WAITING, c.SPEAKING]:
            return
        if self.front_customer().time_left < -0.05:
            self.frame.shake(30)
            Customer.make_mistake()
            self.frame.fronticles.append(TintParticle(color=(200, 0, 128), opacity=128, duration=0.4))
            self.frame.fronticles.append(ReactionParticle((c.WINDOW_WIDTH//2, c.WINDOW_HEIGHT//2 - 160), 4))
            served_customer = self.customers.pop(0)
            self.served_customers.append(served_customer)
            served_customer.update_happiness_surf(0)
            served_customer.state = c.SERVED
            self.frame.pot.empty()
            self.frame.lose_life()

    def draw_plates(self, surface, offset=(0, 0)):
        for customer in self.customers + self.served_customers:
            customer.draw_plate(surface, offset=offset)

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

        self.check_time()

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
    COUNT = -2

    MISTAKE_HANDICAP = 0

    def __init__(self, position, queue, tolerance=1.0, desired_flavor = None):
        Customer.COUNT += 1

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
        self.okay_surf = ImageManager.load("assets/images/customer_served_okay.png")
        self.unhappy_surf = ImageManager.load("assets/images/customer_served_bad.png")
        self.serve_surf = self.happy_surf

        self.state = c.QUEUED
        self.since_spoken = 0

        self.velocity = Pose((-200, 0))

        self.window = ImageManager.load("assets/images/window.png")
        self.window_alpha = 0
        self.window_target_alpha = 255

        self.dialog = self.get_dialog()

        self.happiness = None

        self.plate_visible = False
        self.plate_position = Pose((c.WINDOW_WIDTH*0.7, c.WINDOW_HEIGHT*0.55))
        self.plate = ImageManager.load("assets/images/plate.png")
        self.plate = pygame.transform.scale(self.plate, (self.plate.get_width()*1280/1920, self.plate.get_height()*1280/1920))


        time_scale = 0.2
        self.time_bar = ImageManager.load("assets/images/time_bar.png")
        self.time_bar_frame = ImageManager.load("assets/images/time_frame.png")
        self.time_bar = pygame.transform.scale(self.time_bar, (self.time_bar.get_width() * time_scale, self.time_bar.get_height()*time_scale))
        self.time_bar_frame = pygame.transform.scale(self.time_bar_frame, (self.time_bar_frame.get_width() * time_scale, self.time_bar_frame.get_height() * time_scale))
        self.time_bar_scale = 0
        self.clock = ImageManager.load("assets/images/clock.png")
        self.clock = pygame.transform.scale(self.clock, (self.clock.get_width() * time_scale, self.clock.get_height() * time_scale))

        self.time_left = 1
        self.patience = self.get_patience()

    def get_patience(self):
        if Customer.COUNT == 1:
            return 120
        if Customer.COUNT == 2:
            return 60
        if Customer.COUNT == 3:
            return 30
        scaling = 8
        return 20 * ((3+scaling)/(Customer.COUNT+scaling)) + Customer.MISTAKE_HANDICAP

    @staticmethod
    def make_mistake():
        Customer.MISTAKE_HANDICAP += 10

    def get_dialog(self):
        if self.desired_flavor[c.SWEET] > 80:
            lines = [
                "I want something so sweet my dentist can taste it.",
                "Your sweetest dish, please."
            ]
        elif self.desired_flavor[c.SWEET] > 50:
            lines = [
                "I want something sweet... but not too sweet.",
                "I have a bit of a sweet tooth today."
            ]
        elif self.desired_flavor[c.SPICY] > 80:
            lines = [
                "Make me cry.",
                "Hit me with the spiciest dish you have. I can take it.",
                "I want something that lights my mouth on fire and causes me physical pain. Do you have anything like that?",
            ]
        elif self.desired_flavor[c.SPICY] > 50:
            lines = [
                "Give me something spicy, but don't go overboard.",
            ]
        elif self.desired_flavor[c.SAVORY] > 50:
            lines = [
                "I'm in the mood for something savory today.",
            ]
        else:
            lines = [
                "I'm not looking for anything too extreme.",
                "Give me something on the milder side."
            ]
        return random.choice(lines)

    def speak(self):
        self.state = c.SPEAKING
        self.since_spoken = 0
        self.window_target_alpha = 255

        self.time_left = 1
        random.choice(self.queue.sounds).play()

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

    def serve(self, frame, flavor):
        self.state = c.SERVED
        self.serve_surf = self.happy_surf
        satisfaction = frame.pot.preview.flavor_in_range(flavor)
        if satisfaction == 1:
            self.serve_surf = self.okay_surf
        if satisfaction == 0:
            self.serve_surf = self.unhappy_surf
        self.happiness = self.queue.frame.pot.preview.flavor_in_range(flavor)
        self.queue.frame.happiness_flare(self.happiness)

        Customer.MISTAKE_HANDICAP *= 0.5

    def update_happiness_surf(self, satisfaction):
        self.happiness = satisfaction
        if satisfaction == 1:
            self.serve_surf = self.okay_surf
        if satisfaction == 0:
            self.serve_surf = self.unhappy_surf
        if satisfaction == 2:
            self.serve_surf = self.happy_surf

    def at_target(self):
        return (self.target_position - self.position).magnitude() < 5

    def update(self, dt, events):
        self.since_spoken += dt
        if self.since_spoken > 3 and self.state == c.SPEAKING:
            pass#self.stop_speaking()
        if self.state == c.SERVED:
            self.target_position += self.velocity*dt
            self.velocity += Pose((5000, 0))*dt
        # if self.state == c.SERVED and self.happiness == 0:
        #     self.target_position.y += 250*dt
        #     self.velocity += Pose((-2000, 0)) * dt
        #     self.velocity += Pose((0, 0), 0)*dt

        self.time_left -= 1/self.get_patience() * dt

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

        if self.plate_visible:
            self.plate_position = Pose((self.position.x*1.4 - 500, c.WINDOW_HEIGHT*0.60))

    def plate_appear(self, frame):
        self.plate_visible = True
        self.plate_position = Pose((self.position.x, c.WINDOW_HEIGHT*0.60))
        for i in range(10):
            frame.particles.append(PoofParticle(self.plate_position.get_position(), color=128))

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

        if self.position.angle != 0:
            surf = pygame.transform.rotate(surf, self.position.angle * 180/math.pi)

        w = surf.get_width()
        h = surf.get_height()
        x = self.position.x + offset[0] - w//2
        y = self.position.y + offset[1] - h//2
        surface.blit(surf, (x, y))

        if self.window_alpha > 0:
            self.draw_dialog(surface, offset)

        self.draw_patience_meter(surface, offset)

    def draw_patience_meter(self, surface, offset=(0, 0)):

        if not self.state == c.SPEAKING or self.state == c.WAITING:
            return
        x = self.position.x + offset[0] - 220
        y = self.position.y + offset[1] - 150

        surface.blit(self.time_bar_frame, (x, y))

        width = self.time_left/1
        if width > 0:
            front = pygame.Surface((self.time_bar.get_width() * width, self.time_bar.get_height()))
            front.fill((255, 0, 255))
            front.blit(self.time_bar, (0, 0))
            front.set_colorkey((255, 0, 255))
            surface.blit(front, (x, y))

        surface.blit(self.clock, (x - 40, y - 6))

    def draw_plate(self, surface, offset=(0, 0)):
        if self.plate_visible:
            x = self.plate_position.x + offset[0] - self.plate.get_width()//2
            y = self.plate_position.y + offset[1] - self.plate.get_height()//2
            surface.blit((self.plate), (x, y))

    def draw_dialog(self, surface, offset=(0, 0)):
        self.window.set_alpha(self.window_alpha)
        surface.blit(self.window, (c.WINDOW_WIDTH - self.window.get_width(), 0))

        x = c.WINDOW_WIDTH - 450
        y = 28
        w = 420
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