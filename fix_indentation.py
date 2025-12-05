#!/usr/bin/env python3
"""Fix indentation issues in test files"""

with open("listings/tests.py", "r") as f:
    lines = f.readlines()

fixed_lines = []
in_commented_block = False

for i, line in enumerate(lines):
    # Check if we're in a commented block
    stripped = line.lstrip()
    if stripped.startswith("#"):
        in_commented_block = True
        fixed_lines.append(line)
    elif in_commented_block and (
        stripped.startswith('"city"') or stripped.startswith('"zipcode"')
    ):
        # Fix uncommented lines in commented blocks
        indent = len(line) - len(line.lstrip())
        fixed_lines.append(" " * indent + "#         " + stripped)
    else:
        if stripped and not stripped.startswith("#"):
            in_commented_block = False
        fixed_lines.append(line)

with open("listings/tests.py", "w") as f:
    f.writelines(fixed_lines)

print("Fixed indentation issues")
