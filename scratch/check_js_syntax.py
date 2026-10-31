import sys

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find all script tags
import re

for m in re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script>', content, re.IGNORECASE):
    attrs = m.group(1)
    if 'src=' in attrs:
        continue
    script_content = m.group(2)
    start_pos = m.start(2)
    # calculate line and col
    lines_before = content[:start_pos].split('\n')
    script_start_line = len(lines_before)
    
    print(f"Checking script tag starting at line {script_start_line} (length {len(script_content)} chars)...")
    
    # Character by character scan
    i = 0
    line = script_start_line
    col = len(lines_before[-1]) + 1
    
    state = 'NORMAL' # NORMAL, SINGLE_QUOTE, DOUBLE_QUOTE, TEMPLATE_LITERAL, LINE_COMMENT, BLOCK_COMMENT
    escape = False
    quote_start_line = 0
    quote_start_col = 0
    
    while i < len(script_content):
        c = script_content[i]
        
        if c == '\n':
            line += 1
            col = 1
            if state in ('SINGLE_QUOTE', 'DOUBLE_QUOTE'):
                if not escape:
                    print(f"ERROR: Unterminated string literal started at line {quote_start_line}, col {quote_start_col}! Encountered newline at line {line-1}")
                    # print context
                    sub_lines = content.split('\n')
                    print(f"Line {quote_start_line}: {sub_lines[quote_start_line-1]}")
                    state = 'NORMAL'
            elif state == 'LINE_COMMENT':
                state = 'NORMAL'
            escape = False
            i += 1
            continue
        
        col += 1
        
        if state == 'NORMAL':
            if c == '/' and i + 1 < len(script_content):
                next_c = script_content[i+1]
                if next_c == '/':
                    state = 'LINE_COMMENT'
                    i += 2
                    col += 1
                    continue
                elif next_c == '*':
                    state = 'BLOCK_COMMENT'
                    i += 2
                    col += 1
                    continue
            if c == "'":
                state = 'SINGLE_QUOTE'
                quote_start_line = line
                quote_start_col = col - 1
            elif c == '"':
                state = 'DOUBLE_QUOTE'
                quote_start_line = line
                quote_start_col = col - 1
            elif c == '`':
                state = 'TEMPLATE_LITERAL'
                quote_start_line = line
                quote_start_col = col - 1
        elif state == 'SINGLE_QUOTE':
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == "'":
                state = 'NORMAL'
        elif state == 'DOUBLE_QUOTE':
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == '"':
                state = 'NORMAL'
        elif state == 'TEMPLATE_LITERAL':
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == '`':
                state = 'NORMAL'
        elif state == 'BLOCK_COMMENT':
            if c == '*' and i + 1 < len(script_content) and script_content[i+1] == '/':
                state = 'NORMAL'
                i += 2
                col += 1
                continue
                
        i += 1
        
    print(f"Finished script starting at line {script_start_line}, final state: {state}")

