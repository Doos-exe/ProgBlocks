# ProgBlocks: Block and Compile!

A low-code based programming language built with **Python** and **Pygame**. ProgBlocks allows you to write code by dragging and dropping visual blocks instead of typing syntax, making programming more fun and visual. 

## Features

- **Visual Block Programming**: Drag and drop blocks to write code
- **Keyword Blocks** (Orange): `digit`, `word`, `bet`, `out`
- **Operator Blocks** (Blue): `:`, `adds`, `minus`
- **Separator Blocks** (Gray): `end`
- **Editable Data Blocks** (Purple): Custom values and variables
- **Real-time Compilation**: Compile and run your code instantly
- **Interactive Console**: View output and error messages
- **Symbol Table**: Track all variables and their values
- **Multi-line Code Support**: Write complex programs with multiple statements

## Installation

### Step 1: Install Python
Download and install Python from [python.org](https://www.python.org/downloads/). Make sure to check "Add Python to PATH" during installation.

### Step 2: Install Required Libraries

Open Command Prompt (Windows) or Terminal (Mac/Linux) and run:

```bash
pip install pygame
```

If you have multiple Python versions, you may need to use:
```bash
pip3 install pygame
```

### Step 3: Verify Installation

To verify that pygame is installed correctly, run:
```bash
python -c "import pygame; print(f'Pygame version: {pygame.version.ver}')"
```

## Running ProgBlocks

Navigate to the project directory and run:

```bash
python FINAL_PROJECT.py
```

Or on some systems:
```bash
python3 FINAL_PROJECT.py
```

The ProgBlocks window should open with the GUI ready for use.

## ProgBlocks Language Syntax

### Variable Declaration - `digit` (Integer)
Declares an integer variable.

**Syntax:**
```
digit <identifier> : <value> end
```

**Examples:**
```
digit count : 5 end
digit sum : 5 adds 3 end
digit diff : 10 minus 3 end
```

### Variable Declaration - `word` (String)
Declares a string variable.

**Syntax:**
```
word <identifier> : "<value>" end
```

**Examples:**
```
word greeting : "Hello World" end
word message : "Hello" adds " World" end
```

### Boolean - `bet`
Declares a boolean value (Real or Fake).

**Syntax:**
```
bet <value> end
```

**Examples:**
```
bet Real end
bet Fake end
```

### Output - `out`
Prints a value to the console.

**Syntax:**
```
out <value> end
```

**Examples:**
```
out "Hello" end
out 42 end
```

### Operators

#### `adds` - Addition/Concatenation
- For integers: performs addition
- For strings: concatenates strings

```
digit sum : 10 adds 5 end        // Result: 15
word sentence : "Hello" adds " World" end  // Result: "Hello World"
```

#### `minus` - Subtraction
- For integers: performs subtraction
- Not supported for strings

```
digit diff : 10 minus 3 end      // Result: 7
```

## How to Use the GUI

### Main Components

1. **Template Panel (Left)**: Shows available blocks to drag
   - Orange blocks: Keywords
   - Blue blocks: Operators
   - Gray blocks: Separators
   - Purple blocks: Data/Values

2. **Workspace (Center)**: Where you assemble your code blocks

3. **Console Output (Bottom Right)**: Shows program output and errors

4. **Info Tab**: Displays the symbol table with all variables and their values

### Block Operations

- **Drag a Block**: Click and drag any block from the template panel to the workspace
- **Edit Data Block**: Double-click a purple data block to enter a custom value
- **Delete a Block**: Press `Ctrl+D` after selecting a block (or use the delete button)
- **Compile & Run**: Click the "RUN" button to execute your program
- **Clear Workspace**: Click the "CLEAR" button to remove all blocks

### Keyboard Shortcuts

- `Ctrl+D`: Delete selected block
- `Click + Drag`: Move blocks around the workspace

## Test Cases

The system includes comprehensive test cases for validation:

### Digit Variable Tests
```
digit int : 5 end                          ✓ Correct
digit int : 5                              ✗ Missing end
digit digit : 5 end                        ✗ Invalid identifier (keyword used)
digit int : hello end                      ✗ Invalid literal
digit int : 1 adds 2 end                   ✓ Valid addition
digit int : 2 minus 2 end                  ✓ Valid subtraction
```

### Word Variable Tests
```
word x : "hello" end                       ✓ Correct
word x : "hello" adds " world" end         ✓ Valid concatenation
word test : "tes end                       ✗ Unclosed string
word num : 1 end                           ✗ Invalid literal (expected string)
```

### Boolean Tests
```
bet Real end                               ✓ Correct
bet Fake end                               ✓ Correct
bet x end                                  ✓ Valid identifier
```

### Output Tests
```
out "Hello" end                            ✓ Correct
out 2 end                                  ✓ Correct
out hello end                              ✗ Invalid identifier (missing quotes)
```

## License

This is an academic project developed as a final project for Programming Languages course.

## Support

For issues or questions, contact the development team or refer to the test cases for expected behavior examples.
