import app
import pygame
import os
import math

class Bullet:
    """
    A basic projectile class representing bullets fired by the player.
    Handles movement, collision detection, and damage calculation.
    """

    def __init__(self, player, x, y, vx, vy, size):
        """
        Initialize a bullet projectile.
        
        Args:
            player (Player): The player instance that fired this bullet (for damage calculation)
            x (int): Starting x-coordinate
            y (int): Starting y-coordinate
            vx (float): Velocity component in x-direction
            vy (float): Velocity component in y-direction
            size (int): Diameter of the bullet in pixels
        """
        # Position and movement properties
        self.x = x  # Current x position
        self.y = y  # Current y position
        self.vx = vx  # Horizontal velocity
        self.vy = vy  # Vertical velocity
        self.size = size  # Bullet diameter
        
        # Combat properties
        self.damage = player.base_damage  # Damage based on player's current stats

        # Create bullet visual representation
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)  # Transparent surface
        self.image.fill((255, 255, 255))  # White bullet
        self.rect = self.image.get_rect(center=(self.x, self.y))  # Collision rectangle

    def update(self):
        """
        Update bullet position based on its velocity.
        Called once per frame to move the bullet.
        """
        # Apply velocity to position
        self.x += self.vx
        self.y += self.vy
        
        # Update collision rectangle position
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        """
        Draw the bullet on the specified surface.
        
        Args:
            surface (pygame.Surface): The game surface to draw the bullet on
        """
        surface.blit(self.image, self.rect)

        