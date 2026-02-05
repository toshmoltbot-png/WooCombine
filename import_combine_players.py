#!/usr/bin/env python3
"""
Import Spring 2024 12U Combine Results into Woo-Combine

Usage: python import_combine_players.py <event_id>
"""

import subprocess
import json
import sys
import csv
from io import StringIO

# Parse the Excel file
def get_players_from_excel():
    result = subprocess.run(
        ['npx', 'xlsx-cli', '/Users/tosh/Desktop/Spring 2024 12U Combine Results.xlsx'],
        capture_output=True, text=True, shell=False
    )
    
    csv_data = result.stdout.strip()
    if not csv_data:
        # Try with shell=True for npx
        result = subprocess.run(
            'npx xlsx-cli "/Users/tosh/Desktop/Spring 2024 12U Combine Results.xlsx"',
            capture_output=True, text=True, shell=True
        )
        csv_data = result.stdout.strip()
    
    # Remove BOM if present
    if csv_data.startswith('\ufeff'):
        csv_data = csv_data[1:]
    reader = csv.DictReader(StringIO(csv_data))
    
    players = []
    for row in reader:
        name = row.get('Name', '').strip()
        if not name:
            continue
        
        # Parse name into first/last
        parts = name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        # Get participant number as external_id
        external_id = row.get('Participants #', '').strip()
        
        # Get best scores (best attempt for each drill)
        try:
            broad_jump_1 = float(row.get('Broad Jump 1', 0) or 0)
            broad_jump_2 = float(row.get('Broad Jump 2', 0) or 0)
            broad_jump = max(broad_jump_1, broad_jump_2)  # Higher is better
        except:
            broad_jump = None
        
        try:
            pro_agility_1 = float(row.get('Pro Agility 1', 0) or 0)
            pro_agility_2 = float(row.get('Pro Agility 2', 0) or 0)
            # Lower is better, take best (lowest)
            pro_agility = min(pro_agility_1, pro_agility_2) if pro_agility_1 and pro_agility_2 else (pro_agility_1 or pro_agility_2)
        except:
            pro_agility = None
        
        try:
            forty_yard = float(row.get('40 Yard 1', 0) or 0)
        except:
            forty_yard = None
        
        try:
            star_rating = int(row.get('Star Rating', 0) or 0)
        except:
            star_rating = None
        
        player = {
            "first_name": first_name,
            "last_name": last_name,
            "external_id": external_id,
            "age_group": "12U",
            "number": int(external_id) if external_id.isdigit() else None,
            "scores": {}
        }
        
        # Add scores to scores map
        if broad_jump:
            player["scores"]["broad_jump"] = broad_jump
        if pro_agility:
            player["scores"]["pro_agility"] = pro_agility
        if forty_yard:
            player["scores"]["40m_dash"] = forty_yard  # Map to existing field
        if star_rating:
            player["scores"]["star_rating"] = star_rating
        
        players.append(player)
    
    return players

def main():
    if len(sys.argv) < 2:
        print("Usage: python import_combine_players.py <event_id>")
        print("\nParsed players from spreadsheet:")
        players = get_players_from_excel()
        print(json.dumps(players, indent=2))
        print(f"\nTotal: {len(players)} players")
        return
    
    event_id = sys.argv[1]
    players = get_players_from_excel()
    
    print(f"Uploading {len(players)} players to event {event_id}...")
    
    # Output the payload
    payload = {
        "event_id": event_id,
        "players": players,
        "method": "script",
        "filename": "Spring 2024 12U Combine Results.xlsx"
    }
    
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
