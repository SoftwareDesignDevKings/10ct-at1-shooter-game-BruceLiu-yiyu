import pygame
import app
import math

class Enemy:
    """
    Enemy class representing hostile creatures that chase and attack the player.
    Handles movement, animation, health, and knockback effects.
    """
    
    def __init__(self, x, y, enemy_type, enemy_assets, speed=app.DEFAULT_ENEMY_SPEED):
        """
        Initialize an enemy at specified position with given properties.
        
        Args:
            x (int): Starting x-coordinate
            y (int): Starting y-coordinate
            enemy_type (str): Type of enemy ('orc', 'demon', etc.)
            enemy_assets (dict): Dictionary containing animation frames
            speed (float): Movement speed (default from app settings)
        """
        # Position and movement properties
        self.x = x
        self.y = y
        self.speed = speed
        
        # Animation properties
        self.frames = enemy_assets[enemy_type]  # All animation frames
        self.frame_index = 0  # Current animation frame
        self.animation_timer = 0
        self.animation_speed = 8  # Animation frame rate
        self.image = self.frames[self.frame_index]  # Current displayed image
        self.rect = self.image.get_rect(center=(self.x, self.y))  # Collision rect
        
        # Enemy characteristics
        self.enemy_type = enemy_type  # Determines appearance and stats
        self.facing_left = False  # Direction enemy is facing
        
        # Knockback properties
        self.knockback_dist_remaining = 0  # Remaining knockback distance
        self.knockback_dx = 0  # Knockback x-direction
        self.knockback_dy = 0  # Knockback y-direction

        # Health system - varies by enemy type
        self.max_health = 0  # Base health (overridden per type)
        if enemy_type == "orc":
            self.max_health = 1  # Orcs have 1 health
        elif enemy_type == "demon":
            self.max_health = 2  # Demons have 2 health
        self.health = self.max_health  # Current health
        
    def update(self, player):
        """
        Update enemy state including movement and animation.
        
        Args:
            player (Player): The player instance to chase
        """
        # Handle knockback first if active
        if self.knockback_dist_remaining > 0:
            self.apply_knockback()
        else:
            # Normal movement toward player
            self.move_toward_player(player)
            
        # Update animation
        self.animate()

    def move_toward_player(self, player):
        """
        Move enemy toward the player's current position.
        
        Args:
            player (Player): The target player to move toward
        """
        # Calculate direction vector to player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = (dx**2 + dy**2) ** 0.5  # Distance to player
        
        if dist != 0:  # Prevent division by zero
            # Normalize direction and apply speed
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        
        # Update facing direction based on movement
        self.facing_left = dx < 0
        
        # Update collision rect position
        self.rect.center = (self.x, self.y)

    def apply_knockback(self):
        """
        Apply knockback effect to enemy movement.
        Called when enemy is hit by player attacks.
        """
        # Calculate knockback step for this frame
        step = min(app.ENEMY_KNOCKBACK_SPEED, self.knockback_dist_remaining)
        self.knockback_dist_remaining -= step

        # Apply knockback to position
        self.x += self.knockback_dx * step
        self.y += self.knockback_dy * step

        # Update facing direction based on knockback
        self.facing_left = self.knockback_dx < 0

        # Update collision rect position
        self.rect.center = (self.x, self.y)

    def animate(self):
        """Update enemy animation frame."""
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            # Cycle through animation frames
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            # Update image while maintaining position
            center = self.rect.center
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect()
            self.rect.center = center

    def draw(self, surface):
        """
        Draw enemy sprite and health bar on the given surface.
        
        Args:
            surface (pygame.Surface): The surface to draw on
        """
        # Draw facing correct direction
        if self.facing_left:
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)
            
        # Health bar dimensions
        health_bar_width = 40
        health_bar_height = 5
        health_percent = max(0, self.health / self.max_health)
        
        # Position health bar above enemy
        bar_x = self.rect.centerx - health_bar_width // 2
        bar_y = self.rect.top - 10  # 10 pixels above enemy
        
        # Draw health bar background (red)
        pygame.draw.rect(surface, (255, 0, 0), 
                        (bar_x, bar_y, health_bar_width, health_bar_height))
        
        # Draw current health (green)
        current_width = health_bar_width * health_percent
        pygame.draw.rect(surface, (0, 255, 0), 
                        (bar_x, bar_y, current_width, health_bar_height))

    def set_knockback(self, px, py, dist):
        """
        Initialize knockback effect away from a point.
        
        Args:
            px (int): Source x-coordinate of knockback
            py (int): Source y-coordinate of knockback
            dist (float): Total knockback distance
        """
        # Calculate direction away from source point
        dx = self.x - px
        dy = self.y - py
        length = math.sqrt(dx*dx + dy*dy)
        
        if length != 0:  # Normalize direction
            self.knockback_dx = dx / length
            self.knockback_dy = dy / length
            self.knockback_dist_remaining = dist

