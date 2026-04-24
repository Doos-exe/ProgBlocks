# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ProgBlocks** ("Blox") is a visual block-based programming environment built with Python and Pygame. Users drag blocks from a sidebar onto a blueprint canvas, chain them together, and compile the arrangement into output via a three-phase compiler (Lexical → Syntax → Semantic). The entire project lives in a single file: `FINAL_PROJECT.py`.

## Running the Application

```bash
python FINAL_PROJECT.py
```

Requires Python 3 and Pygame (`pip install pygame`).

## Architecture

The file is structured in three logical sections:

### 1. Block System (`Block` class, lines ~92–225)
- `Block` holds text, color, category, position, and linked-list pointers (`next_block`, `prev_block`)
- `category` determines behavior: `"Keyword"`, `"Operator"`, `"Separator"`, `"Editable"`, `"Conditional"`
- `"Conditional"` blocks render as a C-shape when they have `body_blocks` (nested children)
- `update_position()` recursively repositions chained blocks and nested body blocks
- `draw()` handles three rendering paths: sidebar template, conditional in blueprint (C-shape or normal), regular block

### 2. Compiler (`evaluate_compiler_logic` and helpers, lines ~227–1153)
The compiler pipeline runs on the token sequence extracted from placed blocks:

1. **Tokenization** — `extract_tokens_with_nesting()` does a recursive traversal of chain-starts, appending body tokens inside conditionals and inserting `<keyword>_end` tokens automatically
2. **Lexical** — `lexical_analysis()` validates each token against keywords, operators, separators, literals, and identifiers
3. **Syntax** — checks that the token stream starts with a valid keyword, ends with `end`, and each statement bounded by `end` follows `[KEYWORD/OUT] [ARGS...] end`
4. **Semantic** — walks the token list, evaluates variable declarations (with `digit`/`word`/`bet` types and arithmetic), resolves `out` statements, builds a symbol table with memory offsets

#### Language Syntax
| Construct | Pattern |
|---|---|
| Declare | `digit NAME : VALUE end` |
| Assign with op | `digit NAME : VALUE adds VALUE end` |
| Output | `out VALUE end` |
| Output with op | `out VALUE adds VALUE end` |
| Conditional | `if BODY if_end` (blocks nested spatially) |

- **Types**: `digit` (int, 4 bytes), `word` (string, 1 byte), `bet` (boolean, 2 bytes; values: `real`/`fake`)
- **Operators**: `adds`, `minus`, `mul`, `div` (minus/div unsupported for `word`)

### 3. UI / Main Loop (lines ~1155–1789)
- **Layout**: Fixed 50px header, dynamically sized workspace, draggable-separator console at bottom
- **Global layout state**: `workspace_top`, `workspace_bottom`, `console_top`, `console_bottom`, `zoom_scale` — recalculated on resize/separator drag via `recalculate_ui_positions()`
- **Sidebar** (`sidebar_blocks`): template blocks at fixed left positions; clicking clones a new block into `placed_blocks`
- **Blueprint** (`placed_blocks`): blocks live at logical coordinates; rendered via `get_block_view_rect()` which applies `zoom_scale` and `workspace_scroll_offset`
- **Connections**: on MOUSEBUTTONUP, proximity check snaps dragged block to the nearest free chain end (vertical ≤20px gap, horizontal ≤20px gap)
- **Nesting**: `reorganize_nesting()` runs after every drop, spatially assigns blocks inside conditional C-shapes
- **Explainability window**: `show_explainability_window()` opens a separate Pygame window showing lexical tokens, syntax validation, semantic analysis, and symbol table
- **Controls**: Ctrl+Scroll or +/- buttons to zoom (0.5×–2.0×); arrow keys scroll the workspace; mouse wheel in console scrolls output; separator bar is draggable

## Key Global State

| Variable | Purpose |
|---|---|
| `placed_blocks` | All blocks on the blueprint |
| `sidebar_blocks` | Template blocks in the sidebar |
| `dragging_block` | Currently held block (or `None`) |
| `editing_block` | Block with active text input (Editable category) |
| `zoom_scale` | Current zoom level (0.5–2.0) |
| `workspace_scroll_offset` | Vertical scroll for the blueprint |
| `console_scroll_offset` | Vertical scroll for console output |
| `dynamic_console_height` | Console height (changed by separator drag) |
| `detailed_phases` | Last compiler phase output (used by INFO button) |

## Important Constraints

- Block logical coordinates are unzoomed; `get_block_view_rect()` converts to screen coordinates for hit-testing and drawing
- `evaluate_compiler_logic()` uses global `workspace_top`/`workspace_bottom` to filter out-of-bounds blocks — these must be current before calling
- Blocks dropped to the left of `WORKSPACE_LEFT`, above `workspace_top`, below `workspace_bottom`, or to the right of `WIDTH - WORKSPACE_RIGHT_MARGIN` are automatically removed from `placed_blocks`
- `"Editable"` blocks start disconnection on drag (not on click), so a single click enters text-edit mode without moving the block
