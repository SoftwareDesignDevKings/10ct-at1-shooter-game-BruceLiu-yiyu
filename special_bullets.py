import math
import pygame
import time
class PiercingBullet:
    def __init__(self, base_bullet, pierce_count):
        self.__dict__ = base_bullet.__dict__.copy()
        self.pierce_remaining = pierce_count

class HomingBullet:
    def __init__(self, base_bullet, enemies):
        self.__dict__ = base_bullet.__dict__.copy()
        self.enemies = enemies
        self.homing_strength = 0.1
        self.current_target = None
        
    def find_nearest_enemy(self):
        # Implementation from previous answer
        pass
        
    def update(self):
        # Homing logic from previous answer
        super().update()

class ExplosiveBullet:
    def __init__(self, base_bullet, game_ref):
        self.__dict__ = base_bullet.__dict__.copy()
        self.game = game_ref
        self.exploded = False
        
    def explode(self):
        if not self.exploded:
            self.exploded = True
            # Damage enemies in radius
            for enemy in self.game.enemies:
                distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
                if distance < self.game.player.explosion_radius:
                    enemy.health -= self.game.player.explosion_damage
            # Add visual effect
            self.game.explosions.append(ExplosionEffect(self.x, self.y))
            
    def update(self):
        super().update()
        if self.should_explode():  # Implement collision/range check
            self.explode()

class ExplosionEffect:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 0
        self.max_radius = 50
        self.duration = 0.3  # seconds
        self.start_time = time.time()
        
    def update(self):
        elapsed = time.time() - self.start_time
        progress = elapsed / self.duration
        self.radius = int(self.max_radius * progress)
        return progress < 1.0
        
    def draw(self, surface):
        pygame.draw.circle(surface, (255, 150, 0), (int(self.x), int(self.y)), 
                         self.radius, 2)
        

class Explosion:
    def __init__(self, x, y):
        self.radius = 0
        self.max_radius = 50
        self.x = x
        self.y = y
        self.damage = 2
        self.duration = 0.5  # seconds
        self.start_time = time.time()

    def update(self):
        # Damage enemies in radius
        if self.radius < self.max_radius:
            self.radius += 150 * (1/60)  # 150 pixels per second

        # Check if still active
        return time.time() - self.start_time < self.duration