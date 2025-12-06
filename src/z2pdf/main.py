"""
z2pdf - Z-Machine to PDF debugging tool

Extracts and visualizes information from Z-machine game files:
- Map of rooms with directional connections
- Input vocabulary
- Takable objects

Usage: z2pdf <input.z3> [output.pdf]
"""

import sys
import os
import struct
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

from zparser import ZParser, ZObject

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except ImportError:
    print("Error: reportlab is required. Install with: pip install reportlab")
    sys.exit(1)


@dataclass
class Room:
    """Represents a room/location in the game"""
    obj_num: int
    name: str
    exits: Dict[str, int]  # direction -> destination room object number
    x: float = 0.0  # Layout coordinates
    y: float = 0.0
    objects: List[str] = None  # Objects in this room

    def __post_init__(self):
        if self.objects is None:
            self.objects = []


@dataclass
class GameObject:
    """Represents a takable game object"""
    obj_num: int
    name: str
    location: int  # Parent object number


class ZMapExtractor:
    """Extracts map and game data from Z-machine files"""

    # Common property numbers for directions (these vary by game, but these are typical)
    # In Zork/Infocom games, properties often follow patterns
    DIRECTION_PROPS = {
        'north': [1, 2, 3, 4],     # Try common property numbers
        'south': [1, 2, 3, 4],
        'east': [1, 2, 3, 4],
        'west': [1, 2, 3, 4],
        'northeast': [1, 2, 3, 4],
        'northwest': [1, 2, 3, 4],
        'southeast': [1, 2, 3, 4],
        'southwest': [1, 2, 3, 4],
        'up': [1, 2, 3, 4],
        'down': [1, 2, 3, 4],
        'in': [1, 2, 3, 4],
        'out': [1, 2, 3, 4],
    }

    # Common attributes for rooms and objects
    ATTR_ROOM = [1, 2, 3]  # Common room attributes
    ATTR_TAKABLE = [4, 5, 6]  # Common takable attributes

    def __init__(self, parser: ZParser):
        self.parser = parser
        self.rooms: Dict[int, Room] = {}
        self.objects: List[GameObject] = []

    def extract_all(self):
        """Extract all game data"""
        print("Extracting game data...")
        self._find_rooms()
        self._find_objects()
        self._extract_exits()
        self._associate_objects_with_rooms()
        print(f"Found {len(self.rooms)} rooms and {len(self.objects)} objects")

    def _associate_objects_with_rooms(self):
        """Associate objects with the rooms they're in"""
        for obj in self.objects:
            if obj.location in self.rooms:
                self.rooms[obj.location].objects.append(obj.name)

    def _is_valid_name(self, name: str) -> bool:
        """Check if a name contains mostly valid printable characters"""
        if not name:
            return False

        # Count printable vs non-printable characters
        printable_count = sum(1 for c in name if c.isprintable() and (c.isalnum() or c in ' -.,!?\'"'))
        total_count = len(name)

        # Require at least 70% valid characters
        return total_count > 0 and (printable_count / total_count) >= 0.7

    def _has_property(self, obj_num: int, prop_num: int) -> bool:
        """Check if an object has a specific property number"""
        try:
            obj = self.parser.get_object(obj_num)
            if not obj:
                return False

            prop_addr = obj.properties
            if prop_addr >= len(self.parser.data):
                return False

            text_length = self.parser.read_byte(prop_addr)
            prop_addr += 1 + text_length * 2

            while prop_addr < len(self.parser.data):
                size_byte = self.parser.read_byte(prop_addr)
                if size_byte == 0:
                    break

                if self.parser.header.version <= 3:
                    p_num = size_byte & 0x1F
                    p_size = (size_byte >> 5) + 1
                else:
                    p_num = size_byte & 0x3F
                    if size_byte & 0x80:
                        prop_addr += 1
                        if prop_addr >= len(self.parser.data):
                            break
                        p_size = self.parser.read_byte(prop_addr) & 0x3F
                        if p_size == 0:
                            p_size = 64
                    else:
                        p_size = 1 if not (size_byte & 0x40) else 2

                if p_num == prop_num:
                    return True

                prop_addr += 1 + p_size

            return False
        except (IndexError, struct.error):
            return False

    def _find_rooms(self):
        """Identify room objects in the game"""
        # Better approach: rooms typically share a common parent object (ROOMS container)
        # Find the most common parent among objects with multiple properties

        from collections import Counter

        max_obj = 255 if self.parser.header.version <= 3 else 2000

        # First pass: find objects that look like rooms (have multiple properties)
        # and count their parents
        parent_counts = Counter()
        candidates = []

        for obj_num in range(1, min(max_obj, 256)):
            try:
                obj = self.parser.get_object(obj_num)
                if not obj:
                    continue

                name = self.parser.get_object_name(obj_num)
                if not name or not name.strip():
                    continue

                if not self._is_valid_name(name):
                    continue

                # Check if this object has properties that might be exits
                if self._has_exit_properties(obj_num):
                    parent_counts[obj.parent] += 1
                    candidates.append((obj_num, obj.parent, name))

            except (IndexError, struct.error):
                continue

        # The most common parent is likely the ROOMS container
        if parent_counts:
            rooms_container = parent_counts.most_common(1)[0][0]
        else:
            rooms_container = 27  # Fallback

        # Second pass: collect all objects with that parent
        for obj_num in range(1, min(max_obj, 256)):
            try:
                obj = self.parser.get_object(obj_num)
                if not obj or obj.parent != rooms_container:
                    continue

                name = self.parser.get_object_name(obj_num)
                if not name or not name.strip():
                    continue

                if not self._is_valid_name(name):
                    continue

                self.rooms[obj_num] = Room(
                    obj_num=obj_num,
                    name=name,
                    exits={}
                )
            except (IndexError, struct.error):
                continue

        # If we found few rooms, fall back to the old heuristic
        if len(self.rooms) < 10:
            room_start = 142
            for obj_num in range(room_start, min(max_obj, 300)):
                if obj_num in self.rooms:
                    continue
                try:
                    obj = self.parser.get_object(obj_num)
                    if not obj:
                        break

                    name = self.parser.get_object_name(obj_num)
                    if not name or not name.strip():
                        continue

                    if not self._is_valid_name(name):
                        continue

                    self.rooms[obj_num] = Room(
                        obj_num=obj_num,
                        name=name,
                        exits={}
                    )
                except (IndexError, struct.error):
                    continue

    def _get_directional_properties(self, obj_num: int) -> Dict[int, int]:
        """Get directional properties (1-12) for an object"""
        exits = {}
        try:
            obj = self.parser.get_object(obj_num)
            if not obj:
                return exits

            prop_addr = obj.properties
            if prop_addr >= len(self.parser.data):
                return exits

            text_length = self.parser.read_byte(prop_addr)
            prop_addr += 1 + text_length * 2

            while prop_addr < len(self.parser.data) - 2:
                size_byte = self.parser.read_byte(prop_addr)
                if size_byte == 0:
                    break

                prop_num = size_byte & 0x1F
                prop_size = (size_byte >> 5) + 1

                # Check for directional properties
                if 1 <= prop_num <= 12 and prop_size == 2:
                    target = self.parser.read_word(prop_addr + 1)
                    if target > 0 and target < 300:
                        exits[prop_num] = target

                prop_addr += 1 + prop_size

            return exits
        except (IndexError, struct.error):
            return exits

    def _has_exit_properties(self, obj_num: int) -> bool:
        """Check if object has properties that might be exits"""
        try:
            obj = self.parser.get_object(obj_num)
            if not obj:
                return False

            # Check if object has multiple properties
            # (rooms typically have properties for exits)
            prop_addr = obj.properties
            if prop_addr >= len(self.parser.data):
                return False

            text_length = self.parser.read_byte(prop_addr)
            prop_addr += 1 + text_length * 2

            # Count properties
            prop_count = 0
            while prop_addr < len(self.parser.data):
                size_byte = self.parser.read_byte(prop_addr)
                if size_byte == 0:
                    break
                prop_count += 1

                # Get property size
                if self.parser.header.version <= 3:
                    prop_size = (size_byte >> 5) + 1
                else:
                    if size_byte & 0x80:
                        if prop_addr + 1 >= len(self.parser.data):
                            break
                        prop_size = self.parser.read_byte(prop_addr + 1) & 0x3F
                        if prop_size == 0:
                            prop_size = 64
                        prop_addr += 1
                    else:
                        prop_size = 1 if not (size_byte & 0x40) else 2

                prop_addr += 1 + prop_size

                if prop_count > 3:  # Rooms typically have multiple properties
                    return True

            return False
        except (IndexError, struct.error):
            return False

    def _find_objects(self):
        """Identify takable objects in the game"""
        # Objects are numbered before rooms
        # Find the minimum room number to know where objects end
        if not self.rooms:
            return

        min_room_num = min(self.rooms.keys())

        # Only scan objects before the room range
        for obj_num in range(1, min_room_num):
            try:
                obj = self.parser.get_object(obj_num)
                if not obj:
                    break

                name = self.parser.get_object_name(obj_num)
                if not name or not name.strip():
                    continue

                # Validate name is readable ASCII/printable text
                # Skip objects with garbled names
                if not self._is_valid_name(name):
                    continue

                # Common takable/important objects - filter out scenery
                # Takable objects often have properties 5 and 6 (value/trophyvalue)
                # or property 9 (capacity for containers)
                is_takable = (
                    self._has_property(obj_num, 5) or  # value
                    self._has_property(obj_num, 6) or  # trophyvalue
                    self._has_property(obj_num, 9)     # capacity (container)
                )

                if is_takable:
                    self.objects.append(GameObject(
                        obj_num=obj_num,
                        name=name,
                        location=obj.parent
                    ))
            except (IndexError, struct.error):
                continue

    def _extract_exits(self):
        """
        Extract directional exits from compiled Z-machine bytecode.

        This analyzes room action routines to find room transition patterns.
        Exits in Z-machine games can be encoded in multiple ways:
        1. As routine code that checks player actions and changes location
        2. As data in specialized property formats
        3. Through calls to global movement handlers

        This implementation traces through the bytecode looking for patterns.
        """
        print("Extracting exits from compiled Z-machine bytecode...")

        # Get available tools
        try:
            from opcodes import OpcodeDecoder
            decoder = OpcodeDecoder(self.parser.data, self.parser.header.version)
        except:
            print("Warning: Cannot decode instructions, exit extraction limited")
            return

        # Track room references found in each room's routine
        for room_num, room in self.rooms.items():
            try:
                # Extract room references from the room's action routine
                room_refs = self._find_room_references_in_routine(room_num, decoder)

                # Heuristic: rooms referenced in a room's routine are likely exits
                # Try to infer direction based on room number patterns
                if room_refs:
                    for ref_room in room_refs[:8]:
                        if ref_room in self.rooms:
                            # Infer likely direction from room number relationship
                            direction = self._infer_direction(room_num, ref_room)
                            room.exits[direction] = ref_room

            except Exception as e:
                continue

        total_exits = sum(len(r.exits) for r in self.rooms.values())
        print(f"Extracted {total_exits} potential exit references")

    def _find_room_references_in_routine(self, room_num: int, decoder) -> List[int]:
        """Find room number references in a room's action routine"""
        room_refs = []

        try:
            obj = self.parser.get_object(room_num)
            if not obj:
                return room_refs

            # Find property 1 (action routine)
            prop_addr = obj.properties
            if prop_addr >= len(self.parser.data):
                return room_refs

            text_length = self.parser.read_byte(prop_addr)
            prop_addr += 1 + text_length * 2

            routine_addr = None
            while prop_addr < len(self.parser.data) - 2:
                size_byte = self.parser.read_byte(prop_addr)
                if size_byte == 0:
                    break
                prop_num = size_byte & 0x1F
                prop_size = (size_byte >> 5) + 1

                if prop_num == 1 and prop_size >= 2:
                    routine_addr = self.parser.read_word(prop_addr + 1)
                    break

                prop_addr += 1 + prop_size

            if not routine_addr:
                return room_refs

            # Decode the routine looking for room number constants
            pc = routine_addr
            num_locals = self.parser.data[pc]
            pc += 1
            pc += num_locals * 2

            for _ in range(100):  # Limit to first 100 instructions
                if pc >= len(self.parser.data):
                    break
                try:
                    instr = decoder.decode(pc)

                    # Look for room numbers in operands
                    for op in instr.operands:
                        if isinstance(op, int) and op in self.rooms and op != room_num:
                            if op not in room_refs:
                                room_refs.append(op)

                    pc += instr.size
                except:
                    break

        except Exception as e:
            pass

        return room_refs

    def _infer_direction(self, from_room: int, to_room: int) -> str:
        """
        Infer likely direction based on room numbering and position.
        This is a heuristic - without parsing the actual direction checks,
        we use patterns and room number relationships.
        """
        # Use simple numbering to create unique exit names
        # Format: "to_NNN" where NNN is the target room number
        return f"to_{to_room}"

    def _guess_direction(self, prop_num: int) -> Optional[str]:
        """Guess direction name from property number"""
        # Common mappings (game-specific, this is a guess)
        direction_map = {
            1: 'north', 2: 'south', 3: 'east', 4: 'west',
            5: 'northeast', 6: 'northwest', 7: 'southeast', 8: 'southwest',
            9: 'up', 10: 'down', 11: 'in', 12: 'out'
        }
        return direction_map.get(prop_num)


class StaticExitExtractor:
    """
    Extract room exits using static analysis of Z-machine bytecode.

    This works in two modes:
    1. For games with extended dictionary entries (Infocom): analyze dictionary
       extra bytes to map words to property numbers
    2. For all games: scan room properties for single-byte values that point
       to other room objects (these are exits)

    NO hardcoded direction lists or property mappings - everything is discovered
    dynamically from the game data.
    """

    def __init__(self, data: bytes, parser: ZParser):
        self.data = data
        self.parser = parser
        self.room_objs = set()  # Will be populated with room object numbers

    def _get_object_properties(self, obj_num: int) -> Dict[int, List[int]]:
        """Get all properties for an object."""
        props = {}
        try:
            obj = self.parser.get_object(obj_num)
            if not obj:
                return props

            prop_addr = obj.properties
            if prop_addr >= len(self.data):
                return props

            text_length = self.data[prop_addr]
            prop_addr += 1 + text_length * 2

            while prop_addr < len(self.data) - 10:
                size_byte = self.data[prop_addr]
                if size_byte == 0:
                    break
                prop_num = size_byte & 0x1F
                prop_size = (size_byte >> 5) + 1
                prop_data = list(self.data[prop_addr + 1:prop_addr + 1 + prop_size])
                props[prop_num] = prop_data
                prop_addr += 1 + prop_size
        except:
            pass
        return props

    def _get_property_to_word_mapping(self) -> Dict[int, str]:
        """
        Extract property number -> word mapping from dictionary.

        In Z-machine games with extended dictionary entries (7+ bytes),
        the extra bytes contain property numbers that map words to directions.
        """
        prop_to_word = {}

        dict_addr = self.parser.header.dictionary
        num_seps = self.data[dict_addr]
        dict_addr += 1 + num_seps

        entry_length = self.data[dict_addr]
        num_entries = (self.data[dict_addr + 1] << 8) | self.data[dict_addr + 2]
        dict_addr += 3

        # Only works for games with extended dictionary entries (>4 bytes)
        if entry_length <= 4:
            return prop_to_word

        words = self.parser.get_dictionary_words()

        for i, word in enumerate(words):
            word = word.strip().lower()
            addr = dict_addr + i * entry_length
            # In V3: 4 bytes of encoded text, then extra bytes
            extra = list(self.data[addr + 4:addr + entry_length])

            # Check each byte as potential property number
            for potential_prop in extra:
                if 1 <= potential_prop <= 31:
                    # Only use the first word for each property
                    if potential_prop not in prop_to_word:
                        prop_to_word[potential_prop] = word

        return prop_to_word

    def _find_exit_properties(self, rooms: Dict[int, 'Room']) -> Set[int]:
        """
        Find which property numbers are used for exits.

        Direction/exit properties are typically in the range 13-31.
        Lower properties (1-12) are usually for other purposes like
        synonyms, descriptions, actions, etc.

        For Infocom games: exits are single-byte properties.
        For ZILF games: exits may be embedded in multi-byte properties.
        """
        exit_props = set()

        for room_num in rooms:
            props = self._get_object_properties(room_num)
            for prop_num, prop_data in props.items():
                # Only consider properties 13-31 (typical exit range)
                if prop_num < 13:
                    continue

                # Check if any byte in the property data points to a room
                for byte_val in prop_data:
                    if byte_val in self.room_objs and byte_val != room_num:
                        exit_props.add(prop_num)
                        break

        return exit_props

    def _extract_room_refs_from_property(self, prop_data: List[int],
                                         room_num: int) -> List[int]:
        """
        Extract room references from property data.

        For single-byte properties, the whole value is the destination.
        For multi-byte properties, scan for bytes that are valid room numbers.
        """
        refs = []
        if len(prop_data) == 1:
            # Simple exit - single byte is destination
            if prop_data[0] in self.room_objs and prop_data[0] != room_num:
                refs.append(prop_data[0])
        else:
            # Multi-byte property - look for room refs at any position
            # Prefer unique references (don't duplicate same destination)
            seen = set()
            for byte_val in prop_data:
                if byte_val in self.room_objs and byte_val != room_num:
                    if byte_val not in seen:
                        refs.append(byte_val)
                        seen.add(byte_val)
        return refs

    def extract_exits(self, rooms: Dict[int, 'Room']) -> int:
        """
        Extract exits for all rooms using static analysis.

        This scans room properties to find values pointing to other rooms
        (which are exits), then maps them to dictionary words where possible.

        Works with both Infocom (single-byte exits) and ZILF (multi-byte
        exit tables) game formats.

        Returns: total number of exits found
        """
        self.room_objs = set(rooms.keys())

        if not self.room_objs:
            print("No rooms found to analyze")
            return 0

        # Step 1: Find which property numbers are used for exits
        exit_props = self._find_exit_properties(rooms)
        if not exit_props:
            print("No exit properties found")
            return 0

        print(f"Found exit property numbers: {sorted(exit_props)}")

        # Step 2: Try to map property numbers to dictionary words
        prop_to_word = self._get_property_to_word_mapping()

        # Filter to only properties that are actually used as exits
        prop_to_word = {p: w for p, w in prop_to_word.items() if p in exit_props}

        if prop_to_word:
            print(f"Mapped {len(prop_to_word)} properties to words: {prop_to_word}")
        else:
            print("No property-to-word mapping found in dictionary")

        # Step 3: Extract exits from each room
        total_exits = 0
        words_used = set()

        for room_num, room in rooms.items():
            props = self._get_object_properties(room_num)

            for prop_num in exit_props:
                if prop_num in props:
                    prop_data = props[prop_num]
                    # Extract room references from property data
                    dest_rooms = self._extract_room_refs_from_property(
                        prop_data, room_num)

                    for dest in dest_rooms:
                        # Use dictionary word if known, else use property number
                        word = prop_to_word.get(prop_num, f"p{prop_num}")
                        if word not in room.exits:
                            room.exits[word] = dest
                            total_exits += 1
                            words_used.add(word)
                            break  # Only one exit per property/direction

        print(f"Unique exit words found: {sorted(words_used)}")
        return total_exits


class MapLayoutEngine:
    """Generates 2D layout for room map"""

    def __init__(self, rooms: Dict[int, Room]):
        self.rooms = rooms

    def layout(self):
        """Calculate x,y positions for all rooms"""
        if not self.rooms:
            return

        # Simple force-directed layout
        # Start with first room at origin
        first_room = next(iter(self.rooms.values()))
        first_room.x = 0
        first_room.y = 0

        positioned = {first_room.obj_num}
        queue = [first_room.obj_num]

        # Direction vectors
        dir_vectors = {
            'north': (0, 1), 'south': (0, -1),
            'east': (1, 0), 'west': (-1, 0),
            'northeast': (0.7, 0.7), 'northwest': (-0.7, 0.7),
            'southeast': (0.7, -0.7), 'southwest': (-0.7, -0.7),
            'up': (0, 1.5), 'down': (0, -1.5),
            'in': (0.5, 0), 'out': (-0.5, 0),
        }

        while queue:
            room_num = queue.pop(0)
            room = self.rooms[room_num]

            for direction, target_num in room.exits.items():
                if target_num not in positioned and target_num in self.rooms:
                    # Position based on direction
                    dx, dy = dir_vectors.get(direction, (1, 0))
                    target = self.rooms[target_num]
                    target.x = room.x + dx * 2
                    target.y = room.y + dy * 2

                    positioned.add(target_num)
                    queue.append(target_num)

        # Position unconnected rooms
        next_y = 0
        for room_num, room in self.rooms.items():
            if room_num not in positioned:
                room.x = 10
                room.y = next_y
                next_y -= 2


class PDFGenerator:
    """Generates PDF output"""

    def __init__(self, filename: str):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=letter)
        self.width, self.height = letter

    def generate(self, rooms: Dict[int, Room], objects: List[GameObject],
                 vocabulary: List[str], game_name: str):
        """Generate complete PDF"""

        # Title page
        self._draw_title(game_name)

        # Map pages
        self._draw_map(rooms)

        # Vocabulary
        self._draw_vocabulary(vocabulary)

        # Objects list
        self._draw_objects(objects)

        self.c.save()
        print(f"PDF generated: {self.filename}")

    def _draw_title(self, game_name: str):
        """Draw title page"""
        self.c.setFont("Helvetica-Bold", 24)
        self.c.drawCentredString(self.width / 2, self.height - 2*inch,
                                f"Z-Machine Game Map")
        self.c.setFont("Helvetica", 16)
        self.c.drawCentredString(self.width / 2, self.height - 2.5*inch,
                                game_name)
        self.c.setFont("Helvetica", 10)
        self.c.drawCentredString(self.width / 2, 1*inch,
                                "Generated by z2pdf debugging tool")
        self.c.showPage()

    def _draw_map(self, rooms: Dict[int, Room]):
        """Draw room map across multiple pages if needed"""
        if not rooms:
            return

        # Sort rooms by room number for consistent ordering
        sorted_rooms = sorted(rooms.items(), key=lambda x: x[0])

        # Configuration for readability
        margin = 0.5 * inch
        available_width = self.width - 2 * margin
        available_height = self.height - 2 * margin - 0.5 * inch

        box_width = 1.6 * inch
        box_height = 0.5 * inch
        h_spacing = 1.9 * inch  # horizontal spacing between boxes
        v_spacing = 0.75 * inch  # vertical spacing between boxes

        # Calculate rooms per page
        cols_per_page = int(available_width / h_spacing)
        rows_per_page = int(available_height / v_spacing)
        rooms_per_page = max(1, cols_per_page * rows_per_page)

        # Split rooms into pages
        total_pages = (len(sorted_rooms) + rooms_per_page - 1) // rooms_per_page

        for page_num in range(total_pages):
            start_idx = page_num * rooms_per_page
            end_idx = min(start_idx + rooms_per_page, len(sorted_rooms))
            page_rooms = dict(sorted_rooms[start_idx:end_idx])

            # Draw page title
            self.c.setFont("Helvetica-Bold", 14)
            title = f"Room Map - Page {page_num + 1} of {total_pages}"
            self.c.drawString(margin, self.height - margin + 0.15 * inch, title)

            # Calculate positions for rooms on this page
            # Use a simple grid layout for clarity
            room_positions = {}
            for idx, (room_num, room) in enumerate(page_rooms.items()):
                col = idx % cols_per_page
                row = idx // cols_per_page

                x = margin + col * h_spacing + box_width / 2
                y = self.height - margin - 0.5 * inch - row * v_spacing - box_height / 2

                room_positions[room_num] = (x, y)

            # Draw room boxes (no connection lines)
            for room_num, room in page_rooms.items():
                x, y = room_positions[room_num]

                # Draw box
                self.c.setFillColor(colors.lightblue)
                self.c.setStrokeColor(colors.black)
                self.c.setLineWidth(2)
                self.c.rect(x - box_width/2, y - box_height/2,
                           box_width, box_height, fill=1, stroke=1)

                # Draw room number at top
                self.c.setFont("Helvetica", 7)
                self.c.setFillColor(colors.gray)
                self.c.drawCentredString(x, y + box_height/2 - 0.12*inch, f"#{room_num}")

                # Draw room name
                self.c.setFillColor(colors.black)
                self.c.setFont("Helvetica-Bold", 9)

                # Wrap/truncate name to fit
                max_chars = 20
                name = room.name
                if len(name) > max_chars:
                    # Try to break at space
                    if ' ' in name[:max_chars]:
                        name = name[:name[:max_chars].rfind(' ')] + '...'
                    else:
                        name = name[:max_chars-3] + '...'

                self.c.drawCentredString(x, y + 0.05*inch, name)

                # Draw exits below room name
                if room.exits:
                    self.c.setFont("Helvetica", 6)
                    self.c.setFillColor(colors.darkblue)

                    # Format exits as compact list
                    exit_strs = [f"{d[:2].upper()}:{t}" for d, t in sorted(room.exits.items())]
                    # Split into multiple lines if needed
                    line1 = " ".join(exit_strs[:3])
                    line2 = " ".join(exit_strs[3:6]) if len(exit_strs) > 3 else ""

                    self.c.drawCentredString(x, y - 0.10*inch, line1)
                    if line2:
                        self.c.drawCentredString(x, y - 0.18*inch, line2)

            self.c.showPage()

    def _draw_vocabulary(self, vocabulary: List[str]):
        """Draw vocabulary list"""
        self.c.setFont("Helvetica-Bold", 16)
        self.c.drawString(inch, self.height - inch, "Input Vocabulary")

        self.c.setFont("Helvetica", 8)

        # Draw in columns
        col_width = 1.5 * inch
        cols = 4
        row_height = 0.15 * inch
        x_start = inch
        y_start = self.height - 1.5 * inch

        row = 0
        for i, word in enumerate(sorted(vocabulary)):
            col = i % cols

            x = x_start + col * col_width
            y = y_start - row * row_height

            if y < inch:  # New page
                self.c.showPage()
                self.c.setFont("Helvetica-Bold", 16)
                self.c.drawString(inch, self.height - inch, "Input Vocabulary (continued)")
                self.c.setFont("Helvetica", 8)
                y_start = self.height - 1.5 * inch
                row = 0
                y = y_start - row * row_height

            self.c.drawString(x, y, word)

            # Increment row counter after drawing all columns
            if col == cols - 1:
                row += 1

        self.c.showPage()

    def _draw_objects(self, objects: List[GameObject]):
        """Draw takable objects list"""
        self.c.setFont("Helvetica-Bold", 16)
        self.c.drawString(inch, self.height - inch, "Takable Objects")

        self.c.setFont("Helvetica", 10)
        y = self.height - 1.5 * inch

        for obj in sorted(objects, key=lambda o: o.name):
            if y < inch:
                self.c.showPage()
                self.c.setFont("Helvetica-Bold", 16)
                self.c.drawString(inch, self.height - inch, "Takable Objects (continued)")
                self.c.setFont("Helvetica", 10)
                y = self.height - 1.5 * inch

            self.c.drawString(inch, y, f"* {obj.name}")
            y -= 0.2 * inch

        self.c.showPage()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # Default: use base filename with .pdf extension (no directory)
        base = os.path.splitext(os.path.basename(input_file))[0]
        output_file = base + '.pdf'

    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    print(f"Reading Z-machine file: {input_file}")

    # Read Z-machine file
    with open(input_file, 'rb') as f:
        data = f.read()

    # Parse file
    parser = ZParser(data)
    print(f"Z-Machine version {parser.header.version}")
    print(f"Release {parser.header.release}, Serial {parser.header.serial}")

    # Extract map data (rooms and objects)
    extractor = ZMapExtractor(parser)
    extractor.extract_all()

    # Extract exits using static analysis (no dfrotz required)
    print("\nExtracting exits using static dictionary analysis...")
    exit_extractor = StaticExitExtractor(data, parser)
    total_exits = exit_extractor.extract_exits(extractor.rooms)
    print(f"Extracted {total_exits} exits from {len(extractor.rooms)} rooms")

    # Layout rooms
    layout_engine = MapLayoutEngine(extractor.rooms)
    layout_engine.layout()

    # Get vocabulary
    vocabulary = parser.get_dictionary_words()
    print(f"Found {len(vocabulary)} dictionary words")

    # Generate PDF
    game_name = os.path.basename(input_file)
    pdf = PDFGenerator(output_file)
    pdf.generate(extractor.rooms, extractor.objects, vocabulary, game_name)

    print("Done!")


if __name__ == '__main__':
    main()
