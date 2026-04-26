# ---- Colors ----
BG_COLOR = (10, 12, 20)
WORKSPACE_COLOR = (14, 17, 30)
CONSOLE_COLOR = (8, 10, 16)
WHITE = (220, 225, 240)
BLACK = (0, 0, 0)
GREEN_TEXT = (0, 240, 120)
RED_TEXT = (255, 55, 75)
BLUE_TEXT = (0, 180, 255)
SIDEBAR_BG = (11, 13, 22)
HEADER_BG = (8, 10, 18)
ACCENT_COLOR = (0, 190, 255)
GRID_DOT_COLOR = (22, 28, 48)
ORANGE_BLOCK = (255, 90, 25)
BLUE_BLOCK = (0, 140, 255)
GRAY_BLOCK = (65, 80, 100)
PURPLE_BLOCK = (155, 35, 235)
CYAN_BLOCK = (0, 205, 225)
CLEAR_BTN_COLOR = (210, 35, 60)
RUN_BTN_COLOR = (0, 190, 85)

# ---- Screen ----
ORIGINAL_WIDTH, ORIGINAL_HEIGHT = 900, 650
MINIMUM_WIDTH, MINIMUM_HEIGHT = 600, 400

# ---- Layout ----
SIDEBAR_WIDTH = 170
WORKSPACE_LEFT = 200
WORKSPACE_BOTTOM = 460
CONSOLE_HEIGHT = 160
BUTTON_HEIGHT = 35
HEADER_HEIGHT = 50
CONSOLE_HEIGHT_FIXED = 120
WORKSPACE_RIGHT_MARGIN = 20
SEPARATOR_HEIGHT = 10
MIN_CONSOLE_HEIGHT = 60
MAX_CONSOLE_HEIGHT = int(ORIGINAL_HEIGHT * 0.75)

# ---- Zoom ----
ZOOM_MIN = 0.5
ZOOM_MAX = 2.0
ZOOM_STEP = 0.1

# ---- Language tokens ----
KEYWORDS = {
    'digit', 'word', 'bet', 'out', 'adds', 'minus', 'mul', 'div',
    'end', 'if', 'while', 'for', 'if_end', 'while_end', 'for_end'
}
OPERATORS = {':', ':=', 'adds', 'minus', 'mul', 'div'}
SEPARATORS = {'end'}

# ---- Block palette ----
AVAILABLE_BLOCKS = [
    ("digit",  ORANGE_BLOCK, "Keyword"),
    ("word",   ORANGE_BLOCK, "Keyword"),
    ("bet",    ORANGE_BLOCK, "Keyword"),
    (":",      BLUE_BLOCK,   "Operator"),
    (":=",     BLUE_BLOCK,   "Operator"),
    ("adds",   BLUE_BLOCK,   "Operator"),
    ("minus",  BLUE_BLOCK,   "Operator"),
    ("mul",    BLUE_BLOCK,   "Operator"),
    ("div",    BLUE_BLOCK,   "Operator"),
    ("end",    GRAY_BLOCK,   "Separator"),
    ("out",    GRAY_BLOCK,   "Keyword"),
    ("data",   PURPLE_BLOCK, "Editable"),
    ("if",     CYAN_BLOCK,   "Conditional"),
    ("while",  CYAN_BLOCK,   "Conditional"),
    ("for",    CYAN_BLOCK,   "Conditional"),
]
