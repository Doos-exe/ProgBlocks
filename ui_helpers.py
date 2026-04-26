import pygame
import shared
from constants import (
    HEADER_HEIGHT, CONSOLE_HEIGHT_FIXED, WORKSPACE_LEFT, WORKSPACE_RIGHT_MARGIN,
    SEPARATOR_HEIGHT, MIN_CONSOLE_HEIGHT, MAX_CONSOLE_HEIGHT,
    CONSOLE_COLOR, HEADER_BG, ACCENT_COLOR, GREEN_TEXT, RED_TEXT, BLUE_TEXT, WHITE,
)


def recalculate_ui_positions():
    shared.workspace_top    = HEADER_HEIGHT
    shared.console_top      = shared.HEIGHT - shared.dynamic_console_height
    shared.workspace_bottom = shared.console_top
    shared.console_bottom   = shared.HEIGHT

    shared.console_top = max(shared.HEIGHT - MAX_CONSOLE_HEIGHT, shared.console_top)
    shared.console_top = min(shared.HEIGHT - MIN_CONSOLE_HEIGHT, shared.console_top)
    shared.workspace_bottom = shared.console_top

    button_y = 12
    button_h = 35
    shared.run_rect      = pygame.Rect(shared.WIDTH - 90,  button_y, 80, button_h)
    shared.clear_rect    = pygame.Rect(shared.WIDTH - 180, button_y, 80, button_h)
    shared.info_rect     = pygame.Rect(shared.WIDTH - 270, button_y, 80, button_h)
    shared.zoom_in_rect  = pygame.Rect(shared.WIDTH - 360, button_y, 35, button_h)
    shared.zoom_out_rect = pygame.Rect(shared.WIDTH - 405, button_y, 35, button_h)


def get_block_view_rect(block):
    return pygame.Rect(
        int(block.rect.x * shared.zoom_scale),
        int(block.rect.y * shared.zoom_scale - shared.workspace_scroll_offset),
        int(block.rect.width  * shared.zoom_scale),
        int(block.rect.height * shared.zoom_scale),
    )


def clamp_block_chain_to_workspace(block):
    if block.prev_block is not None:
        return
    chain = []
    cur = block
    min_x, min_y = cur.rect.x, cur.rect.y
    max_right, max_bottom = cur.rect.right, cur.rect.bottom
    while cur:
        chain.append(cur)
        min_x      = min(min_x,      cur.rect.x)
        min_y      = min(min_y,      cur.rect.y)
        max_right  = max(max_right,  cur.rect.right)
        max_bottom = max(max_bottom, cur.rect.bottom)
        cur = cur.next_block

    dx = dy = 0
    if min_x < WORKSPACE_LEFT:
        dx = WORKSPACE_LEFT - min_x
    elif max_right > shared.WIDTH - WORKSPACE_RIGHT_MARGIN:
        dx = (shared.WIDTH - WORKSPACE_RIGHT_MARGIN) - max_right
    if min_y < shared.workspace_top:
        dy = shared.workspace_top - min_y
    elif max_bottom > shared.workspace_bottom:
        dy = shared.workspace_bottom - max_bottom

    if dx or dy:
        block.update_position(block.rect.x + dx, block.rect.y + dy)


def clamp_all_blocks_to_workspace():
    for block in shared.placed_blocks:
        if block.prev_block is None:
            clamp_block_chain_to_workspace(block)


def is_mouse_on_separator(mouse_y):
    return abs(mouse_y - shared.console_top) <= SEPARATOR_HEIGHT // 2


def get_cursor_for_position(mouse_y):
    if is_mouse_on_separator(mouse_y):
        return pygame.SYSTEM_CURSOR_SIZENS
    return pygame.SYSTEM_CURSOR_ARROW


def show_explainability_window(detailed_phases):
    expl_w = max(int(shared.WIDTH  * 1.1), 1000)
    expl_h = max(int(shared.HEIGHT * 1.1), 700)
    win = pygame.display.set_mode((expl_w, expl_h), pygame.RESIZABLE)
    pygame.display.set_caption("ProgBlocks: Explainability Layer")
    running = True
    scroll_offset = 0
    size_map = {'digit': 4, 'word': 1, 'bet': 2}
    LINE_H = 18

    while running:
        win.fill(CONSOLE_COLOR)
        expl_w, expl_h = win.get_size()
        content_min_y = 50
        content_max_y = expl_h - 40

        # Header
        pygame.draw.rect(win, HEADER_BG, (0, 0, expl_w, 55))
        win.blit(shared.font_header.render("COMPILER ANALYSIS PHASES", True, ACCENT_COLOR), (20, 15))
        pygame.draw.line(win, (0, 50, 80),   (0, 53), (expl_w, 53), 4)
        pygame.draw.line(win, ACCENT_COLOR,  (0, 54), (expl_w, 54), 2)

        y = 70
        phase_status = detailed_phases.get("phase_status", {})
        for phase_name, phase_key in [
            ("LEXICAL ANALYSIS",   "lexical"),
            ("SYNTAX ANALYSIS",    "syntax"),
            ("SEMANTIC ANALYSIS",  "semantic"),
        ]:
            color = GREEN_TEXT if phase_status.get(phase_key, False) else RED_TEXT
            if content_min_y < y - scroll_offset < content_max_y:
                win.blit(shared.font_small.render(phase_name, True, color), (20, y - scroll_offset))
            y += LINE_H + 5

            for line in detailed_phases.get(phase_key, []):
                if content_min_y < y - scroll_offset < content_max_y:
                    if line.strip() and not line.startswith("PHASE:"):
                        win.blit(shared.font_console.render(line, True, (200, 200, 200)),
                                 (30, y - scroll_offset))
                    y += LINE_H if line.strip() else 0
            y += 10

        # Symbol table
        if detailed_phases.get("symbol_table"):
            y += 5
            if content_min_y < y - scroll_offset < content_max_y:
                win.blit(shared.font_small.render("SYMBOL TABLE", True, BLUE_TEXT), (20, y - scroll_offset))
            y += LINE_H + 5
            if content_min_y < y - scroll_offset < content_max_y:
                win.blit(shared.font_console.render(
                    f"{'Name':<20} {'Type':<15} {'Scope':<10} {'Offset':<10}",
                    True, (150, 150, 150)), (30, y - scroll_offset))
            y += LINE_H
            if content_min_y < y - scroll_offset < content_max_y:
                win.blit(shared.font_console.render("-" * 55, True, (100, 100, 100)),
                         (30, y - scroll_offset))
            y += LINE_H

            total_bytes = 0
            for sym in detailed_phases["symbol_table"]:
                if content_min_y < y - scroll_offset < content_max_y:
                    win.blit(shared.font_console.render(sym, True, (200, 200, 200)),
                             (30, y - scroll_offset))
                parts = sym.split()
                if len(parts) >= 2:
                    total_bytes += size_map.get(parts[1], 0)
                y += LINE_H

            y += 5
            if content_min_y < y - scroll_offset < content_max_y:
                win.blit(shared.font_console.render(
                    f"Total Memory Used: {total_bytes} bytes", True, (100, 200, 255)),
                    (30, y - scroll_offset))
            y += LINE_H + 10

        # Recovery strategies
        if detailed_phases.get("recovery"):
            y += 5
            if content_min_y < y - scroll_offset < content_max_y:
                win.blit(shared.font_small.render("RECOVERY STRATEGIES", True, (255, 200, 0)),
                         (20, y - scroll_offset))
            y += LINE_H + 5
            for line in detailed_phases["recovery"]:
                if content_min_y < y - scroll_offset < content_max_y:
                    win.blit(shared.font_console.render(line, True, (100, 200, 255)),
                             (30, y - scroll_offset))
                y += LINE_H

        # Footer
        pygame.draw.line(win, (0, 50, 80),  (0, expl_h - 43), (expl_w, expl_h - 43), 4)
        pygame.draw.line(win, ACCENT_COLOR, (0, expl_h - 41), (expl_w, expl_h - 41), 2)
        win.blit(shared.font_small.render(
            "  Scroll: ScrollWheel  |  Close: ESC", True, (70, 90, 120)),
            (20, expl_h - 30))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                expl_w, expl_h = event.size
                win = pygame.display.set_mode((expl_w, expl_h), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEWHEEL:
                scroll_offset = max(0, scroll_offset - 30) if event.y > 0 else scroll_offset + 30
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        shared.clock.tick(60)

    pygame.display.set_mode((shared.WIDTH, shared.HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("ProgBlocks: Block and Compile!")
