import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (100, 150, 240)
GREEN = (50, 200, 100)
RED = (220, 50, 50)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Scratch-style Mini Language Builder")
font = pygame.font.SysFont('Arial', 18)
header_font = pygame.font.SysFont('Arial', 24, bold=True)

# Block data definitions
BLOCK_TYPES = {
    'KEYWORD': ORANGE,
    'OPERATOR': LIGHT_BLUE,
    'IDENTIFIER': GREEN,
    'LITERAL': PURPLE,
    'SEPARATOR': GRAY
}

AVAILABLE_BLOCKS = [
    ('int', 'KEYWORD'), ('float', 'KEYWORD'), ('char', 'KEYWORD'), ('string', 'KEYWORD'),
    ('x', 'IDENTIFIER'), ('y', 'IDENTIFIER'), ('z', 'IDENTIFIER'),
    ('=', 'OPERATOR'), ('+', 'OPERATOR'), ('-', 'OPERATOR'),
    ('*', 'OPERATOR'), ('/', 'OPERATOR'), (';', 'SEPARATOR'),
    ('(', 'SEPARATOR'), (')', 'SEPARATOR'), ('{', 'SEPARATOR'), ('}', 'SEPARATOR'),
    ('10', 'LITERAL'), ('20', 'LITERAL'), ('3.14', 'LITERAL'), ('"Hello"', 'LITERAL')
]

class Block:
    def __init__(self, text, category, x, y):
        self.text = str(text)
        self.category = category
        self.color = BLOCK_TYPES.get(category, GRAY)
        text_surface = font.render(self.text, True, WHITE)
        self.width = max(80, text_surface.get_width() + 20)
        self.height = 40
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.dragging = False

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

# List of blocks currently placed in the workspace
placed_blocks = []
# Sidebar for choosing blocks
sidebar_blocks = []
for i, (text, cat) in enumerate(AVAILABLE_BLOCKS):
    col = i // 12
    row = i % 12
    sidebar_blocks.append(Block(text, cat, 20 + col * 90, 60 + row * 45))

dragging_block = None
offset_x = 0
offset_y = 0
output_message = "Workspace ready. Drag blocks to build your line of code."

def evaluate_code(blocks):
    if not blocks:
        return "Nothing to execute."
    
    # Sort blocks by their x-coordinate to form a sequence
    sorted_blocks = sorted(blocks, key=lambda b: b.rect.x)
    code = " ".join([b.text for b in sorted_blocks])
    
    # Basic evaluation logic inspired by the provided Activity rules
    try:
        # Check for assignment patterns
        if "=" in code:
            parts = code.split("=")
            left_part = parts[0].strip().split()
            right_part = parts[1].strip().rstrip(';').strip()
            
            if len(left_part) == 2: # type identifier
                var_type = left_part[0]
                var_name = left_part[1]
                
                if var_type == 'int':
                    if right_part.isdigit():
                        return f"SUCCESS: Assigned integer {right_part} to variable {var_name}."
                    else:
                        return f"SEMANTIC ERROR: Cannot assign '{right_part}' to int variable {var_name}."
                elif var_type == 'float':
                    try:
                        float(right_part)
                        return f"SUCCESS: Assigned float {right_part} to variable {var_name}."
                    except ValueError:
                        return f"SEMANTIC ERROR: Cannot assign '{right_part}' to float variable {var_name}."
            
        return f"Code analyzed: {code}"
    except Exception as e:
        return f"Error: {str(e)}"

# Main loop
running = True
while running:
    screen.fill((240, 240, 240))
    
    # Draw Sidebar
    pygame.draw.rect(screen, (220, 220, 220), (0, 0, 200, HEIGHT))
    screen.blit(header_font.render("Blocks Library", True, BLACK), (20, 20))
    for b in sidebar_blocks:
        b.draw(screen)
    
    # Draw Workspace
    pygame.draw.rect(screen, (255, 255, 255), (210, 60, 780, 400), border_radius=10)
    screen.blit(header_font.render("Workspace Area", True, BLACK), (220, 20))
    
    # Draw UI elements
    run_btn = pygame.Rect(880, 470, 100, 40)
    pygame.draw.rect(screen, GREEN, run_btn, border_radius=5)
    screen.blit(font.render("RUN", True, WHITE), (run_btn.centerx - 15, run_btn.centery - 10))
    
    clear_btn = pygame.Rect(770, 470, 100, 40)
    pygame.draw.rect(screen, RED, clear_btn, border_radius=5)
    screen.blit(font.render("CLEAR", True, WHITE), (clear_btn.centerx - 25, clear_btn.centery - 10))

    # Output Console
    pygame.draw.rect(screen, (0, 0, 0), (210, 520, 780, 70))
    screen.blit(font.render(output_message, True, (0, 255, 0)), (220, 540))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Clicked on sidebar?
                for b in sidebar_blocks:
                    if b.rect.collidepoint(event.pos):
                        new_block = Block(b.text, b.category, event.pos[0]-40, event.pos[1]-20)
                        new_block.dragging = True
                        placed_blocks.append(new_block)
                        dragging_block = new_block
                        offset_x = new_block.rect.x - event.pos[0]
                        offset_y = new_block.rect.y - event.pos[1]
                        break
                
                # Clicked on placed block?
                if not dragging_block:
                    for b in reversed(placed_blocks):
                        if b.rect.collidepoint(event.pos):
                            b.dragging = True
                            dragging_block = b
                            offset_x = b.rect.x - event.pos[0]
                            offset_y = b.rect.y - event.pos[1]
                            placed_blocks.remove(b)
                            placed_blocks.append(b) # move to top
                            break
                
                # Clicked Run?
                if run_btn.collidepoint(event.pos):
                    output_message = evaluate_code(placed_blocks)
                
                # Clicked Clear?
                if clear_btn.collidepoint(event.pos):
                    placed_blocks = []
                    output_message = "Workspace cleared."
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if dragging_block:
                    dragging_block.dragging = False
                    # Remove if dragged back into the sidebar area
                    if dragging_block.rect.x < 200:
                        placed_blocks.remove(dragging_block)
                    dragging_block = None
                    
        elif event.type == pygame.MOUSEMOTION:
            if dragging_block:
                dragging_block.rect.x = event.pos[0] + offset_x
                dragging_block.rect.y = event.pos[1] + offset_y

    # Draw placed blocks
    for b in placed_blocks:
        b.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()