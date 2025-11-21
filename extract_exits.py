#!/usr/bin/env python3
"""
Extract room exits from Z-machine code by analyzing routines
"""

import sys
sys.path.insert(0, str(__file__).replace('zorkmap', 'z2js').rsplit('/', 1)[0])

from zparser import ZParser
from opcodes import OpcodeDecoder
from typing import Dict, List, Set
from pathlib import Path


class ExitExtractor:
    """Extract exits from Z-machine room routines"""

    # Direction words we're looking for
    DIRECTIONS = {
        'north', 'south', 'east', 'west',
        'northeast', 'northwest', 'southeast', 'southwest',
        'up', 'down', 'in', 'out', 'enter'
    }

    def __init__(self, data: bytes, parser: ZParser):
        self.data = data
        self.parser = parser
        self.decoder = OpcodeDecoder(data, parser.header.version)

        # Build direction word to number mapping
        self.dir_words = {}
        for word in parser.get_dictionary_words():
            word_lower = word.lower()
            if word_lower in self.DIRECTIONS:
                # Find the word number in dictionary
                self.dir_words[word_lower] = word

    def extract_room_exits(self, room_num: int) -> Dict[str, int]:
        """Extract exits from a room's property 1 routine"""
        exits = {}

        try:
            obj = self.parser.get_object(room_num)
            if not obj:
                return exits

            # Find property 1 (room action routine)
            prop_addr = obj.properties
            if prop_addr >= len(self.data):
                return exits

            text_length = self.data[prop_addr]
            prop_addr += 1 + text_length * 2

            routine_addr = None
            while prop_addr < len(self.data) - 2:
                size_byte = self.data[prop_addr]
                if size_byte == 0:
                    break

                prop_num = size_byte & 0x1F
                prop_size = (size_byte >> 5) + 1

                if prop_num == 1 and prop_size >= 2:
                    routine_addr = (self.data[prop_addr + 1] << 8) | self.data[prop_addr + 2]
                    break

                prop_addr += 1 + prop_size

            if not routine_addr:
                return exits

            # Decode the routine looking for exit patterns
            exits = self._analyze_routine(routine_addr, room_num)

        except Exception as e:
            pass

        return exits

    def _analyze_routine(self, routine_addr: int, room_num: int) -> Dict[str, int]:
        """Analyze a routine for exit patterns"""
        exits = {}

        try:
            pc = routine_addr
            num_locals = self.data[pc]
            pc += 1
            pc += num_locals * 2  # Skip local variable defaults

            # Decode up to 100 instructions looking for patterns
            for _ in range(100):
                if pc >= len(self.data):
                    break

                try:
                    instr = self.decoder.decode(pc)

                    # Look for patterns that suggest room transitions
                    # Common pattern: call to GOTO or similar with room number
                    # or direct property lookups followed by jumps

                    # Pattern: call with a large constant that might be a room number
                    if instr.name == 'call' and len(instr.operands) >= 2:
                        for op in instr.operands[1:]:
                            if isinstance(op, int) and 142 <= op < 300:
                                # This might be a room transition
                                # We'd need more context to know the direction
                                pass

                    pc += instr.size

                except:
                    break

        except:
            pass

        return exits


def test_extraction(game_file: str):
    """Test exit extraction on a game file"""
    with open(game_file, 'rb') as f:
        data = f.read()

    parser = ZParser(data)
    extractor = ExitExtractor(data, parser)

    # Test on a few rooms
    test_rooms = [142, 150, 154, 156, 157]

    for room_num in test_rooms:
        room_name = parser.get_object_name(room_num)
        exits = extractor.extract_room_exits(room_num)
        print(f'{room_num}: {room_name:30s} exits={exits}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 extract_exits.py <game.z3>")
        sys.exit(1)

    test_extraction(sys.argv[1])
