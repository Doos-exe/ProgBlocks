import pygame
import sys

import shared
from constants import *
from block import Block
from compiler import evaluate_compiler_logic, reorganize_nesting
from ui_helpers import (
    show_explainability_window, recalculate_ui_positions,
    get_block_view_rect, get_workspace_scroll_limits, clamp_workspace_scroll,
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


def can_enter_condition_slot(block):
    """Return whether a block is valid inside an if/while/for condition."""
    if block.text in CONDITION_OPERATORS:
        return True
    return (
        block.category == "Editable"
        and block.text not in KEYWORDS
        and block.text not in OPERATORS
        and block.text not in SEPARATORS
    )

console_output   = [
    "Blueprint ready!",
    "Drag palette blocks to create copies. Middle/right-drag or scroll to pan.",
]
detailed_phases  = {}
dragging_separator    = False
separator_mouse_offset= 0
panning               = False
panning_button        = None
pan_last_pos          = (0, 0)
drag_candidate        = None
drag_candidate_pos    = (0, 0)

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
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        shade = 80 if hovered else 110
        dark = (max(0, color[0] - shade), max(0, color[1] - shade), max(0, color[2] - shade))
        pygame.draw.rect(screen, dark,  rect, border_radius=4)
        pygame.draw.rect(screen, WHITE if hovered else color, rect, 1, border_radius=4)
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
    # Draw conditional outlines first so body/condition blocks remain legible
    # even when the user created them before placing the conditional block.
    for b in sorted(shared.placed_blocks, key=lambda item: item.category != "Conditional"):
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
            # The viewport changes; the persistent blueprint coordinates do
            # not. Only adjust the scroll position if the new viewport is
            # smaller than the current canvas bounds.
            clamp_workspace_scroll(shared.placed_blocks)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if event.button in (2, 3):
                if (WORKSPACE_LEFT < mx < shared.WIDTH - WORKSPACE_RIGHT_MARGIN and
                        shared.workspace_top < my < shared.workspace_bottom):
                    panning = True
                    panning_button = event.button
                    pan_last_pos = (mx, my)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEALL)
                continue

            if event.button != 1:
                continue

            # Clicking elsewhere commits the current edit. This prevents a
            # hidden caret state from surviving while the user rearranges the
            # blueprint or presses a toolbar button.
            if shared.editing_block:
                shared.editing_block.is_editing = False
                shared.editing_block.update_size()
                shared.editing_block = None
            drag_candidate = None

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
                        # Condition-slot blocks must be detachable before the
                        # editable-block branch handles their text input.
                        if b.in_condition_of is not None and b.category != "Editable":
                            parent = b.in_condition_of
                            if b in parent.condition_blocks:
                                parent.condition_blocks.remove(b)
                            b.in_condition_of = None
                            parent.update_size()
                            parent.update_position(parent.rect.x, parent.rect.y)

                        if b.category == "Editable":
                            b.is_editing = True
                            b.edit_original_text = b.text
                            shared.editing_block = b
                            # A click edits. Moving beyond the threshold in
                            # MOUSEMOTION turns the same interaction into a
                            # drag, preventing typing from moving the block.
                            drag_candidate = b
                            drag_candidate_pos = (mx, my)
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
                        screen = pygame.display.get_surface()
                    else:
                        console_output = [
                            "Run a program first to view compiler analysis."
                        ]
                elif shared.clear_rect.collidepoint(mx, my):
                    shared.placed_blocks.clear()
                    console_output = ["Workspace cleared."]
                    shared.console_scroll_offset = 0
                    shared.workspace_scroll_offset = 0
                    shared.workspace_scroll_offset_x = 0
                    detailed_phases = {}
                    if shared.editing_block:
                        shared.editing_block.is_editing = False
                        shared.editing_block = None
                elif shared.run_rect.collidepoint(mx, my):
                    console_output, detailed_phases = evaluate_compiler_logic(shared.placed_blocks)
                    shared.console_scroll_offset = 0

        elif event.type == pygame.MOUSEBUTTONUP:
            if panning and event.button == panning_button:
                panning = False
                panning_button = None
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            if dragging_separator:
                dragging_separator = False
                clamp_workspace_scroll(shared.placed_blocks)

            if event.button == 1 and shared.dragging_block:
                db = shared.dragging_block
                db.dragging = False
                db.update_size()
                # Apply the release position as well as the last motion
                # event; this makes edge-of-blueprint deletion deterministic.
                db.rect.x = int(
                    (event.pos[0] + shared.workspace_scroll_offset_x - shared.offset_x)
                    / shared.zoom_scale
                )
                db.rect.y = int(
                    (event.pos[1] + shared.workspace_scroll_offset - shared.offset_y)
                    / shared.zoom_scale
                )

                def _remove_db():
                    if db.in_condition_of is not None:
                        parent = db.in_condition_of
                        if db in parent.condition_blocks:
                            parent.condition_blocks.remove(db)
                        db.in_condition_of = None
                        parent.update_size()
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

                # Removal is based on the rendered rectangle, so it remains
                # correct while zooming or panning. A block must be fully
                # inside the blueprint when the mouse is released.
                workspace_rect = pygame.Rect(
                    WORKSPACE_LEFT,
                    shared.workspace_top,
                    shared.WIDTH - WORKSPACE_LEFT - WORKSPACE_RIGHT_MARGIN,
                    shared.workspace_bottom - shared.workspace_top,
                )
                db_view = get_block_view_rect(db)
                dropped_outside = not workspace_rect.contains(db_view)

                if not dropped_outside:
                    # Condition-slot snap. This is intentionally checked
                    # before ordinary connections because the slot is the
                    # only valid horizontal target for a conditional header.
                    snapped = False
                    if db.category != "Conditional" and can_enter_condition_slot(db):
                        for cond in shared.placed_blocks:
                            if cond.category != "Conditional" or cond == db:
                                continue
                            cv = get_block_view_rect(cond)
                            slot_x = cv.x + int(cond.keyword_part_width * shared.zoom_scale)
                            slot_rect = pygame.Rect(
                                slot_x, cv.y, max(0, cv.right - slot_x), cv.height
                            )
                            if slot_rect.collidepoint(db_view.centerx, db_view.centery):
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
                        # Collect both orientations first. Prefer the
                        # horizontal candidate when the user is placing a
                        # block to the right; the previous first-match loop
                        # could incorrectly choose a block's bottom edge.
                        horizontal = []
                        vertical = []
                        for other in shared.placed_blocks:
                            if other == db or other.next_block is not None:
                                continue
                            other_view = get_block_view_rect(other)
                            horizontal_gap = abs(db_view.left - other_view.right)
                            horizontal_alignment = abs(db_view.centery - other_view.centery)
                            vertical_gap = abs(db_view.top - other_view.bottom)
                            vertical_alignment = abs(db_view.centerx - other_view.centerx)
                            if horizontal_gap <= 18 and horizontal_alignment <= 18:
                                horizontal.append((horizontal_gap + horizontal_alignment, other))
                            if vertical_gap <= 18 and vertical_alignment <= 18:
                                vertical.append((vertical_gap + vertical_alignment, other))

                        target = None
                        direction = None
                        if horizontal:
                            _, target = min(horizontal, key=lambda item: item[0])
                            direction = "horizontal"
                        elif vertical:
                            _, target = min(vertical, key=lambda item: item[0])
                            direction = "vertical"

                        if target is not None:
                            if direction == "horizontal":
                                nx = target.rect.right + 2
                                ny = target.rect.y
                                if target.category == "Conditional" and can_enter_condition_slot(db):
                                    parent = target
                                elif target.in_condition_of is not None and can_enter_condition_slot(db):
                                    parent = target.in_condition_of
                                else:
                                    parent = None
                                if parent is not None:
                                    db.in_condition_of = parent
                                    if db not in parent.condition_blocks:
                                        parent.condition_blocks.append(db)
                                    if db in shared.placed_blocks:
                                        shared.placed_blocks.remove(db)
                                        shared.placed_blocks.append(db)
                                    parent.update_size()
                                    parent.update_position(parent.rect.x, parent.rect.y)
                                else:
                                    target.next_block = db
                                    target.connection_direction = "horizontal"
                                    db.prev_block = target
                                    db.update_position(nx, ny)
                            else:
                                ny = target.rect.bottom + 2
                                target.next_block = db
                                target.connection_direction = "vertical"
                                db.prev_block = target
                                db.update_position(target.rect.x, ny)

                if dropped_outside:
                    _remove_db()

                reorganize_nesting(shared.placed_blocks)
                shared.dragging_block = None
                drag_candidate = None
            elif event.button == 1 and drag_candidate is not None:
                # A click is an edit action. Only MOUSEMOTION beyond the
                # drag threshold turns it into a move, so releasing here must
                # leave the caret active for keyboard input.
                drag_candidate = None

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
                max_x, max_y = get_workspace_scroll_limits(shared.placed_blocks)
                shared.workspace_scroll_offset_x = min(
                    max_x, max(0, shared.workspace_scroll_offset_x - dx)
                )
                shared.workspace_scroll_offset = min(
                    max_y, max(0, shared.workspace_scroll_offset - dy)
                )

            if drag_candidate is not None and shared.dragging_block is None:
                dx = event.pos[0] - drag_candidate_pos[0]
                dy = event.pos[1] - drag_candidate_pos[1]
                if dx * dx + dy * dy >= 16:
                    db = drag_candidate
                    db.is_editing = False
                    if shared.editing_block is db:
                        shared.editing_block = None
                    vr = get_block_view_rect(db)
                    shared.offset_x = event.pos[0] - vr.x
                    shared.offset_y = event.pos[1] - vr.y
                    db.dragging = True
                    shared.dragging_block = db
                    drag_candidate = None

            if shared.dragging_block:
                db = shared.dragging_block
                if db.category == "Editable" and db.prev_block is not None:
                    if db.prev_block:
                        db.prev_block.next_block = db.next_block
                    if db.next_block:
                        db.next_block.prev_block = db.prev_block
                    db.prev_block = db.next_block = None
                elif db.category == "Editable" and db.in_condition_of is not None:
                    parent = db.in_condition_of
                    if db in parent.condition_blocks:
                        parent.condition_blocks.remove(db)
                    db.in_condition_of = None
                    parent.update_size()
                    parent.update_position(parent.rect.x, parent.rect.y)
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
            elif WORKSPACE_LEFT < mx < shared.WIDTH - WORKSPACE_RIGHT_MARGIN and \
                    shared.workspace_top < my < shared.workspace_bottom:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    shared.workspace_scroll_offset_x = max(
                        0, shared.workspace_scroll_offset_x - event.y * 30
                    )
                else:
                    _, max_workspace_scroll = get_workspace_scroll_limits(
                        shared.placed_blocks
                    )
                    if event.y > 0:
                        shared.workspace_scroll_offset = max(
                            0, shared.workspace_scroll_offset - 30
                        )
                    elif event.y < 0:
                        shared.workspace_scroll_offset = min(
                            max_workspace_scroll,
                            shared.workspace_scroll_offset + 30,
                        )

        elif event.type == pygame.KEYDOWN:
            if shared.editing_block:
                edited = shared.editing_block
                if event.key == pygame.K_BACKSPACE:
                    if edited.text:
                        edited.text = edited.text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    edited.text = edited.edit_original_text
                    edited.is_editing = False
                    shared.editing_block = None
                elif event.key == pygame.K_RETURN:
                    edited.is_editing = False
                    shared.editing_block = None
                else:
                    try:
                        if event.unicode and event.unicode.isprintable():
                            edited.text += event.unicode
                    except Exception:
                        pass

                edited.update_size()
                if edited.in_condition_of:
                    # Changing the text changes only the condition row. Do
                    # not reflow the conditional body, which can otherwise
                    # make existing body blocks jump downward while typing.
                    edited.in_condition_of.update_condition_layout()
                elif edited.next_block and edited.connection_direction == "horizontal":
                    edited.next_block.update_position(edited.rect.right + 2, edited.rect.y)

            if shared.editing_block is None and event.key == pygame.K_UP:
                shared.workspace_scroll_offset = max(0, shared.workspace_scroll_offset - 30)
            elif shared.editing_block is None and event.key == pygame.K_DOWN:
                max_s = max(
                    0,
                    int(max(
                        (b.content_bottom() for b in shared.placed_blocks),
                        default=shared.workspace_bottom,
                    ) * shared.zoom_scale - shared.workspace_bottom),
                )
                shared.workspace_scroll_offset = min(shared.workspace_scroll_offset + 30, max_s)
            elif shared.editing_block is None and event.key == pygame.K_PAGEUP:
                shared.console_scroll_offset = max(0, shared.console_scroll_offset - 50)
            elif shared.editing_block is None and event.key == pygame.K_PAGEDOWN:
                max_cs = max(0, (len(console_output) - 9) * 17)
                shared.console_scroll_offset = min(shared.console_scroll_offset + 50, max_cs)

    pygame.display.flip()
    shared.clock.tick(60)

pygame.quit()
sys.exit()
