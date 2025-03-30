import app
import pygame
import os
import math

class Bullet:
    def __init__(self, x, y, vx, vy, size, assets):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.animation = assets["bullets"]

        self.frame_index = 0
        self.animation_speed = 8
        self.animation_timer = 0

        self.angle = math.degrees(math.atan2(-vy, vx))  # Negative vy because pygame's y-axis is inverted
        self.image = pygame.transform.rotate(self.animation[self.frame_index], self.angle)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)

        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            #frames = self.animation
            self.frame_index = (self.frame_index + 1) % len(self.animation)
            self.image = self.animation[self.frame_index]
            #center = self.rect.center
            #self.rect = self.image.get_rect()
            #self.rect.center = center

            base_image = self.animation[self.frame_index]
            self.image = pygame.transform.rotate(base_image, self.angle)


    def draw(self, surface):
        surface.blit(self.image, self.rect)

        