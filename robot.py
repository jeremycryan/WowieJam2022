import pygame
import constants as c
from image_manager import ImageManager
from particle import FoodParticle
from primitives import Pose
import math
from ingredient import Ingredient
import random
import time

class Robot:
    POPPING_UP = 0
    UP = 1
    POPPING_DOWN = 2
    DOWN = 3

    SPEAK_FONT = None
    CHARS = {}

    def __init__(self, frame):
        if not self.SPEAK_FONT:
            Robot.SPEAK_FONT = pygame.font.Font("assets/fonts/a_goblin_appears.ttf", 16)
            Robot.CHARS = {char: Robot.SPEAK_FONT.render(char, 1, (255, 255, 255)) for char in c.PRINTABLES}

        self.frame = frame
        self.surf = ImageManager.load("assets/images/robot.png")
        self.up_position = Pose((c.WINDOW_WIDTH * 0.1, c.WINDOW_HEIGHT * 0.32), 0)
        self.down_position = Pose((c.WINDOW_WIDTH * -0.2, c.WINDOW_HEIGHT * 0.3), math.pi/2)
        self.position = self.down_position.copy()
        self.target_position = self.up_position.copy()
        self.pop_up()
        self.since_popped_up = 0
        self.dialog = ImageManager.load("assets/images/robot_dialog.png")
        self.dialog_alpha = 0
        self.dialog_target_alpha = 0
        self.dialog_text = "TASTE ANALYSIS SAYS YUM"



    def pop_up(self):
        self.target_position = self.up_position.copy()
        self.state = Robot.POPPING_UP
        self.dialog_target_alpha = 0

    def randomize_dialog(self, key):
        dialogs = c.ROBOT_DIALOG
        dialogs += ("I HAVE PROVIDED YOU "+key.upper(),)*5
        if "robot" in Ingredient.ingredient_dict[key]:
            dialogs += tuple(Ingredient.ingredient_dict[key]["robot"])
        self.dialog_text = random.choice(dialogs)

    def popped_up(self):
        self.state = Robot.UP
        self.since_popped_up = 0
        self.add_ingredient()

    def pop_down(self):
        self.state = Robot.POPPING_DOWN
        self.target_position = self.down_position.copy()


    def popped_down(self):
        self.state = Robot.DOWN
        self.dialog_target_alpha = 255

    def update(self, dt, events):
        d = self.target_position - self.position
        self.position += d * 8*dt

        if self.dialog_alpha < self.dialog_target_alpha:
            self.dialog_alpha += 2000*dt
            if self.dialog_alpha > self.dialog_target_alpha:
                self.dialog_alpha = self.dialog_target_alpha
        if self.dialog_alpha > self.dialog_target_alpha:
            self.dialog_alpha -= 2000*dt
            if self.dialog_alpha < self.dialog_target_alpha:
                self.dialog_alpha = self.dialog_target_alpha

        if self.state == Robot.POPPING_UP:
            if d.magnitude() < 15:
                self.popped_up()

        if self.state == Robot.POPPING_DOWN:
            if d.magnitude() < 5:
                self.popped_down()

        if self.state == Robot.UP:
            self.since_popped_up += dt
            if self.since_popped_up > 0.5:
                self.pop_down()

    def add_ingredient(self):
        self.target_position = self.up_position
        key = random.choice([key for key in Ingredient.ingredient_dict])
        self.frame.pot.add_ingredient(Ingredient.from_key(key))
        particle = FoodParticle(key, self.frame)
        particle.position = self.position
        particle.velocity = Pose((500, 0))
        self.frame.add_particle(particle)
        self.randomize_dialog(key)

    def draw(self, surface, offset=(0, 0)):
        if self.dialog_alpha > 0:
            pass
            #self.draw_dialog(surface, offset)

        surf = pygame.transform.rotate(self.surf, self.position.angle*180/math.pi)
        w = surf.get_width()
        h = surf.get_height()
        x = self.position.x + offset[0] - w//2
        y = self.position.y + offset[1] - h//2
        surface.blit(surf, (x, y))

    def draw_dialog(self, surface, offset=(0, 0)):
        if self.dialog_alpha <= 0:
            return
        self.dialog.set_alpha(self.dialog_alpha)
        surface.blit(self.dialog, (0, 0))

        x = 20
        y = 40
        w = 200
        h = 100
        spacing = 30
        words = self.dialog_text.split(" ")
        lines = []
        current_line = ""
        line_width = 0
        for word in words:
            word_width = sum(Robot.CHARS[char].get_width() for char in word)
            if line_width + word_width > w:
                lines.append(current_line)
                current_line = ""
                line_width = 0

            current_line += word + " "
            line_width += word_width + Robot.CHARS[" "].get_width()
        if current_line:
            lines.append(current_line)

        x0 = x
        y0 = y + h / 2
        y0 -= spacing * len(lines) / 2
        for line in lines:
            line_width = sum([Robot.CHARS[char].get_width() for char in line])
            x = x0 - line_width // 2 + w // 2
            for i, char in enumerate(line):
                xp, yp = x, y0
                yp += math.sin(time.time() * -32 + i * 2.6) * 1
                surface.blit(Robot.CHARS[char], (xp, yp))
                x += Robot.CHARS[char].get_width()
            y0 += spacing