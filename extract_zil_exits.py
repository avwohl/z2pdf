#!/usr/bin/env python3
"""
Extract room exits from ZIL source files
"""

import re
import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path.home() / 'z2js'))
from zparser import ZParser


def extract_exits_from_zil(zil_file: str) -> Tuple[Dict[str, Dict[str, str]], Dict[str, str]]:
    """
    Extract room exits and names from ZIL source
    Returns: (exits_by_room_id, room_names)
    """
    exits_by_room = {}
    room_names = {}

    with open(zil_file, 'r', encoding='latin-1', errors='ignore') as f:
        content = f.read()

    # Find all ROOM definitions
    room_pattern = r'<ROOM\s+(\S+)\s*\n(.*?)(?=\n<(?:ROOM|OBJECT)|$)'
    rooms = re.findall(room_pattern, content, re.DOTALL)

    for room_id, room_body in rooms:
        # Extract description
        desc_match = re.search(r'\(DESC\s+"([^"]+)"\)', room_body)
        if desc_match:
            room_names[room_id] = desc_match.group(1)

        # Extract directional exits
        exits = {}
        for direction in ['NORTH', 'SOUTH', 'EAST', 'WEST', 'NE', 'NW', 'SE', 'SW', 'UP', 'DOWN', 'IN', 'OUT']:
            # Pattern: (DIRECTION TO TARGET) or (DIRECTION TO TARGET IF...)
            exit_pattern = rf'\({direction}\s+TO\s+(\S+)'
            match = re.search(exit_pattern, room_body)
            if match:
                target = match.group(1).rstrip(')')
                exits[direction.lower()] = target

        if exits:
            exits_by_room[room_id] = exits

    return exits_by_room, room_names


def map_room_names_to_numbers(z3_file: str, room_names: Dict[str, str]) -> Dict[str, int]:
    """
    Map room IDs to object numbers by matching names
    """
    with open(z3_file, 'rb') as f:
        data = f.read()

    parser = ZParser(data)

    # Build a map from lowercased name fragments to object numbers
    room_name_to_num = {}

    for room_num in range(142, 300):
        try:
            obj_name = parser.get_object_name(room_num)
            if obj_name:
                # Clean up the name
                clean_name = obj_name.lower().strip()
                room_name_to_num[clean_name] = room_num
        except:
            pass

    # Now map ZIL room IDs to object numbers
    zil_to_objnum = {}

    for room_id, desc in room_names.items():
        desc_lower = desc.lower()

        # Try exact match first
        if desc_lower in room_name_to_num:
            zil_to_objnum[room_id] = room_name_to_num[desc_lower]
            continue

        # Try fuzzy match
        for obj_name, obj_num in room_name_to_num.items():
            # Check if names are similar enough
            if desc_lower in obj_name or obj_name in desc_lower:
                zil_to_objnum[room_id] = obj_num
                break

    return zil_to_objnum


if __name__ == '__main__':
    zil_file = str(Path.home() / 'zorkie/test-games/zork1/1dungeon.zil')
    z3_file = str(Path.home() / 'zorkie/zork1-final.z3')

    exits_by_room, room_names = extract_exits_from_zil(zil_file)
    zil_to_objnum = map_room_names_to_numbers(z3_file, room_names)

    print(f'Extracted {len(exits_by_room)} rooms with exits')
    print(f'Mapped {len(zil_to_objnum)} room IDs to object numbers')

    # Show some examples
    print('\nExample mappings:')
    for room_id in list(zil_to_objnum.keys())[:10]:
        obj_num = zil_to_objnum[room_id]
        desc = room_names.get(room_id, '?')
        exits = exits_by_room.get(room_id, {})
        print(f'  {room_id:25s} = #{obj_num:3d} ({desc:20s}) - {len(exits)} exits')
