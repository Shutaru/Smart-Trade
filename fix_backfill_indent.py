# fix_backfill_indent.py - Fix indentation in routers/lab.py backfill function

print("?? Fixing backfill loop indentation...")

# This script fixes the backfill While loop's try-except structure
# The except blocks need proper indentation to match the inner try

# Read the file
with open('routers/lab.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the problematic section (around line 215-240)
# The except RateLimitExceeded and except NetworkError blocks need to be indented
# to be inside the while loop's try block

fixed_lines = []
in_while_loop = False
line_num = 0

for i, line in enumerate(lines):
    line_num = i + 1
    
    # Detect start of while loop
    if 'while current_since < request.until:' in line:
      in_while_loop = True
      fixed_lines.append(line)
        continue
    
    # Detect except blocks that are at wrong indentation level (outside while)
    if in_while_loop and line.strip().startswith('except RateLimitExceeded'):
        # This line should be indented to match the inner try (24 spaces = 3 levels of 8)
 fixed_lines.append('          except RateLimitExceeded:\n')
    continue
    
    if in_while_loop and line.strip().startswith('except NetworkError'):
        fixed_lines.append('             except NetworkError:\n')
        continue
    
    # Detect end of while loop (when we see Filter by range comment)
    if '# Filter by range' in line:
        in_while_loop = False
  
    # Keep all other lines as-is
  fixed_lines.append(line)

# Write back
with open('routers/lab.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("? Fixed! Now test with: python -c \"from routers.lab import router; print('OK')\"")
