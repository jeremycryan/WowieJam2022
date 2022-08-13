import constants as c
import math
from primitives import Pose
import pygame
from image_manager import ImageManager
import time

class FlavorPreview:

    def __init__(self, flavors, position, target_flavor=None, target_flavor_spread=0.75,radius=200):
        self.flavors = flavors.copy()
        self.radius = radius
        self.points = self.get_points()
        self.position = Pose(position)
        self.normalize_flavors()
        self.icons = {key: ImageManager.load(c.FLAVOR_ICONS[key]) for key in c.FLAVORS}
        self.you_are_here = ImageManager.load("assets/images/you_are_here.png")
        w = 64 * radius/200
        h = 64 * radius/200
        self.you_are_here = pygame.transform.scale(self.you_are_here, (w, h))
        self.here_shadow = pygame.Surface((20*radius//200, 20*radius//200))
        self.here_shadow.fill((255, 255, 255))
        self.here_shadow.set_colorkey((255, 255, 255))
        pygame.draw.ellipse(self.here_shadow,(0, 0, 0), self.here_shadow.get_rect())
        for key in self.icons:
            surf = self.icons[key]
            self.icons[key] = pygame.transform.scale(surf, (w, h))
        self.flavor_pos = self.position.copy()
        self.target_flavor_pos = self.flavor_pos.copy()
        self.target_flavor = target_flavor.copy() if target_flavor else None
        self.target_flavor_spread = target_flavor_spread
        self.target_overlay = pygame.Surface((10, 10))
        self.goal_flavor = None

    def goal_flavor_pos(self):
        pos = Pose((0, 0))
        for flavor in c.FLAVORS:
            pos += self.points[flavor] * (self.goal_flavor[flavor]/100)
        return pos

    def update_goal_flavor(self, goal):
        self.goal_flavor = goal
        self.target_overlay = pygame.Surface((self.radius*math.sqrt(3), self.radius*1.5))
        self.target_overlay.fill((255, 255, 255))
        self.target_overlay.set_colorkey((0, 0, 0))
        pygame.draw.polygon(self.target_overlay, (0, 0, 0), ((0, self.radius*1.5), (self.radius*math.sqrt(3)/2, 0), (self.radius*math.sqrt(3), self.radius*1.5)))
        self.update_flavor_pos()
        target_surf = self.target_overlay.copy()
        target_surf.fill((255, 0, 0))
        rel_flavor_pos = self.goal_flavor_pos() + Pose((self.target_overlay.get_width()//2, self.target_overlay.get_height()*2/3))
        pygame.draw.circle(target_surf, (255, 255, 0), rel_flavor_pos.get_position(),
                           self.radius * self.target_flavor_spread)
        pygame.draw.circle(target_surf, (0, 255, 0), rel_flavor_pos.get_position(), self.radius * self.target_flavor_spread/2)
        target_surf.blit(self.target_overlay, (0, 0))
        target_surf.set_colorkey((255, 255, 255))
        self.target_overlay = target_surf
        self.target_overlay.set_alpha(50)

    def update_target_flavor(self, flavor):
        self.target_flavor = flavor.copy()
        if not flavor:
            return


    def flavor_in_range(self, flavor):
        if not self.goal_flavor:
            return c.BAD
        norm_points = {key: self.points[key] * (1/self.radius) for key in self.points}
        norm_pos = Pose((0, 0))
        for key in flavor:
            norm_pos += norm_points[key] * flavor[key]*0.01
        want_pos = Pose((0, 0))
        for key in self.goal_flavor:
            want_pos += norm_points[key] * self.goal_flavor[key]*0.01
        dist = (want_pos - norm_pos).magnitude()
        if dist < self.target_flavor_spread/2:
            return c.GREAT
        if dist < self.target_flavor_spread:
            return c.OKAY
        return c.BAD

    def normalize_flavors(self):
        total = 0
        for flavor in c.FLAVORS:
            if flavor not in self.flavors:
                self.flavors[flavor] = 0
            total += self.flavors[flavor]
        for flavor in c.FLAVORS:
            self.flavors[flavor] *= 100/total

    def update_flavors(self, flavors):
        self.flavors = flavors
        self.normalize_flavors()
        self.update_flavor_pos()

    def get_points(self):
        points = {}
        points[c.FLAVORS[0]] = Pose((math.sqrt(3)/2, 0.5)) * self.radius
        points[c.FLAVORS[1]] = Pose((-math.sqrt(3)/2, 0.5)) * self.radius
        points[c.FLAVORS[2]] = Pose((0, -1)) * self.radius
        return points

    def update(self, dt, events):
        d = (self.target_flavor_pos - self.flavor_pos) * 10
        if d.magnitude() > 5:
            self.flavor_pos += d*dt
        else:
            self.flavor_pos = self.target_flavor_pos.copy()
        self.update_flavor_pos()

    def set_position(self, position):
        self.position = Pose(position)
        self.update_flavor_pos()
        self.flavor_pos = self.target_flavor_pos.copy()

    def update_flavor_pos(self):
        position = self.position
        flavor_pos = position
        for key in c.FLAVORS:
            flavor_pos += self.points[key] * self.flavors[key]*0.01
        self.target_flavor_pos = flavor_pos

    def draw(self, surface, offset=(0, 0)):
        position = self.position + Pose(offset)
        corners = [self.points[key] + position for key in c.FLAVORS]
        pygame.draw.polygon(surface, (255, 255, 255), [corner.get_position() for corner in corners])
        pygame.draw.line(surface, (0, 0, 0), corners[0].get_position(), corners[1].get_position(), 2)
        pygame.draw.line(surface, (0, 0, 0), corners[2].get_position(), corners[1].get_position(), 2)
        pygame.draw.line(surface, (0, 0, 0), corners[0].get_position(), corners[2].get_position(), 2)

        x = position.x - self.radius * math.sqrt(3)/2
        y = position.y - self.radius
        surface.blit(self.target_overlay, (x, y))

        if self.radius > 100:
            for key in c.FLAVORS:
                icon = self.icons[key]
                pose = position + self.points[key]
                x = pose.x - icon.get_width()//2
                y = pose.y - icon.get_height()//2
                surface.blit(icon, (x, y))


        x = self.flavor_pos.x - self.here_shadow.get_width()//2
        y = self.flavor_pos.y - self.here_shadow.get_height()//2
        self.here_shadow.set_alpha(100)
        surface.blit(self.here_shadow, (x, y))

        x = self.flavor_pos.x - self.you_are_here.get_width()//2
        y = self.flavor_pos.y - self.you_are_here.get_height() - math.sin(time.time()*3)**2 * 6
        surface.blit(self.you_are_here, (x, y))