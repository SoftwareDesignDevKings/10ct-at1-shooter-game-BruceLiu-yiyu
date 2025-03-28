import app
import pygame

class Bullet:
    def __init__(self, x, y, vx, vy, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        bullet = Bullet(x=100, y=200, vx=5, vy=0, size=20)
        fireball_image_path="assets/fireball.png"
        
        self.image = app.pygame.image.load(fireball_image_path).convert_alpha()
        self.image = app.pygame.transform.scale(self.image, (self.size, self.size))
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        surface.blit(self.image, self.rect)