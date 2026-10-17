import pygame
import shared
from constants import WHITE, ACCENT_COLOR


class Block:
    def __init__(self, text, color, category, x, y, is_template=False):
        self.text = text
        self.color = color
        self.category = category
        self.is_template = is_template
        self.is_editing = False
        self.edit_original_text = text
        self.keyword_part_width = 55
        self.condition_blocks = []
        self.in_condition_of = None
        self.next_block = None
        self.prev_block = None
        self.connection_direction = "vertical"
        self.text_surf = None
        self.rect = None
        self.body_blocks = []
        self.parent_conditional = None
        self.c_depth = 0
        self.update_size()
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.dragging = False

    def update_size(self):
        try:
            if self.category == "Conditional":
                kw_surf = shared.font_small.render(self.text, True, WHITE)
                self.keyword_part_width = max(55, kw_surf.get_width() + 20)
                if self.is_template:
                    self.width = self.keyword_part_width
                elif self.condition_blocks:
                    cond_w = sum(cb.width + 2 for cb in self.condition_blocks) + 10
                    self.width = self.keyword_part_width + max(10, cond_w)
                else:
                    self.width = self.keyword_part_width + 120
                self.height = 35
                self.text_surf = kw_surf
            else:
                text_display = self.text + ("|" if self.is_editing else "")
                text_surf = shared.font_small.render(text_display, True, WHITE)
                self.width = max(80, text_surf.get_width() + 20)
                self.height = 35
                self.text_surf = text_surf
        except Exception:
            self.width = 80
            self.height = 35
            self.text_surf = None
        if self.rect:
            self.rect.width = self.width
            self.rect.height = self.height

    def content_bottom(self):
        """Return the bottom of this block including nested body blocks."""
        bottom = self.rect.bottom
        for body_block in self.body_blocks:
            bottom = max(bottom, body_block.content_bottom())
        if self.next_block:
            bottom = max(bottom, self.next_block.content_bottom())
        return bottom

    def draw(self, surface):
        r, g, b = self.color
        dark_body = (max(0, r - 85), max(0, g - 85), max(0, b - 85))
        highlight  = (min(255, r + 50), min(255, g + 50), min(255, b + 50))

        if self.category == "Conditional":
            kww = int(self.keyword_part_width * shared.zoom_scale)
            cond_dark = (max(0, r - 110), max(0, g - 110), max(0, b - 110))
            kw_rect = pygame.Rect(self.rect.x, self.rect.y, kww, self.rect.height)

            if not self.is_template:
                lw = 3
                if self.body_blocks:
                    # During rendering self.rect is temporarily replaced with
                    # a zoomed view rect, while child blocks retain logical
                    # coordinates. Convert the child's absolute logical
                    # bottom directly to view coordinates so the C-shape is
                    # always drawn below the entire body.
                    body_bottom = max(
                        body_block.content_bottom()
                        for body_block in self.body_blocks
                    )
                    body_bottom_view = int(
                        body_bottom * shared.zoom_scale
                        - shared.workspace_scroll_offset
                        + 15 * shared.zoom_scale
                    )
                    total_h = max(self.rect.height, body_bottom_view - self.rect.y)
                else:
                    total_h = self.rect.height + int(80 * shared.zoom_scale)
                pygame.draw.line(surface, self.color,
                                 (self.rect.x, self.rect.y),
                                 (self.rect.x, self.rect.y + total_h), lw)
                pygame.draw.line(surface, self.color,
                                 (self.rect.x, self.rect.y + total_h),
                                 (self.rect.x + self.rect.width, self.rect.y + total_h), lw)
                if not self.body_blocks:
                    hint = shared.font_small.render("drop body below", True, (50, 75, 100))
                    surface.blit(hint, hint.get_rect(
                        midleft=(self.rect.x + int(20 * shared.zoom_scale),
                                 self.rect.y + self.rect.height + int(26 * shared.zoom_scale))))

            pygame.draw.rect(surface, dark_body, kw_rect, border_radius=4)
            pygame.draw.rect(surface, self.color, kw_rect, 1, border_radius=4)
            pygame.draw.rect(surface, self.color,
                             pygame.Rect(self.rect.x, self.rect.y, 3, self.rect.height))
            pygame.draw.line(surface, highlight,
                             (self.rect.x + 4, self.rect.y + 1),
                             (self.rect.x + kww - 1, self.rect.y + 1), 1)
            kw_surf = self.text_surf or shared.font_small.render(self.text, True, WHITE)
            surface.blit(kw_surf, kw_surf.get_rect(center=kw_rect.center))

            if not self.is_template:
                cond_x = self.rect.x + kww
                cond_rect = pygame.Rect(cond_x, self.rect.y,
                                        self.rect.width - kww, self.rect.height)
                pygame.draw.rect(surface, cond_dark, cond_rect, border_radius=4)
                bc = self.color if self.condition_blocks else (40, 65, 80)
                pygame.draw.line(surface, bc,
                                 (cond_rect.left, cond_rect.top),
                                 (cond_rect.left, cond_rect.bottom - 1), 1)
                pygame.draw.line(surface, bc,
                                 (cond_rect.left, cond_rect.top),
                                 (cond_rect.right, cond_rect.top), 1)
                pygame.draw.line(surface, bc,
                                 (cond_rect.left, cond_rect.bottom - 1),
                                 (cond_rect.right, cond_rect.bottom - 1), 1)
                if not self.condition_blocks:
                    hint = shared.font_small.render("drop value/op", True, (50, 75, 100))
                    surface.blit(hint, hint.get_rect(
                        midleft=(cond_rect.left + 8, cond_rect.centery)))
        else:
            pygame.draw.rect(surface, dark_body, self.rect, border_radius=4)
            pygame.draw.rect(surface, self.color, self.rect, 1, border_radius=4)
            pygame.draw.rect(surface, self.color,
                             pygame.Rect(self.rect.x, self.rect.y, 3, self.rect.height))
            pygame.draw.line(surface, highlight,
                             (self.rect.x + 4, self.rect.y + 1),
                             (self.rect.right - 1, self.rect.y + 1), 1)
            if self.is_editing:
                pygame.draw.rect(surface, ACCENT_COLOR, self.rect, 2, border_radius=4)
            self._draw_text(surface, self.rect)

    def _draw_text(self, surface, rect):
        try:
            if self.text_surf:
                surface.blit(self.text_surf, self.text_surf.get_rect(center=rect.center))
            else:
                text_display = self.text + ("|" if self.is_editing else "")
                ts = shared.font_small.render(text_display, True, WHITE)
                surface.blit(ts, ts.get_rect(center=rect.center))
        except Exception:
            pass

    def update_position(self, x, y):
        self.rect.x = x
        self.rect.y = y
        if self.condition_blocks:
            cx = self.rect.x + self.keyword_part_width + 5
            for cb in self.condition_blocks:
                cb.rect.x = cx
                cb.rect.y = self.rect.y
                cx += cb.width + 2
        if self.body_blocks:
            body_y = self.rect.y + self.rect.height + 5
            body_x = self.rect.x + 20
            for body_block in self.body_blocks:
                body_block.update_position(body_x, body_y)
                body_y = body_block.content_bottom() + 2
        if self.next_block:
            if self.connection_direction == "horizontal":
                self.next_block.update_position(self.rect.right + 2, self.rect.y)
            else:
                if self.category == "Conditional" and self.body_blocks:
                    next_y = max(
                        body_block.content_bottom()
                        for body_block in self.body_blocks
                    ) + 2
                else:
                    next_y = self.rect.y + self.rect.height + 40 + 2
                self.next_block.update_position(self.rect.x, next_y)

    def update_condition_layout(self):
        """Resize a conditional row without reflowing its body downward."""
        if self.category != "Conditional":
            return
        self.update_size()
        cx = self.rect.x + self.keyword_part_width + 5
        for condition_block in self.condition_blocks:
            condition_block.rect.x = cx
            condition_block.rect.y = self.rect.y
            cx += condition_block.width + 2
        if self.next_block and self.connection_direction == "horizontal":
            self.next_block.update_position(self.rect.right + 2, self.rect.y)
