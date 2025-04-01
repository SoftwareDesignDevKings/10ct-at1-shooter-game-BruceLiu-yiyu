# game.py
import pygame
import random
import os
import math
import app
import time
import fireball
import bullet

import weapon
from enemy import Enemy
from player import Player
from coin import Coin
from fireball import Fireball
from weapon import Weapon
from bullet import Bullet

#from powerups import Powerups


def weighted_sample_without_replacement(items, weight_key, k):
        """Select k items from items using weights (from weight_key) without replacement."""
        chosen = []
        items_copy = list(items)
        while items_copy and len(chosen) < k:
            weights = [item[weight_key] for item in items_copy]
            selected = random.choices(items_copy, weights=weights, k=1)[0]
            chosen.append(selected)
            # Remove the selected item so that it cannot be chosen again.
            items_copy.remove(selected)
        return chosen


class Game:
    def __init__(self):
        pygame.init()  # Initialize Pygame
        
        self.screen = pygame.display.set_mode((app.WIDTH, app.HEIGHT))
        pygame.display.set_caption("Shooter")

        
        self.clock = pygame.time.Clock()

        
        self.assets = app.load_assets()

        font_path = os.path.join("assets", "PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)

        self.background = self.create_random_background(
        app.WIDTH, app.HEIGHT, self.assets["floor_tiles"]
    )
        self.running = True
        self.game_over = False

        self.coins = []
        self.weapons = []
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 60
        self.enemies_per_spawn = 1

        self.possible_upgrades = [
            {"name": "SNIPER", "desc": "Bullets pierce enemies", "weight": 3, "min_level": 4},
            {"name": "SPEEDSTER", "desc": "Bullet speed +3, Player speed +50%", "weight": 8, "min_level": 1},
            {"name": "ARCHER", "desc": "Fire additional bullet", "weight": 6, "min_level": 1},
            {"name": "BERSERK", "desc": "Damage multiplier x1.5", "weight": 4, "min_level": 3},
            {"name": "HEALER", "desc": "Heal 1 hp", "weight": 6, "min_level": 3}, 
            {"name": "INVESTOR", "desc": "25% more xp", "weight": 3, "min_level": 1}
        ]
        self.pierce_level = 0
        
        self.in_level_up_menu = False
        self.upgrade_options = []

        self.reset_game()

    def reset_game(self):
        self.player = Player(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
        
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemies_per_spawn = 1

        self.coins = []

        self.pierce_level = 0
        self.pierce_count = 0
        
        self.xp_value = 1

        self.game_over = False

    def create_random_background(self, width, height, floor_tiles):
        bg = pygame.Surface((width, height))
        tile_w = floor_tiles[0].get_width()
        tile_h = floor_tiles[0].get_height()

        for y in range(0, height, tile_h):
            for x in range(0, width, tile_w):
                tile = random.choice(floor_tiles)
                bg.blit(tile, (x, y))

        return bg

    def run(self):
        while self.running:
            
            # TODO: Set a frame rate limit
            self.clock.tick(app.FPS)

            # TODO: Handle player input and events
            self.handle_events()

            # TODO: Update game objects
            if not self.game_over and not self.in_level_up_menu:
                self.update()

            # TODO: Draw everything on the screen
            self.draw()

        pygame.quit()

    def handle_events(self):
        """Process user input (keyboard, mouse, quitting)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                else:
                    if not self.in_level_up_menu:
                        if event.key == pygame.K_SPACE:
                            nearest_enemy = self.find_nearest_enemy()
                            if nearest_enemy:
                                self.player.shoot_toward_enemy(nearest_enemy)
                    else:
                        # In upgrade menu
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                            index = event.key - pygame.K_1  # 0,1,2
                            if 0 <= index < len(self.upgrade_options):
                                upgrade = self.upgrade_options[index]
                                self.apply_upgrade(self.player, upgrade)
                                self.in_level_up_menu = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.player.shoot_toward_mouse(event.pos)
        
    

    def update(self):
        self.player.handle_input()
        self.player.update()
        
        for enemy in self.enemies:
            enemy.update(self.player)

        self.check_player_enemy_collisions()
        self.check_bullet_enemy_collisions()
        self.check_player_coin_collisions()
        self.check_player_weapon_collisions()
        if self.player.health <= 0:
            self.enemies.clear()
            self.game_over = True
            return
        self.spawn_enemies()
        self.check_for_level_up()
        
    def draw(self):
        """Render all game elements to the screen."""
       
        # TODO: Draw the background
        self.screen.blit(self.background, (0, 0))

        for coin in self.coins:
            coin.draw(self.screen)

        # TODO: Draw player, enemies, UI elements
        if not self.game_over:
            self.player.draw(self.screen) 
        
        hp = max(0, min(self.player.health, 5))
        health_img = self.assets["health"][hp]
        self.screen.blit(health_img, (10, 10))

        xp_text_surf = self.font_small.render(f"XP: {self.player.xp}", True, (255, 255, 255))
        self.screen.blit(xp_text_surf, (10, 70))

        next_level_xp = self.player.level * self.player.level * 5
        xp_to_next = max(0, next_level_xp - self.player.xp)
        xp_next_surf = self.font_small.render(f"Next Lvl XP: {xp_to_next}", True, (255, 255, 255))
        self.screen.blit(xp_next_surf, (10, 100))

        level_display = self.font_small.render(f"Level: {self.player.level}", True, (255, 255, 255))
        self.screen.blit(level_display, (10, 130))

        if self.game_over:
            self.draw_game_over_screen()
        if self.in_level_up_menu: 
            self.draw_upgrade_menu()
            
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        for weapon in self.weapons:
            weapon.draw(self.screen)
        # Add durability display
        if self.player.equipped_weapon:
            weapon = self.player.equipped_weapon
            # Health bar dimensions and colors
            bar_width = 40
            bar_height = 6
            background_color = (211, 211, 211)    # Grey
            durability_color = (207, 159, 255)   # Purple
            
            # Calculate position above the wand
            bar_x = weapon.rect.centerx - bar_width // 2
            bar_y = weapon.rect.top - 20  # Position 20 pixels above the wand
            
            # Calculate current durability percentage
            dura_percent = weapon.durability / weapon.max_durability
            current_width = bar_width * dura_percent
            
            # Draw background
            pygame.draw.rect(self.screen, background_color, (bar_x, bar_y, bar_width, bar_height))
            # Draw current durability
            pygame.draw.rect(self.screen, durability_color, (bar_x, bar_y, current_width, bar_height))
        pygame.display.flip()

    def spawn_enemies(self):
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.enemy_spawn_timer = 0
            for _ in range(self.enemies_per_spawn):
                side = random.choice(["top", "bottom", "left", "right"])
                if side == "top":
                    x = random.randint(0, app.WIDTH)
                    y = -app.SPAWN_MARGIN
                elif side == "bottom":
                    x = random.randint(0, app.WIDTH)
                    y = app.HEIGHT + app.SPAWN_MARGIN
                elif side == "left":
                    x = -app.SPAWN_MARGIN
                    y = random.randint(0, app.HEIGHT)
                else:
                    x = app.WIDTH + app.SPAWN_MARGIN
                    y = random.randint(0, app.HEIGHT)

                enemy_type = random.choice(list(self.assets["enemies"].keys()))
                enemy = Enemy(x, y, enemy_type, self.assets["enemies"])
                if 20 > self.player.level > 5: 
                    enemy.max_health += self.player.level + 3
                elif self.player.level > 20:
                    enemy.max_health += self.player.level * 1.5
                else: 
                    enemy.max_health += self.player.level
                enemy.health = enemy.max_health
                self.enemies.append(enemy)

    def check_player_enemy_collisions(self):
        collided = False
        for enemy in self.enemies:
            if enemy.rect.colliderect(self.player.rect):
                collided = True
                break

        if collided:
            self.player.take_damage(1)
            px, py = self.player.x, self.player.y
            for enemy in self.enemies:
                    enemy.set_knockback(px, py, app.PUSHBACK_DISTANCE)


    def draw_game_over_screen(self):
        # Dark overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Game Over text
        game_over_surf = self.font_large.render("GAME OVER!", True, (255, 0, 0))
        game_over_rect = game_over_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 50))
        self.screen.blit(game_over_surf, game_over_rect)

        # Prompt to restart or quit
        prompt_surf = self.font_small.render("Press R to Reset", True, (255, 255, 255))
        prompt_rect = prompt_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 + 20))
        self.screen.blit(prompt_surf, prompt_rect)


    def find_nearest_enemy(self):
        if not self.enemies:
            return None
        nearest = None
        min_dist = float('inf')
        px, py = self.player.x, self.player.y
        for enemy in self.enemies:
            dist = math.sqrt((enemy.x - px)**2 + (enemy.y - py)**2)
            if dist < min_dist:
                min_dist = dist
                nearest = enemy
        return nearest
    
    def check_bullet_enemy_collisions(self):
        # Loop over a copy of the bullets list allowing removal during iteration.
        for bullet in self.player.bullets[:]:
            bullet_pierce_count = 0  # Reset piercing count for this bullet.
            hit_enemies = []  # List to store enemies already hit by this bullet.
            # Loop over a copy of the enemies list as well.
            for enemy in self.enemies[:]:
                # Check collision only if this enemy has not already been hit.
                if pygame.sprite.collide_mask(bullet, enemy) and enemy not in hit_enemies:
                    # Register that we've hit this enemy.
                    hit_enemies.append(enemy)
                    # Apply damage.
                    enemy.health -= bullet.damage
                    bullet_pierce_count += 1

                    # Check if enemy is dead.
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        # Spawn a weapon or a coin based on a random chance.
                        if random.random() < 0.02:  # 2% chance to drop a weapon
                            new_weapon = Weapon(enemy.x, enemy.y, self.assets)
                            self.weapons.append(new_weapon)
                        else:
                            new_coin = Coin(enemy.x, enemy.y)
                            self.coins.append(new_coin)

                    # If the bullet has exceeded its allowed pierce hits, remove it.
                    if bullet_pierce_count > self.pierce_level:
                        self.player.bullets.remove(bullet)
                        # No need to continue checking collisions for this bullet.
                        break
                              # Exit the inner loop if a collision is detected



    def check_player_coin_collisions(self):
        coins_collected = []
        for coin in self.coins:
            if coin.rect.colliderect(self.player.rect):
                coins_collected.append(coin)
                self.player.add_xp(self.xp_value)

        for c in coins_collected:
            if c in self.coins:
                self.coins.remove(c) 
    
    def check_player_weapon_collisions(self): 
        collected_weapons = []
        for weapon in self.weapons: 
            if pygame.sprite.collide_mask(weapon, self.player):
                self.player.equip_weapon(weapon)
                collected_weapons.append(weapon)

        for weapon in collected_weapons:
            self.weapons.remove(weapon)

    def pick_random_upgrades(self, num):
        available_upgrades = [
        up for up in self.possible_upgrades 
        if self.player.level >= up.get("min_level", 1)
        and (up["name"] != "HEALER" or self.player.health < self.player.max_health)
    ]
    # Use the weighted sampler to pick a few unique upgrades.
        return weighted_sample_without_replacement(available_upgrades, "weight", num)
    
    def apply_upgrade(self, player, upgrade):
        name = upgrade["name"]
            
        if name == "BERSERK":
            player.base_damage *= 1.5
        elif name == "SPEEDSTER":
            player.bullet_speed += 3
            player.speed += 0.5
        elif name == "ARCHER":
            player.bullet_count += 2
        elif name == "HEALER":
            if player.health >= 5:
                player.health = 5
            else: 
                player.health += 1
        elif name == "INVESTOR": 
            self.xp_value *= 1.25
        elif name == "SNIPER":
            self.pierce_level += 1
            self.possible_upgrades = [
            up for up in self.possible_upgrades if up["name"] != "SNIPER"
        ]



    def draw_upgrade_menu(self):
        # Dark overlay behind the menu
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_large.render("Choose an Upgrade!", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 3 - 50))
        self.screen.blit(title_surf, title_rect)

        # Options
        upgrade_colors = {
        "BERSERK": (255, 0, 0),       # Red
        "SPEEDSTER": (255, 255, 0),    # Yellow
        "ARCHER": (0, 213, 255),     # Light Blue
        "SNIPER": (0, 255, 0),   # Green
        "HEALER": (255, 182, 193),   # light pink
        "INVESTOR": (160, 32, 240)  # Purple
    }

        for i, upgrade in enumerate(self.upgrade_options):
            text_str = f"{i+1}. {upgrade['name']} - {upgrade['desc']}"
            # Get the color for this upgrade, defaulting to white, if not defined.
            color = upgrade_colors.get(upgrade["name"].upper(), (255, 255, 255))
            option_surf = self.font_small.render(text_str, True, color)
            line_y = app.HEIGHT // 3 + i * 40
            option_rect = option_surf.get_rect(center=(app.WIDTH // 2, line_y))
            self.screen.blit(option_surf, option_rect)


    def check_for_level_up(self):
        xp_needed = self.player.level * self.player.level * 5
        if self.player.xp >= xp_needed:
            # Leveled up
            self.player.level += 1
            self.enemies.clear()
            self.in_level_up_menu = True
            self.upgrade_options = self.pick_random_upgrades(3)

            # Increase enemy spawns each time we level up
            self.enemies_per_spawn += 1

    def weighted_sample_without_replacement(items, weight_key, k):
        """Select k items from items using weights (from weight_key) without replacement."""
        chosen = []
        items_copy = list(items)
        while items_copy and len(chosen) < k:
            weights = [item[weight_key] for item in items_copy]
            selected = random.choices(items_copy, weights=weights, k=1)[0]
            chosen.append(selected)
            # Remove the selected item so that it cannot be chosen again.
            items_copy.remove(selected)
        return chosen