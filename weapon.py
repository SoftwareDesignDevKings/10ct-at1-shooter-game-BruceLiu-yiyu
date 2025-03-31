import pygame
import math

class Weapon:
    def __init__(self, x, y, assets):
        self.x = x
        self.y = y
        self.assets = assets
        self.animation = assets["weapons"]
        self.frame_index = 0
        self.animation_speed = 0.02
        self.image = self.animation[self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))
        self.max_durability = 40
        self.durability = self.max_durability
        self.equipped = False
        self.offset = (-30, 0)  # Position relative to player
        self.facing_left = False


    def update(self, player):
        if player:
            self.facing_left = player.facing_left
        # Update animation frames
        self.frame_index = (self.frame_index + 1) % len(self.animation)
        self.image = self.animation[self.frame_index]
        if self.facing_left:
            self.image = pygame.transform.flip(self.image, True, False)

        # Follow player when equipped
        if self.equipped and player:
            offset_x = -30 if player.facing_left else 30
            self.x = player.x + offset_x
            self.y = player.y
            self.rect.center = (self.x, self.y)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def use(self):
        """Reduce durability and return True if weapon still has charges"""
        self.durability -= 1
        return self.durability > 0  # Returns False when broken