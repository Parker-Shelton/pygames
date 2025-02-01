import pygame
import math
import numpy as np
import sys

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FOV = 60  # Field of view in degrees
HALF_FOV = FOV / 2
MOUSE_SENSITIVITY = 0.2
MOVEMENT_SPEED = 0.05
RAY_COUNT = 160  # Number of rays to cast (resolution)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (100, 100, 255)
DARK_GRAY = (50, 50, 50)
GRAY = (100, 100, 100)
LIGHT_GRAY = (150, 150, 150)

# World map (1 represents walls, 0 represents empty space)
WORLD_MAP = [
    [1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,1,0,0,1],
    [1,0,0,0,0,0,1,0,0,1],
    [1,0,0,1,0,0,0,0,0,1],
    [1,0,0,1,0,0,0,0,0,1],
    [1,0,0,1,0,0,1,0,0,1],
    [1,0,1,1,0,0,1,0,0,1],
    [1,0,0,0,0,0,1,0,0,1],
    [1,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1]
]

MAP_SIZE = len(WORLD_MAP)

# Set up the display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('3D World')
clock = pygame.time.Clock()

class Player:
    def __init__(self):
        self.x = 1.5  # Starting x position
        self.y = 1.5  # Starting y position
        self.angle = 0.0  # Starting angle
        self.height = WINDOW_HEIGHT / 2
        
        # Lock and hide the mouse cursor
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
    
    def handle_mouse(self):
        # Get mouse movement
        mouse_rel = pygame.mouse.get_rel()
        self.angle += math.radians(mouse_rel[0] * MOUSE_SENSITIVITY)
        
    def handle_movement(self, keys):
        # Get the movement vector based on key presses
        dx = 0
        dy = 0
        
        if keys[pygame.K_w]:  # Forward
            dx += math.cos(self.angle) * MOVEMENT_SPEED
            dy += math.sin(self.angle) * MOVEMENT_SPEED
        if keys[pygame.K_s]:  # Backward
            dx -= math.cos(self.angle) * MOVEMENT_SPEED
            dy -= math.sin(self.angle) * MOVEMENT_SPEED
        if keys[pygame.K_a]:  # Strafe left
            dx += math.cos(self.angle - math.pi/2) * MOVEMENT_SPEED
            dy += math.sin(self.angle - math.pi/2) * MOVEMENT_SPEED
        if keys[pygame.K_d]:  # Strafe right
            dx += math.cos(self.angle + math.pi/2) * MOVEMENT_SPEED
            dy += math.sin(self.angle + math.pi/2) * MOVEMENT_SPEED
        
        # Check collision before moving
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Only move if the new position is not inside a wall
        if WORLD_MAP[int(new_y)][int(new_x)] == 0:
            self.x = new_x
            self.y = new_y

def cast_ray(player, angle):
    # Ray casting algorithm using DDA (Digital Differential Analysis)
    ray_dir_x = math.cos(angle)
    ray_dir_y = math.sin(angle)
    
    map_x = int(player.x)
    map_y = int(player.y)
    
    # Length of ray from current position to next x or y-side
    delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else float('inf')
    delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else float('inf')
    
    # Calculate step and initial side_dist
    if ray_dir_x < 0:
        step_x = -1
        side_dist_x = (player.x - map_x) * delta_dist_x
    else:
        step_x = 1
        side_dist_x = (map_x + 1.0 - player.x) * delta_dist_x
        
    if ray_dir_y < 0:
        step_y = -1
        side_dist_y = (player.y - map_y) * delta_dist_y
    else:
        step_y = 1
        side_dist_y = (map_y + 1.0 - player.y) * delta_dist_y
    
    # Perform DDA
    hit = False
    side = 0  # 0 for x-side, 1 for y-side
    
    while not hit:
        # Jump to next map square
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 1
        
        # Check if ray has hit a wall
        if WORLD_MAP[map_y][map_x] == 1:
            hit = True
    
    # Calculate distance to the point of impact
    if side == 0:
        perp_wall_dist = side_dist_x - delta_dist_x
    else:
        perp_wall_dist = side_dist_y - delta_dist_y
    
    return perp_wall_dist, side

def render_world(surface, player):
    # Draw sky
    pygame.draw.rect(surface, BLUE, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT//2))
    # Draw floor
    pygame.draw.rect(surface, DARK_GRAY, (0, WINDOW_HEIGHT//2, WINDOW_WIDTH, WINDOW_HEIGHT//2))
    
    # Cast rays and draw walls
    for x in range(RAY_COUNT):
        # Calculate ray angle
        ray_angle = player.angle - math.radians(HALF_FOV) + (x / RAY_COUNT) * math.radians(FOV)
        
        # Cast ray and get distance
        distance, side = cast_ray(player, ray_angle)
        
        # Calculate wall height
        wall_height = (WINDOW_HEIGHT / distance) if distance > 0 else WINDOW_HEIGHT
        
        # Calculate wall top and bottom
        wall_top = max(0, (WINDOW_HEIGHT - wall_height) / 2)
        wall_bottom = min(WINDOW_HEIGHT, (WINDOW_HEIGHT + wall_height) / 2)
        
        # Calculate wall strip width and position
        strip_width = WINDOW_WIDTH / RAY_COUNT
        strip_pos = x * strip_width
        
        # Choose wall color based on side and add shading based on distance
        base_color = LIGHT_GRAY if side == 1 else GRAY
        shade = min(1.0, 1.0 / (distance * 0.3))  # Distance shading
        wall_color = tuple(int(c * shade) for c in base_color)
        
        # Draw wall strip
        pygame.draw.rect(surface, wall_color, 
                        (strip_pos, wall_top, strip_width + 1, wall_bottom - wall_top))

def draw_minimap(surface, player, scale=20):
    # Draw map
    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            if WORLD_MAP[y][x] == 1:
                pygame.draw.rect(surface, WHITE, 
                               (x * scale, y * scale, scale-1, scale-1))
    
    # Draw player
    player_x = int(player.x * scale)
    player_y = int(player.y * scale)
    pygame.draw.circle(surface, RED, (player_x, player_y), 3)
    
    # Draw player direction
    end_x = player_x + math.cos(player.angle) * 10
    end_y = player_y + math.sin(player.angle) * 10
    pygame.draw.line(surface, RED, (player_x, player_y), (end_x, end_y), 1)

def main():
    player = Player()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        # Handle input
        keys = pygame.key.get_pressed()
        player.handle_mouse()
        player.handle_movement(keys)
        
        # Clear screen
        screen.fill(BLACK)
        
        # Render 3D view
        render_world(screen, player)
        
        # Draw minimap
        draw_minimap(screen, player)
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    main()
