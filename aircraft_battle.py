import pygame
import random
import os
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game constants
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 700

# Colors
WHITE = (255, 255, 255)

# Initialize the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Aircraft Battle")

# Check required files
def check_required_files():
    required_files = [
        "bg.png", "hero1.png", "enemy01.png", "enemy02.png", "enemy03.png",
        "b2.png", "b3.png", "effer.png", "effer2.png", "gameover.png",
        "baozha.ogg"
    ]
    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join("assets", file)):
            missing_files.append(file)
    if missing_files:
        print("Error: Missing required files in assets directory:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    return True

# Load images
def load_image(name):
    try:
        return pygame.image.load(os.path.join("assets", name)).convert_alpha()
    except pygame.error as e:
        print(f"Error loading image {name}: {e}")
        raise

# Game states
MENU = 0
PLAYING = 1
PAUSED = 2
GAME_OVER = 3

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = load_image("hero1.png")
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.last_shot = 0
        self.shoot_delay = 300  # 0.3 seconds in milliseconds

    def update(self):
        pos = pygame.mouse.get_pos()
        self.rect.centerx = pos[0]
        self.rect.centery = pos[1]
        
        # Keep player on screen
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = PlayerBullet(self.rect.centerx, self.rect.top)
            return bullet
        return None

class PlayerBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_image("b2.png")
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type):
        super().__init__()
        self.type = enemy_type
        if enemy_type == "red":
            self.image = load_image("enemy01.png")
            self.speed = 3
        elif enemy_type == "yellow":
            self.image = load_image("enemy02.png")
            self.speed = 4.5
        else:  # blue
            self.image = load_image("enemy03.png")
            self.speed = 4.5
            self.has_shot = False
            
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = load_image("b3.png")
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Calculate direction to target
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx * dx + dy * dy)
        self.speed = 6
        self.dx = dx / dist * self.speed
        self.dy = dy / dist * self.speed
        
        # Store position as float for precise movement
        self.float_x = float(x)
        self.float_y = float(y)

    def update(self):
        self.float_x += self.dx
        self.float_y += self.dy
        self.rect.x = int(self.float_x)
        self.rect.y = int(self.float_y)
        
        if (self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or 
            self.rect.right < 0 or self.rect.left > SCREEN_WIDTH):
            self.kill()

class Game:
    def __init__(self):
        self.load_assets()
        self.reset_game()

    def load_assets(self):
        # Load background
        self.background = load_image("bg.png")
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Load explosion sound
        try:
            self.explosion_sound = pygame.mixer.Sound(os.path.join("assets", "baozha.ogg"))
            self.explosion_sound.set_volume(0.5)  # Set volume to 50%
        except pygame.error as e:
            print(f"Error loading sound baozha.ogg: {e}")
            raise
        
        # Load game over image
        self.game_over_img = load_image("gameover.png")
        
        # Load explosion images
        self.explosion_img = load_image("effer.png")
        self.player_explosion_img = load_image("effer2.png")

    def reset_game(self):
        self.game_state = MENU
        self.score = 0
        self.lives = 3
        self.red_enemy_count = 0
        self.yellow_enemy_count = 0
        
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        
        # Create player
        self.player = Player()
        self.all_sprites.add(self.player)
        self.players.add(self.player)
        
        # Font setup
        self.font = pygame.font.Font(None, 36)

    def spawn_enemy(self):
        if len(self.enemies) < 3:  # Maximum 3 enemies at once
            if self.red_enemy_count >= 5 and random.random() < 0.3:
                enemy = Enemy("yellow")
                self.red_enemy_count = 0
                self.yellow_enemy_count += 1
            elif self.yellow_enemy_count >= 2 and random.random() < 0.3:
                enemy = Enemy("blue")
                self.yellow_enemy_count = 0
            else:
                enemy = Enemy("red")
                self.red_enemy_count += 1
            
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)

    def handle_collisions(self):
        # Player bullets hitting enemies
        hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, True, True)
        for hit in hits:
            self.score += 100
            self.explosion_sound.play()
            
        # Enemy bullets hitting player
        hits = pygame.sprite.groupcollide(self.players, self.enemy_bullets, True, True)
        if hits:
            self.explosion_sound.play()
            self.lives -= 1
            if self.lives > 0:
                self.player = Player()
                self.all_sprites.add(self.player)
                self.players.add(self.player)
            else:
                self.game_state = GAME_OVER
                
        # Enemies colliding with player
        hits = pygame.sprite.groupcollide(self.players, self.enemies, True, True)
        if hits:
            self.explosion_sound.play()
            self.lives -= 1
            if self.lives > 0:
                self.player = Player()
                self.all_sprites.add(self.player)
                self.players.add(self.player)
            else:
                self.game_state = GAME_OVER

    def update(self):
        if self.game_state == PLAYING:
            # Spawn enemies
            if random.random() < 0.03:  # Adjust spawn rate
                self.spawn_enemy()
                
            # Update all sprites
            self.all_sprites.update()
            
            # Handle enemy shooting
            for enemy in self.enemies:
                if enemy.type == "blue" and not enemy.has_shot:
                    if enemy.rect.centery > SCREEN_HEIGHT / 3:
                        enemy.has_shot = True
                        if self.player.alive():
                            bullet = EnemyBullet(
                                enemy.rect.centerx, 
                                enemy.rect.bottom,
                                self.player.rect.centerx,
                                self.player.rect.centery
                            )
                            self.all_sprites.add(bullet)
                            self.enemy_bullets.add(bullet)
            
            # Handle player shooting
            bullet = self.player.shoot()
            if bullet:
                self.all_sprites.add(bullet)
                self.player_bullets.add(bullet)
            
            # Check for collisions
            self.handle_collisions()

    def draw(self):
        screen.blit(self.background, (0, 0))
        
        if self.game_state == MENU:
            # Draw "Start" text
            start_text = self.font.render("Start", True, WHITE)
            text_rect = start_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            screen.blit(start_text, text_rect)
        
        elif self.game_state == PLAYING or self.game_state == PAUSED:
            self.all_sprites.draw(screen)
            
            # Draw score and lives
            score_text = self.font.render(f"Score: {self.score}", True, WHITE)
            lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
            screen.blit(score_text, (10, 10))
            screen.blit(lives_text, (SCREEN_WIDTH - 100, 10))
            
            if self.game_state == PAUSED:
                pause_text = self.font.render("PAUSED", True, WHITE)
                text_rect = pause_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
                screen.blit(pause_text, text_rect)
        
        elif self.game_state == GAME_OVER:
            game_over_rect = self.game_over_img.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            screen.blit(self.game_over_img, game_over_rect)
        
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state == MENU:
                        self.game_state = PLAYING
                    elif self.game_state == GAME_OVER:
                        self.reset_game()
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.game_state == PLAYING:
                            self.game_state = PAUSED
                        elif self.game_state == PAUSED:
                            self.game_state = PLAYING
            
            self.update()
            self.draw()
        
        pygame.quit()

if __name__ == "__main__":
    # Check for required files before starting
    if not check_required_files():
        print("Game cannot start due to missing files.")
        pygame.quit()
        exit(1)
    
    # Set up sound
    pygame.mixer.init()
    pygame.mixer.set_num_channels(8)  # Allow more simultaneous sounds
    
    game = Game()
    game.run()