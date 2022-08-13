from image_manager import ImageManager
from primitives import Pose
import pygame
import math
import constants as c

class Bell:

    def __init__(self, position, frame):
        self.surf = ImageManager.load("assets/images/bell.png")
        self.position = Pose(position)
        self.frame = frame
        self.squash = 0

    def width(self):
        return self.surf.get_width()

    def height(self):
        return self.surf.get_height()

    def update(self, dt, events):
        self.squash -= 3.5*dt
        if self.squash < 0:
            self.squash = 0

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.hovered():
                        self.serve()

    def serve(self):
        if not self.frame.queue.front_customer().state in (c.WAITING, c.SPEAKING):
            return
        self.squash = 1
        self.frame.queue.serve_customer(self.frame.pot.flavors)
        self.frame.pot.empty()


    def draw(self, surface, offset=(0, 0)):
        w = self.width() * (1 - self.squash) + self.width() * self.squash * (math.cos(self.squash * math.pi * 0.65) + 1)
        h = (self.width() * self.height())/w
        x = self.position.x - w//2 + offset[0]
        y = self.position.y - h//2 + offset[1]
        surface.blit(pygame.transform.scale(self.surf, (w, h)), (x, y))

    def hovered(self):
        mpos = pygame.mouse.get_pos()
        if mpos[0] < self.position.x - self.surf.get_width()//2:
            return False
        if mpos[0] > self.position.x + self.surf.get_width()//2:
            return False
        if mpos[1] < self.position.y - self.surf.get_height()//2:
            return False
        if mpos[1] > self.position.y + self.surf.get_height()//2:
            return False
        return True
