import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
WINDOW_SIZE = 900
GRID_SIZE = 20
GRID_COUNT = WINDOW_SIZE // GRID_SIZE
BACKGROUND = (0, 0, 0)
WHITE = (255, 255, 255)
APPLE = (255, 0, 0)
SNAKE = (0, 255, 0)
YELLOW = (255, 255, 0)

# Set up the display
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption('Snake Game')
clock = pygame.time.Clock()

# Initialize font
font = pygame.font.Font(None, 50)

# Initialize score
score = 0

class Snake:
    def __init__(self):
        self.body = [(GRID_COUNT // 2, GRID_COUNT // 2)]
        self.direction = [1, 0]  # Start moving right
        self.grow = False

    def move(self):
        head = self.body[0]
        new_head = (
            (head[0] + self.direction[0]) % GRID_COUNT,  # Wrap around horizontally
            (head[1] + self.direction[1]) % GRID_COUNT   # Wrap around vertically
        )
        
        # Check for self collision only
        if new_head in self.body[1:]:
            return False
        
        self.body.insert(0, new_head)
        if not self.grow:
            self.body.pop()
        else:
            self.grow = False
        return True

    def change_direction(self, new_direction):
        # Prevent 180-degree turns
        if (self.direction[0] != -new_direction[0] or 
            self.direction[1] != -new_direction[1]):
            self.direction = new_direction

def spawn_food(snake_body):
    while True:
        # Ensure food spawns within grid bounds (0 to GRID_COUNT-1)
        x = random.randint(0, GRID_COUNT-1)
        y = random.randint(0, GRID_COUNT-1)
        food = (x, y)
        if food not in snake_body:
            return food

def game_loop():
    snake = Snake()
    food = spawn_food(snake.body)
    global score
    score = 0
    game_speed = 10

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    snake.change_direction([0, -1])
                elif event.key == pygame.K_DOWN:
                    snake.change_direction([0, 1])
                elif event.key == pygame.K_LEFT:
                    snake.change_direction([-1, 0])
                elif event.key == pygame.K_RIGHT:
                    snake.change_direction([1, 0])

        # Move snake
        if not snake.move():
            return  # Exit to game over screen

        # Check for food collision
        if snake.body[0] == food:
            snake.grow = True
            food = spawn_food(snake.body)
            score += 1
            game_speed = min(20, 10 + score // 5)  # Increase speed with score

        # Draw everything
        screen.fill(BACKGROUND)
        
        # Draw food
        food_rect = pygame.Rect(
            food[0] * GRID_SIZE, 
            food[1] * GRID_SIZE, 
            GRID_SIZE, GRID_SIZE
        )
        pygame.draw.rect(screen, APPLE, food_rect)
        
        # Draw snake
        for segment in snake.body:
            segment_rect = pygame.Rect(
                segment[0] * GRID_SIZE, 
                segment[1] * GRID_SIZE, 
                GRID_SIZE, GRID_SIZE
            )
            pygame.draw.rect(screen, SNAKE, segment_rect)

        pygame.display.flip()
        clock.tick(game_speed)

def main():
    running = True
    while running:
        game_loop()
        
        # Game Over Screen with restart option
        game_over_screen = True
        while game_over_screen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Show countdown
                        for i in range(3, 0, -1):
                            screen.fill(BACKGROUND)
                            countdown_text = font.render(f"Restarting in {i}...", True, YELLOW)
                            text_rect = countdown_text.get_rect(center=(WINDOW_SIZE/2, WINDOW_SIZE/2))
                            screen.blit(countdown_text, text_rect)
                            pygame.display.flip()
                            pygame.time.wait(1000)  # Wait 1 second
                        game_over_screen = False
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
            
            screen.fill(BACKGROUND)
            game_over_text = font.render(f'Game Over! Score: {score}', True, WHITE)
            restart_text = font.render('Press R to Restart or Q to Quit', True, YELLOW)
            game_over_rect = game_over_text.get_rect(center=(WINDOW_SIZE/2, WINDOW_SIZE/2 - 30))
            restart_rect = restart_text.get_rect(center=(WINDOW_SIZE/2, WINDOW_SIZE/2 + 30))
            screen.blit(game_over_text, game_over_rect)
            screen.blit(restart_text, restart_rect)
            pygame.display.flip()

if __name__ == '__main__':
    main()
