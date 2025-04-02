import math
import pygame

class Fireball:
    """
    A specialized projectile class that represents magical fireballs.
    Features animated rotation and higher damage than regular bullets.
    """
    
    def __init__(self, player, x, y, vx, vy, size, assets):
        """
        Initialize a fireball projectile.
        
        Args:
            player (Player): The player who shot this fireball (for damage calculation)
            x (int): Starting x-coordinate
            y (int): Starting y-coordinate
            vx (float): Velocity in x-direction
            vy (float): Velocity in y-direction
            size (int): Base size of the projectile
            assets (dict): Dictionary containing animation assets
        """
        # Position and movement properties
        self.x = x
        self.y = y
        self.vx = vx  # Horizontal velocity
        self.vy = vy  # Vertical velocity
        self.size = size  # Projectile size
        
        # Animation properties
        self.animation = assets["bullets"]  # Fireball animation frames
        self.frame_index = 0  # Current animation frame
        self.animation_speed = 4  # Animation frame rate
        self.animation_timer = 0  # Animation timer
        
        # Combat properties
        self.damage = player.base_damage + 3  # Fireballs deal bonus damage
        
        # Calculate rotation angle based on movement direction
        # Negative vy because pygame's y-axis increases downward
        self.angle = math.degrees(math.atan2(-vy, vx))  
        
        # Initialize sprite image and collision rect
        self.image = pygame.transform.rotate(self.animation[self.frame_index], self.angle)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        """
        Update the fireball's position and animation.
        Called once per frame.
        """
        # Update position based on velocity
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)

        # Handle animation updates
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            # Advance to next animation frame
            self.frame_index = (self.frame_index + 1) % len(self.animation)
            
            # Update image with proper rotation
            base_image = self.animation[self.frame_index]
            self.image = pygame.transform.rotate(base_image, self.angle)

    def draw(self, surface):
        """
        Draw the fireball on the specified surface.
        
        Args:
            surface (pygame.Surface): The surface to draw on
        """
        surface.blit(self.image, self.rect)
        