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
    def __init__(self, x, y, assets):
        """Initialize the player with position and image assets."""
        # TODO: 1. Store the player's position
        self.x = x
        self.y = y

        # TODO: 2. Load the player's image from assets
        self.speed = app.PLAYER_SPEED
        self.animations = assets["player"]
        self.state = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8

        self.equipped_weapon = False
        self.weapon = None
        self.weapon_timer = 0
        self.weapon_durability = 20


        # TODO: 3. Create a collision rectangle (self.rect) 
        self.image = self.animations[self.state][self.frame_index]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        #self.mask = pygame.mask.from_surface(self.image)
        self.facing_left = False

        # TODO: 4. Add player health 
        self.xp = 0
        
        self.health = 5
        self.invincible = False

        self.bullet_speed = 10
        self.bullet_size = 10
        self.bullet_count = 1
        self.shoot_cooldown = 1
        self.shoot_timer = 0
        self.bullets = []
        self.assets = assets


        self.level = 1

    def handle_input(self):
        """Check and respond to keyboard/mouse input."""

        # TODO: 1. Capture Keyboard Input
        keys = pygame.key.get_pressed()
        # velocity in X, Y direction
        vel_x, vel_y = 0, 0

        # TODO: 2. Adjust player position with keys pressed, updating the player position to vel_x and vel_y
        if keys[pygame.K_LEFT]:
            # Move character left
            vel_x -= self.speed
        if keys[pygame.K_RIGHT]:
            vel_x += self.speed
        if keys[pygame.K_UP]:
            vel_y -= self.speed
        if keys[pygame.K_DOWN]:
            vel_y += self.speed
        
        if keys[pygame.K_a]:
            # Move character left
            vel_x -= self.speed
        if keys[pygame.K_d]:
            vel_x += self.speed
        if keys[pygame.K_w]:
            vel_y -= self.speed
        if keys[pygame.K_s]:
            vel_y += self.speed

        self.x += vel_x
        self.y += vel_y
        # TODO: 3. Clamp player position to screen bounds
        self.x = max(0, min(self.x, app.WIDTH))
        self.y = max(0, min(self.y, app.HEIGHT))
        self.rect.center = (self.x, self.y)

        # animation state
        if vel_x != 0 or vel_y != 0:
            self.state = "run"
        else:
            self.state = "idle"

        # direction
        if vel_x < 0:
            self.facing_left = True
        elif vel_x > 0:
            self.facing_left = False
        

    def update(self):

        for bullet in self.bullets:
            bullet.update()
            if bullet.y < 0 or bullet.y > app.HEIGHT or bullet.x < 0 or bullet.x > app.WIDTH:
                self.bullets.remove(bullet)


        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.animations[self.state]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center

        if self.equipped_weapon:
            self.equipped_weapon.facing_left = self.facing_left
            self.equipped_weapon.update(self)

            if self.weapon_cooldown > 0:
                self.weapon_cooldown -= 1
            

    def draw(self, surface):
        """Draw the player on the screen."""
        # TODO: Draw the image to the given surface at self.rect
        if self.facing_left:
            flipped_img = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_img, self.rect)
        else:
            surface.blit(self.image, self.rect)
        
        for bullet in self.bullets:
            bullet.draw(surface)

        if self.equipped_weapon:
            self.equipped_weapon.draw(surface)
        

    def take_damage(self, amount):
        """Reduce the player's health by a given amount, not going below zero."""
        if not self.invincible:
            self.health = max(0, self.health - amount)
            # Start the invincibility period
            self.invincible = True
            threading.Thread(target=self._start_invincibility_timer).start()
        else:
            pass

                

        
    def shoot_toward_position(self, tx, ty):
        if self.shoot_timer >= self.shoot_cooldown:
            return
        if self.weapon_timer >= self.shoot_cooldown:
            return
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            return

        vx = (dx / dist) * self.bullet_speed
        vy = (dy / dist) * self.bullet_speed

        angle_spread = 10
        base_angle = math.atan2(vy, vx)
        mid = (self.bullet_count - 1) / 2

        if self.equipped_weapon:
            if not self.equipped_weapon.use():  # REDUCES DURABILITY ONCE PER SHOT
                self.equipped_weapon = None

        for i in range(self.bullet_count):
            offset = i - mid
            spread_radians = math.radians(angle_spread * offset)
            angle = base_angle + spread_radians

            final_vx = math.cos(angle) * self.bullet_speed
            final_vy = math.sin(angle) * self.bullet_speed

            if self.equipped_weapon:
                bullet = Fireball(self.x, self.y, final_vx, final_vy, self.bullet_size, self.assets)
            else:
                bullet = Bullet(self.x, self.y, final_vx, final_vy, self.bullet_size)
            
            self.bullets.append(bullet)
        
        self.shoot_timer = 0
        self.weapon_cooldown = 5
        

    def shoot_toward_mouse(self, pos):
        mx, my = pos # m denotes mouse
        self.shoot_toward_position(mx, my)

    def shoot_toward_enemy(self, enemy):
        self.shoot_toward_position(enemy.x, enemy.y)

    def add_xp(self, amount):
        self.xp += amount

    def _start_invincibility_timer(self):
        """Manage the invincibility timer in a separate thread."""
        invincibility_duration = 0.7 
        time.sleep(invincibility_duration)
        self.invincible = False
    
    def equip_weapon (self, weapon): 
        if self.equipped_weapon:
            return  # Already have a weapon
        weapon.equipped = True
        self.equipped_weapon = weapon