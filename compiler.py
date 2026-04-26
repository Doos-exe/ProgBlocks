import shared
from constants import KEYWORDS, OPERATORS, SEPARATORS, WORKSPACE_LEFT, WORKSPACE_RIGHT_MARGIN


# ---- Token validators ----

def is_valid_identifier(name):
    try:
        if not name:
            return False
        if not (name[0].isalpha() or name[0] == '_'):
            return False
        if name in KEYWORDS:
            return False
        return all(c.isalnum() or c == '_' for c in name)
    except Exception:
        return False


def get_literal_type(literal):
    try:
        stripped = literal.strip('"\'')
        if stripped.lower() in ('real', 'fake'):
            return 'bet'
        if stripped.isdigit():
            return 'digit'
        if (literal.startswith('"') and literal.endswith('"') and len(literal) >= 2) or \
           (literal.startswith("'") and literal.endswith("'") and len(literal) >= 2):
            return 'word'
    except Exception:
        pass
    return None


def is_valid_token(token):
    if token in KEYWORDS or token in OPERATORS or token in SEPARATORS:
        return True
    if get_literal_type(token):
        return True
    if is_valid_identifier(token):
        return True
    return False


# ---- Lexical analysis ----

def lexical_analysis(tokens):
    errors = []
    for i, token in enumerate(tokens):
        if not is_valid_token(token):
            if get_literal_type(token) is None and not is_valid_identifier(token):
                errors.append(f"Lexical Error [{i+1}]: Variable '{token}' not found")
            else:
                errors.append(f"Lexical Error [{i+1}]: Invalid token '{token}'")
    return errors


# ---- Recovery strategies ----

def get_recovery_strategies(error_type, error_details):
    strategies = {
        "lexical_invalid_token": [
            "RECOVERY STRATEGIES:",
            "1. Check token spelling and capitalization",
            "2. Use valid keywords: digit, word, bet, out, end, :, adds, minus, mul, div",
            "3. Variable names must start with letter or underscore",
            "4. Numbers must be wrapped in quotes for string/word types",
            "5. Strings must use double quotes: \"hello\"",
            "6. Booleans must be: true or false",
        ],
        "syntax_missing_end": [
            "RECOVERY STRATEGIES:",
            "1. Every program must end with 'end' block",
            "2. Block structure: TYPE NAME : VALUE end",
            "3. Output structure: out VALUE end",
            "4. Add missing 'end' terminator at the conclusion",
            "5. Chain blocks together: drag and connect visually",
        ],
        "syntax_invalid_start": [
            "RECOVERY STRATEGIES:",
            "1. Programs must start with: digit, word, bet, or out",
            "2. digit = numeric variable declaration",
            "3. word = string variable declaration",
            "4. bet = boolean variable declaration",
            "5. out = output/print statement",
            "6. Start with a declaration or output block",
        ],
        "semantic_type_mismatch": [
            "RECOVERY STRATEGIES:",
            "1. Match value type to declared type",
            "2. digit expects numbers: 42, 3, 100",
            "3. word expects quoted strings: \"hello\", \"world\"",
            "4. bet expects boolean: true or false",
            "5. Check quotes around string values",
            "6. Numbers don't need quotes for digit type",
        ],
        "semantic_undefined_identifier": [
            "RECOVERY STRATEGIES:",
            "1. Declare variable before using in output",
            "2. Variable names are case-sensitive",
            "3. Check spelling of variable names",
            "4. Declare with: digit, word, or bet first",
            "5. Use full declaration: TYPE NAME : VALUE end",
            "6. Then output with: out VARNAME end",
        ],
        "semantic_invalid_declaration": [
            "RECOVERY STRATEGIES:",
            "1. Declaration format: TYPE NAME : VALUE end",
            "2. Replace TYPE with: digit, word, or bet",
            "3. NAME must be valid identifier",
            "4. VALUE must match the TYPE",
            "5. : and end are required separators",
            "6. Example: digit count : 5 end",
        ],
    }
    return strategies.get(error_type, ["No recovery strategies available for this error"])


# ---- Nesting helpers ----

def is_block_inside_conditional(block, conditional_block):
    if conditional_block.category != "Conditional":
        return False
    if conditional_block.body_blocks:
        body_height = sum(b.rect.height + 2 for b in conditional_block.body_blocks) + 20
        total_height = conditional_block.rect.height + body_height
    else:
        total_height = conditional_block.rect.height + 40
    total_height_with_buffer = total_height + 100
    body_left   = conditional_block.rect.x + 10
    body_top    = conditional_block.rect.y + conditional_block.rect.height + 5
    body_bottom = conditional_block.rect.y + total_height_with_buffer
    return (block.rect.centerx >= body_left and
            body_top <= block.rect.centery <= body_bottom)


def reorganize_nesting(placed_blocks):
    for block in placed_blocks:
        block.parent_conditional = None
    for cond in placed_blocks:
        if cond.category == "Conditional":
            cond.body_blocks.clear()

    for block in placed_blocks:
        if block.category == "Conditional" or block.in_condition_of is not None:
            continue
        for cond in placed_blocks:
            if cond.category == "Conditional" and cond != block:
                if is_block_inside_conditional(block, cond):
                    block.parent_conditional = cond
                    break

    for block in placed_blocks:
        if block.in_condition_of is not None:
            continue
        if block.parent_conditional is not None:
            if (block.prev_block is not None and
                    block.prev_block.parent_conditional != block.parent_conditional):
                block.prev_block.next_block = None
                block.prev_block = None

    for block in placed_blocks:
        if block.in_condition_of is not None:
            continue
        if block.parent_conditional is not None:
            cond = block.parent_conditional
            if block.prev_block is None or block.prev_block.parent_conditional != cond:
                if block not in cond.body_blocks:
                    cond.body_blocks.append(block)

    for cond in placed_blocks:
        if cond.category == "Conditional":
            cond.update_position(cond.rect.x, cond.rect.y)


# ---- Token extraction ----

def extract_tokens_with_nesting(blocks):
    tokens = []

    def traverse_block(block):
        if block.is_template or block.in_condition_of is not None:
            return
        if block in [b for cond in blocks
                     if cond.category == "Conditional"
                     for b in cond.body_blocks
                     if cond.parent_conditional]:
            return
        tokens.append(block.text.strip())
        if block.category == "Conditional" and block.condition_blocks:
            for cb in block.condition_blocks:
                tokens.append(cb.text.strip())
        if block.category == "Conditional" and block.body_blocks:
            for body_block in block.body_blocks:
                traverse_block(body_block)
            tokens.append(block.text + "_end")
        if block.next_block:
            traverse_block(block.next_block)

    chain_starts = [
        b for b in blocks
        if b.prev_block is None
        and b.parent_conditional is None
        and b.in_condition_of is None
        and not b.is_template
    ]
    chain_starts.sort(key=lambda b: (b.rect.y, b.rect.x))
    for start in chain_starts:
        traverse_block(start)
    return tokens


# ---- Main compiler entry point ----

def evaluate_compiler_logic(blocks):
    if not blocks:
        return ["Error: No blocks in workspace.", "Status: COMPILATION FAILED"], {}

    valid_blocks = [
        b for b in blocks
        if (b.rect.x >= WORKSPACE_LEFT and
            b.rect.x + b.rect.width <= shared.WIDTH - WORKSPACE_RIGHT_MARGIN and
            b.rect.y >= shared.workspace_top and
            b.rect.y + b.rect.height <= shared.workspace_bottom)
    ]
    if not valid_blocks:
        return ["Error: No blocks in valid blueprint area.", "Status: COMPILATION FAILED"], {}

    reorganize_nesting(valid_blocks)

    chain_starts = [b for b in valid_blocks
                    if b.prev_block is None and b.parent_conditional is None]
    if not chain_starts:
        return ["Error: No valid blocks found.", "Status: COMPILATION FAILED"], {}

    chain_starts.sort(key=lambda b: (b.rect.y, b.rect.x))

    tokens = extract_tokens_with_nesting(valid_blocks)
    if not tokens:
        return ["Error: No valid tokens.", "Status: COMPILATION FAILED"], {}

    results = []
    compiled_lines = []
    output_results = []
    detailed_phases = {
        "lexical": [], "syntax": [], "semantic": [],
        "recovery": [], "symbol_table": [], "phase_status": {}
    }

    # -- Lexical --
    lexical_errors = lexical_analysis(tokens)
    if lexical_errors:
        results.extend(lexical_errors)
        results.append("Status: LEXICAL ANALYSIS FAILED")
        detailed_phases["lexical"] = ["PHASE: LEXICAL ANALYSIS"] + lexical_errors
        detailed_phases["lexical"].append("Result: [FAILED]")
        detailed_phases["recovery"] = get_recovery_strategies("lexical_invalid_token", "")
        return results, detailed_phases

    detailed_phases["lexical"].append("PHASE: LEXICAL ANALYSIS")
    detailed_phases["lexical"].append(f"Tokens: {' '.join(tokens)}")
    for i, token in enumerate(tokens):
        if token in KEYWORDS:
            detailed_phases["lexical"].append(f"  [{i+1}] '{token}' -> Keyword")
        elif token in OPERATORS:
            detailed_phases["lexical"].append(f"  [{i+1}] '{token}' -> Operator")
        elif token in SEPARATORS:
            detailed_phases["lexical"].append(f"  [{i+1}] '{token}' -> Separator")
        else:
            lt = get_literal_type(token)
            if lt:
                detailed_phases["lexical"].append(f"  [{i+1}] '{token}' -> Literal ({lt})")
            else:
                detailed_phases["lexical"].append(f"  [{i+1}] '{token}' -> Identifier")
    detailed_phases["lexical"].append("Result: [PASSED]")
    results.append("Checking Lexical... OK")

    # -- Syntax --
    detailed_phases["syntax"].append("PHASE: SYNTAX ANALYSIS")
    if tokens[-1] != "end":
        results.append("Syntax Error: Missing 'end' terminator")
        results.append("Status: SYNTAX ANALYSIS FAILED")
        detailed_phases["syntax"].append("ERROR: Missing 'end' terminator")
        detailed_phases["syntax"].append("Result: [FAILED]")
        detailed_phases["recovery"] = get_recovery_strategies("syntax_missing_end", "")
        return results, detailed_phases
    elif tokens[0] not in ('digit', 'word', 'bet', 'out'):
        results.append(f"Syntax Error: Invalid start token '{tokens[0]}'")
        results.append("Status: SYNTAX ANALYSIS FAILED")
        detailed_phases["syntax"].append(f"ERROR: Invalid start token '{tokens[0]}'")
        detailed_phases["syntax"].append("Result: [FAILED]")
        detailed_phases["recovery"] = get_recovery_strategies("syntax_invalid_start", tokens[0])
        return results, detailed_phases

    for i, token in enumerate(tokens):
        if token in KEYWORDS and i > 0 and tokens[i-1] in ('digit', 'word', 'bet'):
            results.append(f"Syntax Error [{i+1}]: Cannot use keyword '{token}' as identifier")
            results.append("Status: SYNTAX ANALYSIS FAILED")
            detailed_phases["syntax"].append(
                f"ERROR: Keyword '{token}' cannot be used as identifier at position {i+1}")
            detailed_phases["syntax"].append("Result: [FAILED]")
            detailed_phases["recovery"] = get_recovery_strategies("syntax_invalid_start", "")
            return results, detailed_phases

    detailed_phases["syntax"].append(f"Program structure validation:")
    detailed_phases["syntax"].append(f"  Total tokens: {len(tokens)}")
    statement_start = 0
    statement_num = 1
    for i, token in enumerate(tokens):
        if token == 'end':
            statement_tokens = tokens[statement_start:i+1]
            if statement_tokens:
                first = statement_tokens[0]
                last  = statement_tokens[-1]
                stmt_str = ' '.join(statement_tokens)
                if first in ('digit', 'word', 'bet', 'out') and last == 'end':
                    detailed_phases["syntax"].append(
                        f"  Statement {statement_num}: {stmt_str} - [VALID]")
                else:
                    results.append(f"Syntax Error: Invalid statement structure at Statement {statement_num}")
                    results.append(f"Statement {statement_num}: {stmt_str}")
                    results.append("Expected: [KEYWORD/OUT] [ARGS...] end")
                    results.append("Status: SYNTAX ANALYSIS FAILED")
                    detailed_phases["syntax"].append(
                        f"ERROR: Invalid statement structure at Statement {statement_num}")
                    detailed_phases["syntax"].append(f"  First token: '{first}' - expected keyword")
                    detailed_phases["syntax"].append(f"  Last token: '{last}' - expected 'end'")
                    detailed_phases["syntax"].append("Result: [FAILED]")
                    detailed_phases["recovery"] = get_recovery_strategies("syntax_invalid_start", "")
                    return results, detailed_phases
                statement_num += 1
            statement_start = i + 1

    detailed_phases["syntax"].append("Result: [PASSED]")
    results.append("Checking Syntax... OK")

    # -- Semantic --
    variables = {}
    variable_types = {}
    memory_offset = 0
    offset_sizes = {'digit': 4, 'word': 1, 'bet': 2}
    error_occurred = False
    detailed_phases["semantic"].append("PHASE: SEMANTIC ANALYSIS")

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ('digit', 'word', 'bet'):
            # bet comparison pattern: bet NAME := V1 V2 end
            if (token == 'bet' and i + 5 < len(tokens)
                    and tokens[i+2] == ':=' and tokens[i+5] == 'end'):
                var_name = tokens[i+1]
                value1   = tokens[i+3]
                value2   = tokens[i+4]

                if var_name in KEYWORDS or var_name in OPERATORS or var_name in SEPARATORS:
                    kind = "keyword" if var_name in KEYWORDS else "reserved symbol"
                    results.append(f"Semantic Error [{i+2}]: '{var_name}' is a {kind}, cannot use as variable name")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: {kind.capitalize()} '{var_name}' cannot be used as variable name")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "")
                    break

                if '"' in var_name or "'" in var_name or not is_valid_identifier(var_name):
                    results.append(f"Semantic Error [{i+2}]: Invalid variable name '{var_name}'")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Invalid variable name at token {i+2}")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "")
                    break

                if var_name in variables:
                    results.append(f"Semantic Error [{i+2}]: Variable '{var_name}' already declared")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Duplicate variable name '{var_name}'")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "")
                    break

                def resolve_value(val, pos):
                    if val in variables:
                        return variables[val], None
                    lt = get_literal_type(val)
                    if lt == 'digit':
                        try:
                            return int(val.strip('"\'')), None
                        except Exception:
                            return float(val.strip('"\'')), None
                    elif lt == 'word':
                        return val.strip('"\''), None
                    elif lt == 'bet':
                        return val.strip('"\'').lower() == 'real', None
                    else:
                        msg = (f"Semantic Error [{pos}]: Variable '{val}' not found"
                               if is_valid_identifier(val)
                               else f"Semantic Error [{pos}]: Invalid value '{val}'")
                        return None, msg

                val1, err1 = resolve_value(value1, i+3)
                if err1:
                    results.append(err1)
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Cannot resolve value at token {i+3}")
                    break
                val2, err2 = resolve_value(value2, i+4)
                if err2:
                    results.append(err2)
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Cannot resolve value at token {i+4}")
                    break

                variables[var_name] = (val1 == val2)
                variable_types[var_name] = 'bet'
                compiled_lines.append(f"bet {var_name} := {value1} {value2} end")
                detailed_phases["semantic"].append(f"  Comparison: bet {var_name} := {value1} {value2}")
                bet_result = "Real" if variables[var_name] else "Fake"
                detailed_phases["semantic"].append(
                    f"    Variable '{var_name}' assigned comparison result: {bet_result} (type: bet)")
                detailed_phases["symbol_table"].append(
                    f"{var_name:<20} {'bet':<15} {0:<12} {memory_offset}")
                memory_offset += offset_sizes.get('bet', 0)
                i += 6
                continue

            # Standard declaration: TYPE NAME : VALUE [OP VALUE2] end
            has_op = (i + 6 < len(tokens) and tokens[i+2] == ':'
                      and tokens[i+4] in ('adds', 'minus', 'mul', 'div')
                      and tokens[i+6] == 'end')

            if not has_op:
                if not (i + 4 < len(tokens) and tokens[i+2] == ':' and tokens[i+4] == 'end'):
                    if not (i + 6 < len(tokens) and tokens[i+4] in ('adds', 'minus')):
                        results.append(
                            f"Semantic Error [{i+1}]: Invalid declaration - expected ID : VALUE end")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Invalid declaration at token {i+1}")
                        detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "")
                        break

            var_name  = tokens[i+1]
            value     = tokens[i+3]
            exp_type  = token
            val_strip = value.strip('"\'')
            value2    = tokens[i+5] if has_op else None
            val2_strip= value2.strip('"\'') if value2 else None

            # Validate variable name
            for check, kind in [
                (var_name in KEYWORDS, "keyword"),
                (var_name in OPERATORS or var_name in SEPARATORS,
                 "mathematical keyword" if var_name in ('adds', 'minus') else "reserved symbol"),
                ('"' in var_name or "'" in var_name, "quoted name"),
                (not is_valid_identifier(var_name), "invalid identifier"),
            ]:
                if check:
                    results.append(f"Semantic Error [{i+2}]: '{var_name}' is a {kind}, cannot use as variable name")
                    error_occurred = True
                    detailed_phases["semantic"].append(
                        f"ERROR: {kind.capitalize()} '{var_name}' cannot be used as variable name")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "")
                    break
            if error_occurred:
                break

            if var_name in variables:
                results.append(f"Semantic Error [{i+2}]: Variable '{var_name}' already declared")
                error_occurred = True
                detailed_phases["semantic"].append(f"ERROR: Duplicate variable name '{var_name}'")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "")
                break

            # Type-check value
            actual_type = get_literal_type(value)
            if actual_type is None:
                if is_valid_identifier(value):
                    if value not in variables:
                        results.append(f"Semantic Error [{i+3}]: Variable '{value}' not found")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Undefined variable '{value}'")
                        detailed_phases["recovery"] = get_recovery_strategies("semantic_undefined_identifier", value)
                        break
                    actual_type = variable_types.get(value, exp_type)
                else:
                    results.append(f"Semantic Error [{i+3}]: Variable '{value}' not found")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Invalid value or undefined variable '{value}'")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_undefined_identifier", value)
                    break

            if actual_type != exp_type:
                results.append(f"Semantic Error [{i+3}]: Type mismatch - expected {exp_type}, got {actual_type or 'invalid'}")
                error_occurred = True
                detailed_phases["semantic"].append(
                    f"ERROR: Type mismatch at '{var_name}' - expected {exp_type}, got {actual_type}")
                detailed_phases["recovery"] = get_recovery_strategies("semantic_type_mismatch", "")
                break

            if has_op:
                actual_type2 = get_literal_type(value2)
                if actual_type2 is None:
                    if is_valid_identifier(value2):
                        if value2 not in variables:
                            results.append(f"Semantic Error [{i+5}]: Variable '{value2}' not found")
                            error_occurred = True
                            detailed_phases["semantic"].append(f"ERROR: Undefined variable '{value2}'")
                            detailed_phases["recovery"] = get_recovery_strategies("semantic_undefined_identifier", value2)
                            break
                        actual_type2 = variable_types.get(value2, exp_type)
                    else:
                        results.append(f"Semantic Error [{i+5}]: Variable '{value2}' not found")
                        error_occurred = True
                        detailed_phases["semantic"].append(f"ERROR: Invalid value or undefined variable '{value2}'")
                        detailed_phases["recovery"] = get_recovery_strategies("semantic_undefined_identifier", value2)
                        break

                if actual_type2 != exp_type:
                    results.append(f"Semantic Error [{i+5}]: Type mismatch in operation - expected {exp_type}, got {actual_type2 or 'invalid'}")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Type mismatch in operation")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_type_mismatch", "")
                    break

                op = tokens[i+4]
                if op in ('minus', 'div') and exp_type == 'word':
                    results.append(f"Semantic Error [{i+4}]: {op.capitalize()} operation is not supported for word type")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: {op.capitalize()} cannot be used with word type")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_type_mismatch", "")
                    break

            # Evaluate and bind
            op = tokens[i+4] if has_op else None

            def get_val(v, strip):
                if v in variables:
                    return variables[v]
                if exp_type == 'digit':
                    try:
                        return int(strip)
                    except Exception:
                        return float(strip)
                if exp_type == 'word':
                    return strip
                return strip.lower() == 'real'

            val1 = get_val(value, val_strip)
            if has_op:
                val2 = get_val(value2, val2_strip)
                if op == 'adds':
                    result = val1 + val2
                elif op == 'minus':
                    result = val1 - val2
                elif op == 'mul':
                    if exp_type == 'word':
                        try:
                            result = val1 * (int(val2) if isinstance(val2, str) else val2)
                        except Exception:
                            results.append(f"Semantic Error [{i+5}]: String multiplication requires numeric multiplier")
                            error_occurred = True
                            detailed_phases["semantic"].append("ERROR: String multiplication requires numeric multiplier")
                            break
                    else:
                        result = val1 * val2
                elif op == 'div':
                    if val2 == 0:
                        results.append(f"Semantic Error [{i+5}]: Division by zero")
                        error_occurred = True
                        detailed_phases["semantic"].append("ERROR: Division by zero")
                        break
                    result = val1 / val2
                variables[var_name] = result
            else:
                variables[var_name] = val1

            variable_types[var_name] = exp_type

            if has_op:
                compiled_lines.append(f"{exp_type} {var_name} : {value} {op} {value2} end")
                detailed_phases["semantic"].append(
                    f"  Declaration: {exp_type} {var_name} : {value} {op} {value2}")
                detailed_phases["semantic"].append(
                    f"    Variable '{var_name}' bound to value '{variables[var_name]}' (type: {exp_type})")
            else:
                compiled_lines.append(f"{exp_type} {var_name} : {value} end")
                detailed_phases["semantic"].append(f"  Declaration: {exp_type} {var_name} : {value}")
                detailed_phases["semantic"].append(
                    f"    Variable '{var_name}' bound to value '{value}' (type: {exp_type})")

            detailed_phases["symbol_table"].append(
                f"{var_name:<20} {exp_type:<15} {0:<12} {memory_offset}")
            memory_offset += offset_sizes.get(exp_type, 0)
            i += 7 if has_op else 5

        elif token == 'out':
            has_out_op = (i + 4 < len(tokens)
                          and tokens[i+2] in ('adds', 'minus', 'mul', 'div')
                          and tokens[i+4] == 'end')
            if not has_out_op:
                if i + 2 >= len(tokens) or tokens[i+2] != 'end':
                    results.append(
                        f"Semantic Error [{i+1}]: Invalid output - expected out VALUE end")
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Invalid output statement at token {i+1}")
                    detailed_phases["recovery"] = get_recovery_strategies("semantic_invalid_declaration", "")
                    break

            out_val1 = tokens[i+1]

            if has_out_op:
                op      = tokens[i+2]
                out_val2= tokens[i+3]
                compiled_lines.append(f"out {out_val1} {op} {out_val2} end")

                def get_out_val(v, pos):
                    if v in variables:
                        return variables[v], None
                    lt = get_literal_type(v)
                    if lt == 'digit':
                        try:
                            return int(v.strip('"\'')), None
                        except Exception:
                            return float(v.strip('"\'')), None
                    elif lt == 'word':
                        return v.strip('"\''), None
                    return None, f"Semantic Error [{pos}]: Undefined identifier or invalid value '{v}'"

                val1, err1 = get_out_val(out_val1, i+1)
                if err1:
                    results.append(err1)
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Invalid output value '{out_val1}'")
                    break
                val2, err2 = get_out_val(out_val2, i+3)
                if err2:
                    results.append(err2)
                    error_occurred = True
                    detailed_phases["semantic"].append(f"ERROR: Invalid output value '{out_val2}'")
                    break

                if op == 'adds':
                    result = val1 + val2
                elif op == 'minus':
                    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                        result = val1 - val2
                    elif isinstance(val1, str) and isinstance(val2, str):
                        results.append(f"Semantic Error [{i+2}]: Minus operation is not supported for word type")
                        error_occurred = True
                        detailed_phases["semantic"].append("ERROR: Minus cannot be used with word type")
                        break
                    else:
                        results.append(f"Semantic Error [{i+1}]: Cannot use minus with mixed types")
                        error_occurred = True
                        detailed_phases["semantic"].append("ERROR: Type mismatch in minus operation")
                        break
                elif op == 'mul':
                    result = val1 * val2
                elif op == 'div':
                    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                        if val2 == 0:
                            results.append(f"Semantic Error [{i+3}]: Division by zero")
                            error_occurred = True
                            detailed_phases["semantic"].append("ERROR: Division by zero")
                            break
                        result = val1 / val2
                    else:
                        results.append(f"Semantic Error [{i+2}]: Division operation only works with digits")
                        error_occurred = True
                        detailed_phases["semantic"].append("ERROR: Division only works with digits")
                        break

                output_results.append(f"> {result}")
                detailed_phases["semantic"].append(
                    f"  Output: {out_val1} {op} {out_val2} = {result}")
                i += 5
            else:
                compiled_lines.append(f"out {out_val1} end")
                if out_val1 in variables:
                    out_v = variables[out_val1]
                    if isinstance(out_v, bool):
                        out_v = "Real" if out_v else "Fake"
                    output_results.append(f"> {out_v}")
                    detailed_phases["semantic"].append(
                        f"  Output: Variable '{out_val1}' = {out_v}")
                else:
                    lt = get_literal_type(out_val1)
                    if lt:
                        stripped = out_val1.strip('"\'')
                        if lt == 'digit':
                            try:
                                val = int(stripped)
                            except Exception:
                                val = float(stripped)
                            output_results.append(f"> {val}")
                            detailed_phases["semantic"].append(
                                f"  Output: Literal value '{val}' (type: {lt})")
                        elif lt == 'word':
                            output_results.append(f"> {stripped}")
                            detailed_phases["semantic"].append(
                                f"  Output: Literal string '{stripped}'")
                        else:
                            output_results.append(f"> {out_val1}")
                            detailed_phases["semantic"].append(
                                f"  Output: Literal value '{out_val1}'")
                    else:
                        results.append(
                            f"Semantic Error [{i+1}]: Undefined identifier '{out_val1}'")
                        error_occurred = True
                        detailed_phases["semantic"].append(
                            f"ERROR: Undefined identifier '{out_val1}'")
                        detailed_phases["recovery"] = get_recovery_strategies(
                            "semantic_undefined_identifier", out_val1)
                        break
                i += 3
        else:
            i += 1

    if not error_occurred:
        results.append("Checking Semantical... OK")
    if compiled_lines:
        results.append("Compiled Output:")
        results.extend(compiled_lines)
    if output_results:
        results.extend(output_results)

    if error_occurred:
        results.append("Status: SEMANTIC ANALYSIS FAILED")
        detailed_phases["semantic"].append("Result: [FAILED]")
    else:
        results.append("Status: COMPILATION SUCCESS")
        results.append("Program executed successfully!")
        detailed_phases["semantic"].append("Result: [PASSED]")

    detailed_phases["phase_status"] = {
        "lexical":  "PASSED" in " ".join(detailed_phases.get("lexical", [])),
        "syntax":   "PASSED" in " ".join(detailed_phases.get("syntax", [])),
        "semantic": "PASSED" in " ".join(detailed_phases.get("semantic", [])),
    }
    return results, detailed_phases
