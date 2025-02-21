import pygame
import random
import math
import time
import pygame.gfxdraw
import pygame.mixer
from pygame import Vector2
import os
from pathlib import Path

# Game constants
WIDTH = 800
HEIGHT = 600

# Initialize Pygame with better graphics
pygame.init()
pygame.mixer.init()
pygame.display.set_caption("Geometry Rush")

# Set up better graphics
FLAGS = pygame.DOUBLEBUF | pygame.HWSURFACE
screen = pygame.display.set_mode((WIDTH, HEIGHT), FLAGS)
screen.set_alpha(None)  # Improves performance

# Load and set up sounds
SOUND_DIR = Path("sounds")
SOUND_DIR.mkdir(exist_ok=True)

class SoundManager:
    def __init__(self):
        self.sounds = {
            'jump': pygame.mixer.Sound('sounds/jump.wav') if os.path.exists('sounds/jump.wav') else None,
            'death': pygame.mixer.Sound('sounds/death.wav') if os.path.exists('sounds/death.wav') else None,
            'portal': pygame.mixer.Sound('sounds/portal.wav') if os.path.exists('sounds/portal.wav') else None,
            'music': 'sounds/background.mp3' if os.path.exists('sounds/background.mp3') else None
        }
        
    def play(self, sound_name, volume=1.0):
        if self.sounds.get(sound_name):
            self.sounds[sound_name].set_volume(volume)
            self.sounds[sound_name].play()

    def play_music(self):
        if self.sounds['music']:
            pygame.mixer.music.load(self.sounds['music'])
            pygame.mixer.music.play(-1)  # Loop indefinitely

class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.surf = pygame.Surface((10, 10), pygame.SRCALPHA)
        
    def emit(self, pos, color, num_particles=10, speed_range=(2, 5), size_range=(2, 6)):
        for _ in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(*speed_range)
            size = random.uniform(*size_range)
            lifetime = random.randint(20, 40)
            
            self.particles.append({
                'pos': Vector2(pos),
                'vel': Vector2(math.cos(angle), math.sin(angle)) * speed,
                'color': color,
                'size': size,
                'lifetime': lifetime,
                'max_lifetime': lifetime
            })

    def update_and_draw(self, screen, camera_offset=(0, 0)):
        alive_particles = []
        for p in self.particles:
            p['pos'] += p['vel']
            p['lifetime'] -= 1
            
            if p['lifetime'] > 0:
                alpha = int(255 * (p['lifetime'] / p['max_lifetime']))
                color = (*p['color'], alpha)
                
                pos = (int(p['pos'].x - camera_offset[0]), 
                      int(p['pos'].y - camera_offset[1]))
                
                # Draw glow effect
                for radius in range(int(p['size'] * 2), 0, -1):
                    alpha = int(100 * (radius / (p['size'] * 2)))
                    pygame.gfxdraw.filled_circle(screen, 
                                              pos[0], pos[1], 
                                              radius, 
                                              (*p['color'], alpha))
                
                alive_particles.append(p)
                
        self.particles = alive_particles

class GlowEffect:
    @staticmethod
    def draw_glow(surface, color, pos, radius, intensity=1):
        glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        for i in range(radius, 0, -2):
            alpha = int(intensity * (i / radius) * 255)
            pygame.draw.circle(glow_surf, (*color, alpha), 
                            (radius * 2, radius * 2), i)
        surface.blit(glow_surf, (pos[0] - radius * 2, pos[1] - radius * 2), 
                    special_flags=pygame.BLEND_ADD)

# Colors
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GRID_COLOR = (40, 40, 40)
GROUND_COLOR = (30, 30, 30)
CYAN = (0, 255, 255)

# Add new colors for zones
GRASS_COLORS = [(34, 139, 34), (0, 100, 0), (50, 205, 50)]
SNOW_COLORS = [(255, 250, 250), (240, 248, 255), (176, 196, 222)]
LAVA_COLORS = [(255, 69, 0), (178, 34, 34), (139, 0, 0)]

# Add new colors
ORANGE = (255, 165, 0)
PURPLE = (147, 0, 211)
GREEN = (0, 255, 0)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = 30
        self.velocity = [random.uniform(-2, 2), random.uniform(-5, -1)]
        self.size = random.randint(3, 6)

    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)

    def draw(self, screen, camera_offset):
        if self.lifetime > 0:
            pygame.draw.circle(screen, self.color, 
                             (int(self.x - camera_offset[0]), 
                              int(self.y - camera_offset[1])), 
                             int(self.size))

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.target_y = 0

    def update(self, target_x, target_y):
        self.x = target_x - WIDTH/3
        self.target_y = target_y - HEIGHT/2
        # Smooth camera vertical following
        self.y += (self.target_y - self.y) * 0.1

class Zone:
    def __init__(self, type_name, start_x):
        self.type = type_name
        self.start_x = start_x
        self.length = 3000  # Length of each zone
        if type_name == "grass":
            self.colors = GRASS_COLORS
            self.bg_color = (100, 200, 100)
        elif type_name == "snow":
            self.colors = SNOW_COLORS
            self.bg_color = (200, 225, 255)
        elif type_name == "lava":
            self.colors = LAVA_COLORS
            self.bg_color = (150, 50, 0)

class GameState:
    MAIN_MENU = 0
    SETTINGS = 1
    LOADING = 2
    PLAYING = 3
    PAUSED = 4
    GAME_OVER = 5
    RESPAWNING = 6

class Settings:
    def __init__(self):
        self.music_volume = 100
        self.sfx_volume = 100
        self.difficulty = "Normal"
        self.selected_option = 0
        self.options = ["Music Volume", "SFX Volume", "Difficulty", "Back"]
        self.difficulties = ["Easy", "Normal", "Hard"]

    def update(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.options)
            elif event.key == pygame.K_LEFT:
                self.adjust_setting(-1)
            elif event.key == pygame.K_RIGHT:
                self.adjust_setting(1)
            elif event.key == pygame.K_RETURN and self.options[self.selected_option] == "Back":
                return GameState.MAIN_MENU
        return GameState.SETTINGS

    def adjust_setting(self, direction):
        option = self.options[self.selected_option]
        if option == "Music Volume":
            self.music_volume = max(0, min(100, self.music_volume + direction * 10))
        elif option == "SFX Volume":
            self.sfx_volume = max(0, min(100, self.sfx_volume + direction * 10))
        elif option == "Difficulty":
            current_idx = self.difficulties.index(self.difficulty)
            new_idx = (current_idx + direction) % len(self.difficulties)
            self.difficulty = self.difficulties[new_idx]

    def draw(self, screen):
        screen.fill((20, 20, 40))
        
        # Draw fancy background
        for i in range(20):
            color = (40 + i * 2, 40 + i * 2, 80 + i * 2)
            pygame.draw.rect(screen, color, (0, i * 30, WIDTH, 30))

        title_font = pygame.font.Font(None, 74)
        option_font = pygame.font.Font(None, 50)
        
        # Draw title with shadow
        title = title_font.render("Settings", True, WHITE)
        title_shadow = title_font.render("Settings", True, (40, 40, 40))
        title_rect = title.get_rect(center=(WIDTH/2, 100))
        screen.blit(title_shadow, (title_rect.x + 3, title_rect.y + 3))
        screen.blit(title, title_rect)

        y_position = 200
        for i, option in enumerate(self.options):
            selected = i == self.selected_option
            color = CYAN if selected else WHITE
            
            if option == "Music Volume":
                text = f"Music Volume: {self.music_volume}%"
            elif option == "SFX Volume":
                text = f"SFX Volume: {self.sfx_volume}%"
            elif option == "Difficulty":
                text = f"Difficulty: {self.difficulty}"
            else:
                text = option

            option_text = option_font.render(text, True, color)
            if selected:
                pygame.draw.rect(screen, color, (WIDTH/4, y_position - 5, WIDTH/2, 50), 2)
            
            screen.blit(option_text, (WIDTH/2 - option_text.get_width()/2, y_position))
            y_position += 80

class Game:
    def __init__(self):
        self.state = GameState.MAIN_MENU
        self.loading_progress = 0
        self.particles = []
        self.camera = Camera()
        self.player = Player()
        self.game_objects = []
        self.zones = self.generate_zones()
        self.current_zone = self.zones[0]
        self.score = 0
        self.settings = Settings()
        self.menu_selection = 0
        self.menu_options = ["Play", "Settings", "Quit"]
        self.high_score = 0
        self.respawn_timer = 60
        self.respawn_duration = 60
        self.respawn_animation = 0
        self.death_time = 0
        self.game_over_particles = []

    def generate_zones(self):
        zones = []
        zone_types = ["grass", "snow", "lava"]
        for i in range(len(zone_types)):
            zones.append(Zone(zone_types[i], i * 3000))
        return zones

    def update_current_zone(self):
        for zone in self.zones:
            if zone.start_x <= self.player.x < zone.start_x + zone.length:
                self.current_zone = zone
                break

    def draw_loading_screen(self, screen):
        screen.fill((20, 20, 40))
        self.loading_progress += 2
        progress = min(100, self.loading_progress)
        
        # Draw fancy loading animation
        pygame.draw.rect(screen, (40, 40, 80), (WIDTH/4 - 5, HEIGHT/2 - 25, WIDTH/2 + 10, 50))
        pygame.draw.rect(screen, WHITE, (WIDTH/4, HEIGHT/2 - 20, WIDTH/2, 40))
        progress_width = (WIDTH/2) * (progress/100)
        gradient_bars = 20
        bar_width = progress_width / gradient_bars
        
        for i in range(gradient_bars):
            bar_color = (0, 200 - i * 5, 255 - i * 5)
            bar_x = WIDTH/4 + (i * bar_width)
            if bar_x < WIDTH/4 + progress_width:
                pygame.draw.rect(screen, bar_color, 
                               (bar_x, HEIGHT/2 - 15, bar_width + 1, 30))

        # Draw loading text with animation
        font = pygame.font.Font(None, 50)
        dots = "." * ((pygame.time.get_ticks() // 500) % 4)
        loading_text = font.render(f"Loading{dots}", True, WHITE)
        screen.blit(loading_text, (WIDTH/2 - loading_text.get_width()/2, HEIGHT/2 + 50))
        
        if progress >= 100:
            self.state = GameState.PLAYING
            self.game_objects = generate_level_segment(800, 0)

    def draw_menu(self, screen):
        screen.fill((20, 20, 40))
        
        # Draw animated background
        t = pygame.time.get_ticks() / 1000
        for i in range(20):
            y = (i * 40 + t * 50) % HEIGHT
            pygame.draw.line(screen, (40, 40, 80), (0, y), (WIDTH, y), 2)

        title_font = pygame.font.Font(None, 100)
        option_font = pygame.font.Font(None, 60)

        # Draw title with glow effect
        title = "Cubic Hopper"
        for offset in range(5, 0, -1):
            color = (0, 100 + offset * 30, 255 - offset * 30)
            title_text = title_font.render(title, True, color)
            title_rect = title_text.get_rect(center=(WIDTH/2, HEIGHT/4))
            screen.blit(title_text, (title_rect.x + offset, title_rect.y + offset))
        
        title_text = title_font.render(title, True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH/2, HEIGHT/4))
        screen.blit(title_text, title_rect)

        # Draw menu options
        for i, option in enumerate(self.menu_options):
            selected = i == self.menu_selection
            color = CYAN if selected else WHITE
            text = option_font.render(option, True, color)
            text_rect = text.get_rect(center=(WIDTH/2, HEIGHT/2 + i * 80))
            
            if selected:
                # Draw selection indicator
                pygame.draw.rect(screen, color, 
                               (text_rect.x - 20, text_rect.y - 10, 
                                text_rect.width + 40, text_rect.height + 20), 3)
                # Draw animated arrows
                arrow_offset = abs(math.sin(t * 5)) * 20
                pygame.draw.polygon(screen, color, 
                    [(text_rect.x - 40 - arrow_offset, text_rect.centery),
                     (text_rect.x - 20 - arrow_offset, text_rect.centery - 10),
                     (text_rect.x - 20 - arrow_offset, text_rect.centery + 10)])
                pygame.draw.polygon(screen, color,
                    [(text_rect.right + 40 + arrow_offset, text_rect.centery),
                     (text_rect.right + 20 + arrow_offset, text_rect.centery - 10),
                     (text_rect.right + 20 + arrow_offset, text_rect.centery + 10)])
            
            screen.blit(text, text_rect)

    def start_new_game(self):
        self.player = Player()
        self.game_objects = generate_level_segment(800, 0)
        self.particles = []
        self.game_over_particles = []
        self.score = 0
        self.respawn_timer = 60
        self.respawn_duration = 60
        self.state = GameState.RESPAWNING
        self.respawn_animation = 0

    def draw_game_over(self, screen):
        # Darken the background
        dark_surface = pygame.Surface((WIDTH, HEIGHT))
        dark_surface.fill((0, 0, 0))
        dark_surface.set_alpha(128)
        screen.blit(dark_surface, (0, 0))

        # Calculate time since death for animations
        time_since_death = pygame.time.get_ticks() - self.death_time
        animation_progress = min(1, time_since_death / 1000)  # 1 second animation

        # Create game over particles if needed
        if len(self.game_over_particles) == 0:
            for _ in range(50):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(2, 5)
                color = random.choice([GOLD, SILVER, WHITE])
                self.game_over_particles.append({
                    'x': WIDTH/2,
                    'y': HEIGHT/2,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'color': color,
                    'size': random.randint(2, 4)
                })

        # Update and draw particles
        for particle in self.game_over_particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.1  # Gravity
            pygame.draw.circle(screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 
                             particle['size'])

        # Draw game over text with animation
        title_font = pygame.font.Font(None, 100)
        score_font = pygame.font.Font(None, 74)
        
        # Animated title
        title_y = HEIGHT/3 - 50 * (1 - animation_progress)
        game_over_text = title_font.render("Game Over!", True, WHITE)
        text_rect = game_over_text.get_rect(center=(WIDTH/2, title_y))
        
        # Add glow effect
        for offset in range(3):
            glow_surface = title_font.render("Game Over!", True, (50, 50, 150))
            glow_rect = glow_surface.get_rect(center=(WIDTH/2 + offset, title_y + offset))
            screen.blit(glow_surface, glow_rect)
        screen.blit(game_over_text, text_rect)

        # Score display with animation
        score_y = HEIGHT/2 + 50 * animation_progress
        score_text = score_font.render(f"Score: {self.score}", True, GOLD)
        high_score_text = score_font.render(f"Best: {self.high_score}", True, SILVER)
        
        screen.blit(score_text, score_text.get_rect(center=(WIDTH/2, score_y)))
        screen.blit(high_score_text, high_score_text.get_rect(center=(WIDTH/2, score_y + 60)))

        # Draw restart prompt with pulsing animation
        if time_since_death > 1000:  # Show after 1 second
            prompt_font = pygame.font.Font(None, 50)
            pulse = (math.sin(time_since_death / 200) + 1) / 2  # Pulsing effect
            prompt_color = (255, 255, 255, int(128 + 127 * pulse))
            prompt_text = prompt_font.render("Press SPACE to Restart", True, prompt_color)
            screen.blit(prompt_text, prompt_text.get_rect(center=(WIDTH/2, HEIGHT * 3/4)))

    def draw_respawn_animation(self, screen):
        # Draw regular game state
        screen.fill(self.current_zone.bg_color)
        camera_offset = (self.camera.x, self.camera.y)
        draw_background(screen, camera_offset, self.current_zone)
        
        # Draw all game objects
        for obj in self.game_objects:
            obj.draw(screen, camera_offset)
        
        self.player.draw(screen, camera_offset)
        
        # Add respawn animation overlay
        self.respawn_animation += 1
        progress = min(1.0, self.respawn_animation / max(1, self.respawn_duration))
        
        # Flash effect
        flash_alpha = int(255 * (1 - progress))
        flash_surface = pygame.Surface((WIDTH, HEIGHT))
        flash_surface.fill(WHITE)
        flash_surface.set_alpha(flash_alpha)
        screen.blit(flash_surface, (0, 0))
        
        # Zoom effect on player
        if progress < 1:
            zoom = 2 - progress
            player_surface = pygame.Surface((int(self.player.size * zoom), int(self.player.size * zoom)), pygame.SRCALPHA)
            pygame.draw.rect(player_surface, BLUE, (0, 0, int(self.player.size * zoom), int(self.player.size * zoom)))
            screen.blit(player_surface, (
                self.player.x - int(self.player.size * zoom/2),
                self.player.y - int(self.player.size * zoom/2)
            ))

    def update_game(self):
        if self.state == GameState.RESPAWNING:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.state = GameState.PLAYING
                self.respawn_timer = self.respawn_duration
            return

        if self.player.is_dead:
            if self.state != GameState.GAME_OVER:
                self.state = GameState.GAME_OVER
                self.death_time = pygame.time.get_ticks()
                self.high_score = max(self.high_score, self.score)
            return

        if self.player.is_dead:
            return

        self.player.update()
        self.camera.update(self.player.x, self.player.y)
        self.update_current_zone()

        # Update and check all game objects
        to_remove = []
        for obj in self.game_objects:
            if isinstance(obj, Portal):
                if (self.player.x < obj.x + obj.width and
                    self.player.x + self.player.size > obj.x):
                    self.player.apply_portal_effect(obj.type, obj.effects[obj.type]["multiplier"])
                    # Add particles
                    for _ in range(10):
                        self.particles.append(Particle(obj.x, obj.y, obj.color))
            elif isinstance(obj, Obstacle) and obj.type == "spike":
                if (self.player.x < obj.x + obj.width and
                    self.player.x + self.player.size > obj.x and
                    self.player.y < obj.y + obj.height and
                    self.player.y + self.player.size > obj.y):
                    self.particles.extend(self.player.die())

            # Remove objects that are far behind
            if obj.x < self.player.x - WIDTH:
                to_remove.append(obj)
                self.score += 1

        # Remove off-screen objects
        for obj in to_remove:
            self.game_objects.remove(obj)

        # Generate new objects with increasing difficulty
        if not self.game_objects or self.player.x > max(obj.x for obj in self.game_objects) - WIDTH:
            next_x = (max(obj.x for obj in self.game_objects) 
                     if self.game_objects 
                     else self.player.x + WIDTH)
            difficulty = int(self.player.x_pos)  # Ensure difficulty is an integer
            new_objects = generate_level_segment(int(next_x), difficulty)
            self.game_objects.extend(new_objects)

        # Update particles
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for particle in self.particles:
            particle.update()

class Player:
    def __init__(self):
        self.x = 100
        self.y = HEIGHT - 150
        self.size = 40
        self.velocity = 0
        self.gravity = 0.8
        self.jump_power = -15
        self.is_jumping = False
        self.rotation = 0
        self.rotation_speed = 5
        self.ground_y = HEIGHT - 150
        self.rotation_velocity = 0
        self.speed = 5  # Add horizontal speed
        self.x_pos = 0  # Track total distance
        self.is_dead = False
        self.speed_multiplier = 1.0
        self.gravity_multiplier = 1.0
        self.size_multiplier = 1.0
        self.particle_system = ParticleSystem()
        self.trail_points = []
        self.glow_color = (0, 255, 255)
        self.glow_intensity = 1.0

    def jump(self, boost=False):
        if not self.is_jumping or boost:
            self.velocity = self.jump_power * (2 if boost else 1)
            self.is_jumping = True

    def update(self):
        if self.is_dead:
            return

        # Apply multipliers to movement
        actual_speed = self.speed * self.speed_multiplier
        self.x += actual_speed
        self.x_pos += actual_speed
        
        if self.is_jumping:
            self.rotation_velocity = 8 * self.speed_multiplier
        self.rotation += self.rotation_velocity
        
        # Apply gravity multiplier
        self.velocity += self.gravity * self.gravity_multiplier
        self.y += self.velocity
        
        if self.y > self.ground_y:
            self.y = self.ground_y
            self.velocity = 0
            self.is_jumping = False
            self.rotation_velocity = 0

        # Add particles when moving
        if self.is_jumping or abs(self.velocity) > 1:
            self.particle_system.emit(
                (self.x + self.size/2, self.y + self.size/2),
                self.glow_color,
                num_particles=2,
                speed_range=(1, 3),
                size_range=(2, 4)
            )
        
        # Update trail
        self.trail_points.insert(0, (self.x + self.size/2, self.y + self.size/2))
        if len(self.trail_points) > 10:
            self.trail_points.pop()

    def die(self):
        self.is_dead = True
        return [Particle(self.x + self.size/2, self.y + self.size/2, BLUE) for _ in range(20)]

    def apply_portal_effect(self, portal_type, multiplier):
        if portal_type == "speed":
            self.speed_multiplier = multiplier
        elif portal_type == "gravity":
            self.gravity_multiplier *= multiplier
        elif portal_type == "size":
            self.size_multiplier = multiplier
            self.size = 40 * self.size_multiplier

    def draw(self, screen, camera_offset):
        # Draw trail
        for i, point in enumerate(self.trail_points):
            alpha = int(255 * (1 - i/len(self.trail_points)))
            GlowEffect.draw_glow(screen, 
                               self.glow_color, 
                               (point[0] - camera_offset[0],
                                point[1] - camera_offset[1]),
                               int(self.size/2 * (1 - i/len(self.trail_points))),
                               self.glow_intensity)
        
        # Draw player with glow
        pos = (self.x + self.size/2 - camera_offset[0],
               self.y + self.size/2 - camera_offset[1])
        GlowEffect.draw_glow(screen, self.glow_color, pos, int(self.size/1.5))
        
        # Draw player shape
        # Create a surface for the cube
        cube_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.rect(cube_surface, BLUE, (0, 0, self.size, self.size))
        
        # Add design to the cube
        pygame.draw.line(cube_surface, CYAN, (0, 0), (self.size, self.size), 2)
        pygame.draw.line(cube_surface, CYAN, (0, self.size), (self.size, 0), 2)
        
        # Rotate the surface
        rotated_surface = pygame.transform.rotate(cube_surface, self.rotation)
        new_rect = rotated_surface.get_rect(center=(self.x + self.size/2 - camera_offset[0], self.y + self.size/2 - camera_offset[1]))
        screen.blit(rotated_surface, new_rect)

        # Update and draw particles
        self.particle_system.update_and_draw(screen, camera_offset)

class JumpPad:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 10
        self.speed = 5

    def update(self):
        self.x -= self.speed
        
    def draw(self, screen, camera_offset):
        pygame.draw.rect(screen, YELLOW, (self.x - camera_offset[0], self.y - camera_offset[1], self.width, self.height))

class Obstacle:
    def __init__(self, x, y, type="block"):
        self.x = x
        self.y = y
        self.type = type
        self.speed = 5
        
        if type == "block":
            self.width = 40
            self.height = 40
        elif type == "spike":
            self.width = 40
            self.height = 40
        elif type == "platform":
            self.width = 100
            self.height = 20

    def update(self):
        self.x -= self.speed

    def draw(self, screen, camera_offset):
        if self.type == "block":
            pygame.draw.rect(screen, RED, (self.x - camera_offset[0], self.y - camera_offset[1], self.width, self.height))
        elif self.type == "spike":
            # Draw detailed spike
            points = [
                (self.x - camera_offset[0], self.y + self.height - camera_offset[1]),
                (self.x + self.width/2 - camera_offset[0], self.y - camera_offset[1]),
                (self.x + self.width - camera_offset[0], self.y + self.height - camera_offset[1])
            ]
            # Main spike
            pygame.draw.polygon(screen, RED, points)
            # Outline
            pygame.draw.lines(screen, (200, 0, 0), True, points, 2)
            # Inner detail
            inner_points = [
                (points[0][0] + self.width * 0.2, points[0][1] - self.height * 0.2),
                (points[1][0], points[1][1] + self.height * 0.2),
                (points[2][0] - self.width * 0.2, points[2][1] - self.height * 0.2)
            ]
            pygame.draw.polygon(screen, (255, 100, 100), inner_points)
        elif self.type == "platform":
            pygame.draw.rect(screen, WHITE, (self.x - camera_offset[0], self.y - camera_offset[1], self.width, self.height))

class Portal:
    def __init__(self, x, y, portal_type):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 80
        self.type = portal_type
        self.particle_timer = 0
        
        # Portal effects
        self.effects = {
            "speed": {"color": ORANGE, "multiplier": 1.5},
            "gravity": {"color": PURPLE, "multiplier": -1},
            "size": {"color": GREEN, "multiplier": 0.7}
        }
        self.color = self.effects[portal_type]["color"]

    def draw(self, screen, camera_offset):
        x = self.x - camera_offset[0]
        y = self.y - camera_offset[1]
        
        # Draw portal base
        pygame.draw.ellipse(screen, self.color, (x, y, self.width, self.height))
        pygame.draw.ellipse(screen, WHITE, (x, y, self.width, self.height), 2)
        
        # Draw portal effects (swirling particles)
        self.particle_timer += 0.1
        for i in range(4):
            offset = i * (math.pi/2) + self.particle_timer
            particle_x = x + self.width/2 + math.cos(offset) * 15
            particle_y = y + self.height/2 + math.sin(offset) * 15
            pygame.draw.circle(screen, WHITE, (int(particle_x), int(particle_y)), 2)

        # Draw portal glow
        GlowEffect.draw_glow(screen, self.color, 
                           (x + self.width/2, y + self.height/2),
                           max(self.width, self.height))
        
        # Draw swirling particles
        t = time.time()
        for i in range(8):
            angle = t * 5 + i * math.pi/4
            radius = 20 + math.sin(t * 3 + i) * 5
            px = x + self.width/2 + math.cos(angle) * radius
            py = y + self.height/2 + math.sin(angle) * radius
            GlowEffect.draw_glow(screen, WHITE, (px, py), 5, 0.5)

def generate_level_segment(start_x, difficulty):
    objects = []
    current_x = start_x
    
    # Ensure num_obstacles is an integer
    num_obstacles = int(3 + difficulty // 1000)
    
    for _ in range(max(3, num_obstacles)):  # Ensure minimum 3 obstacles
        # More spike probability as difficulty increases
        spike_weight = min(10, 2 + difficulty//500)  # Cap the maximum weight
        weights = [1, int(spike_weight), 1]
        obstacle_type = random.choices(["block", "spike", "platform"], weights=weights)[0]
        
        if obstacle_type == "platform":
            y = random.randint(HEIGHT - 250, HEIGHT - 200)
        else:
            y = HEIGHT - 150
            
        # Add portal with increasing probability
        portal_chance = min(0.4, 0.1 + (difficulty / 10000))  # Cap at 40% chance
        if random.random() < portal_chance:
            portal_type = random.choice(["speed", "gravity", "size"])
            objects.append(Portal(current_x - 150, HEIGHT - 200, portal_type))
            
        # Add jump pad with increasing probability
        jump_pad_chance = min(0.5, 0.3 + (difficulty / 5000))  # Cap at 50% chance
        if random.random() < jump_pad_chance:
            objects.append(JumpPad(current_x - 100, HEIGHT - 160))
            
        objects.append(Obstacle(current_x, y, obstacle_type))
        
        # Decrease space between obstacles as difficulty increases
        min_space = max(100, 200 - (difficulty // 1000))  # Minimum space of 100
        max_space = max(min_space + 50, 300 - (difficulty // 800))  # Keep reasonable gap
        space = random.randint(int(min_space), int(max_space))
        current_x += space
        
    return objects

def draw_background(screen, camera_offset, current_zone):
    # Draw grid
    for x in range(0, WIDTH, 40):
        pygame.draw.line(screen, GRID_COLOR, (x - camera_offset[0] % 40, 0), (x - camera_offset[0] % 40, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(screen, GRID_COLOR, (0, y - camera_offset[1] % 40), (WIDTH, y - camera_offset[1] % 40))
        
    # Draw ground
    pygame.draw.rect(screen, GROUND_COLOR, (0, HEIGHT - 100 - camera_offset[1], WIDTH, 100))
    pygame.draw.line(screen, WHITE, (0, HEIGHT - 100 - camera_offset[1]), (WIDTH, HEIGHT - 100 - camera_offset[1]), 2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    game = Game()
    clock = pygame.time.Clock()
    sound_manager = SoundManager()
    sound_manager.play_music()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game.state == GameState.MAIN_MENU:
                    if event.key == pygame.K_UP:
                        game.menu_selection = (game.menu_selection - 1) % len(game.menu_options)
                    elif event.key == pygame.K_DOWN:
                        game.menu_selection = (game.menu_selection + 1) % len(game.menu_options)
                    elif event.key == pygame.K_RETURN:
                        if game.menu_options[game.menu_selection] == "Play":
                            game.state = GameState.LOADING
                        elif game.menu_options[game.menu_selection] == "Settings":
                            game.state = GameState.SETTINGS
                        elif game.menu_options[game.menu_selection] == "Quit":
                            running = False
                elif game.state == GameState.SETTINGS:
                    game.state = game.settings.update(event)
                elif game.state == GameState.PLAYING:
                    if event.key == pygame.K_SPACE:
                        game.player.jump()
                        sound_manager.play('jump')
                    elif event.key == pygame.K_ESCAPE:
                        game.state = GameState.MAIN_MENU
                elif event.key == pygame.K_SPACE and game.state == GameState.GAME_OVER:
                    game.start_new_game()

        if game.state == GameState.MAIN_MENU:
            game.draw_menu(screen)
        elif game.state == GameState.SETTINGS:
            game.settings.draw(screen)
        elif game.state == GameState.LOADING:
            game.draw_loading_screen(screen)
        elif game.state == GameState.PLAYING:
            game.update_game()

            # Draw everything
            screen.fill(game.current_zone.bg_color)
            camera_offset = (game.camera.x, game.camera.y)
            
            # Draw background and objects
            draw_background(screen, camera_offset, game.current_zone)
            
            # Draw all game objects
            for obj in game.game_objects:
                obj.draw(screen, camera_offset)
            
            game.player.draw(screen, camera_offset)
            
            # Draw particles
            for particle in game.particles:
                particle.draw(screen, camera_offset)

            # Draw score
            font = pygame.font.Font(None, 36)
            score_text = font.render(f'Score: {game.score}', True, WHITE)
            screen.blit(score_text, (10, 10))
        elif game.state == GameState.GAME_OVER:
            game.draw_game_over(screen)
        elif game.state == GameState.RESPAWNING:
            game.update_game()
            game.draw_respawn_animation(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
