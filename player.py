import threading
import pygame
import app  # Contains global settings like WIDTH, HEIGHT, PLAYER_SPEED, etc.
import math
import random
import time
import weapon

from bullet import Bullet
from fireball import Fireball

class Player:
    """
    The player character class that handles movement, combat, and state management.
    """
    
    def __init__(self, x, y, assets):
        """
        Initialize the player with position and assets.
        
        Args:
            x (int): Starting x-coordinate
            y (int): Starting y-coordinate
            assets (dict): Dictionary containing animation assets
        """
        # Position and movement properties
        self.x = x
        self.y = y
        self.speed = app.PLAYER_SPEED
        
        # Animation properties
        self.animations = assets["player"]
        self.state = "idle"  # Current animation state
        self.frame_index = 0  # Current animation frame
        self.animation_timer = 0
        self.animation_speed = 8  # Animation frame rate
        
        # Weapon properties
        self.equipped_weapon = False  # Whether player has a weapon
        self.weapon = None  # Weapon instance
        self.weapon_timer = 0  # Cooldown timer
        self.weapon_durability = 20  # Default weapon durability

        # Collision and rendering
        self.image = self.animations[self.state][self.frame_index]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.facing_left = False  # Direction player is facing

        # Health and stats
        self.xp = 0  # Experience points
        self.health = 5  # Current health
        self.max_health = 5  # Maximum health
        self.invincible = False  # Invincibility flag after taking damage

        # Combat properties
        self.bullet_speed = 10  # Speed of projectiles
        self.bullet_size = 10  # Size of projectiles
        self.bullet_count = 1  # Number of projectiles per shot
        self.shoot_cooldown = 1  # Shooting cooldown time
        self.shoot_timer = 0  # Current cooldown timer
        self.bullets = []  # Active projectiles
        self.assets = assets  # Reference to game assets
        self.base_damage = 1  # Base damage per projectile

        # Progression
        self.level = 1  # Current player level

    def handle_input(self):
        """Process keyboard input to control player movement."""
        keys = pygame.key.get_pressed()
        vel_x, vel_y = 0, 0  # Movement velocity components

        # Movement controls (arrow keys and WASD)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            vel_x -= self.speed  # Move left
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vel_x += self.speed  # Move right
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            vel_y -= self.speed  # Move up
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            vel_y += self.speed  # Move down

        # Update position with boundary checking
        self.x += vel_x
        self.y += vel_y
        self.x = max(0, min(self.x, app.WIDTH))  # Clamp to screen width
        self.y = max(0, min(self.y, app.HEIGHT))  # Clamp to screen height
        self.rect.center = (self.x, self.y)

        # Update animation state based on movement
        if vel_x != 0 or vel_y != 0:
            self.state = "run"  # Moving animation
        else:
            self.state = "idle"  # Standing animation

        # Update facing direction
        if vel_x < 0:
            self.facing_left = True  # Facing left
        elif vel_x > 0:
            self.facing_left = False  # Facing right

    def update(self):
        """Update player state including bullets, animation, and weapon."""
        # Update all active bullets
        for bullet in self.bullets[:]:  # Iterate over copy to allow removal
            bullet.update()
            # Remove bullets that go off-screen
            if (bullet.y < 0 or bullet.y > app.HEIGHT or 
                bullet.x < 0 or bullet.x > app.WIDTH):
                self.bullets.remove(bullet)

        # Handle animation updates
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations[self.state]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            # Maintain position during animation
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center

        # Update equipped weapon if present
        if self.equipped_weapon:
            self.equipped_weapon.facing_left = self.facing_left
            self.equipped_weapon.update(self)
            
            # Handle weapon cooldown
            if self.weapon_cooldown > 0:
                self.weapon_cooldown -= 1

    def draw(self, surface):
        """
        Draw the player and all active bullets on the given surface.
        
        Args:
            surface (pygame.Surface): The surface to draw on
        """
        # Draw player with proper facing direction
        if self.facing_left:
            flipped_img = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_img, self.rect)
        else:
            surface.blit(self.image, self.rect)
        
        # Draw all active bullets
        for bullet in self.bullets:
            bullet.draw(surface)

        # Draw equipped weapon if present
        if self.equipped_weapon:
            self.equipped_weapon.draw(surface)

    def take_damage(self, amount):
        """
        Reduce player health by specified amount, with invincibility frames.
        
        Args:
            amount (int): Amount of damage to take
        """
        if not self.invincible:
            self.health = max(0, self.health - amount)
            # Start invincibility period in separate thread
            self.invincible = True
            threading.Thread(target=self._start_invincibility_timer).start()

    def shoot_toward_position(self, tx, ty):
        """
        Shoot projectiles toward a target position.
        
        Args:
            tx (int): Target x-coordinate
            ty (int): Target y-coordinate
        """
        # Check shooting cooldown
        if (self.shoot_timer >= self.shoot_cooldown or 
            self.weapon_timer >= self.shoot_cooldown):
            return

        # Calculate direction vector
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:  # Prevent division by zero
            return

        # Normalize direction vector
        vx = (dx / dist) * self.bullet_speed
        vy = (dy / dist) * self.bullet_speed

        # Calculate spread for multiple projectiles
        angle_spread = 10  # Degrees between projectiles
        base_angle = math.atan2(vy, vx)  # Base angle toward target
        mid = (self.bullet_count - 1) / 2  # Middle projectile index

        # Use weapon durability if equipped
        if self.equipped_weapon:
            if not self.equipped_weapon.use():  # Returns False when broken
                self.equipped_weapon = None

        # Create each projectile
        for i in range(self.bullet_count):
            # Calculate spread angle for this projectile
            offset = i - mid
            spread_radians = math.radians(angle_spread * offset)
            angle = base_angle + spread_radians

            # Calculate final velocity components
            final_vx = math.cos(angle) * self.bullet_speed
            final_vy = math.sin(angle) * self.bullet_speed

            # Create appropriate bullet type
            if self.equipped_weapon:
                bullet = Fireball(self, self.x, self.y, final_vx, final_vy, 
                                 self.bullet_size, self.assets)
            else:
                bullet = Bullet(self, self.x, self.y, final_vx, final_vy, 
                              self.bullet_size)
            
            self.bullets.append(bullet)
        
        # Reset cooldown timers
        self.shoot_timer = 0
        self.weapon_cooldown = 5

    def shoot_toward_mouse(self, pos):
        """
        Shoot toward mouse cursor position.
        
        Args:
            pos (tuple): (x,y) mouse position
        """
        mx, my = pos
        self.shoot_toward_position(mx, my)

    def shoot_toward_enemy(self, enemy):
        """Shoot toward an enemy's position."""
        self.shoot_toward_position(enemy.x, enemy.y)

    def add_xp(self, amount):
        """Add experience points to the player."""
        self.xp += amount

    def _start_invincibility_timer(self):
        """
        Private method to handle invincibility timer in separate thread.
        Waits for duration then clears invincibility flag.
        """
        invincibility_duration = 0.7  # Seconds of invincibility
        time.sleep(invincibility_duration)
        self.invincible = False
    
    def equip_weapon(self, weapon): 
        """
        Equip a weapon to the player.
        
        Args:
            weapon (Weapon): The weapon to equip
        """
        if self.equipped_weapon:
            return  # Player can only hold one weapon at a time
            
        weapon.equipped = True
        self.equipped_weapon = weapon