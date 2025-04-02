import pygame
import math

class Weapon:
    """
    A weapon class that can be equipped by the player.
    Handles weapon animation, positioning, and durability.
    """
    
    def __init__(self, x, y, assets):
        """
        Initialize a weapon at specified position with given assets.
        
        Args:
            x (int): Initial x-coordinate of the weapon
            y (int): Initial y-coordinate of the weapon
            assets (dict): Dictionary containing weapon animation frames
        """
        # Position and rendering properties
        self.x = x
        self.y = y
        self.assets = assets
        self.animation = assets["weapons"]  # Animation frames
        self.frame_index = 0  # Current animation frame
        self.animation_speed = 0.02  # Speed of animation
        self.image = self.animation[self.frame_index]  # Current image
        self.rect = self.image.get_rect(center=(x, y))  # Collision/position rectangle
        
        # Durability properties
        self.max_durability = 40  # Maximum uses before breaking
        self.durability = self.max_durability  # Current durability
        
        # Equipment status
        self.equipped = False  # Whether weapon is currently equipped
        self.offset = (-30, 0)  # Position relative to player when equipped
        self.facing_left = False  # Direction weapon is facing

    def update(self, player):
        """
        Update weapon state including animation and positioning.
        
        Args:
            player (Player): The player instance this weapon may be following
        """
        # Update facing direction based on player
        if player:
            self.facing_left = player.facing_left
            
        # Advance animation frame
        self.frame_index = (self.frame_index + 1) % len(self.animation)
        self.image = self.animation[self.frame_index]
        
        # Flip image if facing left
        if self.facing_left:
            self.image = pygame.transform.flip(self.image, True, False)

        # Handle positioning when equipped to player
        if self.equipped and player:
            # Calculate offset based on facing direction
            offset_x = -30 if player.facing_left else 30
            # Update position to follow player
            self.x = player.x + offset_x
            self.y = player.y
            self.rect.center = (self.x, self.y)

    def draw(self, surface):
        """
        Draw the weapon on the specified surface.
        
        Args:
            surface (pygame.Surface): The surface to draw the weapon on
        """
        surface.blit(self.image, self.rect)

    def use(self):
        """
        Use the weapon (reduce durability by one charge).
        
        Returns:
            bool: True if weapon still has durability, False if broken
        """
        self.durability -= 1
        return self.durability > 0  # Returns False when broken