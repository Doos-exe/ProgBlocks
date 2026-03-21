# ProgBlocks: Block and Compile!
## Official Programming Language Documentation

---

## Table of Contents
1. [Introduction](#introduction)
2. [Language Overview](#language-overview)
3. [Data Types](#data-types)
4. [Syntax and Structure](#syntax-and-structure)
5. [Keywords and Operators](#keywords-and-operators)
6. [Examples](#examples)
7. [The Compiler Architecture](#the-compiler-architecture)
8. [Error Handling and Recovery](#error-handling-and-recovery)
9. [Getting Started](#getting-started)

---

## Introduction

**ProgBlocks** is a visual block-based programming language designed to teach programming concepts through an intuitive drag-and-drop interface. Rather than writing code line by line, users arrange colored blocks to create executable programs. Each block represents a specific programming construct, and the compiler validates and executes the resulting program.

ProgBlocks bridges the gap between visual programming and traditional syntax, making programming accessible while maintaining core computer science principles.

### Key Features
- **Visual Block-Based Interface**: Drag and drop blocks to build programs
- **Three-Phase Compiler**: Lexical, Syntax, and Semantic analysis
- **Type Safety**: Strong typing with automatic type checking
- **Error Recovery**: Intelligent error messages with recovery suggestions
- **Explainability Layer**: Detailed compilation phase visualization
- **Real-Time Feedback**: Immediate console output and error reporting

---

## Language Overview

ProgBlocks is a statically-typed, imperative language with four main operations:
1. **Variable Declaration**: Create typed variables (digit, word, or bet)
2. **Variable Assignment**: Assign values to variables with optional operations
3. **Output**: Display values to the console
4. **Comparison**: Compare values using the := operator

### Program Structure

A valid ProgBlocks program consists of one or more **statements**, where each statement ends with the `end` keyword:

```
[STATEMENT 1] end [STATEMENT 2] end ... [FINAL STATEMENT] end
```

Every program must end with the `end` terminator.

---

## Data Types

ProgBlocks supports three fundamental data types:

### 1. **digit** - Numeric Type
- Represents integers and floating-point numbers
- Examples: `5`, `42`, `3.14`, `100`
- Operations: Addition (`adds`), Subtraction (`minus`)
- Used for mathematical calculations

### 2. **word** - String Type
- Represents text and strings
- Must be enclosed in double quotes: `"hello"`, `"world"`
- Operations: Concatenation (`adds`), Substring removal (`minus`)
- Used for text manipulation

### 3. **bet** - Boolean Type
- Represents true/false values
- Valid values: `"real"` (true), `"fake"` (false)
- Supports comparison with `:=` operator
- Results of comparisons are always `bet` type

---

## Syntax and Structure

### Basic Variable Declaration

**Syntax:**
```
[TYPE] [NAME] : [VALUE] end
```

**Components:**
- `[TYPE]`: One of `digit`, `word`, or `bet`
- `[NAME]`: Valid variable identifier
- `:`: Separator (colon)
- `[VALUE]`: Literal value or reference to another variable
- `end`: Statement terminator

**Examples:**
```
digit count : 10 end
word greeting : "hello" end
bet is_valid : real end
```

### Variable Declaration with Operations

**Syntax:**
```
[TYPE] [NAME] : [VALUE1] [OPERATOR] [VALUE2] end
```

**Valid Operators:**
- `adds`: Addition (digit) or Concatenation (word)
- `minus`: Subtraction (digit only - NOT supported for word type)

**Examples:**
```
digit sum : 5 adds 3 end          (Result: 8)
digit difference : 10 minus 3 end (Result: 7)
word message : "hello" adds " world" end  (Result: "hello world")
```

### Bet Type Comparison (Assignment)

**Syntax:**
```
bet [NAME] := [VALUE1] [VALUE2] end
```

This compares two values and checks if they are equal. Both values must be of the same type.

**Examples:**
```
bet is_matching := real fake end     (Result: false)
bet same_numbers := 5 5 end          (Result: true)
bet string_equal := "abc" "abc" end  (Result: true)
```

### Output Statement

**Syntax:**
```
out [VALUE] end
```

Displays a value to the console. Can output variables, literals, or computed results.

**Examples:**
```
out 42 end
out "Hello World" end
out myVariable end
```

### Output with Operations

**Syntax:**
```
out [VALUE1] [OPERATOR] [VALUE2] end
```

Performs an operation and outputs the result.

**Examples:**
```
out 10 adds 5 end           (Displays: 15)
out "abc" adds "def" end    (Displays: abcdef)
out 20 minus 8 end          (Displays: 12)
```

---

## Keywords and Operators

### Keywords

| Keyword | Purpose |
|---------|---------|
| `digit` | Declare numeric variable |
| `word` | Declare string variable |
| `bet` | Declare boolean variable |
| `out` | Output/print statement |
| `end` | Statement terminator |

### Operators

| Operator | Name | Usage | Supported Types |
|----------|------|-------|-----------------|
| `:` | Assignment | `digit x : 5 end` | All types |
| `:=` | Comparison | `bet result := value1 value2 end` | All types |
| `adds` | Addition/Concatenation | `digit sum : 5 adds 3 end` | digit, word |
| `minus` | Subtraction | `digit diff : 10 minus 3 end` | digit only |

### Valid Identifiers

Variable names must:
- Start with a letter (a-z, A-Z) or underscore (_)
- Contain only alphanumeric characters and underscores
- NOT be a reserved keyword
- NOT be a reserved symbol

**Valid Examples:** `count`, `_name`, `value1`, `myVar`
**Invalid Examples:** `5count` (starts with digit), `my-var` (contains hyphen)

---

## Examples

### Example 1: Simple Arithmetic

```
digit first : 10 end
digit second : 5 end
digit result : first adds second end
out result end
```

**Output:** `> 15`

### Example 2: String Manipulation

```
word greeting : "hello" end
word target : " world" end
word message : greeting adds target end
out message end
```

**Output:** `> hello world`

### Example 3: Boolean Comparison

```
digit num1 : 7 end
digit num2 : 7 end
bet are_equal := num1 num2 end
out are_equal end
```

**Output:** `> True`

### Example 4: Complex Program

```
word firstName : "John" end
word lastName : "Doe" end
word fullName : firstName adds lastName end

digit age : 25 end
digit birthYear : 1999 end
digit calculatedAge : 2024 minus birthYear end

out fullName end
out calculatedAge end
```

**Output:**
```
> JohnDoe
> 25
```

### Example 5: Bet Type with Real/Fake

```
bet status1 : real end
bet status2 : fake end
bet comparison := status1 status2 end
out comparison end
```

**Output:** `> False`

---

## The Compiler Architecture

ProgBlocks uses a three-phase compiler to validate and execute programs:

### Phase 1: Lexical Analysis

**Purpose:** Tokenize input and classify tokens

**Checks:**
- Validates each token is a recognized keyword, operator, separator, or identifier
- Classifies tokens by type (Keyword, Operator, Separator, Literal, Identifier)
- Reports invalid or unknown tokens

**Example:**
```
Input: digit count : 5 end
Tokens: [digit] [count] [:] [5] [end]
Classification:
  [1] 'digit' -> Keyword
  [2] 'count' -> Identifier
  [3] ':' -> Operator
  [4] '5' -> Literal (digit)
  [5] 'end' -> Separator
Status: [PASSED]
```

### Phase 2: Syntax Analysis

**Purpose:** Validate program structure and statement format

**Checks:**
- Verifies program starts with valid keyword (digit, word, bet, out)
- Verifies program ends with 'end' terminator
- Validates statement structure by 'end' delimiter
- Checks that keywords are not used as identifiers
- Validates overall program grammar

**Statement Structure:**
- Declaration: `TYPE NAME : VALUE [OP VALUE] end`
- Output: `out VALUE [OP VALUE] end`

### Phase 3: Semantic Analysis

**Purpose:** Validate meaning, types, and variable usage

**Checks:**
- Variable declaration and duplicate name detection
- Type matching between declared type and assigned value
- Variable reference validation (used before declaration)
- Operation compatibility with types
- Symbol table creation with memory allocation

**Symbol Table Example:**
```
Name                 Type            Scope       Offset
count                digit           0           0
message              word            0           4
is_valid             bet             0           5
```

---

## Error Handling and Recovery

ProgBlocks provides intelligent error detection with recovery strategies.

### Error Categories

#### Lexical Errors
- Invalid tokens
- Unknown symbols
- Malformed identifiers

**Recovery Suggestions:**
1. Check token spelling and capitalization
2. Use valid keywords: digit, word, bet, out, end, :, adds, minus
3. Variable names must start with letter or underscore
4. Use proper quotes for strings

#### Syntax Errors
- Missing 'end' terminator
- Invalid program start
- Malformed statements

**Recovery Suggestions:**
1. Every program must end with 'end' block
2. Programs must start with: digit, word, bet, or out
3. Use correct block structure: TYPE NAME : VALUE end

#### Semantic Errors
- Type mismatch
- Undefined variables
- Duplicate variable names
- Invalid declarations

**Recovery Suggestions:**
1. Match value type to declared type
2. Declare variables before using them
3. Use different names for different variables
4. Follow declaration format: TYPE NAME : VALUE end

### Example Error Messages

```
Semantic Error [5]: Type mismatch - expected digit, got word
  Variable 'sum' declared as digit but assigned word "hello"

RECOVERY STRATEGIES:
1. Match value type to declared type
2. digit expects numbers: 42, 3, 100
3. word expects quoted strings: "hello", "world"
4. Check quotes around string values
```

---

## Getting Started

### Step 1: Understand the Interface

**Left Panel (Blox):** Drag available block templates
- **Keywords:** digit, word, bet, out
- **Operators:** :, :=, adds, minus
- **Separators:** end
- **Editable Data:** data blocks (customizable purple blocks)

**Center Panel (Blueprint):** Drop and arrange blocks to build programs

**Right Panel:** Control buttons
- **CLEAR:** Remove all blocks
- **RUN:** Execute the program
- **INFO:** View detailed compiler analysis

### Step 2: Build Your Program

1. Drag blocks from the left sidebar
2. Arrange them in the blueprint area (top to bottom)
3. Click on editable data blocks to customize values
4. Connect blocks by placing them near each other

### Step 3: Run and Debug

1. Click **RUN** to compile and execute
2. View output in the console area
3. Click **INFO** to see detailed analysis
4. Read error messages and recovery suggestions
5. Modify blocks and try again

### Step 4: Explore Features

- **Scroll Workspace:** Use UP/DOWN arrow keys
- **Scroll Console:** Use mouse wheel in console area
- **Edit Data Blocks:** Click on purple editable blocks
- **Move Blocks:** Drag blocks to new positions
- **Delete Blocks:** Drag outside the blueprint area

---

## Advanced Concepts

### Type Inference and Operations

ProgBlocks enforces strict type checking:
- `digit + digit = digit`
- `word + word = word`
- `digit - digit = digit`
- `word - word = NOT ALLOWED` (minus operation not supported for word type)
- `bet := any any = bet`

### Variable Scope

All variables declared in ProgBlocks have **global scope**. Once declared, a variable is accessible throughout the program.

### Memory Model

Each variable occupies memory based on type:
- `digit`: 4 bytes
- `word`: 1 byte (only counts variable name; string content is dynamic)
- `bet`: 2 bytes

Symbol table tracks memory allocation and offset positions.

### Connection Rules

When building programs:
- Blocks can connect **vertically** (below another block)
- Blocks can connect **horizontally** (to the right of another block)
- Chain connections follow top-to-bottom, left-to-right precedence
- Blocks must stay within the blueprint area (200px to end, 60px to 460px vertically)

---

## Best Practices

1. **Use Meaningful Names:** `total` is better than `x`
2. **Keep Statements Simple:** One operation per statement when possible
3. **Test Incrementally:** Build and run programs step by step
4. **Read Error Messages:** They provide specific guidance
5. **Use Comments:** Add data blocks with explanatory text (they're ignored)
6. **Type Consistency:** Ensure types match throughout your program

---

## Limitations and Future Goals

### Current Limitations
- No user-defined functions or procedures
- No conditional statements (if/else)
- No loops (while/for)
- Single-pass compilation
- No import/module system

### Future Enhancements
- Control flow (if/else, switch)
- Looping constructs (for, while)
- Functions and procedures
- Arrays and collections
- File I/O operations
- Advanced type system

---

## Conclusion

ProgBlocks demonstrates that visual programming can be both powerful and intuitive. By combining block-based interface design with a traditional three-phase compiler, ProgBlocks offers a unique learning platform for understanding programming fundamentals, compiler design, and software development principles.

Whether you're learning to code or teaching programming concepts, ProgBlocks provides immediate feedback, clear error messages, and a structured approach to building executable programs.

---

## Appendix: Complete Grammar

```
Program     ::= Statement+
Statement   ::= Declaration "end" | OutputStatement "end"
Declaration ::= Type Identifier ":" Value [Operation Value]
OutputStatement ::= "out" Value [Operation Value]
Type        ::= "digit" | "word" | "bet"
Operation   ::= "adds" | "minus"
Value       ::= Literal | Identifier
Literal     ::= Number | String | BoolValue
BoolValue   ::= "real" | "fake"
Identifier  ::= [a-zA-Z_][a-zA-Z0-9_]*
Number      ::= [0-9]+ | [0-9]+ "." [0-9]+
String      ::= '"' [^"]* '"'
```

---

**ProgBlocks v1.0** - *Block and Compile!*

*Created as a final project demonstrating compiler design, visual programming, and user interface principles.*
