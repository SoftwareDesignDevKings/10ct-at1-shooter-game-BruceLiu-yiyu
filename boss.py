from enemy import Enemy
import app
import random
import pygame

class Boss(Enemy):
    """
    A specialized Enemy class representing boss characters.
    Bosses have increased health, size, and difficulty compared to regular enemies.
    Inherits from the base Enemy class.
    """
    
    def __init__(self, x, y, enemy_assets, player, speed=2):
        """
        Initialize a boss enemy with enhanced properties.
        
        Args:
            x (int): Starting x-coordinate
            y (int): Starting y-coordinate
            enemy_assets (dict): Dictionary containing animation frames for different enemy types
            player (Player): Reference to the player for difficulty scaling
            speed (float): Movement speed (default 2, slower than regular enemies)
        """
        # Randomly select an enemy type to use as the base for this boss
        enemy_type = random.choice(list(enemy_assets.keys()))
        # Initialize using the parent Enemy class constructor
        super().__init__(x, y, enemy_type, enemy_assets, speed)
        
        # Boss-specific health scaling - significantly higher than regular enemies
        base_health = 50  # Base health value
        if player.level <= 10: 
            self.max_health = base_health * player.level  # Scale with player level
        else: 
            self.max_health = base_health * player.level * 5
        self.health = self.max_health  # Start at full health
        
        # Scale up the boss sprite to make it visually distinct
        boss_scale = 2  # Double the size of regular enemies (adjust as needed)
        
        # Resize all animation frames
        self.frames = [
            pygame.transform.scale(
                frame, 
                (int(frame.get_width() * boss_scale),  # New width
                 int(frame.get_height() * boss_scale))  # New height
            ) 
            for frame in self.frames
        ]
        
        # Update the current image and collision rectangle
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=(self.x, self.y))