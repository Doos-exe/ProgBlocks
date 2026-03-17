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
pygame.display.set_caption("ProgBlocks: Block and Compile!")

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

"""This function checks if a name is a valid identifier which starts with a letter 
    or underscore followed by alphanumeric characters, It invalid if it is a keyword, 
    starts with a digit, or contains special characters.""" 
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

"""This function get and determines the literal type, if it is a digit, word, or bet"""
def get_literal_type(literal):
    try:
        stripped = literal.strip('"\'')
        if stripped.isdigit():
            return 'digit'
        # Check for word (string) literals - must have both opening and closing quotes
        if literal.startswith('"') and literal.endswith('"') and len(literal) >= 2:
            return 'word'
        if literal.startswith("'") and literal.endswith("'") and len(literal) >= 2:
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

def get_recovery_strategies(error_type, error_details):
    """Return recovery strategies for different error types"""
    strategies = {
        "lexical_invalid_token": [
            "RECOVERY STRATEGIES:",
            "1. Check token spelling and capitalization",
            "2. Use valid keywords: digit, word, bet, out, end, :, adds, minus",
            "3. Variable names must start with letter or underscore",
            "4. Numbers must be wrapped in quotes for string/word types",
            "5. Strings must use double quotes: \"hello\"",
            "6. Booleans must be: true or false"
        ],
        "syntax_missing_end": [
            "RECOVERY STRATEGIES:",
            "1. Every program must end with 'end' block",
            "2. Block structure: TYPE NAME : VALUE end",
            "3. Output structure: out VALUE end",
            "4. Add missing 'end' terminator at the conclusion",
            "5. Chain blocks together: drag and connect visually"
        ],
        "syntax_invalid_start": [
            "RECOVERY STRATEGIES:",
            "1. Programs must start with: digit, word, bet, or out",
            "2. digit = numeric variable declaration",
            "3. word = string variable declaration",
            "4. bet = boolean variable declaration",
            "5. out = output/print statement",
            "6. Start with a declaration or output block"
        ],
        "semantic_type_mismatch": [
            "RECOVERY STRATEGIES:",
            "1. Match value type to declared type",
            "2. digit expects numbers: 42, 3, 100",
            "3. word expects quoted strings: \"hello\", \"world\"",
            "4. bet expects boolean: true or false",
            "5. Check quotes around string values",
            "6. Numbers don't need quotes for digit type"
        ],
        "semantic_undefined_identifier": [
            "RECOVERY STRATEGIES:",
            "1. Declare variable before using in output",
            "2. Variable names are case-sensitive",
            "3. Check spelling of variable names",
            "4. Declare with: digit, word, or bet first",
            "5. Use full declaration: TYPE NAME : VALUE end",
            "6. Then output with: out VARNAME end"
        ],
        "semantic_invalid_declaration": [
            "RECOVERY STRATEGIES:",
            "1. Declaration format: TYPE NAME : VALUE end",
            "2. Replace TYPE with: digit, word, or bet",
            "3. NAME must be valid identifier",
            "4. VALUE must match the TYPE",
            "5. : and end are required separators",
            "6. Example: digit count : 5 end"
        ]
    }
    return strategies.get(error_type, ["No recovery strategies available for this error"])


"""This function is for the compiler or block logic"""
def evaluate_compiler_logic(blocks):
    if not blocks:
        return ["Error: No blocks in workspace.", "Status: COMPILATION FAILED"], {}

    # Connection of Blocks
    curr = blocks[0] if blocks else None
    while curr and curr.prev_block:
        curr = curr.prev_block
    chain = []
    while curr:
        chain.append(curr)
        curr = curr.next_block

    if not chain:
        return ["Error: No valid blocks found.", "Status: COMPILATION FAILED"], {}

    # Tokenization of Block Texts
    tokens = [block.text.strip() for block in chain if block.text and block.text.strip()]

    if not tokens:
        return ["Error: No valid tokens.", "Status: COMPILATION FAILED"], {}

    results = []
    compiled_lines = []
    detailed_phases = {"lexical": [], "syntax": [], "semantic": [], "recovery": []}

    # Lexical Analysis
    lexical_errors = lexical_analysis(tokens)
    if lexical_errors:
        results.extend(lexical_errors)
        results.append("Status: LEXICAL ANALYSIS FAILED")
        detailed_phases["lexical"] = ["PHASE: LEXICAL ANALYSIS"] + lexical_errors
        detailed_phases["lexical"].append("Result: [FAILED]")
        detailed_phases["recovery"] = get_recovery_strategies("lexical_invalid_token", "")
        return results, detailed_phases

    # Build detailed lexical output
    detailed_phases["lexical"].append("PHASE: LEXICAL ANALYSIS")
    detailed_phases["lexical"].append(f"Tokens: {' '.join(tokens)}")
    for i, token in enumerate(tokens):
        if token in KEYWORDS:
            detailed_phases["lexical"].append(f"  [{i+1}] '{token}' -> Keyword")
        elif token in OPERATORS:
            detailed_phases["lexical"].append(f"  [{i+1}] '{token}' -> Operator")
        elif token in SEPARATORS:
            detailed_phases["lexical"].append(f"  [{i+1}] '{token}' -> Separator")
        else:
            lit_type = get_literal_type(token)
            if lit_type:
                detailed_phases["lexical"].append(f"  [{i+1}] '{token}' -> Literal ({lit_type})")
            else:
                detailed_phases["lexical"].append(f"  [{i+1}] '{token}' -> Identifier")
    detailed_phases["lexical"].append("Result: [PASSED]")

    results.append("Checking Lexical... OK")

    # Syntax Analysis
    detailed_phases["syntax"].append("PHASE: SYNTAX ANALYSIS")
    if tokens[-1] != "end":
        results.append("Syntax Error: Missing 'end' terminator")
        results.append("Status: SYNTAX ANALYSIS FAILED")
        detailed_phases["syntax"].append("ERROR: Missing 'end' terminator")
        detailed_phases["syntax"].append("Result: [FAILED]")
        detailed_phases["recovery"] = get_recovery_strategies("syntax_missing_end", "")
        return results, detailed_phases
    elif tokens[0] not in ['digit', 'word', 'bet', 'out']:
        results.append(f"Syntax Error: Invalid start token '{tokens[0]}'")
        results.append("Status: SYNTAX ANALYSIS FAILED")
        detailed_phases["syntax"].append(f"ERROR: Invalid start token '{tokens[0]}'")
        detailed_phases["syntax"].append("Result: [FAILED]")
        detailed_phases["recovery"] = get_recovery_strategies("syntax_invalid_start", tokens[0])
        return results, detailed_phases

    detailed_phases["syntax"].append(f"First token: {tokens[0]} (Valid)")
    detailed_phases["syntax"].append(f"Last token: {tokens[-1]} (Valid terminator)")
    detailed_phases["syntax"].append("Result: [PASSED]")

    results.append("Checking Syntax... OK")

    # Semantic Analysis
    variables = {}
    error_occurred = False
    detailed_phases["semantic"].append("PHASE: SEMANTIC ANALYSIS")

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # If invalid token
        if token in ['digit', 'word', 'bet']:
            if i + 4 >= len(tokens) or tokens[i+2] != ':' or tokens[i+4] != 'end':
                results.append(f"Semantic Error [{i+1}]: Invalid declaration - expected ID : VALUE end")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Invalid declaration at token {i+1}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "")
                break

            var_name = tokens[i+1]
            value = tokens[i+3]
            expected_type = token

            # Check if variable name is a keyword - not allowed
            if var_name in KEYWORDS:
                results.append(f"Semantic Error [{i+2}]: '{var_name}' is a keyword, cannot use as variable name")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Keyword '{var_name}' cannot be used as variable name at token {i+2}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", f"use a different name, not '{var_name}'")
                break

            # Check if variable name is an operator - not allowed
            if var_name in OPERATORS or var_name in SEPARATORS:
                error_detail = "mathematical keyword" if var_name in ['adds', 'minus'] else "reserved symbol"
                results.append(f"Semantic Error [{i+2}]: '{var_name}' is a {error_detail}, cannot use as variable name")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: {error_detail.capitalize()} '{var_name}' cannot be used as variable name at token {i+2}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", f"'{var_name}' is a {error_detail}, use a different name")
                break

            # Check if variable name contains or is quotes - not allowed
            if '"' in var_name or "'" in var_name:
                results.append(f"Semantic Error [{i+2}]: Variable name cannot contain quotes: '{var_name}'")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Variable name contains quotes at token {i+2}: '{var_name}'")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "remove quotes from variable name")
                break

            # Check if variable name is valid identifier format
            if not is_valid_identifier(var_name):
                results.append(f"Semantic Error [{i+2}]: '{var_name}' is not a valid variable name")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Invalid variable name at token {i+2}: '{var_name}'")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "use valid identifier: letters, numbers, underscores")
                break

            # Type Mismatch Checker
            actual_type = get_literal_type(value)
            if actual_type != expected_type:
                results.append(f"Semantic Error [{i+3}]: Type mismatch - expected {expected_type}, got {actual_type or 'invalid'}")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Type mismatch at '{var_name}' - expected {expected_type}, got {actual_type}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_type_mismatch", f"expected {expected_type}, got {actual_type}")
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
                compiled_lines.append(f"digit {var_name} : {value} end")
            elif expected_type == 'word':
                compiled_lines.append(f"word {var_name} : {value} end")
            elif expected_type == 'bet':
                compiled_lines.append(f"bet {var_name} : {value} end")

            detailed_phases["semantic"].append(f"  Declaration: {expected_type} {var_name} : {value}")
            detailed_phases["semantic"].append(f"    Variable '{var_name}' bound to value '{value}' (type: {expected_type})")
            i += 5

        # Output Statement
        elif token == 'out':
            if i + 2 >= len(tokens) or tokens[i+2] != 'end':
                results.append(f"Semantic Error [{i+1}]: Invalid output - expected ID/LITERAL end")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Invalid output statement at token {i+1}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "output format: out VALUE end")
                break

            output_value = tokens[i+1]
            compiled_lines.append(f"out {output_value} end")

            # Variable output
            if output_value in variables:
                results.append(f"> {variables[output_value]}")
                detailed_phases["semantic"].append(f"  Output: Variable '{output_value}' = {variables[output_value]}")
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
                        detailed_phases["semantic"].append(f"  Output: Literal value '{val}' (type: {lit_type})")
                    elif lit_type == 'word':
                        results.append(f"> {output_value.strip('\"\'')}")
                        detailed_phases["semantic"].append(f"  Output: Literal string '{output_value.strip('\"\'')}'")
                    else:
                        results.append(f"> {output_value}")
                        detailed_phases["semantic"].append(f"  Output: Literal value '{output_value}'")
                else:
                    results.append(f"Semantic Error [{i+1}]: Undefined identifier '{output_value}'")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Undefined identifier '{output_value}' at token {i+1}")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_undefined_identifier", output_value)
                    break

            i += 3
        else:
            i += 1

    if not error_occurred:
        results.append("Checking Semantical... OK")

    # Compiled Output
    if compiled_lines:
        results.append("Compiled Output:")
        results.extend(compiled_lines)

    # Compiler Status
    if error_occurred:
        results.append("Status: SEMANTIC ANALYSIS FAILED")
        detailed_phases["semantic"].append("Result: [FAILED]")
    else:
        results.append("Status: COMPILATION SUCCESS")
        results.append("Program executed successfully!")
        detailed_phases["semantic"].append("Result: [PASSED]")

    return results, detailed_phases

# ---- EXPLAINABILITY WINDOW ----
def show_explainability_window(detailed_phases):
    detail_window = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption("ProgBlocks: Explainability Layer")
    detail_running = True
    scroll_offset = 0

    while detail_running:
        detail_window.fill(CONSOLE_COLOR)

        # Draw header
        header_text = font_header.render("COMPILER ANALYSIS PHASES", True, BLUE_TEXT)
        detail_window.blit(header_text, (20, 15))

        y_pos = 60
        line_height = 18

        # Display each phase
        for phase_name, phase_color, phase_indent in [
            ("LEXICAL ANALYSIS", GREEN_TEXT if "PASSED" in " ".join(detailed_phases.get("lexical", [])) else RED_TEXT, 0),
            ("SYNTAX ANALYSIS", GREEN_TEXT if "PASSED" in " ".join(detailed_phases.get("syntax", [])) else RED_TEXT, 0),
            ("SEMANTIC ANALYSIS", GREEN_TEXT if "PASSED" in " ".join(detailed_phases.get("semantic", [])) else RED_TEXT, 0)
        ]:
            phase_key = phase_name.lower().split()[0]

            # Phase header
            if y_pos - scroll_offset > 0 and y_pos - scroll_offset < 680:
                phase_header = font_small.render(phase_name, True, phase_color)
                detail_window.blit(phase_header, (20 + phase_indent, y_pos - scroll_offset))
            y_pos += line_height + 5

            # Phase details
            for detail_line in detailed_phases.get(phase_key, []):
                if y_pos - scroll_offset > 0 and y_pos - scroll_offset < 680:
                    detail_text = font_console.render(detail_line, True, (200, 200, 200))
                    detail_window.blit(detail_text, (30 + phase_indent, y_pos - scroll_offset))
                y_pos += line_height

            y_pos += 10

        # Display recovery strategies if there are errors
        if detailed_phases.get("recovery"):
            y_pos += 5
            if y_pos - scroll_offset > 0 and y_pos - scroll_offset < 680:
                recovery_header = font_small.render("RECOVERY STRATEGIES", True, (255, 200, 0))
                detail_window.blit(recovery_header, (20, y_pos - scroll_offset))
            y_pos += line_height + 5

            for strategy_line in detailed_phases.get("recovery", []):
                if y_pos - scroll_offset > 0 and y_pos - scroll_offset < 680:
                    strategy_text = font_console.render(strategy_line, True, (100, 200, 255))
                    detail_window.blit(strategy_text, (30, y_pos - scroll_offset))
                y_pos += line_height

        # Draw scroll instructions
        scroll_text = font_small.render("Scroll: UP/DOWN arrows | Close: ESC", True, BLUE_TEXT)
        detail_window.blit(scroll_text, (20, 650))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                detail_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    detail_running = False
                elif event.key == pygame.K_UP:
                    scroll_offset = max(0, scroll_offset - 30)
                elif event.key == pygame.K_DOWN:
                    scroll_offset += 30

        clock.tick(60)

    pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ProgBlocks: Official Logic Edition")

# ---- UI & MAIN LOOP ----
sidebar_blocks = [Block(t, c, cat, 15 + (i%2)*85, 60 + (i//2)*45, True) for i, (t, c, cat) in enumerate(AVAILABLE_BLOCKS)]
placed_blocks = []
dragging_block = None
editing_block = None
offset_x, offset_y = 0, 0
console_output = ["Blueprint ready!", "Drag blocks from the left to start building your program."]
detailed_phases = {}

clear_rect = pygame.Rect(WIDTH - 230, 415, 100, 35)
run_rect = pygame.Rect(WIDTH - 115, 415, 100, 35)
info_rect = pygame.Rect(WIDTH - 350, 415, 100, 35)

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
    pygame.draw.rect(screen, BLUE_TEXT, info_rect, border_radius=8)
    screen.blit(font_small.render("INFO", True, WHITE), (info_rect.centerx - 18, info_rect.centery - 10))
    
    pygame.draw.rect(screen, CONSOLE_COLOR, (200, 460, WIDTH - 220, 160))
    for i, line in enumerate(console_output[-9:]):
        color = BLUE_TEXT if line.startswith(">") else (GREEN_TEXT if "PASSED" in line or "OK" in line or "SUCCESS" in line or "ready" in line else RED_TEXT)
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
                            b.dragging = True
                            dragging_block = b
                            offset_x = mouse_x - b.rect.x
                            offset_y = mouse_y - b.rect.y
                            break  # Just enter edit mode and mark for potential drag, don't disconnect yet

                        # Only disconnect and drag non-editable blocks
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
                    detailed_phases = {}
                    if editing_block:
                        editing_block.is_editing = False
                        editing_block = None
                elif run_rect.collidepoint(mouse_x, mouse_y):
                    console_output, detailed_phases = evaluate_compiler_logic(placed_blocks)
                elif info_rect.collidepoint(mouse_x, mouse_y):
                    if detailed_phases:
                        show_explainability_window(detailed_phases)
        
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
                # If dragging an editable block that hasn't been disconnected yet, disconnect it now
                if dragging_block.category == "Editable" and dragging_block.prev_block is not None:
                    if dragging_block.prev_block:
                        dragging_block.prev_block.next_block = dragging_block.next_block
                    if dragging_block.next_block:
                        dragging_block.next_block.prev_block = dragging_block.prev_block
                    dragging_block.prev_block = None
                    dragging_block.next_block = None

                dragging_block.rect.x = event.pos[0] - offset_x
                dragging_block.rect.y = event.pos[1] - offset_y
        
        elif event.type == pygame.KEYDOWN:
            if editing_block:
                if event.key == pygame.K_BACKSPACE:
                    if len(editing_block.text) > 0:
                        editing_block.text = editing_block.text[:-1]
                    editing_block.update_size()
                elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    editing_block.is_editing = False
                    editing_block.update_size()
                    editing_block = None
                else:
                    try:
                        editing_block.text += event.unicode
                        editing_block.update_size()
                    except:
                        pass
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()