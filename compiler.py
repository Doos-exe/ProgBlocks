"""Lexing, parsing, semantic analysis, and execution for ProgBlocks.

The editor stores a program as linked blocks. This module turns that block
tree into tokens, parses the tokens into statements, and then executes the
statements. Keeping parsing separate from execution prevents malformed block
arrangements from causing an IndexError or a partially executed program.
"""

import ast
import re

import shared
from constants import (
    KEYWORDS,
    OPERATORS,
    SEPARATORS,
    WORKSPACE_LEFT,
    WORKSPACE_RIGHT_MARGIN,
)


CONDITIONALS = {"if", "while", "for"}
CONDITIONAL_ENDS = {f"{name}_end" for name in CONDITIONALS}
DECLARATION_TYPES = {"digit", "word", "bet"}
ARITHMETIC_OPERATORS = {"adds", "minus", "mul", "div"}
COMPARISON_OPERATORS = {"==", "!=", "<", ">", "<=", ">="}


# ---- Token validators ----------------------------------------------------

def is_valid_identifier(name):
    """Return whether *name* is a legal user-defined identifier."""
    try:
        if not isinstance(name, str) or not name:
            return False
        if not (name[0].isalpha() or name[0] == "_"):
            return False
        if name in KEYWORDS or name in OPERATORS or name in SEPARATORS:
            return False
        return all(char.isalnum() or char == "_" for char in name)
    except (TypeError, IndexError):
        return False


def get_literal_type(literal):
    """Return ``digit``, ``word``, or ``bet`` for a literal token.

    Boolean words are deliberately checked only when unquoted. In the old
    implementation ``"real"`` was treated as a boolean instead of a string.
    """
    if not isinstance(literal, str):
        return None
    token = literal.strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return "word"
    if token.lower() in {"real", "fake", "true", "false"}:
        return "bet"
    if re.fullmatch(r"[+-]?\d+", token):
        return "digit"
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+)", token):
        return "digit"
    return None


def is_valid_token(token):
    return (
        token in KEYWORDS
        or token in OPERATORS
        or token in SEPARATORS
        or get_literal_type(token) is not None
        or is_valid_identifier(token)
    )


def lexical_analysis(tokens):
    errors = []
    for position, token in enumerate(tokens, start=1):
        if not is_valid_token(token):
            errors.append(f"Lexical Error [{position}]: Invalid token '{token}'")
    return errors


# ---- Recovery guidance ---------------------------------------------------

def get_recovery_strategies(error_type, error_details=""):
    strategies = {
        "lexical_invalid_token": [
            "RECOVERY STRATEGIES:",
            "1. Check token spelling and capitalization",
            "2. Use valid keywords and operators from the palette",
            "3. Identifiers must start with a letter or underscore",
            "4. Strings must be enclosed in single or double quotes",
            "5. Boolean values are real/fake (true/false are also accepted)",
        ],
        "syntax_missing_end": [
            "RECOVERY STRATEGIES:",
            "1. Use TYPE NAME : VALUE end for declarations",
            "2. Use out VALUE end for output",
            "3. Conditional bodies close with if_end, while_end, or for_end",
            "4. Check that blocks are connected in the intended order",
        ],
        "syntax_invalid_start": [
            "RECOVERY STRATEGIES:",
            "1. Programs start with digit, word, bet, out, if, while, or for",
            "2. A declaration needs a name, a colon, a value, and end",
            "3. A conditional needs a condition and a body",
        ],
        "semantic_type_mismatch": [
            "RECOVERY STRATEGIES:",
            "1. digit values and arithmetic operands must be numeric",
            "2. word values must be quoted strings",
            "3. bet values must be real/fake or a comparison result",
            "4. adds needs matching digit or word types",
            "5. minus and div work only with digits",
            "6. A word can be multiplied by a digit repeat count",
        ],
        "semantic_undefined_identifier": [
            "RECOVERY STRATEGIES:",
            "1. Declare a variable before using it",
            "2. Variable names are case-sensitive",
            "3. Check the spelling of the identifier",
        ],
        "semantic_invalid_declaration": [
            "RECOVERY STRATEGIES:",
            "1. Declaration format: TYPE NAME : VALUE [OP VALUE] end",
            "2. Use a unique identifier that is not a keyword",
            "3. Use := with two values for a bet comparison",
        ],
        "semantic_invalid_condition": [
            "RECOVERY STRATEGIES:",
            "1. if/while accepts a bet variable or VALUE COMPARISON VALUE",
            "2. Comparison operators are ==, !=, <, >, <=, and >=",
            "3. for accepts one non-negative digit count",
            "4. Add at least one statement inside the conditional body",
        ],
    }
    return strategies.get(error_type, ["No recovery strategies available for this error"])


# ---- Conditional layout --------------------------------------------------

def _conditional_body_bounds(conditional_block):
    """Return a forgiving but finite drop area for a conditional body."""
    body_top = conditional_block.rect.bottom + 5
    known_height = sum(
        max(35, body.rect.height) + 2 for body in conditional_block.body_blocks
    )
    body_bottom = min(
        shared.workspace_bottom,
        body_top + max(220, known_height + 120),
    )
    body_left = conditional_block.rect.x + 12
    body_right = conditional_block.rect.x + max(
        conditional_block.rect.width + 180, 500
    )
    return body_left, body_top, body_right, body_bottom


def is_block_inside_conditional(block, conditional_block):
    if conditional_block.category != "Conditional" or block is conditional_block:
        return False
    if block.in_condition_of is not None:
        return False
    left, top, right, bottom = _conditional_body_bounds(conditional_block)
    return (
        left <= block.rect.centerx <= right
        and top <= block.rect.centery <= bottom
    )


def _parent_candidate(block, conditionals):
    candidates = [
        conditional
        for conditional in conditionals
        if is_block_inside_conditional(block, conditional)
    ]
    if not candidates:
        return None
    # The lower/innermost conditional wins when nested conditionals overlap.
    return max(candidates, key=lambda item: (item.rect.y, item.rect.x))


def reorganize_nesting(placed_blocks):
    """Rebuild conditional parent/body relationships after a block move."""
    conditionals = [b for b in placed_blocks if b.category == "Conditional"]

    for block in placed_blocks:
        block.parent_conditional = None
    for conditional in conditionals:
        conditional.body_blocks.clear()

    # Include conditional blocks so nested if/while/for blocks work.
    for block in placed_blocks:
        if block.in_condition_of is None:
            block.parent_conditional = _parent_candidate(block, conditionals)

    # A chain cannot cross a conditional boundary. Disconnect both sides;
    # otherwise a body could be compiled once as a body and once at top level.
    for block in placed_blocks:
        parent = block.parent_conditional
        if parent is None or block.in_condition_of is not None:
            continue
        if block.prev_block is not None and block.prev_block.parent_conditional is not parent:
            block.prev_block.next_block = None
            block.prev_block = None
        if block.next_block is not None and block.next_block.parent_conditional is not parent:
            block.next_block.prev_block = None
            block.next_block = None

    # Store only chain heads in body_blocks. update_position() lays out the
    # remainder of each chain recursively.
    for block in placed_blocks:
        parent = block.parent_conditional
        if parent is None or block.in_condition_of is not None:
            continue
        if block.prev_block is None or block.prev_block.parent_conditional is not parent:
            parent.body_blocks.append(block)

    for conditional in conditionals:
        conditional.body_blocks.sort(key=lambda item: (item.rect.y, item.rect.x))
        conditional.update_position(conditional.rect.x, conditional.rect.y)


# ---- Token extraction ----------------------------------------------------

def extract_tokens_with_nesting(blocks):
    """Flatten the block hierarchy while adding explicit conditional closers."""
    tokens = []
    visited = set()

    def traverse(block):
        if block is None or block.is_template or block.in_condition_of is not None:
            return
        if id(block) in visited:
            return
        visited.add(id(block))
        tokens.append(block.text.strip())

        if block.category == "Conditional":
            for condition_block in block.condition_blocks:
                if not condition_block.is_template:
                    tokens.append(condition_block.text.strip())
            for body_block in sorted(
                block.body_blocks, key=lambda item: (item.rect.y, item.rect.x)
            ):
                traverse(body_block)
            tokens.append(f"{block.text.strip()}_end")

        if block.next_block is not None:
            traverse(block.next_block)

    starts = [
        block
        for block in blocks
        if not block.is_template
        and block.prev_block is None
        and block.parent_conditional is None
        and block.in_condition_of is None
    ]
    starts.sort(key=lambda item: (item.rect.y, item.rect.x))
    for start in starts:
        traverse(start)
    return tokens


# ---- Parser --------------------------------------------------------------

class ParseError(Exception):
    def __init__(self, message, position):
        super().__init__(message)
        self.message = message
        self.position = position


def _expect(tokens, position, expected, description):
    if position >= len(tokens) or tokens[position] != expected:
        actual = "end of program" if position >= len(tokens) else f"'{tokens[position]}'"
        raise ParseError(f"Expected {description}, got {actual}", position)
    return position + 1


def _parse_operand(tokens, position):
    if position >= len(tokens):
        raise ParseError("Expected a value, got end of program", position)
    token = tokens[position]
    if token in KEYWORDS or token in OPERATORS or token in SEPARATORS:
        raise ParseError(f"Expected a value, got '{token}'", position)
    if get_literal_type(token) is None and not is_valid_identifier(token):
        raise ParseError(f"Invalid value '{token}'", position)
    return token, position + 1


def _parse_expression(tokens, position):
    first, position = _parse_operand(tokens, position)
    if position < len(tokens) and tokens[position] in ARITHMETIC_OPERATORS:
        operator = tokens[position]
        second, position = _parse_operand(tokens, position + 1)
        return (first, operator, second), position
    return (first, None, None), position


def _parse_statement(tokens, position, closing=None):
    if position >= len(tokens):
        raise ParseError("Expected a statement, got end of program", position)
    keyword = tokens[position]

    if keyword in CONDITIONAL_ENDS:
        raise ParseError(f"Unexpected '{keyword}'", position)

    # Assignment: NAME : VALUE [OP VALUE] end
    # This is intentionally separate from declarations so loop bodies can
    # update an existing variable without redeclaring it.
    if (
        is_valid_identifier(keyword)
        and position + 1 < len(tokens)
        and tokens[position + 1] == ":"
    ):
        expression, next_pos = _parse_expression(tokens, position + 2)
        next_pos = _expect(tokens, next_pos, "end", "'end'")
        return {
            "kind": "assignment",
            "name": keyword,
            "expression": expression,
        }, next_pos

    if keyword in DECLARATION_TYPES:
        if keyword == "bet" and position + 2 < len(tokens) and tokens[position + 2] == ":=":
            if position + 1 >= len(tokens) or not is_valid_identifier(tokens[position + 1]):
                raise ParseError("bet requires a valid variable name", position + 1)
            left, next_pos = _parse_operand(tokens, position + 3)
            right, next_pos = _parse_operand(tokens, next_pos)
            next_pos = _expect(tokens, next_pos, "end", "'end'")
            return {
                "kind": "bet_declaration",
                "name": tokens[position + 1],
                "left": left,
                "right": right,
            }, next_pos

        if position + 1 >= len(tokens) or not is_valid_identifier(tokens[position + 1]):
            raise ParseError(f"{keyword} requires a valid variable name", position + 1)
        next_pos = _expect(tokens, position + 2, ":", "':'")
        expression, next_pos = _parse_expression(tokens, next_pos)
        next_pos = _expect(tokens, next_pos, "end", "'end'")
        return {
            "kind": "declaration",
            "type": keyword,
            "name": tokens[position + 1],
            "expression": expression,
        }, next_pos

    if keyword == "out":
        expression, next_pos = _parse_expression(tokens, position + 1)
        next_pos = _expect(tokens, next_pos, "end", "'end'")
        return {"kind": "output", "expression": expression}, next_pos

    if keyword in CONDITIONALS:
        condition_start = position + 1
        if condition_start >= len(tokens) or tokens[condition_start] in CONDITIONAL_ENDS:
            raise ParseError(f"{keyword} requires a condition", condition_start)
        if tokens[condition_start] in DECLARATION_TYPES:
            declaration = tokens[condition_start]
            raise ParseError(
                f"{keyword} conditions use a value, not declaration keyword '{declaration}'; "
                "use the variable name only",
                condition_start,
            )
        first, next_pos = _parse_operand(tokens, condition_start)
        condition = [first]
        if next_pos < len(tokens) and tokens[next_pos] in COMPARISON_OPERATORS:
            operator = tokens[next_pos]
            second, next_pos = _parse_operand(tokens, next_pos + 1)
            condition.extend([operator, second])

        expected_end = f"{keyword}_end"
        body, next_pos = _parse_statements(tokens, next_pos, expected_end)
        if not body:
            raise ParseError(f"{keyword} body cannot be empty", next_pos)
        next_pos = _expect(tokens, next_pos, expected_end, f"'{expected_end}'")
        return {
            "kind": "conditional",
            "keyword": keyword,
            "condition": condition,
            "body": body,
        }, next_pos

    raise ParseError(f"Unexpected token '{keyword}'", position)


def _parse_statements(tokens, position=0, closing=None):
    statements = []
    while position < len(tokens) and tokens[position] != closing:
        if tokens[position] in CONDITIONAL_ENDS:
            raise ParseError(f"Unexpected '{tokens[position]}'", position)
        statement, position = _parse_statement(tokens, position, closing)
        statements.append(statement)
    return statements, position


def parse_program(tokens):
    statements, position = _parse_statements(tokens)
    if not statements:
        raise ParseError("Program contains no statements", 0)
    if position != len(tokens):
        raise ParseError(f"Unexpected token '{tokens[position]}'", position)
    return statements


# ---- Semantic analysis and execution ------------------------------------

class SemanticError(Exception):
    def __init__(self, message, position=0, recovery="semantic_type_mismatch"):
        super().__init__(message)
        self.message = message
        self.position = position
        self.recovery = recovery


def _literal_value(token):
    literal_type = get_literal_type(token)
    if literal_type == "digit":
        number = token.strip()
        return int(number) if re.fullmatch(r"[+-]?\d+", number) else float(number)
    if literal_type == "word":
        try:
            return ast.literal_eval(token)
        except (ValueError, SyntaxError):
            return token[1:-1]
    if literal_type == "bet":
        return token.strip().lower() in {"real", "true"}
    return None


def _display_value(value):
    if isinstance(value, bool):
        return "Real" if value else "Fake"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _apply_operator(operator, left, left_type, right, right_type, position):
    if operator == "adds":
        if left_type == right_type and left_type in {"digit", "word"}:
            return left_type, left + right
        raise SemanticError(
            "adds requires two values of the same digit or word type",
            position,
            "semantic_type_mismatch",
        )
    if operator == "minus":
        if left_type == right_type == "digit":
            return "digit", left - right
        raise SemanticError("minus works only with two digits", position, "semantic_type_mismatch")
    if operator == "mul":
        if left_type == right_type == "digit":
            return "digit", left * right
        if left_type == "word" and right_type == "digit" and isinstance(right, int):
            return "word", left * right
        raise SemanticError(
            "mul requires two digits or a word multiplied by a digit",
            position,
            "semantic_type_mismatch",
        )
    if operator == "div":
        if left_type == right_type == "digit":
            if right == 0:
                raise SemanticError("Division by zero", position, "semantic_type_mismatch")
            return "digit", left / right
        raise SemanticError("div works only with two digits", position, "semantic_type_mismatch")
    raise SemanticError(f"Unknown operator '{operator}'", position, "semantic_type_mismatch")


def _run_program(statements, detailed_phases):
    variables = {}
    outputs = []
    symbols = []
    memory_offset = 0
    memory_size = {"digit": 4, "word": 1, "bet": 2}

    def resolve(token, position):
        if token in variables:
            return variables[token]
        literal_type = get_literal_type(token)
        if literal_type is not None:
            return literal_type, _literal_value(token)
        raise SemanticError(
            f"Variable '{token}' not found",
            position,
            "semantic_undefined_identifier",
        )

    def evaluate_expression(expression, position):
        first, operator, second = expression
        left_type, left = resolve(first, position)
        if operator is None:
            return left_type, left
        right_type, right = resolve(second, position + 2)
        return _apply_operator(operator, left, left_type, right, right_type, position + 1)

    def declare(name, value_type, value, position):
        nonlocal memory_offset
        if name in variables:
            raise SemanticError(
                f"Variable '{name}' already declared",
                position,
                "semantic_invalid_declaration",
            )
        variables[name] = (value_type, value)
        symbols.append(f"{name:<20} {value_type:<15} {'global':<12} {memory_offset}")
        memory_offset += memory_size[value_type]

    def evaluate_condition(statement):
        condition = statement["condition"]
        keyword = statement["keyword"]
        if keyword == "for":
            if len(condition) != 1:
                raise SemanticError(
                    "for accepts one digit count", 0, "semantic_invalid_condition"
                )
            value_type, value = resolve(condition[0], 0)
            if value_type != "digit" or not _numeric(value) or value < 0 or int(value) != value:
                raise SemanticError(
                    "for count must be a non-negative whole number",
                    0,
                    "semantic_invalid_condition",
                )
            return int(value)

        if len(condition) == 1:
            value_type, value = resolve(condition[0], 0)
            if value_type != "bet":
                raise SemanticError(
                    f"{keyword} requires a bet value or a comparison",
                    0,
                    "semantic_invalid_condition",
                )
            return bool(value)

        if len(condition) != 3 or condition[1] not in COMPARISON_OPERATORS:
            raise SemanticError(
                "Invalid conditional expression", 0, "semantic_invalid_condition"
            )
        left_type, left = resolve(condition[0], 0)
        right_type, right = resolve(condition[2], 0)
        if left_type != right_type:
            raise SemanticError(
                "Compared values must have matching types", 0, "semantic_type_mismatch"
            )
        operator = condition[1]
        if operator == "==":
            return left == right
        if operator == "!=":
            return left != right
        if operator == "<":
            return left < right
        if operator == ">":
            return left > right
        if operator == "<=":
            return left <= right
        return left >= right

    def run_statement(statement):
        kind = statement["kind"]
        if kind == "assignment":
            if statement["name"] not in variables:
                raise SemanticError(
                    f"Variable '{statement['name']}' not found",
                    0,
                    "semantic_undefined_identifier",
                )
            actual_type, value = evaluate_expression(statement["expression"], 0)
            expected_type, _ = variables[statement["name"]]
            if actual_type != expected_type:
                raise SemanticError(
                    f"Type mismatch - expected {expected_type}, got {actual_type}",
                    0,
                    "semantic_type_mismatch",
                )
            variables[statement["name"]] = (expected_type, value)
            detailed_phases["semantic"].append(
                f"  Assignment: {statement['name']} -> {_display_value(value)}"
            )
            return

        if kind == "declaration":
            actual_type, value = evaluate_expression(statement["expression"], 0)
            expected_type = statement["type"]
            if actual_type != expected_type:
                raise SemanticError(
                    f"Type mismatch - expected {expected_type}, got {actual_type}",
                    0,
                    "semantic_type_mismatch",
                )
            declare(statement["name"], actual_type, value, 0)
            detailed_phases["semantic"].append(
                f"  Declaration: {expected_type} {statement['name']} -> {_display_value(value)}"
            )
            return

        if kind == "bet_declaration":
            left_type, left = resolve(statement["left"], 0)
            right_type, right = resolve(statement["right"], 0)
            if left_type != right_type:
                raise SemanticError(
                    "bet comparison values must have matching types",
                    0,
                    "semantic_type_mismatch",
                )
            value = left == right
            declare(statement["name"], "bet", value, 0)
            detailed_phases["semantic"].append(
                f"  Comparison: {statement['name']} = {_display_value(value)}"
            )
            return

        if kind == "output":
            _, value = evaluate_expression(statement["expression"], 0)
            outputs.append(f"> {_display_value(value)}")
            detailed_phases["semantic"].append(f"  Output: {_display_value(value)}")
            return

        if kind == "conditional":
            keyword = statement["keyword"]
            if keyword == "if":
                result = evaluate_condition(statement)
                detailed_phases["semantic"].append(
                    f"  if condition -> {'Real' if result else 'Fake'}"
                )
                if result:
                    for child in statement["body"]:
                        run_statement(child)
                return

            if keyword == "for":
                count = evaluate_condition(statement)
                detailed_phases["semantic"].append(f"  for loop -> {count} iteration(s)")
                for _ in range(count):
                    for child in statement["body"]:
                        run_statement(child)
                return

            iterations = 0
            while evaluate_condition(statement):
                iterations += 1
                if iterations > 100:
                    raise SemanticError(
                        "while loop exceeded 100 iterations; check that its condition changes",
                        0,
                        "semantic_invalid_condition",
                    )
                for child in statement["body"]:
                    run_statement(child)
            detailed_phases["semantic"].append(
                f"  while loop -> {iterations} iteration(s)"
            )

    for statement in statements:
        run_statement(statement)
    return outputs, symbols


def _render_statement(statement, indent=0):
    prefix = "  " * indent
    kind = statement["kind"]
    if kind == "assignment":
        first, operator, second = statement["expression"]
        expression = f"{first} {operator} {second}" if operator else first
        return [f"{prefix}{statement['name']} : {expression} end"]
    if kind == "declaration":
        first, operator, second = statement["expression"]
        expression = f"{first} {operator} {second}" if operator else first
        return [f"{prefix}{statement['type']} {statement['name']} : {expression} end"]
    if kind == "bet_declaration":
        return [
            f"{prefix}bet {statement['name']} := {statement['left']} {statement['right']} end"
        ]
    if kind == "output":
        first, operator, second = statement["expression"]
        expression = f"{first} {operator} {second}" if operator else first
        return [f"{prefix}out {expression} end"]
    if kind == "conditional":
        condition = " ".join(statement["condition"])
        lines = [f"{prefix}{statement['keyword']} {condition}"]
        for child in statement["body"]:
            lines.extend(_render_statement(child, indent + 1))
        lines.append(f"{prefix}{statement['keyword']}_end")
        return lines
    return []


def _set_phase_status(detailed_phases, lexical, syntax, semantic):
    detailed_phases["phase_status"] = {
        "lexical": lexical,
        "syntax": syntax,
        "semantic": semantic,
    }


# ---- Main compiler entry point ------------------------------------------

def evaluate_compiler_logic(blocks):
    if not blocks:
        return ["Error: No blocks in workspace.", "Status: COMPILATION FAILED"], {}

    # Block coordinates belong to the persistent blueprint canvas, not to the
    # current viewport. Resizing the window or panning must not invalidate a
    # program that is still present in the workspace.
    valid_blocks = [block for block in blocks if not block.is_template]
    if not valid_blocks:
        return ["Error: No blocks in valid blueprint area.", "Status: COMPILATION FAILED"], {}

    reorganize_nesting(valid_blocks)
    tokens = extract_tokens_with_nesting(valid_blocks)
    if not tokens:
        return ["Error: No valid tokens.", "Status: COMPILATION FAILED"], {}

    results = []
    detailed_phases = {
        "lexical": [],
        "syntax": [],
        "semantic": [],
        "recovery": [],
        "symbol_table": [],
        "phase_status": {},
    }

    detailed_phases["lexical"].append("PHASE: LEXICAL ANALYSIS")
    detailed_phases["lexical"].append(f"Tokens: {' '.join(tokens)}")
    lexical_errors = lexical_analysis(tokens)
    if lexical_errors:
        results.extend(lexical_errors)
        results.append("Status: LEXICAL ANALYSIS FAILED")
        detailed_phases["lexical"].extend(lexical_errors)
        detailed_phases["lexical"].append("Result: [FAILED]")
        detailed_phases["recovery"] = get_recovery_strategies("lexical_invalid_token")
        _set_phase_status(detailed_phases, False, False, False)
        return results, detailed_phases

    for position, token in enumerate(tokens, start=1):
        if token in SEPARATORS:
            token_kind = "Separator"
        elif token in OPERATORS:
            token_kind = "Operator"
        elif token in KEYWORDS:
            token_kind = "Keyword"
        elif get_literal_type(token):
            token_kind = f"Literal ({get_literal_type(token)})"
        else:
            token_kind = "Identifier"
        detailed_phases["lexical"].append(f"  [{position}] '{token}' -> {token_kind}")
    detailed_phases["lexical"].append("Result: [PASSED]")
    results.append("Checking Lexical... OK")

    detailed_phases["syntax"].append("PHASE: SYNTAX ANALYSIS")
    try:
        statements = parse_program(tokens)
    except ParseError as error:
        results.append(f"Syntax Error [{error.position + 1}]: {error.message}")
        results.append("Status: SYNTAX ANALYSIS FAILED")
        detailed_phases["syntax"].append(
            f"ERROR [{error.position + 1}]: {error.message}"
        )
        detailed_phases["syntax"].append("Result: [FAILED]")
        recovery = (
            "syntax_missing_end"
            if "end" in error.message.lower() or "close" in error.message.lower()
            else "syntax_invalid_start"
        )
        detailed_phases["recovery"] = get_recovery_strategies(recovery)
        _set_phase_status(detailed_phases, True, False, False)
        return results, detailed_phases

    detailed_phases["syntax"].append(
        f"Program structure validation: {len(statements)} statement(s)"
    )
    detailed_phases["syntax"].extend(
        f"  Statement {number}: {line}"
        for number, statement in enumerate(statements, start=1)
        for line in _render_statement(statement)
    )
    detailed_phases["syntax"].append("Result: [PASSED]")
    results.append("Checking Syntax... OK")

    detailed_phases["semantic"].append("PHASE: SEMANTIC ANALYSIS")
    try:
        output_results, symbols = _run_program(statements, detailed_phases)
    except SemanticError as error:
        results.append(f"Semantic Error [{error.position + 1}]: {error.message}")
        results.append("Status: SEMANTIC ANALYSIS FAILED")
        detailed_phases["semantic"].append(
            f"ERROR [{error.position + 1}]: {error.message}"
        )
        detailed_phases["semantic"].append("Result: [FAILED]")
        detailed_phases["recovery"] = get_recovery_strategies(error.recovery)
        _set_phase_status(detailed_phases, True, True, False)
        return results, detailed_phases

    detailed_phases["symbol_table"] = symbols
    detailed_phases["semantic"].append("Result: [PASSED]")
    compiled_lines = [
        line for statement in statements for line in _render_statement(statement)
    ]
    results.append("Checking Semantical... OK")
    results.append("Compiled Output:")
    results.extend(compiled_lines)
    results.extend(output_results)
    results.append("Status: COMPILATION SUCCESS")
    results.append("Program executed successfully!")
    _set_phase_status(detailed_phases, True, True, True)
    return results, detailed_phases
