"""
Mutable global state shared across all modules.
All modules import this module and access state via shared.<name>.
The main file sets fonts and clock after pygame.init().
"""
import pygame
from constants import ORIGINAL_WIDTH, ORIGINAL_HEIGHT, CONSOLE_HEIGHT_FIXED, HEADER_HEIGHT

# ---- Window dimensions ----
WIDTH = ORIGINAL_WIDTH
HEIGHT = ORIGINAL_HEIGHT

# ---- Layout boundaries (recalculated on resize / separator drag) ----
workspace_top = HEADER_HEIGHT
workspace_bottom = HEIGHT - CONSOLE_HEIGHT_FIXED
console_top = HEIGHT - CONSOLE_HEIGHT_FIXED
console_bottom = HEIGHT
dynamic_console_height = CONSOLE_HEIGHT_FIXED

# ---- Zoom & scroll ----
zoom_scale = 1.0
workspace_scroll_offset = 0
console_scroll_offset = 0

# ---- Fonts (None until set by main after pygame.init()) ----
font_small = None
font_header = None
font_console = None
font_label = None

# ---- pygame clock (set by main) ----
clock = None

# ---- UI button rects (recalculated by recalculate_ui_positions) ----
clear_rect   = pygame.Rect(0, 0, 80, 35)
run_rect     = pygame.Rect(0, 0, 80, 35)
info_rect    = pygame.Rect(0, 0, 80, 35)
zoom_in_rect = pygame.Rect(0, 0, 35, 35)
zoom_out_rect= pygame.Rect(0, 0, 35, 35)

# ---- Block state ----
placed_blocks = []
dragging_block = None
editing_block = None
offset_x = 0
offset_y = 0
