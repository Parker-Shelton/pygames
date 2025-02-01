import pygame
import math
import numpy as np
import sys
import random
from queue import Queue

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
MAP_SIZE = 15  # Size of the map (must be odd number)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
DARK_GRAY = (50, 50, 50)
GRAY = (100, 100, 100)
LIGHT_GRAY = (150, 150, 150)

# Special wall types
WALL_NORMAL = 1
WALL_START = 2
WALL_END = 3

def generate_random_map():
    # Initialize map with walls
    world_map = [[1 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
    
    # Create empty space in the middle
    for y in range(1, MAP_SIZE-1):
        for x in range(1, MAP_SIZE-1):
            world_map[y][x] = random.randint(0, 1)
    
    # Place start cube on left wall and ensure adjacent space is empty
    start_y = random.randint(1, MAP_SIZE-2)
    world_map[start_y][0] = WALL_START
    world_map[start_y][1] = 0  # Ensure path from start
    world_map[start_y-1][1] = 0  # Create some room to move
    world_map[start_y+1][1] = 0
    
    # Make sure the map is traversable using flood fill
    def flood_fill():
        visited = [[False for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        distances = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        q = Queue()
        # Start flood fill from the space next to start cube
        q.put((1, start_y))
        visited[start_y][1] = True
        
        while not q.empty():
            x, y = q.get()
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_x, new_y = x + dx, y + dy
                if (0 <= new_x < MAP_SIZE and 0 <= new_y < MAP_SIZE and 
                    not visited[new_y][new_x] and world_map[new_y][new_x] == 0):
                    visited[new_y][new_x] = True
                    distances[new_y][new_x] = distances[y][x] + 1
                    q.put((new_x, new_y))
        
        return visited, distances
    
    # Keep generating new maps until we get one that's sufficiently connected
    while True:
        visited, distances = flood_fill()
        empty_spaces = sum(1 for y in range(1, MAP_SIZE-1) 
                         for x in range(1, MAP_SIZE-1) 
                         if world_map[y][x] == 0)
        reachable_spaces = sum(1 for y in range(MAP_SIZE) 
                             for x in range(MAP_SIZE) 
                             if visited[y][x])
        
        # If at least 70% of empty spaces are reachable, try to place end cube
        if reachable_spaces >= 0.7 * empty_spaces:
            # Try to place end cube on right wall
            best_end_y = None
            max_dist = 0
            
            # Check all positions on right wall
            for y in range(1, MAP_SIZE-1):
                # Check if the space next to the wall is reachable
                if visited[y][MAP_SIZE-2]:
                    dist = distances[y][MAP_SIZE-2]
                    if dist > max_dist:
                        max_dist = dist
                        best_end_y = y
            
            # If we found a good spot and it's far enough
            if best_end_y and max_dist > MAP_SIZE // 2:
                world_map[best_end_y][MAP_SIZE-1] = WALL_END
                # Ensure path to end is clear
                world_map[best_end_y][MAP_SIZE-2] = 0
                world_map[best_end_y-1][MAP_SIZE-2] = 0
                world_map[best_end_y+1][MAP_SIZE-2] = 0
                break
        
        # Otherwise, regenerate the middle of the map
        for y in range(1, MAP_SIZE-1):
            for x in range(1, MAP_SIZE-1):
                world_map[y][x] = random.randint(0, 1)
        # Ensure path from start is clear
        world_map[start_y][1] = 0
        world_map[start_y-1][1] = 0
        world_map[start_y+1][1] = 0
    
    return world_map

# Generate the initial world map
WORLD_MAP = generate_random_map()

# Set up the display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('3D World')
clock = pygame.time.Clock()

class Player:
    def __init__(self):
        self.reset_position()
        
        # Lock and hide the mouse cursor
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
    
    def reset_position(self):
        # Find start cube position
        start_pos = None
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                if WORLD_MAP[y][x] == WALL_START:
                    start_pos = (x, y)
                    break
            if start_pos:
                break
        
        # Position player next to start cube
        if start_pos[0] == 0:  # Start cube on left wall
            self.x = start_pos[0] + 1.5  # Place slightly right of the wall
        elif start_pos[0] == MAP_SIZE - 1:  # Start cube on right wall
            self.x = start_pos[0] - 1.5  # Place slightly left of the wall
        else:
            self.x = start_pos[0] + 0.5
            
        self.y = start_pos[1] + 0.5  # Center in the tile
        self.angle = 0.0  # Starting angle
        self.height = WINDOW_HEIGHT / 2
    
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
    
    def check_end_cube(self):
        # Check if player is close to end cube
        player_tile_x = int(self.x)
        player_tile_y = int(self.y)
        
        # Calculate exact distance to player center
        player_center_x = self.x
        player_center_y = self.y
        
        # Check immediate adjacent tiles only (not diagonals)
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            check_x = player_tile_x + dx
            check_y = player_tile_y + dy
            if (0 <= check_x < MAP_SIZE and 0 <= check_y < MAP_SIZE and 
                WORLD_MAP[check_y][check_x] == WALL_END):
                # Calculate distance to the end cube center
                cube_center_x = check_x + 0.5
                cube_center_y = check_y + 0.5
                distance = math.sqrt((player_center_x - cube_center_x)**2 + 
                                  (player_center_y - cube_center_y)**2)
                # Player must be within 1.2 units of the cube center
                if distance < 1.2:
                    return True
        return False

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
        if WORLD_MAP[map_y][map_x] != 0:
            hit = True
    
    # Calculate distance to the point of impact
    if side == 0:
        perp_wall_dist = side_dist_x - delta_dist_x
    else:
        perp_wall_dist = side_dist_y - delta_dist_y
    
    return perp_wall_dist, side, WORLD_MAP[map_y][map_x]

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
        distance, side, wall_type = cast_ray(player, ray_angle)
        
        # Calculate wall height
        wall_height = (WINDOW_HEIGHT / distance) if distance > 0 else WINDOW_HEIGHT
        
        # Calculate wall top and bottom
        wall_top = max(0, (WINDOW_HEIGHT - wall_height) / 2)
        wall_bottom = min(WINDOW_HEIGHT, (WINDOW_HEIGHT + wall_height) / 2)
        
        # Calculate wall strip width and position
        strip_width = WINDOW_WIDTH / RAY_COUNT
        strip_pos = x * strip_width
        
        # Choose wall color based on type and side
        if wall_type == WALL_START:
            base_color = RED
            # Draw normal wall strip for start cube
            shade = min(1.0, 1.0 / (distance * 0.3))
            wall_color = tuple(int(c * shade) for c in base_color)
            pygame.draw.rect(surface, wall_color, 
                           (strip_pos, wall_top, strip_width + 1, wall_bottom - wall_top))
        elif wall_type == WALL_END:
            base_color = GREEN
            # Draw stairs effect for end cube
            num_steps = 8  # Number of stair steps
            step_height = (wall_bottom - wall_top) / num_steps
            
            for step in range(num_steps):
                # Calculate step positions
                step_top = wall_top + step * step_height
                step_bottom = step_top + step_height
                
                # Make steps appear to go down by adjusting shading
                step_shade = min(1.0, 1.0 / (distance * 0.3)) * (1 - step/num_steps * 0.5)
                step_color = tuple(int(c * step_shade) for c in base_color)
                
                # Draw step
                pygame.draw.rect(surface, step_color,
                               (strip_pos, step_top, strip_width + 1, step_bottom - step_top))
                
                # Draw diagonal line for step edge (darker)
                edge_color = tuple(int(c * step_shade * 0.7) for c in base_color)
                if strip_width > 2:  # Only draw if strip is wide enough
                    pygame.draw.line(surface, edge_color,
                                   (strip_pos, step_bottom),
                                   (strip_pos + strip_width, step_bottom))
        else:
            base_color = LIGHT_GRAY if side == 1 else GRAY
            # Draw normal wall strip
            shade = min(1.0, 1.0 / (distance * 0.3))
            wall_color = tuple(int(c * shade) for c in base_color)
            pygame.draw.rect(surface, wall_color, 
                           (strip_pos, wall_top, strip_width + 1, wall_bottom - wall_top))

def draw_minimap(surface, player, scale=20):
    # Draw map
    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            if WORLD_MAP[y][x] != 0:
                color = WHITE
                if WORLD_MAP[y][x] == WALL_START:
                    color = RED
                elif WORLD_MAP[y][x] == WALL_END:
                    color = GREEN
                pygame.draw.rect(surface, color, 
                               (x * scale, y * scale, scale-1, scale-1))
    
    # Draw player
    player_x = int(player.x * scale)
    player_y = int(player.y * scale)
    pygame.draw.circle(surface, RED, (player_x, player_y), 3)
    
    # Draw player direction
    end_x = player_x + math.cos(player.angle) * 10
    end_y = player_y + math.sin(player.angle) * 10
    pygame.draw.line(surface, RED, (player_x, player_y), (end_x, end_y), 1)

def draw_loading_screen(surface, level):
    surface.fill(BLACK)
    
    # Draw loading text
    font = pygame.font.Font(None, 74)
    text = font.render(f"Level {level} Complete!", True, WHITE)
    text_rect = text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 50))
    surface.blit(text, text_rect)
    
    # Draw loading animation
    loading_text = "Loading next level..."
    loading_font = pygame.font.Font(None, 36)
    dots = "." * ((pygame.time.get_ticks() // 500) % 4)  # Animated dots
    loading = loading_font.render(loading_text + dots, True, WHITE)
    loading_rect = loading.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 + 50))
    surface.blit(loading, loading_rect)
    
    pygame.display.flip()

def main():
    global WORLD_MAP  # Make WORLD_MAP global so we can modify it
    player = Player()
    level = 1
    loading_start_time = 0
    is_loading = False
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        current_time = pygame.time.get_ticks()
        
        if is_loading:
            # Show loading screen for 2 seconds
            if current_time - loading_start_time >= 2000:
                # Generate new map and reset player
                WORLD_MAP = generate_random_map()
                player.reset_position()
                is_loading = False
                level += 1
            else:
                draw_loading_screen(screen, level)
                continue
        
        # Handle input
        keys = pygame.key.get_pressed()
        player.handle_mouse()
        player.handle_movement(keys)
        
        # Check if player reached end cube
        if player.check_end_cube():
            is_loading = True
            loading_start_time = current_time
            continue
        
        # Draw world
        render_world(screen, player)
        
        # Draw minimap (commented out but kept for future use)
        # draw_minimap(screen, player)
        
        # Draw level counter
        font = pygame.font.Font(None, 36)
        level_text = font.render(f"Level: {level}", True, WHITE)
        screen.blit(level_text, (10, 10))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    main()
