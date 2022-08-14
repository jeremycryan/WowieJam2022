from primitives import Pose
from ingredient import Ingredient
from image_manager import ImageManager
import constants as c
import math
import random
import pygame

class Particle:

    food = False

    def __init__(self, position=(0, 0), velocity=(0, 0), duration=1):
        self.position = Pose(position)
        self.velocity = Pose(velocity)
        self.destroyed = False
        self.duration = duration
        self.age = 0


    def update(self, dt, events):
        if self.destroyed:
            return
        self.position += self.velocity * dt
        if self.age > self.duration:
            self.destroy()
        self.age += dt

    def draw(self, surf, offset=(0, 0)):
        if self.destroyed:
            return

    def through(self):
        return min(0.999, self.age/self.duration)

    def destroy(self):
        self.destroyed = True


class FoodParticle(Particle):
    def __init__(self, key, frame):
        self.surf = pygame.transform.scale(Ingredient.get_surf(key), (160, 160))
        self.food = True

        super().__init__(duration=5)
        self.position = Pose((-160, c.WINDOW_HEIGHT//2), random.random()*360)
        self.velocity = Pose((1200 + (random.random() - 0.5) * 500, -750 - random.random()*200), random.random()*math.pi/2 + math.pi/4)
        self.acceleration = Pose((0, 5000))
        self.splattered = False
        self.frame = frame

    def draw(self, surface, offset=(0, 0)):
        surf = pygame.transform.rotate(self.surf, self.position.angle*180/math.pi)

        x = self.position.x + offset[0] - surf.get_width()//2
        y = self.position.y + offset[1] - surf.get_height()//2
        surface.blit(surf, (x, y))

    def update(self, dt, events):
        if self.position.y <= c.WINDOW_HEIGHT*0.60:
            super().update(dt, events)
        else:
            if not self.splattered:
                self.splattered = True
                for i in range(20):
                    self.frame.particles.append(SplatterParticle(self.position.get_position()))
        self.velocity += self.acceleration*dt

class PoofParticle(Particle):
    def __init__(self, position, color=255):
        self.surf = ImageManager.load("assets/images/smoke particle.png")
        super().__init__(duration=1.0, position=position)
        speed = random.random()**2 * 800 + 500
        angle = random.random() * math.pi*2
        self.velocity = Pose((math.cos(angle), -math.sin(angle))) * speed
        self.age += 0.8*random.random()
        self.angle = random.random() * 360

    def draw(self, surf, offset=(0, 0)):
        size = 100 * (1 - self.through())
        surface = pygame.transform.rotate(self.surf, self.angle)
        surface = pygame.transform.scale(surface, (size, size))

        x = self.position.x - surface.get_width()//2
        y = self.position.y - surface.get_height()//2
        surface.set_alpha(255 * (1 - self.through()))
        surface.set_colorkey((255, 0, 255))
        surf.blit(surface, (x, y))

    def update(self, dt, events):
        super().update(dt, events)
        self.velocity *= 0.0005**dt
        self.angle += 45*dt


class PanPoof(PoofParticle):
    def update(self, dt, events):
        super().update(dt, events)
        if self.velocity.y > -20:
            self.velocity.y = -20

class SplatterParticle(Particle):
    def __init__(self, position):
        super().__init__(duration=0.45, position=position)
        self.velocity = Pose((0, 0))
        self.velocity.x = random.random() * 800 - 400
        self.velocity.y = random.random() * -500 - 600
        self.position.y += 50

    def draw(self, surf, offset=(0, 0)):
        pygame.draw.circle(surf, (255, 255, 255), self.position.get_position(), 6 * (1 - self.through()))

    def update(self, dt, events):
        super().update(dt, events)
        self.velocity.y += 4000*dt
