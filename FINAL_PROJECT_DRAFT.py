import pygame
import sys

# Initialize Pygame
pygame.init()

# ---- UI/UX Design ----
# Background Colors
BG_COLOR = (211, 211, 211)
WORKSPACE_COLOR = (245, 245, 245)
CONSOLE_COLOR = (0, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN_TEXT = (0, 255, 0)
RED_TEXT = (255, 50, 50)
BLUE_TEXT = (100, 149, 237)

# Block Colors
ORANGE_BLOCK = (255, 140, 0)
BLUE_BLOCK = (70, 130, 180)
GRAY_BLOCK = (169, 169, 169)
PURPLE_BLOCK = (153, 50, 204)
CLEAR_BTN_COLOR = (244, 67, 54)
RUN_BTN_COLOR = (76, 175, 80)

# Screen Setup
WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ProgBlocks: Official Logic Edition")

# Fonts
font_small = pygame.font.SysFont('Arial', 16, bold=True)
font_header = pygame.font.SysFont('Arial', 24, bold=True)
font_console = pygame.font.SysFont('Consolas', 14)

# Keywords, Operators, Separators
KEYWORDS = {'digit', 'word', 'bet', 'out', 'adds', 'minus', 'end'}
OPERATORS = {':', 'adds', 'minus'}
SEPARATORS = {'end'}

# The Blocks of ProgBlocks
AVAILABLE_BLOCKS = [
    ("digit", ORANGE_BLOCK, "Keyword"),
    ("word", ORANGE_BLOCK, "Keyword"),
    ("bet", ORANGE_BLOCK, "Keyword"),
    (":", BLUE_BLOCK, "Operator"),
    ("adds", BLUE_BLOCK, "Operator"),
    ("minus", BLUE_BLOCK, "Operator"),
    ("end", GRAY_BLOCK, "Separator"),
    ("out", GRAY_BLOCK, "Keyword"),
    ("data", PURPLE_BLOCK, "Editable")
]

class Block:
    def __init__(self, text, color, category, x, y, is_template=False):
        self.text = text
        self.color = color
        self.category = category
        self.is_template = is_template
        self.is_editing = False
        self.next_block = None
        self.prev_block = None
        self.update_size()
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.dragging = False

    def update_size(self):
        try:
            text_surf = font_small.render(self.text + ("|" if self.is_editing else ""), True, WHITE)
            self.width = max(80, text_surf.get_width() + 20)
            self.height = 35
        except:
            self.width = 80
            self.height = 35

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        if self.is_editing:
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
        try:
            text_surf = font_small.render(self.text + ("|" if self.is_editing else ""), True, WHITE)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)
        except:
            pass

    def update_position(self, x, y):
        self.rect.x = x
        self.rect.y = y
        if self.next_block:
            self.next_block.update_position(self.rect.right + 2, self.rect.y)

# ---- THE COMPILER ----
"""This function checks if the token is valid"""
def is_valid_token(token):
    # Keywords, operators, separators are valid
    if token in KEYWORDS or token in OPERATORS or token in SEPARATORS:
        return True
    
    # Valid literals
    lit_type = get_literal_type(token)
    if lit_type:
        return True
    
    # Valid identifiers 
    if is_valid_identifier(token):
        return True
    
    return False

"""This function checks if a name is a valid identifier which starts with a letter or underscore followed by alphanumeric characters,
    It invalid if it is a keyword, starts with a digit, or contains special characters.""" 
def is_valid_identifier(name):
    try:
        if not name or len(name) == 0:
            return False
        if not (name[0].isalpha() or name[0] == '_'):
            return False
        if name in KEYWORDS:
            return False
        return all(c.isalnum() or c == '_' for c in name)
    except:
        return False

"""This function get and determines the literal type,
    if it is a digit, word, or bet"""
def get_literal_type(literal):
    try:
        stripped = literal.strip('"\'')
        if stripped.isdigit():
            return 'digit'
        if literal.startswith('"') and literal.endswith('"'):
            return 'word'
        if literal.startswith("'") and literal.endswith("'"):
            return 'word'
        if stripped.lower() in ['true', 'false']:
            return 'bet'
    except:
        pass
    return None

"""This function performs lexical analysis of the compiler input"""
def lexical_analysis(tokens):
    errors = []
    for i, token in enumerate(tokens):
        if not is_valid_token(token):
            if token in KEYWORDS:
                errors.append(f"Lexical Error [{i+1}]: '{token}' is a keyword, cannot use as identifier")
            elif get_literal_type(token) is None and not is_valid_identifier(token):
                errors.append(f"Lexical Error [{i+1}]: '{token}' is not a valid token")
            else:
                errors.append(f"Lexical Error [{i+1}]: Invalid token '{token}'")
    return errors

"""This function is for the compiler or block logic"""
def evaluate_compiler_logic(blocks):
    if not blocks:
        return ["Error: No blocks in workspace.", "Status: COMPILATION FAILED"]
    
    # Connection of Blocks
    curr = blocks[0] if blocks else None
    while curr and curr.prev_block:
        curr = curr.prev_block
    chain = []
    while curr:
        chain.append(curr)
        curr = curr.next_block
    
    if not chain:
        return ["Error: No valid blocks found.", "Status: COMPILATION FAILED"]
    
    # Tokenization of Block Texts
    tokens = [block.text.strip() for block in chain if block.text and block.text.strip()]
    
    if not tokens:
        return ["Error: No valid tokens.", "Status: COMPILATION FAILED"]
    
    results = []
    compiled_lines = []
    
    # Lexical Analysis
    lexical_errors = lexical_analysis(tokens)
    if lexical_errors:
        results.extend(lexical_errors)
        results.append("Status: LEXICAL ANALYSIS FAILED")
        return results
    
    results.append("Checking Lexical... OK")
    
    # Syntax Analysis
    if tokens[-1] != "end":
        results.append("Syntax Error: Missing 'end' terminator")
        results.append("Status: SYNTAX ANALYSIS FAILED")
        return results
    elif tokens[0] not in ['digit', 'word', 'bet', 'out']:
        results.append(f"Syntax Error: Invalid start token '{tokens[0]}'")
        results.append("Status: SYNTAX ANALYSIS FAILED")
        return results
    
    results.append("Checking Syntax... OK")
    
    # Semantic Analysis
    variables = {}
    error_occurred = False
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # If invalid token
        if token in ['digit', 'word', 'bet']:
            if i + 4 >= len(tokens) or tokens[i+2] != ':' or tokens[i+4] != 'end':
                results.append(f"Semantic Error [{i+1}]: Invalid declaration - expected ID : VALUE end")
                error_occurred = True
                break
            
            var_name = tokens[i+1]
            value = tokens[i+3]
            expected_type = token
            
            # Type Mismatch Checker
            actual_type = get_literal_type(value)
            if actual_type != expected_type:
                results.append(f"Semantic Error [{i+3}]: Type mismatch - expected {expected_type}, got {actual_type or 'invalid'}")
                error_occurred = True
                break
            
            # Binding variable to value
            if expected_type == 'digit':
                try:
                    variables[var_name] = int(value.strip('"\''))
                except:
                    variables[var_name] = float(value.strip('"\''))
            elif expected_type == 'word':
                variables[var_name] = value.strip('"\'')
            elif expected_type == 'bet':
                variables[var_name] = value.strip('"\'').lower() == 'true'

            if expected_type == 'digit':
                compiled_lines.append(f"int {var_name} = {value};")
            elif expected_type == 'word':
                compiled_lines.append(f"string {var_name} = {value};")
            elif expected_type == 'bet':
                compiled_lines.append(f"bool {var_name} = {value};")

            results.append(f"✓ Stored {expected_type} '{var_name}' = '{value}'")
            i += 5
            
        # Output Statement
        elif token == 'out':
            if i + 2 >= len(tokens) or tokens[i+2] != 'end':
                results.append(f"Semantic Error [{i+1}]: Invalid output - expected ID/LITERAL end")
                error_occurred = True
                break
            
            output_value = tokens[i+1]
            compiled_lines.append(f"print({output_value});")
            
            # Variable output
            if output_value in variables:
                results.append(f"> {variables[output_value]}")
            # Literal output
            else:
                lit_type = get_literal_type(output_value)
                if lit_type:
                    if lit_type == 'digit':
                        try:
                            val = int(output_value.strip('"\''))
                        except:
                            val = float(output_value.strip('"\''))
                        results.append(f"> {val}")
                    elif lit_type == 'word':
                        results.append(f"> {output_value.strip('\"\'')}")
                    else:
                        results.append(f"> {output_value}")
                else:
                    results.append(f"Semantic Error [{i+1}]: Undefined identifier '{output_value}'")
                    error_occurred = True
                    break
            
            i += 3
        else:
            i += 1
    
    # Compiled Output
    if compiled_lines:
        results.append("Compiled Output:")
        results.extend(compiled_lines)

    # Compiler Status
    if error_occurred:
        results.append("Status: SEMANTIC ANALYSIS FAILED")
    else:
        results.append("Status: COMPILATION SUCCESS")
        results.append("Program executed successfully!")
    
    return results

# ---- UI & MAIN LOOP ----
sidebar_blocks = [Block(t, c, cat, 15 + (i%2)*85, 60 + (i//2)*45, True) for i, (t, c, cat) in enumerate(AVAILABLE_BLOCKS)]
placed_blocks = []
dragging_block = None
editing_block = None
offset_x, offset_y = 0, 0
console_output = ["Blueprint ready!", "Drag blocks from the left to start building your program."]

clear_rect = pygame.Rect(WIDTH - 230, 415, 100, 35)
run_rect = pygame.Rect(WIDTH - 115, 415, 100, 35)

# MAIN LOOP
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BG_COLOR)
    
    screen.blit(font_header.render("Blox", True, BLACK), (20, 15))
    screen.blit(font_header.render("Blueprint", True, BLACK), (200, 15))
    pygame.draw.rect(screen, WORKSPACE_COLOR, (200, 60, WIDTH - 220, 340), border_radius=5)
    
    pygame.draw.rect(screen, CLEAR_BTN_COLOR, clear_rect, border_radius=8)
    screen.blit(font_small.render("CLEAR", True, WHITE), (clear_rect.centerx - 25, clear_rect.centery - 10))
    pygame.draw.rect(screen, RUN_BTN_COLOR, run_rect, border_radius=8)
    screen.blit(font_small.render("RUN", True, WHITE), (run_rect.centerx - 15, run_rect.centery - 10))
    
    pygame.draw.rect(screen, CONSOLE_COLOR, (200, 460, WIDTH - 220, 160))
    for i, line in enumerate(console_output[-9:]):
        color = BLUE_TEXT if line.startswith(">") else (GREEN_TEXT if "✓" in line or "OK" in line or "SUCCESS" in line or "ready" in line else RED_TEXT)
        try:
            screen.blit(font_console.render(line, True, color), (210, 470 + i * 17))
        except:
            pass

    for b in sidebar_blocks: b.draw(screen)
    for b in placed_blocks: b.draw(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            
            sidebar_hit = False
            for b in sidebar_blocks:
                if b.rect.collidepoint(mouse_x, mouse_y):
                    new_block = Block(b.text, b.color, b.category, mouse_x, mouse_y)
                    new_block.dragging = True
                    dragging_block = new_block
                    offset_x = 0
                    offset_y = 0
                    placed_blocks.append(new_block)
                    sidebar_hit = True
                    break
            
            if not sidebar_hit:
                for b in reversed(placed_blocks):
                    if b.rect.collidepoint(mouse_x, mouse_y):
                        if b.category == "Editable":
                            if editing_block and editing_block != b:
                                editing_block.is_editing = False
                            b.is_editing = True
                            editing_block = b
                        
                        if b.prev_block:
                            b.prev_block.next_block = b.next_block
                        if b.next_block:
                            b.next_block.prev_block = b.prev_block
                        
                        b.prev_block = None
                        b.next_block = None
                        b.dragging = True
                        dragging_block = b
                        offset_x = mouse_x - b.rect.x
                        offset_y = mouse_y - b.rect.y
                        break
                
                if clear_rect.collidepoint(mouse_x, mouse_y):
                    placed_blocks.clear()
                    console_output = ["Workspace cleared."]
                    if editing_block:
                        editing_block.is_editing = False
                        editing_block = None
                elif run_rect.collidepoint(mouse_x, mouse_y):
                    console_output = evaluate_compiler_logic(placed_blocks)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if dragging_block:
                dragging_block.dragging = False
                dragging_block.update_size()
                
                for other in placed_blocks:
                    if other != dragging_block and other.next_block is None:
                        if (abs(dragging_block.rect.left - other.rect.right) < 20 and 
                            abs(dragging_block.rect.centery - other.rect.centery) < 20):
                            other.next_block = dragging_block
                            dragging_block.prev_block = other
                            dragging_block.update_position(other.rect.right + 2, other.rect.y)
                            break
                
                if dragging_block.rect.x < 190 and dragging_block not in sidebar_blocks:
                    if dragging_block in placed_blocks:
                        placed_blocks.remove(dragging_block)
                
                dragging_block = None
        
        elif event.type == pygame.MOUSEMOTION:
            if dragging_block:
                dragging_block.rect.x = event.pos[0] - offset_x
                dragging_block.rect.y = event.pos[1] - offset_y
        
        elif event.type == pygame.KEYDOWN:
            if editing_block:
                if event.key == pygame.K_BACKSPACE:
                    if len(editing_block.text) > 0:
                        editing_block.text = editing_block.text[:-1]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    editing_block.is_editing = False
                    editing_block = None
                else:
                    try:
                        editing_block.text += event.unicode
                    except:
                        pass
                if editing_block:
                    editing_block.update_size()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()