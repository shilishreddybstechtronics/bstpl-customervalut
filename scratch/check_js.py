import re

def check_file(filepath):
    print(f"=== Checking {filepath} ===")
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    m = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
    if not m:
        print('No script tag found!')
        return

    js = m.group(1)
    start_line = html[:m.start(1)].count('\n') + 1
    print(f'Script starts at line {start_line}')

    stack = []
    in_sl_comment = False
    in_ml_comment = False
    in_single_quote = False
    in_double_quote = False
    in_regex = False
    template_stack = []

    lines = js.split('\n')
    errors = []
    prev_non_ws = ''

    for line_idx, line in enumerate(lines):
        cur_line = start_line + line_idx
        col = 0
        while col < len(line):
            ch = line[col]
            if (in_single_quote or in_double_quote or in_regex) and ch == '\\':
                col += 2
                continue
            if in_sl_comment:
                break
            elif in_ml_comment:
                if ch == '*' and col + 1 < len(line) and line[col+1] == '/':
                    in_ml_comment = False
                    col += 2
                    prev_non_ws = '/'
                    continue
                col += 1
                continue
            elif in_single_quote:
                if ch == "'":
                    in_single_quote = False
                    prev_non_ws = "'"
                col += 1
                continue
            elif in_double_quote:
                if ch == '"':
                    in_double_quote = False
                    prev_non_ws = '"'
                col += 1
                continue
            elif in_regex:
                if ch == '/':
                    in_regex = False
                    prev_non_ws = '/'
                col += 1
                continue
            
            # Normal code or template
            if ch == '/' and col + 1 < len(line) and line[col+1] == '/':
                in_sl_comment = True
                break
            elif ch == '/' and col + 1 < len(line) and line[col+1] == '*':
                in_ml_comment = True
                col += 2
                continue
            elif ch == '/':
                # check if division or regex
                if prev_non_ws in '(=,:[!&|?{;~^+-%*<>':
                    in_regex = True
                    col += 1
                    continue
            elif ch == "'":
                in_single_quote = True
                col += 1
                continue
            elif ch == '"':
                in_double_quote = True
                col += 1
                continue
            elif ch == '`':
                if template_stack and template_stack[-1] == '`':
                    template_stack.pop()
                    prev_non_ws = '`'
                else:
                    template_stack.append('`')
                col += 1
                continue
            
            if template_stack and template_stack[-1] == '`':
                if ch == '\\':
                    col += 2
                    continue
                if ch == '$' and col + 1 < len(line) and line[col+1] == '{':
                    template_stack.append('${')
                    stack.append(('${', cur_line, col))
                    col += 2
                    continue
                col += 1
                continue
            
            # Normal JS code
            if not ch.isspace():
                prev_non_ws = ch

            if ch in '({[':
                stack.append((ch, cur_line, col))
            elif ch in ')}]':
                if not stack:
                    errors.append(f'Unmatched closing {ch} at line {cur_line}:{col}')
                else:
                    top, l, c = stack.pop()
                    if (top == '(' and ch != ')') or (top == '[' and ch != ']') or ((top == '{' or top == '${') and ch != '}'):
                        errors.append(f'Mismatched closing {ch} at line {cur_line}:{col}, opened {top} at line {l}:{c}')
                    if top == '${':
                        if template_stack and template_stack[-1] == '${':
                            template_stack.pop()
            col += 1
        in_sl_comment = False
        if in_single_quote:
            errors.append(f'Unterminated single quote at end of line {cur_line}')
            in_single_quote = False
        if in_double_quote:
            errors.append(f'Unterminated double quote at end of line {cur_line}')
            in_double_quote = False
        if in_regex:
            errors.append(f'Unterminated regex at end of line {cur_line}')
            in_regex = False

    print(f'Done scanning. Remaining stack: {len(stack)}, Errors: {len(errors)}')
    for err in errors[:20]:
        print('Error:', err)
    if stack:
        print('Unclosed opened tokens (last 10):')
        for top, l, c in stack[-10:]:
            print(f'  {top} from line {l}:{c}')

check_file('frontend/index.html')
check_file('frontend/dashboard.html')
