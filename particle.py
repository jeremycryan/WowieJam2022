from primitives import Pose
from ingredient import Ingredient
from image_manager import ImageManager
import constants as c
import math
import random
import pygame

from sound_manager import SoundManager


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
        self.position = Pose((200 + random.random() * 300, -100), random.random()*360)
        self.velocity = Pose((0, 1000), random.random() * 10 - 5)
        self.acceleration = Pose((0, 5000))
        self.splattered = False
        self.frame = frame
        self.plops = [SoundManager.load(f"assets/sounds/item plop_{x}.wav") for x in range(1, 15)]
        for plop in self.plops:
            plop.set_volume(0.7)

    def draw(self, surface, offset=(0, 0)):
        surf = pygame.transform.rotate(self.surf, self.position.angle*180/math.pi)

        x = self.position.x + offset[0] - surf.get_width()//2
        y = self.position.y + offset[1] - surf.get_height()//2
        surface.blit(surf, (x, y))

    def update(self, dt, events):
        self.velocity += self.acceleration*dt
        if self.position.y < c.WINDOW_HEIGHT*0.60:
            super().update(dt, events)
        if self.position.y > c.WINDOW_HEIGHT*0.6:
            self.position.y = c.WINDOW_HEIGHT*0.6
            if not self.splattered:
                self.splattered = True
                random.choice(self.plops).play()
                for i in range(20):
                    self.frame.particles.append(SplatterParticle(self.position.get_position()))

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


class ReactionParticle(Particle):

    def __init__(self, position, score):
        self.score = score
        velocity = (0, -50)
        super().__init__(position, velocity=velocity, duration=0.75)
        if self.score == 0:
            self.surf = ImageManager.load("assets/images/eww.png")
        elif self.score == 1:
            self.surf = ImageManager.load("assets/images/okay.png")
        elif self.score == 2:
            self.surf = ImageManager.load("assets/images/perfect.png")
        else:
            self.surf = ImageManager.load("assets/images/timesup.png")

    def draw(self, surface, offset=(0, 0)):
        if self.score == 2:
            copy = pygame.transform.scale2x(self.surf)
            w = copy.get_width()
            h = copy.get_height()
            x = self.position.x - w // 2 + offset[0]
            y = self.position.y - h // 2 + offset[1]
            copy.set_alpha(100 * (1 - self.through()))
            surface.blit(copy, (x, y))

        surf = self.surf
        w = surf.get_width()
        h = surf.get_height()
        x = self.position.x - w//2 + offset[0]
        y = self.position.y - h//2 + offset[1]
        surf.set_alpha(255 * (1 - self.through()))
        surface.blit(surf, (x, y))


class TintParticle(Particle):

    def __init__(self, duration=0.25, color=(0, 0, 0), opacity=255):
        super().__init__(duration=duration)
        surf = pygame.Surface((c.WINDOW_SIZE))
        surf.fill((color))
        self.surf = surf
        self.opacity = opacity

    def draw(self, surf, offset=(0, 0)):
        self.surf.set_alpha((self.opacity - self.opacity*self.through()))
        surf.blit(self.surf, (0, 0))


class LifeParticle(Particle):
    FONT = None

    def __init__(self, duration=1, lives=3):
        super().__init__(duration=duration)
        self.full = ImageManager.load("assets/images/life.png")
        self.empty = ImageManager.load("assets/images/life_empty.png")
        self.lives = lives
        self.banner = pygame.Surface((c.WINDOW_WIDTH, 1))
        self.banner.fill((0, 0, 0))
        self.banner.set_alpha(128)

        self.buzzer = SoundManager.load("assets/sounds/end buzzer.wav")
        self.buzzer.set_volume(0.3)
        if self.lives < 0:
            self.buzzer.play()

        if not LifeParticle.FONT:
            LifeParticle.FONT = pygame.font.Font("assets/fonts/AllTheWayToTheSun.ttf", 55)


        if self.lives < 0:
            self.text = LifeParticle.FONT.render("GAME OVER!", 1, (255, 255, 255))
        else:
            self.text = LifeParticle.FONT.render("LIFE LOST!", 1, (255, 255, 255))

    def draw(self, surf, offset=(0, 0)):


        banner = pygame.transform.scale(self.banner, (c.WINDOW_WIDTH, min(200, 800*(1-self.through()))))
        surf.blit(banner, (c.WINDOW_WIDTH//2 - banner.get_width()//2, c.WINDOW_HEIGHT//2 - banner.get_height()//2))

        if self.through() < 0.75:
            alpha = 255
        else:
            alpha = (1 - (self.through()-0.75)/0.25)**0.5 * 255
        yoff = 57
        if self.lives < 0:
            yoff = 0
        self.text.set_alpha(alpha)
        surf.blit(self.text, (c.WINDOW_WIDTH//2 - self.text.get_width()//2, c.WINDOW_HEIGHT//2 - self.text.get_height()//2 - yoff))

        if self.lives<0:
            return

        spacing = 20
        width = self.full.get_width() * 3 + spacing * 2
        x = c.WINDOW_WIDTH//2 - width//2
        y = c.WINDOW_HEIGHT//2 - self.full.get_height()//2 + 30

        self.full.set_alpha(alpha)
        self.empty.set_alpha(alpha)
        for i in range(3)[::-1]:
            if i >= (3 - self.lives):
                surf.blit(self.full, (x, y))
            else:
                surf.blit(self.empty, (x, y))
            x += spacing + self.full.get_width()