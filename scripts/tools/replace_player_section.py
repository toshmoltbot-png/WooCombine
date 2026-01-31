#!/usr/bin/env python3
"""Replace the Player Upload Section in EventSetup.jsx"""

# Read the original file
with open("frontend/src/components/EventSetup.jsx", "r") as f:
    lines = f.readlines()

# Read the new section
with open("TEMP_NEW_PLAYER_SECTION.txt", "r") as f:
    new_section = f.read()

# Find start and end
start_line = None
end_line = None

for i, line in enumerate(lines):
    if "Step 3: Add Players Section" in line:
        start_line = i
    if start_line is not None and "Step 4: Invite Coaches & Share" in line:
        end_line = i - 1  # Line before Step 4
        break

if start_line is None or end_line is None:
    print("❌ Could not find section boundaries")
    exit(1)

print(f"📍 Found Step 3 section: lines {start_line + 1} to {end_line + 1} ({end_line - start_line + 1} lines)")
print(f"🔄 Replacing with new section ({len(new_section.splitlines())} lines)")

# Build new file
new_lines = lines[:start_line] + [new_section + "\n"] + lines[end_line + 1:]

# Write output
with open("frontend/src/components/EventSetup.jsx", "w") as f:
    f.writelines(new_lines)

print(f"✅ Replaced Player Upload Section!")
print(f"   Old: {end_line - start_line + 1} lines → New: {len(new_section.splitlines())} lines")
print(f"   Net reduction: {(end_line - start_line + 1) - len(new_section.splitlines())} lines")

