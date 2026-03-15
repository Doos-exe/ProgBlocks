import pygame
import sys

# Initialize Pygame
pygame.init()

# --- COLORS ---
BG_COLOR = (211, 211, 211)
WORKSPACE_COLOR = (245, 245, 245)
CONSOLE_COLOR = (0, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN_TEXT = (0, 255, 0)
RED_TEXT = (255, 50, 50)
HIGHLIGHT_COLOR = (255, 255, 0) # For snapping preview

# Block Colors
ORANGE_BLOCK = (255, 140, 0)
BLUE_BLOCK = (70, 130, 180)
GRAY_BLOCK = (169, 169, 169)
PURPLE_BLOCK = (153, 50, 204)
CLEAR_BTN_COLOR = (244, 67, 54)
RUN_BTN_COLOR = (76, 175, 80)

# --- SCREEN SETUP ---
WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ProgBlocks: Snap & Edit")

# --- FONTS ---
font_small = pygame.font.SysFont('Arial', 16, bold=True)
font_header = pygame.font.SysFont('Arial', 24, bold=True)
font_console = pygame.font.SysFont('Consolas', 14)

# --- CONFIGURATION ---
AVAILABLE_BLOCKS = [
    ("digit", ORANGE_BLOCK, "TYPE"),
    ("word", ORANGE_BLOCK, "TYPE"),
    ("bet", ORANGE_BLOCK, "TYPE"),
    (":", BLUE_BLOCK, "OP"),
    ("adds", BLUE_BLOCK, "OP"),
    ("minus", BLUE_BLOCK, "OP"),
    ("end", GRAY_BLOCK, "DELIM"),
    ("out", GRAY_BLOCK, "OUT"),
    ("data", PURPLE_BLOCK, "EDITABLE") # This one is editable
]

class Block:
    def __init__(self, text, color, category, x, y, is_template=False):
        self.text = text
        self.color = color
        self.category = category
        self.is_template = is_template
        self.is_editing = False
        
        # Connection properties
        self.next_block = None
        self.prev_block = None
        
        self.update_size()
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.dragging = False

    def update_size(self):
        text_surf = font_small.render(self.text + ("|" if self.is_editing else ""), True, WHITE)
        self.width = max(80, text_surf.get_width() + 20)
        self.height = 35

    def draw(self, surface):
        # Draw snapping preview
        if self.dragging:
            # Logic for snapping handled in main loop, but we can highlight here if needed
            pass
            
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        if self.is_editing:
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
            
        text_surf = font_small.render(self.text + ("|" if self.is_editing else ""), True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def update_position(self, x, y):
        self.rect.x = x
        self.rect.y = y
        if self.next_block:
            self.next_block.update_position(self.rect.right + 2, self.rect.y)

# --- INITIALIZE UI ---
sidebar_blocks = []
for i, (text, color, cat) in enumerate(AVAILABLE_BLOCKS):
    col = i % 2
    row = i // 2
    sidebar_blocks.append(Block(text, color, cat, 15 + col * 85, 60 + row * 45, is_template=True))

placed_blocks = []
dragging_block = None
editing_block = None
offset_x, offset_y = 0, 0
console_output = ["Blueprint ready! Use Purple blocks for custom data/names."]

def get_root(block):
    curr = block
    while curr.prev_block:
        curr = curr.prev_block
    return curr

def get_chain(block):
    root = get_root(block)
    chain = []
    curr = root
    while curr:
        chain.append(curr)
        curr = curr.next_block
    return chain

def evaluate_chain(blocks):
    if not blocks:
        return ["Error: No blocks in workspace."]
    
    # Find the longest chain or the chain starting at the leftmost block
    # For simplicity, we take the chain of the first block found in workspace
    root = get_root(blocks[0])
    chain = get_chain(root)
    tokens = [b.text for b in chain]
    code_str = " ".join(tokens)
    
    results = [f"Code: {code_str}"]
    
    # --- CHEAT SHEET LOGIC ---
    if tokens[-1] != "end":
        results.append("Syntax Error: Chain must end with 'end'.")
    elif tokens[0] not in ["digit", "word", "bet", "out"]:
        results.append("Syntax Error: Start with a Type or 'out'.")
    else:
        # Basic Semantic check
        if tokens[0] == "digit" and len(tokens) >= 4:
             val = tokens[3]
             if not val.isdigit():
                 results.append(f"Semantic Error: 'digit' cannot be {val}.")
        
    if len(results) == 1:
        results.append("Status: COMPILATION SUCCESS")
    else:
        results.append("Status: COMPILATION FAILED")
    return results

# --- BUTTONS ---
clear_rect = pygame.Rect(WIDTH - 230, 415, 100, 35)
run_rect = pygame.Rect(WIDTH - 115, 415, 100, 35)

# --- MAIN LOOP ---
running = True
while running:
    screen.fill(BG_COLOR)
    
    # UI Elements
    screen.blit(font_header.render("Blox", True, BLACK), (20, 15))
    screen.blit(font_header.render("Blueprint", True, BLACK), (200, 15))
    pygame.draw.rect(screen, WORKSPACE_COLOR, (200, 60, WIDTH - 220, 340), border_radius=5)
    
    pygame.draw.rect(screen, CLEAR_BTN_COLOR, clear_rect, border_radius=8)
    screen.blit(font_small.render("CLEAR", True, WHITE), (clear_rect.centerx - 25, clear_rect.centery - 10))
    pygame.draw.rect(screen, RUN_BTN_COLOR, run_rect, border_radius=8)
    screen.blit(font_small.render("RUN", True, WHITE), (run_rect.centerx - 15, run_rect.centery - 10))
    
    pygame.draw.rect(screen, CONSOLE_COLOR, (200, 460, WIDTH - 220, 150))
    for i, line in enumerate(console_output[-7:]):
        color = GREEN_TEXT if any(x in line for x in ["SUCCESS", "ready", "Code:"]) else RED_TEXT
        screen.blit(font_console.render(line, True, color), (210, 470 + i * 20))

    # Draw Blocks
    for b in sidebar_blocks: b.draw(screen)
    for b in placed_blocks: b.draw(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 1. Sidebar Click
            for b in sidebar_blocks:
                if b.rect.collidepoint(event.pos):
                    new_b = Block(b.text, b.color, b.category, b.rect.x, b.rect.y)
                    new_b.dragging = True
                    dragging_block = new_b
                    offset_x, offset_y = b.rect.x - event.pos[0], b.rect.y - event.pos[1]
                    placed_blocks.append(new_b)
                    break
            
            # 2. Workspace Click
            if not dragging_block:
                for b in reversed(placed_blocks):
                    if b.rect.collidepoint(event.pos):
                        # Start editing if it's an editable block
                        if b.category == "EDITABLE":
                            if editing_block: editing_block.is_editing = False
                            editing_block = b
                            b.is_editing = True
                        
                        # Break connection when picking up
                        if b.prev_block:
                            b.prev_block.next_block = None
                            b.prev_block = None
                            
                        b.dragging = True
                        dragging_block = b
                        offset_x, offset_y = b.rect.x - event.pos[0], b.rect.y - event.pos[1]
                        placed_blocks.remove(b)
                        placed_blocks.append(b)
                        break
                else:
                    if editing_block:
                        editing_block.is_editing = False
                        editing_block = None
            
            # 3. Buttons
            if clear_rect.collidepoint(event.pos):
                placed_blocks = []
                console_output = ["Workspace cleared."]
            elif run_rect.collidepoint(event.pos):
                console_output = evaluate_chain(placed_blocks)

        elif event.type == pygame.MOUSEBUTTONUP:
            if dragging_block:
                dragging_block.dragging = False
                # Snapping Logic
                for other in placed_blocks:
                    if other != dragging_block and not other.next_block:
                        # Check if dragging_block's left is near other's right
                        if abs(dragging_block.rect.left - other.rect.right) < 20 and \
                           abs(dragging_block.rect.centery - other.rect.centery) < 20:
                            other.next_block = dragging_block
                            dragging_block.prev_block = other
                            dragging_block.update_position(other.rect.right + 2, other.rect.y)
                            break
                
                if dragging_block.rect.x < 190:
                    placed_blocks.remove(dragging_block)
                dragging_block = None
                
        elif event.type == pygame.MOUSEMOTION:
            if dragging_block:
                dragging_block.update_position(event.pos[0] + offset_x, event.pos[1] + offset_y)

        elif event.type == pygame.KEYDOWN:
            if editing_block:
                if event.key == pygame.K_BACKSPACE:
                    editing_block.text = editing_block.text[:-1]
                elif event.key == pygame.K_RETURN:
                    editing_block.is_editing = False
                    editing_block = None
                else:
                    if len(editing_block.text) < 15:
                        editing_block.text += event.unicode
                if editing_block:
                    editing_block.update_size()
                    # Re-align chain after size change
                    root = get_root(editing_block)
                    root.update_position(root.rect.x, root.rect.y)

    pygame.display.flip()

pygame.quit()
sys.exit()
