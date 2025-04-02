# game.py
# Main game module for the shooter game

# Import required libraries and modules
import pygame
import random
import os
import math
import app
import time
import fireball
import bullet

# Import game classes
import weapon
from enemy import Enemy
from player import Player
from coin import Coin
from fireball import Fireball
from weapon import Weapon
from bullet import Bullet
from boss import Boss

def weighted_sample_without_replacement(items, weight_key, k):
    """
    Select k items from items using weights (from weight_key) without replacement.
    
    Args:
        items: List of items to choose from
        weight_key: Key in each item dictionary that contains the weight value
        k: Number of items to select
        
    Returns:
        List of selected items
    """
    chosen = []
    items_copy = list(items)
    while items_copy and len(chosen) < k:
        weights = [item[weight_key] for item in items_copy]
        selected = random.choices(items_copy, weights=weights, k=1)[0]
        chosen.append(selected)
        # Remove the selected item so it can't be chosen again
        items_copy.remove(selected)
    return chosen

class Game:
    """
    Main game class that handles game initialization, main loop, and game logic.
    """
    
    def __init__(self):
        """Initialize the game with all necessary components."""
        pygame.init()  # Initialize Pygame
        
        # Set up display
        self.screen = pygame.display.set_mode((app.WIDTH, app.HEIGHT))
        pygame.display.set_caption("Shooter")
        
        # Set up game clock
        self.clock = pygame.time.Clock()

        # Load game assets
        self.assets = app.load_assets()

        # Load fonts
        font_path = os.path.join("assets", "PressStart2P.ttf")
        self.font_small = pygame.font.Font(font_path, 18)
        self.font_large = pygame.font.Font(font_path, 32)

        # Create game background
        self.background = self.create_random_background(
            app.WIDTH, app.HEIGHT, self.assets["floor_tiles"]
        )
        
        # Game state flags
        self.running = True
        self.game_over = False

        # Game object containers
        self.coins = []
        self.weapons = []
        self.enemies = []
        
        # Enemy spawning variables
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 60
        self.enemies_per_spawn = 1

        # Boss enemy
        self.boss = None

        # Possible player upgrades with their properties
        self.possible_upgrades = [
            {"name": "SNIPER", "desc": "Bullets pierce enemies", "weight": 3, "min_level": 6},
            {"name": "SPEEDSTER", "desc": "Bullet speed +3, Player speed +80%", "weight": 7, "min_level": 1},
            {"name": "ARCHER", "desc": "Fire two additional bullet", "weight": 6, "min_level": 1},
            {"name": "BERSERK", "desc": "Damage multiplier x1.5", "weight": 4, "min_level": 3},
            {"name": "HEALER", "desc": "Heal 1 hp", "weight": 6, "min_level": 3}, 
            {"name": "INVESTOR", "desc": "25% more xp", "weight": 4, "min_level": 1}
        ]
        
        # Upgrade-related variables
        self.pierce_level = 0
        self.in_level_up_menu = False
        self.upgrade_options = []


        self.xp_scale_factor = 4  # XP scaling factor for level up

        # Initialize game state
        self.reset_game()

    def reset_game(self):
        """Reset the game to its initial state."""
        # Create player at center of screen
        self.player = Player(app.WIDTH // 2, app.HEIGHT // 2, self.assets)
        
        # Reset enemies
        self.enemies = []
        self.enemy_spawn_timer = 0
        self.enemies_per_spawn = 1

        # Reset coins
        self.coins = []

        # Reset upgrade stats
        self.pierce_level = 0
        self.pierce_count = 0
        
        # Reset player progression
        self.xp_value = 1
        self.player.level = 1
        self.boss = None
        self.weapons = []

        # Reset game state
        self.game_over = False

    def create_random_background(self, width, height, floor_tiles):
        """
        Create a randomly tiled background surface.
        
        Args:
            width: Width of the background
            height: Height of the background
            floor_tiles: List of tile images to use
            
        Returns:
            A pygame Surface with the tiled background
        """
        bg = pygame.Surface((width, height))
        tile_w = floor_tiles[0].get_width()
        tile_h = floor_tiles[0].get_height()

        # Tile the background with random floor tiles
        for y in range(0, height, tile_h):
            for x in range(0, width, tile_w):
                tile = random.choice(floor_tiles)
                bg.blit(tile, (x, y))

        return bg

    def run(self):
        """Main game loop."""
        while self.running:
            # Control game speed
            self.clock.tick(app.FPS)

            # Handle user input
            self.handle_events()

            # Update game state if not in menus
            if not self.game_over and not self.in_level_up_menu:
                self.update()

            # Draw everything
            self.draw()

        # Quit pygame when game loop ends
        pygame.quit()

    def handle_events(self):
        """Process user input (keyboard, mouse, quitting)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Quit the game if window is closed
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    # Game over screen controls
                    if event.key == pygame.K_r:
                        self.reset_game()  # Restart game
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False  # Quit game
                else:
                    if not self.in_level_up_menu:
                        # In-game controls
                        if event.key == pygame.K_SPACE:
                            # Shoot at nearest enemy
                            nearest_enemy = self.find_nearest_enemy()
                            if nearest_enemy:
                                self.player.shoot_toward_enemy(nearest_enemy)
                    else:
                        # Upgrade menu controls
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                            index = event.key - pygame.K_1  # 0,1,2
                            if 0 <= index < len(self.upgrade_options):
                                upgrade = self.upgrade_options[index]
                                self.apply_upgrade(self.player, upgrade)
                                self.in_level_up_menu = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Shoot toward mouse position
                    self.player.shoot_toward_mouse(event.pos)
    
    def update(self):
        """Update all game objects and check game state."""
        # Update player
        self.player.handle_input()
        self.player.update()
        
        # Update boss if present
        if hasattr(self, "boss") and self.boss is not None:
            self.boss.update(self.player)
            self.boss.draw(self.screen)
            # Remove boss if defeated
            if self.boss.health <= 0:
                self.boss = None

        # Only spawn/update regular enemies if no boss is active
        if self.boss is None:
            for enemy in self.enemies:
                enemy.update(self.player)

        # Check for collisions
        self.check_player_enemy_collisions()
        self.check_bullet_enemy_collisions()
        self.check_player_coin_collisions()
        self.check_player_weapon_collisions()
        
        # Check for game over
        if self.player.health <= 0:
            self.enemies.clear()
            self.game_over = True
            return
            
        # Spawn enemies and check for level up
        self.spawn_enemies()
        self.check_for_level_up()
        
    def draw(self):
        """Render all game elements to the screen."""
        # Draw background
        self.screen.blit(self.background, (0, 0))

        # Draw coins
        for coin in self.coins:
            coin.draw(self.screen)

        # Draw player if game is active
        if not self.game_over:
            self.player.draw(self.screen) 
        
        # Draw health display
        hp = max(0, min(self.player.health, 5))
        health_img = self.assets["health"][hp]
        self.screen.blit(health_img, (10, 10))

        # Draw XP information
        xp_text_surf = self.font_small.render(f"XP: {self.player.xp}", True, (255, 255, 255))
        self.screen.blit(xp_text_surf, (10, 70))

        next_level_xp = self.player.level * self.player.level * self.xp_scale_factor
        xp_to_next = max(0, next_level_xp - self.player.xp)
        xp_next_surf = self.font_small.render(f"Next Lvl XP: {xp_to_next}", True, (255, 255, 255))
        self.screen.blit(xp_next_surf, (10, 100))

        # Draw level display
        level_display = self.font_small.render(f"Level: {self.player.level}", True, (255, 255, 255))
        self.screen.blit(level_display, (10, 130))

        # Draw special screens if needed
        if self.game_over:
            self.draw_game_over_screen()
        if self.in_level_up_menu: 
            self.draw_upgrade_menu()
            
        # Draw boss or enemies
        if self.boss is not None:
            self.boss.draw(self.screen)
        else:
            for enemy in self.enemies:
                enemy.draw(self.screen)
        
        # Draw weapons
        for weapon in self.weapons:
            weapon.draw(self.screen)
            
        # Draw weapon durability if equipped
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
            
        # Update display
        pygame.display.flip()

    def spawn_enemies(self):
        """Spawn new enemies at regular intervals."""
        self.enemy_spawn_timer += 1
        
        # Don't spawn regular enemies if boss is active
        if hasattr(self, "boss") and self.boss is not None and self.boss.health > 0:
            return
        else: 
            if self.enemy_spawn_timer >= self.enemy_spawn_interval:
                self.enemy_spawn_timer = 0
                for _ in range(self.enemies_per_spawn):
                    # Choose random spawn side
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

                    # Create enemy with scaled stats based on player level
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
        """Check for collisions between player and enemies."""
        collided = False

        # Check boss collision
        if self.boss is not None:
            if pygame.sprite.collide_mask(self.boss, self.player):
                collided = True

        # Check regular enemy collisions
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
        """
        Draw the game over screen with options to restart or quit.
        """
        # Create a semi-transparent overlay for the game over screen
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with 180 alpha (semi-transparent)
        self.screen.blit(overlay, (0, 0))

        # Render "GAME OVER!" text in large red font
        game_over_surf = self.font_large.render("GAME OVER!", True, (255, 0, 0))
        game_over_rect = game_over_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 - 50))
        self.screen.blit(game_over_surf, game_over_rect)

        # Render restart instructions
        prompt_surf = self.font_small.render("Press R to Reset", True, (255, 255, 255))
        prompt_rect = prompt_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 2 + 20))
        self.screen.blit(prompt_surf, prompt_rect)

    def find_nearest_enemy(self):
        """
        Find the enemy closest to the player.
        
        Returns:
            The nearest Enemy object or None if no enemies exist
        """
        if not self.enemies:
            return None
            
        nearest = None
        min_dist = float('inf')  # Initialize with very large distance
        px, py = self.player.x, self.player.y
        
        # Calculate distance to each enemy and find the nearest one
        for enemy in self.enemies:
            dist = math.sqrt((enemy.x - px)**2 + (enemy.y - py)**2)
            if dist < min_dist:
                min_dist = dist
                nearest = enemy
        return nearest
    
    def check_bullet_enemy_collisions(self):
        """
        Check for collisions between bullets and enemies/boss.
        Handles damage application, piercing, and death effects.
        """
        # Loop over a copy of the bullets list to allow removal during iteration
        for bullet in self.player.bullets[:]:
            # Check for boss collision first
            if self.boss is not None:
                if pygame.sprite.collide_mask(bullet, self.boss):
                    self.boss.health -= bullet.damage
                    # Remove bullet unless it has piercing capability
                    if self.pierce_level <= 0: 
                        self.player.bullets.remove(bullet)
                    # Check if boss was defeated
                    if self.boss.health <= 0:
                        self.boss = None
                    break  # Stop checking other enemies for this bullet

            # Track how many enemies this bullet has pierced through
            bullet_pierce_count = 0
            hit_enemies = []  # Track enemies already hit by this bullet
            
            # Check collisions with regular enemies
            for enemy in self.enemies[:]:
                if pygame.sprite.collide_mask(bullet, enemy) and enemy not in hit_enemies:
                    hit_enemies.append(enemy)
                    enemy.health -= bullet.damage
                    bullet_pierce_count += 1

                    # Handle enemy death
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        # Random chance to drop weapon (2%) or coin (98%)
                        if random.random() < 0.02:
                            new_weapon = Weapon(enemy.x, enemy.y, self.assets)
                            self.weapons.append(new_weapon)
                        else:
                            new_coin = Coin(enemy.x, enemy.y)
                            self.coins.append(new_coin)

                    # Remove bullet if it has exceeded its pierce limit
                    if bullet_pierce_count > self.pierce_level:
                        self.player.bullets.remove(bullet)
                        break  # Stop checking other enemies for this bullet

    def check_player_coin_collisions(self):
        """
        Check for and handle player collisions with coins.
        Adds XP for each collected coin.
        """
        coins_collected = []
        for coin in self.coins:
            if coin.rect.colliderect(self.player.rect):
                coins_collected.append(coin)
                self.player.add_xp(self.xp_value)
            
        # Remove collected coins from game
        for c in coins_collected:
            if c in self.coins:
                self.coins.remove(c) 

    
    def check_player_weapon_collisions(self): 
        """
        Check for and handle player collisions with weapons.
        Equips collected weapons to the player.
        """
        collected_weapons = []
        for weapon in self.weapons: 
            if pygame.sprite.collide_mask(weapon, self.player):
                self.player.equip_weapon(weapon)
                collected_weapons.append(weapon)

        # Remove collected weapons from game
        for weapon in collected_weapons:
            self.weapons.remove(weapon)

    def pick_random_upgrades(self, num):
        """
        Select random upgrades based on player level and weights.
        
        Args:
            num: Number of upgrades to select
            
        Returns:
            List of selected upgrade dictionaries
        """
        # Filter available upgrades based on player level and health
        available_upgrades = [
            up for up in self.possible_upgrades 
            if self.player.level >= up.get("min_level", 1)
            and (up["name"] != "HEALER" or self.player.health < self.player.max_health)
        ]
        # Use weighted selection to pick upgrades
        return weighted_sample_without_replacement(available_upgrades, "weight", num)
    
    def apply_upgrade(self, player, upgrade):
        """
        Apply the selected upgrade to the player.
        
        Args:
            player: The Player object to upgrade
            upgrade: Dictionary containing upgrade details
        """
        name = upgrade["name"]
            
        if name == "BERSERK":
            player.base_damage *= 1.5  # Increase damage
        elif name == "SPEEDSTER":
            player.bullet_speed += 3  # Faster bullets
            player.speed += 0.8  # Faster movement
        elif name == "ARCHER":
            player.bullet_count += 2  # More bullets per shot
        elif name == "HEALER":
            # Heal player, with different amounts based on current health
            if player.health >= 5:
                player.health = 5  # Cap at max health
            elif player.health <= 1: 
                player.health += 2  # Bigger heal when very low
            else: 
                player.health += 1  # Normal heal
        elif name == "INVESTOR": 
            self.xp_value *= 1.25  # XP bonus
        elif name == "SNIPER":
            self.pierce_level += 1  # Bullets pierce enemies
            # Remove SNIPER from possible upgrades after taking it once
            self.possible_upgrades = [
                up for up in self.possible_upgrades if up["name"] != "SNIPER"
            ]

    def draw_upgrade_menu(self):
        """
        Draw the level-up upgrade selection menu.
        """
        # Create semi-transparent overlay
        overlay = pygame.Surface((app.WIDTH, app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Draw title
        title_surf = self.font_large.render("Choose an Upgrade!", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(app.WIDTH // 2, app.HEIGHT // 3 - 50))
        self.screen.blit(title_surf, title_rect)

        # Color mapping for different upgrade types
        upgrade_colors = {
            "BERSERK": (255, 0, 0),       # Red
            "SPEEDSTER": (255, 255, 0),    # Yellow
            "ARCHER": (0, 213, 255),     # Light Blue
            "SNIPER": (0, 255, 0),   # Green
            "HEALER": (255, 182, 193),   # Light pink
            "INVESTOR": (160, 32, 240)  # Purple
        }

        # Draw each upgrade option with its corresponding color
        for i, upgrade in enumerate(self.upgrade_options):
            text_str = f"{i+1}. {upgrade['name']} - {upgrade['desc']}"
            color = upgrade_colors.get(upgrade["name"].upper(), (255, 255, 255))
            option_surf = self.font_small.render(text_str, True, color)
            line_y = app.HEIGHT // 3 + i * 40
            option_rect = option_surf.get_rect(center=(app.WIDTH // 2, line_y))
            self.screen.blit(option_surf, option_rect)

    def check_for_level_up(self):
        """
        Check if player has enough XP to level up and handle level progression.
        Spawns boss every 5 levels.
        """
        xp_needed = self.player.level * self.player.level * self.xp_scale_factor
        if self.player.xp >= xp_needed:
            # Level up the player
            self.player.level += 1
            self.enemies.clear()  # Clear current enemies
            self.in_level_up_menu = True
            self.upgrade_options = self.pick_random_upgrades(3)  # Get 3 upgrade options
        
            # Every 5 levels, spawn a boss
            if self.player.level % 5 == 0:
                self.enemies.clear()  # Clear any remaining enemies
                self.coins.clear()  # Clear any remaining coins
                boss_x = app.WIDTH // 2
                boss_y = app.HEIGHT // 4
                selected_enemy_type = random.choice(list(self.assets["enemies"].keys()))
                self.boss = Boss(boss_x, boss_y, self.assets["enemies"], self.player, speed=2)
            else:
                self.boss = None  # Ensure no boss is active on non-boss levels

            # Increase enemy spawn rate with each level
            self.enemies_per_spawn += 1
