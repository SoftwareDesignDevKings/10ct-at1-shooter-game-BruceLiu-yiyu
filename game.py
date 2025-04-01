# game.py
import pygame
import random
import os
import math
import app
import time
import weapon
from enemy import Enemy
from player import Player
from coin import Coin
from fireball import Fireball
from weapon import Weapon
#from powerups import Powerups

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
        
        self.in_level_up_menu = False
        self.upgrade_options = []

        self.reset_game()

    '''def simulate_chance(max_number):
            # Generate a random number between 1 and 100
            chance_value = random.randint(0, max_number)
            return chance_value'''
        
    def reset_game(self):
        self.player = Player(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
        
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemies_per_spawn = 1

        self.coins = []
        #self.powerups = []
        
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

        for explosion in self.explosions:
            explosion.draw(self.screen)
            # Refresh the screen
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
        prompt_surf = self.font_small.render("Press R to Play Again or ESC to Quit", True, (255, 255, 255))
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
        for bullet in self.player.bullets[:]:
            for enemy in self.enemies[:]:
                if pygame.sprite.collide_mask(bullet, enemy):
                    enemy.health -= bullet.damage
                # Remove bullet regardless of enemy survival
                    self.player.bullets.remove(bullet)
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)

                        new_coin = Coin(enemy.x, enemy.y)
                        self.coins.append(new_coin)  
                        if random.random() < 0.05: 
                            new_weapon = Weapon(enemy.x, enemy.y, self.assets)
                            self.weapons.append(new_weapon)
                        break  # Exit the inner loop if a collision is detected


    def check_player_coin_collisions(self):
        coins_collected = []
        for coin in self.coins:
            if coin.rect.colliderect(self.player.rect):
                coins_collected.append(coin)
                self.player.add_xp(1)

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
        possible_upgrades = [
        {"name": "Piercing Bullets", "desc": "Bullets pierce 1 extra enemy"},
        {"name": "Homing Bullets", "desc": "Bullets track nearby enemies"},
        {"name": "Explosive Rounds", "desc": "Bullets explode on impact"},
        {"name": "Faster Bullet", "desc": "Bullet speed +2"},
        {"name": "Extra Bullet", "desc": "Fire additional bullet"},
        {"name": "Shorter Cooldown", "desc": "Shoot more frequently"}
    ]
        return random.sample(possible_upgrades, k=num)
    
    def apply_upgrade(self, player, upgrade):
        name = upgrade["name"]
            
        if name == "Higher Damage":
            for bullet in self.player.bullets: 
                bullet.damage *= 1.5
        elif name == "Faster Bullet":
            player.bullet_speed += 2
        elif name == "Extra Bullet":
            player.bullet_count += 1
        elif name == "Homing Bullets":
            player.homing = True
        elif name == "Piercing Bullets":
            player.piercing += 1
        elif name == "Explosive Rounds":
            player.explosive = True



    def draw_upgrade_menu(self):
        # Dark overlay behind the menu
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_large.render("Choose an Upgrade!", True, (255, 255, 0))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 3 - 50))
        self.screen.blit(title_surf, title_rect)

        # Options
        for i, upgrade in enumerate(self.upgrade_options):
            text_str = f"{i+1}. {upgrade['name']} - {upgrade['desc']}"
            option_surf = self.font_small.render(text_str, True, (255, 255, 255))
            line_y = app.HEIGHT // 3 + i * 40
            option_rect = option_surf.get_rect(center=(app.WIDTH // 2, line_y))
            self.screen.blit(option_surf, option_rect)


    def check_for_level_up(self):
        xp_needed = self.player.level * self.player.level * 5
        if self.player.xp >= xp_needed:
            # Leveled up
            self.player.level += 1
            self.in_level_up_menu = True
            self.upgrade_options = self.pick_random_upgrades(3)

            # Increase enemy spawns each time we level up
            self.enemies_per_spawn += 1