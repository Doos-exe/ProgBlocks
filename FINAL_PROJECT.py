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
ORIGINAL_WIDTH, ORIGINAL_HEIGHT = 900, 650
MINIMUM_WIDTH, MINIMUM_HEIGHT = 600, 400
WIDTH, HEIGHT = ORIGINAL_WIDTH, ORIGINAL_HEIGHT

# Sidebar and workspace constants
SIDEBAR_WIDTH = 170
WORKSPACE_LEFT = 200
WORKSPACE_BOTTOM = 460
CONSOLE_HEIGHT = 160
BUTTON_HEIGHT = 35

# Zoom and layout variables
zoom_scale = 1.0
ZOOM_MIN = 0.5
ZOOM_MAX = 2.0
ZOOM_STEP = 0.1

# Dynamic layout boundaries (calculated in recalculate_ui_positions)
HEADER_HEIGHT = 50
CONSOLE_HEIGHT_FIXED = 120
WORKSPACE_RIGHT_MARGIN = 20

# Separator configuration for draggable console
SEPARATOR_HEIGHT = 10  # Draggable zone height (±5px from separator line)
MIN_CONSOLE_HEIGHT = 60  # Minimum console height when dragged
MAX_CONSOLE_HEIGHT = int(ORIGINAL_HEIGHT * 0.75)  # Max before workspace becomes too small

workspace_top = HEADER_HEIGHT
workspace_bottom = HEIGHT - CONSOLE_HEIGHT_FIXED
console_top = HEIGHT - CONSOLE_HEIGHT_FIXED
console_bottom = HEIGHT

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("ProgBlocks: Block and Compile!")

# Fonts
font_small = pygame.font.SysFont('Arial', 16, bold=True)
font_header = pygame.font.SysFont('Arial', 24, bold=True)
font_console = pygame.font.SysFont('Consolas', 14)

# Keywords, Operators, Separators
KEYWORDS = {'digit', 'word', 'bet', 'out', 'adds', 'minus', 'end'}
OPERATORS = {':', ':=', 'adds', 'minus'}
SEPARATORS = {'end'}

# The Blocks of ProgBlocks
AVAILABLE_BLOCKS = [
    ("digit", ORANGE_BLOCK, "Keyword"),
    ("word", ORANGE_BLOCK, "Keyword"),
    ("bet", ORANGE_BLOCK, "Keyword"),
    (":", BLUE_BLOCK, "Operator"),
    (":=", BLUE_BLOCK, "Operator"),
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
        self.connection_direction = "vertical"  
        self.text_surf = None  
        self.rect = None  
        self.update_size()
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.dragging = False

    def update_size(self):
        try:
            text_display = self.text + ("|" if self.is_editing else "")
            text_surf = font_small.render(text_display, True, WHITE)
            self.width = max(80, text_surf.get_width() + 20)
            self.height = 35
            self.text_surf = text_surf  
        except:
            self.width = 80
            self.height = 35
            self.text_surf = None
        if self.rect:
            self.rect.width = self.width
            self.rect.height = self.height

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        if self.is_editing:
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
        try:
            if self.text_surf:
                text_rect = self.text_surf.get_rect(center=self.rect.center)
                surface.blit(self.text_surf, text_rect)
            else:
                text_display = self.text + ("|" if self.is_editing else "")
                text_surf = font_small.render(text_display, True, WHITE)
                text_rect = text_surf.get_rect(center=self.rect.center)
                surface.blit(text_surf, text_rect)
        except:
            pass

    def update_position(self, x, y):
        self.rect.x = x
        self.rect.y = y
        if self.next_block:
            # Binding of blocks
            if self.connection_direction == "horizontal":
                # Sticking the block to the right
                self.next_block.update_position(self.rect.right + 2, self.rect.y)
            else:
                # Sticking the block below
                self.next_block.update_position(self.rect.x, self.rect.bottom + 2)

# ---- THE COMPILER ----
"""This function checks if the token is valid"""
def is_valid_token(token):
    # Valid Keywords, Operators, Separators
    if token in KEYWORDS or token in OPERATORS or token in SEPARATORS:
        return True
    
    # Valid Literals
    lit_type = get_literal_type(token)
    if lit_type:
        return True
    
    # Valid Identifiers 
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

        # Check for bet values either 'real' or 'fake' 
        if stripped.lower() in ['real', 'fake']:
            return 'bet'

        # Check for digit
        if stripped.isdigit():
            return 'digit'

        # Check for word (string) literals - must have both opening and closing quotes
        if literal.startswith('"') and literal.endswith('"') and len(literal) >= 2:
            return 'word'
        if literal.startswith("'") and literal.endswith("'") and len(literal) >= 2:
            return 'word'
    except:
        pass
    return None

"""This function performs lexical analysis of the compiler input"""
def lexical_analysis(tokens):
    errors = []
    for i, token in enumerate(tokens):
        if not is_valid_token(token):
            if get_literal_type(token) is None and not is_valid_identifier(token):
                errors.append(f"Lexical Error [{i+1}]: Variable '{token}' not found")
            else:
                errors.append(f"Lexical Error [{i+1}]: Invalid token '{token}'")
    return errors

# Recovery strategies for different error types
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
    # No blocks in the blueprint area
    if not blocks:
        return ["Error: No blocks in workspace.", "Status: COMPILATION FAILED"], {}

    # Remove blocks that are outside the blueprint area
    valid_blocks = [b for b in blocks if b.rect.x >= WORKSPACE_LEFT and b.rect.x + b.rect.width <= WIDTH - WORKSPACE_RIGHT_MARGIN and b.rect.y >= workspace_top and b.rect.y + b.rect.height <= workspace_bottom]

    if not valid_blocks:
        return ["Error: No blocks in valid blueprint area.", "Status: COMPILATION FAILED"], {}

    # Initial block detection
    chain_starts = [b for b in valid_blocks if b.prev_block is None]

    if not chain_starts:
        return ["Error: No valid blocks found.", "Status: COMPILATION FAILED"], {}

    # The precedence of blocks (Top to Bottom, Left to Right)
    chain_starts.sort(key=lambda b: (b.rect.y, b.rect.x))

    # Reading the chains of blocks
    all_chains = []
    for start_block in chain_starts:
        chain = []
        curr = start_block
        while curr:
            chain.append(curr)
            curr = curr.next_block
        all_chains.append(chain)

    # Tokenization of all blocks within the chains
    all_blocks = []
    for chain in all_chains:
        all_blocks.extend(chain)

    # Tokenization of Block Texts
    tokens = [block.text.strip() for block in all_blocks if block.text and block.text.strip()]

    if not tokens:
        return ["Error: No valid tokens.", "Status: COMPILATION FAILED"], {}

    results = []
    compiled_lines = []
    output_results = []  
    detailed_phases = {"lexical": [], "syntax": [], "semantic": [], "recovery": [], "symbol_table": [], "phase_status": {}}

    # Lexical Analysis
    lexical_errors = lexical_analysis(tokens)
    if lexical_errors:
        results.extend(lexical_errors)
        results.append("Status: LEXICAL ANALYSIS FAILED")
        detailed_phases["lexical"] = ["PHASE: LEXICAL ANALYSIS"] + lexical_errors
        detailed_phases["lexical"].append("Result: [FAILED]")
        detailed_phases["recovery"] = get_recovery_strategies("lexical_invalid_token", "")
        return results, detailed_phases

    # Keyword Classification and Token Details
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

    # Keywords as identifiers checker
    for i, token in enumerate(tokens):
        if token in KEYWORDS and i > 0 and tokens[i-1] in ['digit', 'word', 'bet']:
            results.append(f"Syntax Error [{i+1}]: Cannot use keyword '{token}' as identifier")
            results.append("Status: SYNTAX ANALYSIS FAILED")
            detailed_phases["syntax"].append(f"ERROR: Keyword '{token}' cannot be used as identifier at position {i+1}")
            detailed_phases["syntax"].append("Result: [FAILED]")
            detailed_phases["recovery"] = get_recovery_strategies("syntax_invalid_start", "")
            return results, detailed_phases

    # Statement validation
    detailed_phases["syntax"].append(f"Program structure validation:")
    detailed_phases["syntax"].append(f"  Total tokens: {len(tokens)}")

    # Parse statements by 'end' delimiter
    statement_start = 0
    statement_num = 1
    syntax_error = False
    for i, token in enumerate(tokens):
        if token == 'end':
            # Extract statement
            statement_tokens = tokens[statement_start:i+1]
            if statement_tokens:
                first = statement_tokens[0]
                last = statement_tokens[-1]
                token_count = len(statement_tokens)
                statement_str = ' '.join(statement_tokens)

                # Validate statement structure
                if first in ['digit', 'word', 'bet', 'out'] and last == 'end':
                    detailed_phases["syntax"].append(f"  Statement {statement_num}: {statement_str} - [VALID]")
                else:
                    # Invalid statement - report error and stop
                    results.append(f"Syntax Error: Invalid statement structure at Statement {statement_num}")
                    results.append(f"Statement {statement_num}: {statement_str}")
                    results.append(f"Expected: [KEYWORD/OUT] [ARGS...] end")
                    results.append("Status: SYNTAX ANALYSIS FAILED")
                    detailed_phases["syntax"].append(f"ERROR: Invalid statement structure at Statement {statement_num}")
                    detailed_phases["syntax"].append(f"  Statement {statement_num}: {statement_str}")
                    detailed_phases["syntax"].append(f"  First token: '{first}' - expected keyword (digit/word/bet/out)")
                    detailed_phases["syntax"].append(f"  Last token: '{last}' - expected 'end'")
                    detailed_phases["syntax"].append("Result: [FAILED]")
                    detailed_phases["recovery"] = get_recovery_strategies("syntax_invalid_start", "")
                    return results, detailed_phases

                statement_num += 1
            statement_start = i + 1

    detailed_phases["syntax"].append("Result: [PASSED]")

    results.append("Checking Syntax... OK")

    # Semantic Analysis
    variables = {}
    variable_types = {}  # Check for datatypes
    memory_offset = 0  # Counter for memory offsets for symbol table
    offset_sizes = {'digit': 4, 'word': 1, 'bet': 2}  # Width of each datatype
    error_occurred = False
    detailed_phases["semantic"].append("PHASE: SEMANTIC ANALYSIS")

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # If invalid token
        if token in ['digit', 'word', 'bet']:
            # Comparison for the bet datatype: 
            if token == 'bet' and i + 5 < len(tokens) and tokens[i+2] == ':=' and tokens[i+5] == 'end':
                # Comparison pattern: bet NAME := VALUE1 VALUE2 end
                var_name = tokens[i+1]
                value1 = tokens[i+3]
                value2 = tokens[i+4]
                expected_type = 'bet'

                # Validate variable name
                if var_name in KEYWORDS or var_name in OPERATORS or var_name in SEPARATORS:
                    error_detail = "keyword" if var_name in KEYWORDS else "reserved symbol"
                    results.append(f"Semantic Error [{i+2}]: '{var_name}' is a {error_detail}, cannot use as variable name")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: {error_detail.capitalize()} '{var_name}' cannot be used as variable name")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", f"use a different name, not '{var_name}'")
                    break

                if '"' in var_name or "'" in var_name or not is_valid_identifier(var_name):
                    results.append(f"Semantic Error [{i+2}]: Invalid variable name '{var_name}'")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Invalid variable name at token {i+2}")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "use valid identifier")
                    break

                # Check for duplicate variable names
                if var_name in variables:
                    results.append(f"Semantic Error [{i+2}]: Variable '{var_name}' already declared")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Duplicate variable name '{var_name}' at token {i+2}")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", f"use a different variable name, '{var_name}' is already declared")
                    break

                # Get actual values for comparison
                val1 = None
                val2 = None

                # Resolve value1
                if value1 in variables:
                    val1 = variables[value1]
                else:
                    lit_type = get_literal_type(value1)
                    if lit_type == 'digit':
                        try:
                            val1 = int(value1.strip('"\''))
                        except:
                            val1 = float(value1.strip('"\''))
                    elif lit_type == 'word':
                        val1 = value1.strip('"\'')
                    elif lit_type == 'bet':
                        val1 = value1.strip('"\'').lower() == 'real'
                    else:
                        if is_valid_identifier(value1):
                            results.append(f"Semantic Error [{i+3}]: Variable '{value1}' not found")
                        else:
                            results.append(f"Semantic Error [{i+3}]: Invalid value '{value1}'")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Cannot resolve value at token {i+3}")
                        break

                # Resolve value2
                if value2 in variables:
                    val2 = variables[value2]
                else:
                    lit_type = get_literal_type(value2)
                    if lit_type == 'digit':
                        try:
                            val2 = int(value2.strip('"\''))
                        except:
                            val2 = float(value2.strip('"\''))
                    elif lit_type == 'word':
                        val2 = value2.strip('"\'')
                    elif lit_type == 'bet':
                        val2 = value2.strip('"\'').lower() == 'real'
                    else:
                        if is_valid_identifier(value2):
                            results.append(f"Semantic Error [{i+4}]: Variable '{value2}' not found")
                        else:
                            results.append(f"Semantic Error [{i+4}]: Invalid value '{value2}'")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Cannot resolve value at token {i+4}")
                        break

                # Perform comparison and assign result
                variables[var_name] = val1 == val2
                variable_types[var_name] = 'bet'  # Store type
                compiled_lines.append(f"bet {var_name} := {value1} {value2} end")
                detailed_phases["semantic"].append(f"  Comparison: bet {var_name} := {value1} {value2}")
                bet_result = "Real" if variables[var_name] else "Fake"
                detailed_phases["semantic"].append(f"    Variable '{var_name}' assigned comparison result: {bet_result} (type: bet)")

                # Add to symbol table
                scope_level = 0
                detailed_phases["symbol_table"].append(f"{var_name:<20} {'bet':<15} {scope_level:<12} {memory_offset}")
                memory_offset += offset_sizes.get('bet', 0)

                i += 6
                continue

            # Check for operation pattern or simple pattern
            has_operation = False
            operation = None

            if i + 6 < len(tokens) and tokens[i+2] == ':' and tokens[i+4] in ['adds', 'minus'] and tokens[i+6] == 'end':
                has_operation = True
                operation = tokens[i+4]
            elif i + 4 >= len(tokens) or tokens[i+2] != ':' or tokens[i+4] != 'end':
                # Invalid structure
                if not (i + 6 < len(tokens) and tokens[i+4] in ['adds', 'minus']):
                    results.append(f"Semantic Error [{i+1}]: Invalid declaration - expected ID : VALUE end")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Invalid declaration at token {i+1}")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "")
                    break

            var_name = tokens[i+1]
            value = tokens[i+3]
            expected_type = token
            value_stripped = value.strip('"\'')
            if has_operation:
                value2 = tokens[i+5]
                value2_stripped = value2.strip('"\'')
            else:
                value2_stripped = None

            # Check if variable name is a keyword 
            if var_name in KEYWORDS:
                results.append(f"Semantic Error [{i+2}]: '{var_name}' is a keyword, cannot use as variable name")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Keyword '{var_name}' cannot be used as variable name at token {i+2}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", f"use a different name, not '{var_name}'")
                break

            # Check if variable name is an operator
            if var_name in OPERATORS or var_name in SEPARATORS:
                error_detail = "mathematical keyword" if var_name in ['adds', 'minus'] else "reserved symbol"
                results.append(f"Semantic Error [{i+2}]: '{var_name}' is a {error_detail}, cannot use as variable name")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: {error_detail.capitalize()} '{var_name}' cannot be used as variable name at token {i+2}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", f"'{var_name}' is a {error_detail}, use a different name")
                break

            # Check if variable name contains or is quotes
            if '"' in var_name or "'" in var_name:
                results.append(f"Semantic Error [{i+2}]: Variable name cannot contain quotes: '{var_name}'")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Variable name contains quotes at token {i+2}: '{var_name}'")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "remove quotes from variable name")
                break

            # Check if variable name is valid
            if not is_valid_identifier(var_name):
                results.append(f"Semantic Error [{i+2}]: '{var_name}' is not a valid variable name")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Invalid variable name at token {i+2}: '{var_name}'")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "use valid identifier: letters, numbers, underscores")
                break

            # Check for duplicate variable names
            if var_name in variables:
                results.append(f"Semantic Error [{i+2}]: Variable '{var_name}' already declared")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Duplicate variable name '{var_name}' at token {i+2}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", f"use a different variable name, '{var_name}' is already declared")
                break

            # Type Mismatch Checker
            actual_type = get_literal_type(value)
            if actual_type is None:
                if is_valid_identifier(value):
                    if value not in variables:
                        results.append(f"Semantic Error [{i+3}]: Variable '{value}' not found")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Undefined variable at token {i+3}: '{value}'")
                        detailed_phases["recovery"] = get_recovery_strategies("semantic_undefined_identifier", value)
                        break
                    actual_type = variable_types.get(value, expected_type)
                else:
                    results.append(f"Semantic Error [{i+3}]: Variable '{value}' not found")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Invalid value or undefined variable at token {i+3}: '{value}'")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_undefined_identifier", value)
                    break

            if actual_type != expected_type:
                results.append(f"Semantic Error [{i+3}]: Type mismatch - expected {expected_type}, got {actual_type or 'invalid'}")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Type mismatch at '{var_name}' - expected {expected_type}, got {actual_type}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_type_mismatch", f"expected {expected_type}, got {actual_type}")
                break

            # Type check second operand if operation exists
            if has_operation:
                actual_type2 = get_literal_type(value2)
                if actual_type2 is None:
                    if is_valid_identifier(value2):
                        if value2 not in variables:
                            results.append(f"Semantic Error [{i+5}]: Variable '{value2}' not found")
                            error_occurred = True
                            detailed_phases["semantic"].append(f"ERROR: Undefined variable at token {i+5}: '{value2}'")
                            detailed_phases["recovery"] = get_recovery_strategies("semantic_undefined_identifier", value2)
                            break
                        actual_type2 = variable_types.get(value2, expected_type)
                    else:
                        results.append(f"Semantic Error [{i+5}]: Variable '{value2}' not found")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Invalid value or undefined variable at token {i+5}: '{value2}'")
                        detailed_phases["recovery"] = get_recovery_strategies("semantic_undefined_identifier", value2)
                        break

                if actual_type2 != expected_type:
                    results.append(f"Semantic Error [{i+5}]: Type mismatch in operation - expected {expected_type}, got {actual_type2 or 'invalid'}")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Type mismatch in operation - expected {expected_type}, got {actual_type2}")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_type_mismatch", f"both operands must be {expected_type}")
                    break

            # Check if minus operation is used with word type (not allowed)
            if has_operation and operation == 'minus' and expected_type == 'word':
                results.append(f"Semantic Error [{i+4}]: Minus operation is not supported for word (string) type")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Minus operation cannot be used with word type at token {i+4}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_type_mismatch", "minus operation is only available for digit type, not word type")
                break

            # Binding variable to value 
            if expected_type == 'digit':
                # Get value from variable or literal
                if value in variables:
                    val1 = variables[value]
                else:
                    try:
                        val1 = int(value_stripped)
                    except:
                        val1 = float(value_stripped)

                if has_operation:
                    # Get second value from variable or literal
                    if value2 in variables:
                        val2 = variables[value2]
                    else:
                        try:
                            val2 = int(value2_stripped)
                        except:
                            val2 = float(value2_stripped)

                    if operation == 'adds':
                        variables[var_name] = val1 + val2
                    elif operation == 'minus':
                        variables[var_name] = val1 - val2
                else:
                    variables[var_name] = val1

            elif expected_type == 'word':
                # Get value from variable or literal
                if value in variables:
                    val1 = variables[value]
                else:
                    val1 = value_stripped

                if has_operation:
                    # Get second value from variable or literal
                    if value2 in variables:
                        val2 = variables[value2]
                    else:
                        val2 = value2_stripped

                    if operation == 'adds':
                        variables[var_name] = val1 + val2
                    elif operation == 'minus':
                        # Minus operation not supported for word type
                        results.append(f"Semantic Error [{i+4}]: Minus operation is not supported for word (string) type")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Minus operation cannot be used with word type at token {i+4}")
                        detailed_phases["recovery"] = get_recovery_strategies("semantic_type_mismatch", "minus operation is only available for digit type, not word type")
                        break
                else:
                    variables[var_name] = val1

            elif expected_type == 'bet':
                # Get value from variable or literal
                if value in variables:
                    val1 = variables[value]
                else:
                    val1 = value_stripped.lower() == 'real'
                variables[var_name] = val1

            # Store variable type for later reference
            variable_types[var_name] = expected_type

            # Compile output
            if has_operation:
                compiled_lines.append(f"{expected_type} {var_name} : {value} {operation} {value2} end")
            else:
                if expected_type == 'digit':
                    compiled_lines.append(f"digit {var_name} : {value} end")
                elif expected_type == 'word':
                    compiled_lines.append(f"word {var_name} : {value} end")
                elif expected_type == 'bet':
                    compiled_lines.append(f"bet {var_name} : {value} end")

            # Semantic detail output
            if has_operation:
                detailed_phases["semantic"].append(f"  Declaration: {expected_type} {var_name} : {value} {operation} {value2}")
                detailed_phases["semantic"].append(f"    Variable '{var_name}' bound to value '{variables[var_name]}' (type: {expected_type})")
            else:
                detailed_phases["semantic"].append(f"  Declaration: {expected_type} {var_name} : {value}")
                detailed_phases["semantic"].append(f"    Variable '{var_name}' bound to value '{value}' (type: {expected_type})")

            # Add to symbol table (formatted as table with scope and offset)
            scope_level = 0  # Global scope
            detailed_phases["symbol_table"].append(f"{var_name:<20} {expected_type:<15} {scope_level:<12} {memory_offset}")
            # Update memory offset for next variable
            memory_offset += offset_sizes.get(expected_type, 0)

            # Increment by 7 if operation, else 5
            i += 7 if has_operation else 5

        # Output Statement
        elif token == 'out':
            # Check for operation pattern: out VALUE OP VALUE end (5 tokens)
            # or simple pattern: out VALUE end (3 tokens)
            has_out_operation = False
            operation = None

            if i + 4 < len(tokens) and tokens[i+2] in ['adds', 'minus'] and tokens[i+4] == 'end':
                # 5-token pattern: out VALUE OP VALUE end
                has_out_operation = True
                operation = tokens[i+2]
            elif i + 2 >= len(tokens) or tokens[i+2] != 'end':
                results.append(f"Semantic Error [{i+1}]: Invalid output - expected out VALUE end or out VALUE OP VALUE end")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Invalid output statement at token {i+1}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "output format: out VALUE end")
                break

            output_value1 = tokens[i+1]

            # Handle output with operation
            if has_out_operation:
                output_value2 = tokens[i+3]
                compiled_lines.append(f"out {output_value1} {operation} {output_value2} end")

                # Get values for both operands
                val1 = None
                val2 = None
                is_digit_op = False

                # Get first value
                if output_value1 in variables:
                    val1 = variables[output_value1]
                else:
                    lit_type = get_literal_type(output_value1)
                    if lit_type == 'digit':
                        is_digit_op = True
                        try:
                            val1 = int(output_value1.strip('"\''))
                        except:
                            val1 = float(output_value1.strip('"\''))
                    elif lit_type == 'word':
                        val1 = output_value1.strip('"\'')
                    else:
                        results.append(f"Semantic Error [{i+1}]: Undefined identifier or invalid value '{output_value1}'")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Invalid output value '{output_value1}'")
                        break

                # Get second value
                if output_value2 in variables:
                    val2 = variables[output_value2]
                else:
                    lit_type = get_literal_type(output_value2)
                    if lit_type == 'digit':
                        is_digit_op = True
                        try:
                            val2 = int(output_value2.strip('"\''))
                        except:
                            val2 = float(output_value2.strip('"\''))
                    elif lit_type == 'word':
                        val2 = output_value2.strip('"\'')
                    else:
                        results.append(f"Semantic Error [{i+3}]: Undefined identifier or invalid value '{output_value2}'")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Invalid output value '{output_value2}'")
                        break

                # Perform operation and output
                if operation == 'adds':
                    result = val1 + val2
                elif operation == 'minus':
                    # Minus operation only supported for digit type
                    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                        # Both are numbers - do subtraction
                        result = val1 - val2
                    elif isinstance(val1, str) and isinstance(val2, str):
                        # String minus operation is not allowed
                        results.append(f"Semantic Error [{i+2}]: Minus operation is not supported for word (string) type")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Minus operation cannot be used with word type")
                        break
                    else:
                        # Type mismatch
                        results.append(f"Semantic Error [{i+1}]: Cannot use minus with mixed types")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Type mismatch in minus operation")
                        break

                output_results.append(f"> {result}")
                detailed_phases["semantic"].append(f"  Output: {output_value1} {operation} {output_value2} = {result}")
                i += 5
            else:
                # Simple output without operation
                compiled_lines.append(f"out {output_value1} end")

                # Variable output
                if output_value1 in variables:
                    output_val = variables[output_value1]
                    # Convert bet (boolean) values to Real/Fake
                    if isinstance(output_val, bool):
                        output_val = "Real" if output_val else "Fake"
                    output_results.append(f"> {output_val}")
                    detailed_phases["semantic"].append(f"  Output: Variable '{output_value1}' = {output_val}")
                # Literal output
                else:
                    lit_type = get_literal_type(output_value1)
                    if lit_type:
                        # Cache stripped value to avoid redundant .strip() calls
                        output_stripped = output_value1.strip('"\'')
                        if lit_type == 'digit':
                            try:
                                val = int(output_stripped)
                            except:
                                val = float(output_stripped)
                            output_results.append(f"> {val}")
                            detailed_phases["semantic"].append(f"  Output: Literal value '{val}' (type: {lit_type})")
                        elif lit_type == 'word':
                            output_results.append(f"> {output_stripped}")
                            detailed_phases["semantic"].append(f"  Output: Literal string '{output_stripped}'")
                        else:
                            output_results.append(f"> {output_value1}")
                            detailed_phases["semantic"].append(f"  Output: Literal value '{output_value1}'")
                    else:
                        results.append(f"Semantic Error [{i+1}]: Undefined identifier '{output_value1}'")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Undefined identifier '{output_value1}' at token {i+1}")
                        detailed_phases["recovery"] = get_recovery_strategies("semantic_undefined_identifier", output_value1)
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

    # Output Results (in correct order after compiled output)
    if output_results:
        results.extend(output_results)

    # Compiler Status
    if error_occurred:
        results.append("Status: SEMANTIC ANALYSIS FAILED")
        detailed_phases["semantic"].append("Result: [FAILED]")
    else:
        results.append("Status: COMPILATION SUCCESS")
        results.append("Program executed successfully!")
        detailed_phases["semantic"].append("Result: [PASSED]")

    # Pre-compute phase status to avoid per-frame string operations
    detailed_phases["phase_status"] = {
        "lexical": "PASSED" in " ".join(detailed_phases.get("lexical", [])),
        "syntax": "PASSED" in " ".join(detailed_phases.get("syntax", [])),
        "semantic": "PASSED" in " ".join(detailed_phases.get("semantic", []))
    }

    return results, detailed_phases

# ---- EXPLAINABILITY WINDOW ----
def show_explainability_window(detailed_phases):
    # Make explainability window proportional to main window size
    expl_width = max(int(WIDTH * 1.1), 1000)
    expl_height = max(int(HEIGHT * 1.1), 700)
    detail_window = pygame.display.set_mode((expl_width, expl_height), pygame.RESIZABLE)
    pygame.display.set_caption("ProgBlocks: Explainability Layer")
    detail_running = True
    scroll_offset = 0
    size_map = {'digit': 4, 'word': 1, 'bet': 2}  # Width of each datatype

    while detail_running:
        detail_window.fill(CONSOLE_COLOR)
        expl_width, expl_height = detail_window.get_size()

        # Calculate drawable area bounds for content
        content_min_y = 50
        content_max_y = expl_height - 40

        # Draw header
        header_text = font_header.render("COMPILER ANALYSIS PHASES", True, BLUE_TEXT)
        detail_window.blit(header_text, (20, 15))

        # Draw separator line below header
        pygame.draw.line(detail_window, BLUE_TEXT, (20, 50), (expl_width - 20, 50), 1)

        y_pos = 70  # Start lower with separator
        line_height = 18

        # Display each phase
        for phase_name, phase_color, phase_indent in [
            ("LEXICAL ANALYSIS", GREEN_TEXT if detailed_phases.get("phase_status", {}).get("lexical", False) else RED_TEXT, 0),
            ("SYNTAX ANALYSIS", GREEN_TEXT if detailed_phases.get("phase_status", {}).get("syntax", False) else RED_TEXT, 0),
            ("SEMANTIC ANALYSIS", GREEN_TEXT if detailed_phases.get("phase_status", {}).get("semantic", False) else RED_TEXT, 0)
        ]:
            phase_key = phase_name.lower().split()[0]

            # Phase header
            if y_pos - scroll_offset > content_min_y and y_pos - scroll_offset < content_max_y:
                phase_header = font_small.render(phase_name, True, phase_color)
                detail_window.blit(phase_header, (20 + phase_indent, y_pos - scroll_offset))
            y_pos += line_height + 5

            # Phase details - improved formatting
            phase_details = detailed_phases.get(phase_key, [])
            for detail_line in phase_details:
                if y_pos - scroll_offset > content_min_y and y_pos - scroll_offset < content_max_y:
                    # Skip empty lines or header lines that start with "PHASE:"
                    if detail_line.strip() and not detail_line.startswith("PHASE:"):
                        detail_text = font_console.render(detail_line, True, (200, 200, 200))
                        detail_window.blit(detail_text, (30 + phase_indent, y_pos - scroll_offset))
                    y_pos += line_height if detail_line.strip() else 0

            y_pos += 10

        # Display symbol table if there are variables
        if detailed_phases.get("symbol_table"):
            y_pos += 5
            if y_pos - scroll_offset > content_min_y and y_pos - scroll_offset < content_max_y:
                symbol_header = font_small.render("SYMBOL TABLE", True, BLUE_TEXT)
                detail_window.blit(symbol_header, (20, y_pos - scroll_offset))
            y_pos += line_height + 5

            # Display column headers
            if y_pos - scroll_offset > content_min_y and y_pos - scroll_offset < content_max_y:
                column_header = font_console.render(f"{'Name':<20} {'Type':<15} {'Scope':<10} {'Offset':<10}", True, (150, 150, 150))
                detail_window.blit(column_header, (30, y_pos - scroll_offset))
            y_pos += line_height

            # Display separator
            if y_pos - scroll_offset > content_min_y and y_pos - scroll_offset < content_max_y:
                separator = font_console.render("-" * 55, True, (100, 100, 100))
                detail_window.blit(separator, (30, y_pos - scroll_offset))
            y_pos += line_height

            # Display symbol table and calculate total byte used
            total_bytes = 0
            for symbol_line in detailed_phases.get("symbol_table", []):
                if y_pos - scroll_offset > content_min_y and y_pos - scroll_offset < content_max_y:
                    symbol_text = font_console.render(symbol_line, True, (200, 200, 200))
                    detail_window.blit(symbol_text, (30, y_pos - scroll_offset))

                # Calculate bytes for this variable
                parts = symbol_line.split()
                if len(parts) >= 2:
                    var_type = parts[1]
                    total_bytes += size_map.get(var_type, 0)

                y_pos += line_height

            # Display total bytes used
            y_pos += 5
            if y_pos - scroll_offset > content_min_y and y_pos - scroll_offset < content_max_y:
                total_text = font_console.render(f"Total Memory Used: {total_bytes} bytes", True, (100, 200, 255))
                detail_window.blit(total_text, (30, y_pos - scroll_offset))
            y_pos += line_height + 10

        # Display recovery strategies if there are errors
        if detailed_phases.get("recovery"):
            y_pos += 5
            if y_pos - scroll_offset > content_min_y and y_pos - scroll_offset < content_max_y:
                recovery_header = font_small.render("RECOVERY STRATEGIES", True, (255, 200, 0))
                detail_window.blit(recovery_header, (20, y_pos - scroll_offset))
            y_pos += line_height + 5

            for strategy_line in detailed_phases.get("recovery", []):
                if y_pos - scroll_offset > content_min_y and y_pos - scroll_offset < content_max_y:
                    strategy_text = font_console.render(strategy_line, True, (100, 200, 255))
                    detail_window.blit(strategy_text, (30, y_pos - scroll_offset))
                y_pos += line_height

        # Draw scroll instructions at the bottom with separator
        pygame.draw.line(detail_window, BLUE_TEXT, (20, expl_height - 40), (expl_width - 20, expl_height - 40), 1)
        scroll_text = font_small.render("Scroll: ScrollWheel | Close: ESC", True, BLUE_TEXT)
        detail_window.blit(scroll_text, (20, expl_height - 30))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                detail_running = False
            elif event.type == pygame.VIDEORESIZE:
                # Handle explainability window resize
                expl_width, expl_height = event.size[0], event.size[1]
                detail_window = pygame.display.set_mode((expl_width, expl_height), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:  # Scroll up
                    scroll_offset = max(0, scroll_offset - 30)
                elif event.y < 0:  # Scroll down
                    scroll_offset += 30
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    detail_running = False

        clock.tick(60)

    pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("ProgBlocks: Official Logic Edition")

# ---- HELPER FUNCTIONS FOR RESIZABLE WINDOW ----
def recalculate_ui_positions():
    """Recalculate all UI positions based on current window size"""
    global clear_rect, run_rect, info_rect, zoom_in_rect, zoom_out_rect
    global workspace_top, workspace_bottom, console_top, console_bottom
    global dynamic_console_height

    # Header area is fixed at 50px from top
    workspace_top = HEADER_HEIGHT
    console_top = HEIGHT - dynamic_console_height
    workspace_bottom = console_top
    console_bottom = HEIGHT

    # Constrain console_top to valid range based on console height bounds
    console_top = max(HEIGHT - MAX_CONSOLE_HEIGHT, console_top)
    console_top = min(HEIGHT - MIN_CONSOLE_HEIGHT, console_top)
    workspace_bottom = console_top

    # Buttons in header (right side, top padding of 12px)
    button_y = 12
    button_h = 35

    # Right-aligned buttons: INFO, CLEAR, RUN, ZOOM-, ZOOM+
    # Each button is 80px wide (except zoom buttons at 35px)
    run_rect = pygame.Rect(WIDTH - 90, button_y, 80, button_h)
    clear_rect = pygame.Rect(WIDTH - 180, button_y, 80, button_h)
    info_rect = pygame.Rect(WIDTH - 270, button_y, 80, button_h)
    zoom_in_rect = pygame.Rect(WIDTH - 360, button_y, 35, button_h)
    zoom_out_rect = pygame.Rect(WIDTH - 405, button_y, 35, button_h)


def get_block_view_rect(block):
    """Return the on-screen rect for a block with the current zoom/scroll."""
    return pygame.Rect(
        int(block.rect.x * zoom_scale),
        int(block.rect.y * zoom_scale - workspace_scroll_offset),
        int(block.rect.width * zoom_scale),
        int(block.rect.height * zoom_scale),
    )


def clamp_block_chain_to_workspace(block):
    """Keep a block chain inside the workspace without breaking links."""
    if block.prev_block is not None:
        return

    chain_blocks = []
    current = block
    min_x = current.rect.x
    min_y = current.rect.y
    max_right = current.rect.right
    max_bottom = current.rect.bottom

    while current:
        chain_blocks.append(current)
        min_x = min(min_x, current.rect.x)
        min_y = min(min_y, current.rect.y)
        max_right = max(max_right, current.rect.right)
        max_bottom = max(max_bottom, current.rect.bottom)
        current = current.next_block

    delta_x = 0
    delta_y = 0

    if min_x < WORKSPACE_LEFT:
        delta_x = WORKSPACE_LEFT - min_x
    elif max_right > WIDTH - WORKSPACE_RIGHT_MARGIN:
        delta_x = (WIDTH - WORKSPACE_RIGHT_MARGIN) - max_right

    if min_y < workspace_top:
        delta_y = workspace_top - min_y
    elif max_bottom > workspace_bottom:
        delta_y = workspace_bottom - max_bottom

    if delta_x or delta_y:
        block.update_position(block.rect.x + delta_x, block.rect.y + delta_y)


def clamp_all_blocks_to_workspace():
    """Re-clamp all placed block roots after a resize."""
    for block in placed_blocks:
        if block.prev_block is None:
            clamp_block_chain_to_workspace(block)


def is_mouse_on_separator(mouse_y):
    """Check if mouse Y position is near the separator (within SEPARATOR_HEIGHT/2)"""
    return abs(mouse_y - console_top) <= SEPARATOR_HEIGHT // 2


def get_cursor_for_position(mouse_y):
    """Return appropriate cursor style based on position"""
    if is_mouse_on_separator(mouse_y):
        return pygame.SYSTEM_CURSOR_SIZENS  # Vertical resize cursor
    return pygame.SYSTEM_CURSOR_ARROW

# ---- UI & MAIN LOOP ----
sidebar_blocks = [Block(t, c, cat, 15 + (i%2)*85, HEADER_HEIGHT + 10 + (i//2)*45, True) for i, (t, c, cat) in enumerate(AVAILABLE_BLOCKS)]
placed_blocks = []
dragging_block = None
editing_block = None
offset_x, offset_y = 0, 0
console_output = ["Blueprint ready!", "Drag blocks from the left to start building your program."]
detailed_phases = {}
workspace_scroll_offset = 0  # Vertical scroll offset for code workspace
console_scroll_offset = 0  # Vertical scroll offset for console output

# Draggable separator state
dragging_separator = False
separator_mouse_offset = 0
dynamic_console_height = CONSOLE_HEIGHT_FIXED  # Will change based on drag

# Initialize UI positions (call helper to calculate button positions)
recalculate_ui_positions()

running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BG_COLOR)

    # Draw header background
    pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, HEADER_HEIGHT))
    pygame.draw.line(screen, BLACK, (0, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT), 1)

    # Title and labels
    screen.blit(font_header.render("Blox", True, BLACK), (20, 12))
    screen.blit(font_header.render("Blueprint", True, BLACK), (WORKSPACE_LEFT + 10, 12))

    # Draw buttons with labels
    buttons_info = [
        (info_rect, "INFO", BLUE_TEXT),
        (clear_rect, "CLEAR", CLEAR_BTN_COLOR),
        (run_rect, "RUN", RUN_BTN_COLOR),
    ]
    for rect, label, color in buttons_info:
        pygame.draw.rect(screen, color, rect, border_radius=8)
        text = font_small.render(label, True, WHITE)
        screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))

    # Zoom buttons
    pygame.draw.rect(screen, BLUE_TEXT, zoom_out_rect, border_radius=8)
    minus_text = font_small.render("-", True, WHITE)
    screen.blit(minus_text, (zoom_out_rect.centerx - minus_text.get_width()//2, zoom_out_rect.centery - minus_text.get_height()//2))

    pygame.draw.rect(screen, BLUE_TEXT, zoom_in_rect, border_radius=8)
    plus_text = font_small.render("+", True, WHITE)
    screen.blit(plus_text, (zoom_in_rect.centerx - plus_text.get_width()//2, zoom_in_rect.centery - plus_text.get_height()//2))

    # Workspace area
    workspace_height = workspace_bottom - workspace_top
    pygame.draw.rect(screen, WORKSPACE_COLOR, (WORKSPACE_LEFT, workspace_top, WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN, workspace_height), border_radius=5)

    # Console area - draw BEFORE setting clip
    pygame.draw.rect(screen, CONSOLE_COLOR, (WORKSPACE_LEFT, console_top, WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN, dynamic_console_height))

    # Draw draggable separator (visual feedback)
    separator_color = (100, 150, 200) if dragging_separator else (80, 120, 180)
    pygame.draw.line(screen, separator_color,
                     (WORKSPACE_LEFT, console_top),
                     (WIDTH - WORKSPACE_RIGHT_MARGIN, console_top),
                     3)

    # Draw handle in the middle to show it's draggable
    handle_x = (WORKSPACE_LEFT + WIDTH - WORKSPACE_RIGHT_MARGIN) // 2
    pygame.draw.line(screen, separator_color,
                     (handle_x - 15, console_top - 2),
                     (handle_x - 15, console_top + 2),
                     2)
    pygame.draw.line(screen, separator_color,
                     (handle_x, console_top - 2),
                     (handle_x, console_top + 2),
                     2)
    pygame.draw.line(screen, separator_color,
                     (handle_x + 15, console_top - 2),
                     (handle_x + 15, console_top + 2),
                     2)

    # Keep placed blocks visually inside the blueprint area so they never draw
    # on top of the Blox sidebar when resizing or scrolling.
    workspace_clip = pygame.Rect(
        WORKSPACE_LEFT,
        workspace_top,
        WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN,
        workspace_height,
    )
    screen.set_clip(workspace_clip)

    # Draw placed blocks with scroll and zoom offset applied (BEFORE sidebar so sidebar appears on top)
    for b in placed_blocks:
        draw_rect = get_block_view_rect(b)
        if draw_rect.y + draw_rect.height <= workspace_bottom:
            original_rect = b.rect
            b.rect = draw_rect
            b.draw(screen)
            b.rect = original_rect

    # Reset clipping before drawing sidebar
    screen.set_clip(None)

    # Draw sidebar blocks (drawn AFTER placed blocks so they appear on top)
    for b in sidebar_blocks: b.draw(screen)

    # Draw console output with scroll support
    line_height = 17  # Height of each line
    console_start_y = console_top + 10  # Starting Y position in console
    console_max_y = console_bottom  # Maximum Y position

    # Set clipping rect for console area to prevent text overflow
    console_clip = pygame.Rect(WORKSPACE_LEFT, console_top, WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN, dynamic_console_height)
    screen.set_clip(console_clip)

    # Draw all lines with scroll offset
    for i, line in enumerate(console_output):
        # Calculate Y position with scroll offset
        y_pos = console_start_y + (i * line_height) - console_scroll_offset

        # Only draw if within console area
        if y_pos > console_top and y_pos < console_max_y:
            color = BLUE_TEXT if line.startswith(">") else (GREEN_TEXT if "PASSED" in line or "OK" in line or "SUCCESS" in line or "ready" in line else RED_TEXT)
            try:
                screen.blit(font_console.render(line, True, color), (WORKSPACE_LEFT + 10, y_pos))
            except:
                pass

    # Reset clipping
    screen.set_clip(None)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            # Handle window resize event
            WIDTH, HEIGHT = max(event.size[0], MINIMUM_WIDTH), max(event.size[1], MINIMUM_HEIGHT)
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            recalculate_ui_positions()
            clamp_all_blocks_to_workspace()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            # Check for separator drag FIRST (highest priority)
            if is_mouse_on_separator(mouse_y):
                dragging_separator = True
                separator_mouse_offset = mouse_y - console_top
                continue  # Skip to next event

            sidebar_hit = False
            for b in sidebar_blocks:
                if b.rect.collidepoint(mouse_x, mouse_y):
                    new_block = Block(
                        b.text,
                        b.color,
                        b.category,
                        int(mouse_x / zoom_scale),
                        int((mouse_y + workspace_scroll_offset) / zoom_scale),
                    )
                    new_block.dragging = True
                    dragging_block = new_block
                    offset_x = 0
                    offset_y = 0
                    placed_blocks.append(new_block)
                    sidebar_hit = True
                    break
            
            if not sidebar_hit:
                for b in reversed(placed_blocks):
                    view_rect = get_block_view_rect(b)
                    if view_rect.collidepoint(mouse_x, mouse_y):
                        if b.category == "Editable":
                            if editing_block and editing_block != b:
                                editing_block.is_editing = False
                            b.is_editing = True
                            editing_block = b
                            b.dragging = True
                            dragging_block = b
                            offset_x = mouse_x - view_rect.x
                            offset_y = mouse_y - view_rect.y
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
                        offset_x = mouse_x - view_rect.x
                        offset_y = mouse_y - view_rect.y
                        break

                if zoom_in_rect.collidepoint(mouse_x, mouse_y):
                    zoom_scale = min(ZOOM_MAX, zoom_scale + ZOOM_STEP)
                elif zoom_out_rect.collidepoint(mouse_x, mouse_y):
                    zoom_scale = max(ZOOM_MIN, zoom_scale - ZOOM_STEP)
                elif info_rect.collidepoint(mouse_x, mouse_y):
                    if detailed_phases:
                        show_explainability_window(detailed_phases)
                elif clear_rect.collidepoint(mouse_x, mouse_y):
                    placed_blocks.clear()
                    console_output = ["Workspace cleared."]
                    detailed_phases = {}
                    if editing_block:
                        editing_block.is_editing = False
                        editing_block = None
                elif run_rect.collidepoint(mouse_x, mouse_y):
                    console_output, detailed_phases = evaluate_compiler_logic(placed_blocks)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            # Finalize separator drag
            if dragging_separator:
                dragging_separator = False
                # Clamp all blocks to ensure they fit within new workspace bounds
                clamp_all_blocks_to_workspace()

            if dragging_block:
                dragging_block.dragging = False
                dragging_block.update_size()
                
                for other in placed_blocks:
                    if other != dragging_block and other.next_block is None:
                        # Only allow connections if parent block is within bounds
                        if other.rect.y >= workspace_top and other.rect.y < workspace_bottom:
                            # Check for VERTICAL connection (block below another)
                            if (abs(dragging_block.rect.top - other.rect.bottom) < 20 and
                                abs(dragging_block.rect.centerx - other.rect.centerx) < 20):
                                # Check if vertical connection would keep block in bounds
                                new_y = other.rect.bottom + 2
                                if new_y >= workspace_top and new_y + dragging_block.rect.height <= workspace_bottom:  # Stays within workspace
                                    # Connect vertically - block goes below
                                    other.next_block = dragging_block
                                    other.connection_direction = "vertical"
                                    dragging_block.prev_block = other
                                    dragging_block.update_position(other.rect.x, new_y)
                                    break
                            # Check for HORIZONTAL connection (block to the right of another)
                            elif (abs(dragging_block.rect.left - other.rect.right) < 20 and
                                  abs(dragging_block.rect.centery - other.rect.centery) < 20):
                                # Check if horizontal connection would keep block in bounds
                                new_x = other.rect.right + 2
                                new_y = other.rect.y
                                if (new_x >= WORKSPACE_LEFT and new_x + dragging_block.rect.width <= WIDTH - WORKSPACE_RIGHT_MARGIN and
                                    new_y >= workspace_top and new_y < workspace_bottom):  # Stays in bounds
                                    # Connect horizontally - block goes to the right
                                    other.next_block = dragging_block
                                    other.connection_direction = "horizontal"
                                    dragging_block.prev_block = other
                                    dragging_block.update_position(new_x, new_y)
                                    break
                
                if (dragging_block.rect.right < WORKSPACE_LEFT and dragging_block not in sidebar_blocks):
                    if dragging_block in placed_blocks:
                        placed_blocks.remove(dragging_block)

                # Remove blocks that go above workspace area
                if dragging_block in placed_blocks and dragging_block.rect.bottom < workspace_top:
                    # Disconnect this block and any blocks connected to it
                    if dragging_block.prev_block:
                        dragging_block.prev_block.next_block = None
                    if dragging_block.next_block:
                        # Chain removal for all connected blocks
                        curr = dragging_block.next_block
                        if dragging_block.prev_block:
                            dragging_block.prev_block.next_block = curr
                        if curr:
                            curr.prev_block = dragging_block.prev_block
                    dragging_block.prev_block = None
                    dragging_block.next_block = None
                    placed_blocks.remove(dragging_block)

                # Remove blocks that go to the right outside bounds
                if dragging_block in placed_blocks and dragging_block.rect.x > WIDTH - WORKSPACE_RIGHT_MARGIN:
                    # Disconnect this block and any blocks connected to it
                    if dragging_block.prev_block:
                        dragging_block.prev_block.next_block = None
                    if dragging_block.next_block:
                        curr = dragging_block.next_block
                        if dragging_block.prev_block:
                            dragging_block.prev_block.next_block = curr
                        if curr:
                            curr.prev_block = dragging_block.prev_block
                    dragging_block.prev_block = None
                    dragging_block.next_block = None
                    placed_blocks.remove(dragging_block)

                # Remove blocks that go below console area
                if dragging_block in placed_blocks and dragging_block.rect.y > workspace_bottom:
                    # Disconnect this block and any blocks connected to it
                    if dragging_block.prev_block:
                        dragging_block.prev_block.next_block = None
                    if dragging_block.next_block:
                        # Chain removal for all connected blocks below
                        curr = dragging_block.next_block
                        if dragging_block.prev_block:
                            dragging_block.prev_block.next_block = curr
                        if curr:
                            curr.prev_block = dragging_block.prev_block
                    dragging_block.prev_block = None
                    dragging_block.next_block = None
                    placed_blocks.remove(dragging_block)

                dragging_block = None

        elif event.type == pygame.MOUSEMOTION:
            if dragging_separator:
                new_console_top = event.pos[1] - separator_mouse_offset

                # Clamp console height to valid range
                new_console_top = max(HEIGHT - MAX_CONSOLE_HEIGHT, new_console_top)
                new_console_top = min(HEIGHT - MIN_CONSOLE_HEIGHT, new_console_top)

                # Update dynamic height
                new_height = HEIGHT - new_console_top
                if new_height != dynamic_console_height:
                    dynamic_console_height = new_height
                    # Recalculate UI positions with new console height
                    recalculate_ui_positions()

            if dragging_block:
                # If dragging an editable block that hasn't been disconnected yet, disconnect it now
                if dragging_block.category == "Editable" and dragging_block.prev_block is not None:
                    if dragging_block.prev_block:
                        dragging_block.prev_block.next_block = dragging_block.next_block
                    if dragging_block.next_block:
                        dragging_block.next_block.prev_block = dragging_block.prev_block
                    dragging_block.prev_block = None
                    dragging_block.next_block = None

                dragging_block.rect.x = int((event.pos[0] - offset_x) / zoom_scale)
                dragging_block.rect.y = int((event.pos[1] + workspace_scroll_offset - offset_y) / zoom_scale)

        elif event.type == pygame.MOUSEWHEEL:
            # Mouse wheel scrolling - Ctrl+Scroll for zoom, regular scroll for console
            mouse_x, mouse_y = pygame.mouse.get_pos()

            # Ctrl+Scroll for zoom in workspace
            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                if event.y > 0:  # Scroll up = zoom in
                    zoom_scale = min(ZOOM_MAX, zoom_scale + ZOOM_STEP)
                elif event.y < 0:  # Scroll down = zoom out
                    zoom_scale = max(ZOOM_MIN, zoom_scale - ZOOM_STEP)
            # Regular scroll in console area
            elif WORKSPACE_LEFT < mouse_x < WIDTH - WORKSPACE_RIGHT_MARGIN and console_top < mouse_y < console_bottom:
                if event.y > 0:  # Scroll up
                    console_scroll_offset = max(0, console_scroll_offset - 30)
                elif event.y < 0:  # Scroll down
                    max_console_scroll = max(0, (len(console_output) - 7) * 17)
                    console_scroll_offset = min(console_scroll_offset + 30, max_console_scroll)
        
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
            # Scroll workspace with arrow keys (works even when editing)
            if event.key == pygame.K_UP:
                workspace_scroll_offset = max(0, workspace_scroll_offset - 30)
            elif event.key == pygame.K_DOWN:
                # Calculate maximum scroll based on deepest block
                if placed_blocks:
                    deepest_block = max(placed_blocks, key=lambda b: b.rect.bottom)
                    max_scroll = max(0, deepest_block.rect.bottom - 500)
                else:
                    max_scroll = 0
                workspace_scroll_offset = min(workspace_scroll_offset + 30, max_scroll)
            # Scroll console with Page Up/Page Down keys
            elif event.key == pygame.K_PAGEUP:
                console_scroll_offset = max(0, console_scroll_offset - 50)
            elif event.key == pygame.K_PAGEDOWN:
                # Calculate maximum scroll based on number of lines
                max_console_scroll = max(0, (len(console_output) - 9) * 17)
                console_scroll_offset = min(console_scroll_offset + 50, max_console_scroll)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()