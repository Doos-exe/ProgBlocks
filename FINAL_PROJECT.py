import pygame
import sys

import shared
from constants import *
from block import Block
from compiler import evaluate_compiler_logic, reorganize_nesting
from ui_helpers import (
    show_explainability_window, recalculate_ui_positions,
    get_block_view_rect, clamp_all_blocks_to_workspace,
    is_mouse_on_separator,
)

# ---- Initialize ----
pygame.init()

shared.font_small  = pygame.font.SysFont('Consolas', 14, bold=True)
shared.font_header = pygame.font.SysFont('Consolas', 18, bold=True)
shared.font_console= pygame.font.SysFont('Consolas', 13)
shared.font_label  = pygame.font.SysFont('Consolas', 10, bold=True)

screen = pygame.display.set_mode((shared.WIDTH, shared.HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("ProgBlocks: Block and Compile!")

sidebar_blocks = [
    Block(t, c, cat, 15 + (i % 2) * 85, HEADER_HEIGHT + 10 + (i // 2) * 45, True)
    for i, (t, c, cat) in enumerate(AVAILABLE_BLOCKS)
]

console_output   = ["Blueprint ready!", "Drag blocks from the left to start building your program."]
detailed_phases  = {}
dragging_separator    = False
separator_mouse_offset= 0
panning               = False
pan_last_pos          = (0, 0)

recalculate_ui_positions()

shared.clock = pygame.time.Clock()
running = True

# ---- Main Loop ----
while running:
    screen.fill(BG_COLOR)

    # Sidebar panel
    pygame.draw.rect(screen, SIDEBAR_BG, (0, 0, WORKSPACE_LEFT - 1, shared.HEIGHT))

    # Header
    pygame.draw.rect(screen, HEADER_BG, (0, 0, shared.WIDTH, HEADER_HEIGHT))
    pygame.draw.line(screen, (0, 50, 80),   (0, HEADER_HEIGHT), (shared.WIDTH, HEADER_HEIGHT), 4)
    pygame.draw.line(screen, ACCENT_COLOR,  (0, HEADER_HEIGHT - 1), (shared.WIDTH, HEADER_HEIGHT - 1), 2)
    pygame.draw.line(screen, ACCENT_COLOR,  (WORKSPACE_LEFT - 1, HEADER_HEIGHT),
                     (WORKSPACE_LEFT - 1, shared.HEIGHT), 1)

    # Title
    prog_surf   = shared.font_header.render("Prog",   True, WHITE)
    blocks_surf = shared.font_header.render("Blocks", True, ACCENT_COLOR)
    screen.blit(prog_surf,   (16, 15))
    screen.blit(blocks_surf, (16 + prog_surf.get_width(), 15))
    screen.blit(shared.font_header.render("Blueprint", True, (55, 70, 100)), (WORKSPACE_LEFT + 10, 15))
    screen.blit(shared.font_label.render("PALETTE", True, (45, 55, 80)), (10, HEADER_HEIGHT - 13))

    # Header buttons
    for rect, label, color in [
        (shared.info_rect,  "INFO",  BLUE_TEXT),
        (shared.clear_rect, "CLEAR", CLEAR_BTN_COLOR),
        (shared.run_rect,   "RUN",   RUN_BTN_COLOR),
    ]:
        dark = (max(0, color[0] - 110), max(0, color[1] - 110), max(0, color[2] - 110))
        pygame.draw.rect(screen, dark,  rect, border_radius=4)
        pygame.draw.rect(screen, color, rect, 1, border_radius=4)
        txt = shared.font_small.render(label, True, color)
        screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

    # Zoom buttons
    for zrect, label in [(shared.zoom_out_rect, "-"), (shared.zoom_in_rect, "+")]:
        pygame.draw.rect(screen, (10, 18, 30), zrect, border_radius=4)
        pygame.draw.rect(screen, ACCENT_COLOR, zrect, 1, border_radius=4)
        zt = shared.font_small.render(label, True, ACCENT_COLOR)
        screen.blit(zt, (zrect.centerx - zt.get_width()//2, zrect.centery - zt.get_height()//2))

    zoom_lbl = shared.font_label.render(f"{int(shared.zoom_scale * 100)}%", True, (70, 90, 120))
    screen.blit(zoom_lbl, (shared.zoom_in_rect.right + 6,
                            shared.zoom_in_rect.centery - zoom_lbl.get_height()//2))

    # Workspace
    ws_height = shared.workspace_bottom - shared.workspace_top
    pygame.draw.rect(screen, WORKSPACE_COLOR,
                     (WORKSPACE_LEFT, shared.workspace_top,
                      shared.WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN, ws_height))

    # Dot grid
    screen.set_clip(pygame.Rect(WORKSPACE_LEFT, shared.workspace_top,
                                shared.WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN, ws_height))
    dot_oy = int(shared.workspace_scroll_offset) % 20
    dot_ox = int(shared.workspace_scroll_offset_x) % 20
    for gx in range(WORKSPACE_LEFT + (20 - dot_ox) % 20, shared.WIDTH - WORKSPACE_RIGHT_MARGIN, 20):
        for gy in range(shared.workspace_top + (20 - dot_oy) % 20, shared.workspace_bottom, 20):
            pygame.draw.circle(screen, GRID_DOT_COLOR, (gx, gy), 1)
    screen.set_clip(None)

    # Console area
    pygame.draw.rect(screen, CONSOLE_COLOR,
                     (WORKSPACE_LEFT, shared.console_top,
                      shared.WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN,
                      shared.dynamic_console_height))
    pygame.draw.rect(screen, (12, 14, 24),
                     (WORKSPACE_LEFT, shared.console_top,
                      shared.WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN, 20))
    pygame.draw.line(screen, (25, 35, 55),
                     (WORKSPACE_LEFT, shared.console_top + 20),
                     (shared.WIDTH - WORKSPACE_RIGHT_MARGIN, shared.console_top + 20), 1)
    screen.blit(shared.font_label.render("OUTPUT", True, ACCENT_COLOR),
                (WORKSPACE_LEFT + 10, shared.console_top + 5))

    # Separator
    sep_color = (0, 220, 255) if dragging_separator else ACCENT_COLOR
    pygame.draw.line(screen, (0, 50, 80),
                     (WORKSPACE_LEFT, shared.console_top),
                     (shared.WIDTH - WORKSPACE_RIGHT_MARGIN, shared.console_top), 5)
    pygame.draw.line(screen, sep_color,
                     (WORKSPACE_LEFT, shared.console_top),
                     (shared.WIDTH - WORKSPACE_RIGHT_MARGIN, shared.console_top), 2)
    hx = (WORKSPACE_LEFT + shared.WIDTH - WORKSPACE_RIGHT_MARGIN) // 2
    for hxi in [hx - 15, hx, hx + 15]:
        pygame.draw.circle(screen, sep_color, (hxi, shared.console_top), 2)

    # Draw placed blocks (clipped to workspace)
    ws_clip = pygame.Rect(WORKSPACE_LEFT, shared.workspace_top,
                          shared.WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN, ws_height)
    screen.set_clip(ws_clip)
    for b in shared.placed_blocks:
        dr = get_block_view_rect(b)
        if dr.y + dr.height <= shared.workspace_bottom:
            orig = b.rect
            b.rect = dr
            b.draw(screen)
            b.rect = orig
    screen.set_clip(None)

    # Sidebar blocks on top
    for b in sidebar_blocks:
        b.draw(screen)

    # Console output
    line_h        = 17
    con_start_y   = shared.console_top + 24
    screen.set_clip(pygame.Rect(WORKSPACE_LEFT, shared.console_top,
                                shared.WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN,
                                shared.dynamic_console_height))
    for idx, line in enumerate(console_output):
        y_pos = con_start_y + idx * line_h - shared.console_scroll_offset
        if shared.console_top < y_pos < shared.console_bottom:
            if line.startswith(">"):
                col = ACCENT_COLOR
            elif any(k in line for k in ("PASSED", "OK", "SUCCESS", "ready", "Drag", "cleared")):
                col = GREEN_TEXT
            elif "Error" in line or "FAILED" in line:
                col = RED_TEXT
            elif "Compiled Output:" in line:
                col = BLUE_TEXT
            else:
                col = (155, 165, 185)
            try:
                screen.blit(shared.font_console.render(line, True, col),
                            (WORKSPACE_LEFT + 10, y_pos))
            except Exception:
                pass
    screen.set_clip(None)

    # ---- Events ----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            shared.WIDTH  = max(event.size[0], MINIMUM_WIDTH)
            shared.HEIGHT = max(event.size[1], MINIMUM_HEIGHT)
            screen = pygame.display.set_mode((shared.WIDTH, shared.HEIGHT), pygame.RESIZABLE)
            recalculate_ui_positions()
            clamp_all_blocks_to_workspace()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if is_mouse_on_separator(my):
                dragging_separator = True
                separator_mouse_offset = my - shared.console_top
                continue

            sidebar_hit = False
            for b in sidebar_blocks:
                if b.rect.collidepoint(mx, my):
                    nb = Block(b.text, b.color, b.category,
                               int((mx + shared.workspace_scroll_offset_x) / shared.zoom_scale),
                               int((my + shared.workspace_scroll_offset) / shared.zoom_scale))
                    nb.dragging = True
                    shared.dragging_block = nb
                    shared.offset_x = 0
                    shared.offset_y = 0
                    shared.placed_blocks.append(nb)
                    sidebar_hit = True
                    break

            if not sidebar_hit:
                for b in reversed(shared.placed_blocks):
                    vr = get_block_view_rect(b)
                    if vr.collidepoint(mx, my):
                        if b.category == "Editable":
                            if shared.editing_block and shared.editing_block != b:
                                shared.editing_block.is_editing = False
                            b.is_editing = True
                            shared.editing_block = b
                            b.dragging = True
                            shared.dragging_block = b
                            shared.offset_x = mx - vr.x
                            shared.offset_y = my - vr.y
                            break

                        if b.in_condition_of is not None:
                            parent = b.in_condition_of
                            if b in parent.condition_blocks:
                                parent.condition_blocks.remove(b)
                            b.in_condition_of = None
                            parent.update_size()
                            parent.update_position(parent.rect.x, parent.rect.y)
                            b.dragging = True
                            shared.dragging_block = b
                            shared.offset_x = mx - vr.x
                            shared.offset_y = my - vr.y
                            break

                        if b.prev_block:
                            b.prev_block.next_block = b.next_block
                        if b.next_block:
                            b.next_block.prev_block = b.prev_block
                        b.prev_block = None
                        b.next_block = None
                        b.dragging = True
                        shared.dragging_block = b
                        shared.offset_x = mx - vr.x
                        shared.offset_y = my - vr.y
                        break

                if shared.zoom_in_rect.collidepoint(mx, my):
                    shared.zoom_scale = min(ZOOM_MAX, shared.zoom_scale + ZOOM_STEP)
                elif shared.zoom_out_rect.collidepoint(mx, my):
                    shared.zoom_scale = max(ZOOM_MIN, shared.zoom_scale - ZOOM_STEP)
                elif shared.info_rect.collidepoint(mx, my):
                    if detailed_phases:
                        show_explainability_window(detailed_phases)
                elif shared.clear_rect.collidepoint(mx, my):
                    shared.placed_blocks.clear()
                    console_output = ["Workspace cleared."]
                    detailed_phases = {}
                    if shared.editing_block:
                        shared.editing_block.is_editing = False
                        shared.editing_block = None
                elif shared.run_rect.collidepoint(mx, my):
                    console_output, detailed_phases = evaluate_compiler_logic(shared.placed_blocks)

                if (shared.dragging_block is None and
                        mx > WORKSPACE_LEFT and
                        shared.workspace_top < my < shared.workspace_bottom):
                    panning = True
                    pan_last_pos = (mx, my)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEALL)

        elif event.type == pygame.MOUSEBUTTONUP:
            if panning:
                panning = False
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            if dragging_separator:
                dragging_separator = False
                clamp_all_blocks_to_workspace()

            if shared.dragging_block:
                db = shared.dragging_block
                db.dragging = False
                db.update_size()

                # Condition-slot snap
                snapped = False
                if db.category != "Conditional":
                    for cond in shared.placed_blocks:
                        if cond.category == "Conditional" and cond != db:
                            cv = get_block_view_rect(cond)
                            slot_x = cv.x + int(cond.keyword_part_width * shared.zoom_scale)
                            slot_rect = pygame.Rect(slot_x, cv.y, cv.right - slot_x, cv.height)
                            dv = get_block_view_rect(db)
                            if slot_rect.collidepoint(dv.centerx, dv.centery):
                                if db.prev_block:
                                    db.prev_block.next_block = db.next_block
                                if db.next_block:
                                    db.next_block.prev_block = db.prev_block
                                db.prev_block = db.next_block = None
                                db.in_condition_of = cond
                                if db not in cond.condition_blocks:
                                    cond.condition_blocks.append(db)
                                if db in shared.placed_blocks:
                                    shared.placed_blocks.remove(db)
                                    shared.placed_blocks.append(db)
                                cond.update_size()
                                cond.update_position(cond.rect.x, cond.rect.y)
                                snapped = True
                                break

                if not snapped:
                    for other in shared.placed_blocks:
                        if other != db and other.next_block is None:
                            if other.rect.y >= shared.workspace_top and other.rect.y < shared.workspace_bottom:
                                # Vertical connection
                                if (abs(db.rect.top - other.rect.bottom) < 20 and
                                        abs(db.rect.centerx - other.rect.centerx) < 20):
                                    ny = other.rect.bottom + 2
                                    if shared.workspace_top <= ny and ny + db.rect.height <= shared.workspace_bottom:
                                        other.next_block = db
                                        other.connection_direction = "vertical"
                                        db.prev_block = other
                                        db.update_position(other.rect.x, ny)
                                        break
                                # Horizontal connection
                                elif (abs(db.rect.left - other.rect.right) < 20 and
                                      abs(db.rect.centery - other.rect.centery) < 20):
                                    nx = other.rect.right + 2
                                    ny = other.rect.y
                                    if (nx >= WORKSPACE_LEFT and
                                            nx + db.rect.width <= shared.WIDTH - WORKSPACE_RIGHT_MARGIN and
                                            shared.workspace_top <= ny < shared.workspace_bottom):
                                        if other.category == "Conditional":
                                            cp = other
                                        elif other.in_condition_of is not None:
                                            cp = other.in_condition_of
                                        else:
                                            cp = None
                                        if cp is not None:
                                            db.in_condition_of = cp
                                            if db not in cp.condition_blocks:
                                                cp.condition_blocks.append(db)
                                            if db in shared.placed_blocks:
                                                shared.placed_blocks.remove(db)
                                                shared.placed_blocks.append(db)
                                            cp.update_size()
                                            cp.update_position(cp.rect.x, cp.rect.y)
                                        else:
                                            other.next_block = db
                                            other.connection_direction = "horizontal"
                                            db.prev_block = other
                                            db.update_position(nx, ny)
                                        break

                def _remove_db():
                    if db.category == "Conditional":
                        for cb in db.condition_blocks:
                            cb.in_condition_of = None
                            if cb in shared.placed_blocks:
                                shared.placed_blocks.remove(cb)
                        db.condition_blocks.clear()
                    if db.prev_block:
                        db.prev_block.next_block = db.next_block
                    if db.next_block:
                        db.next_block.prev_block = db.prev_block
                    db.prev_block = db.next_block = None
                    if db in shared.placed_blocks:
                        shared.placed_blocks.remove(db)

                if db.rect.right < WORKSPACE_LEFT and db not in sidebar_blocks:
                    _remove_db()
                if db in shared.placed_blocks and db.rect.bottom < shared.workspace_top:
                    _remove_db()
                if db in shared.placed_blocks and db.rect.x > shared.WIDTH - WORKSPACE_RIGHT_MARGIN:
                    _remove_db()
                if db in shared.placed_blocks and db.rect.y > shared.workspace_bottom:
                    _remove_db()

                reorganize_nesting(shared.placed_blocks)
                shared.dragging_block = None

        elif event.type == pygame.MOUSEMOTION:
            if dragging_separator:
                new_top = event.pos[1] - separator_mouse_offset
                new_top = max(shared.HEIGHT - MAX_CONSOLE_HEIGHT, new_top)
                new_top = min(shared.HEIGHT - MIN_CONSOLE_HEIGHT, new_top)
                new_h = shared.HEIGHT - new_top
                if new_h != shared.dynamic_console_height:
                    shared.dynamic_console_height = new_h
                    recalculate_ui_positions()

            if panning:
                dx = event.pos[0] - pan_last_pos[0]
                dy = event.pos[1] - pan_last_pos[1]
                pan_last_pos = event.pos
                shared.workspace_scroll_offset_x = max(0, shared.workspace_scroll_offset_x - dx)
                shared.workspace_scroll_offset    = max(0, shared.workspace_scroll_offset    - dy)

            if shared.dragging_block:
                db = shared.dragging_block
                if db.category == "Editable" and db.prev_block is not None:
                    if db.prev_block:
                        db.prev_block.next_block = db.next_block
                    if db.next_block:
                        db.next_block.prev_block = db.prev_block
                    db.prev_block = db.next_block = None
                db.rect.x = int((event.pos[0] + shared.workspace_scroll_offset_x - shared.offset_x) / shared.zoom_scale)
                db.rect.y = int((event.pos[1] + shared.workspace_scroll_offset    - shared.offset_y) / shared.zoom_scale)

        elif event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                if event.y > 0:
                    shared.zoom_scale = min(ZOOM_MAX, shared.zoom_scale + ZOOM_STEP)
                elif event.y < 0:
                    shared.zoom_scale = max(ZOOM_MIN, shared.zoom_scale - ZOOM_STEP)
            elif (WORKSPACE_LEFT < mx < shared.WIDTH - WORKSPACE_RIGHT_MARGIN and
                  shared.console_top < my < shared.console_bottom):
                if event.y > 0:
                    shared.console_scroll_offset = max(0, shared.console_scroll_offset - 30)
                elif event.y < 0:
                    max_cs = max(0, (len(console_output) - 7) * 17)
                    shared.console_scroll_offset = min(shared.console_scroll_offset + 30, max_cs)

        elif event.type == pygame.KEYDOWN:
            if shared.editing_block:
                if event.key == pygame.K_BACKSPACE:
                    if shared.editing_block.text:
                        shared.editing_block.text = shared.editing_block.text[:-1]
                    shared.editing_block.update_size()
                elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    shared.editing_block.is_editing = False
                    shared.editing_block.update_size()
                    shared.editing_block = None
                else:
                    try:
                        shared.editing_block.text += event.unicode
                        shared.editing_block.update_size()
                    except Exception:
                        pass

            if event.key == pygame.K_UP:
                shared.workspace_scroll_offset = max(0, shared.workspace_scroll_offset - 30)
            elif event.key == pygame.K_DOWN:
                max_s = max(0, max((b.rect.bottom for b in shared.placed_blocks), default=0) - 500)
                shared.workspace_scroll_offset = min(shared.workspace_scroll_offset + 30, max_s)
            elif event.key == pygame.K_PAGEUP:
                shared.console_scroll_offset = max(0, shared.console_scroll_offset - 50)
            elif event.key == pygame.K_PAGEDOWN:
                max_cs = max(0, (len(console_output) - 9) * 17)
                shared.console_scroll_offset = min(shared.console_scroll_offset + 50, max_cs)

    pygame.display.flip()
    shared.clock.tick(60)

pygame.quit()
sys.exit()
