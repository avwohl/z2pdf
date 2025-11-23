# z2pdf Development Rules

## Exit Detection

**DO NOT limit to "direction words"**. Test EVERY dictionary word in every room to find which ones cause movement to a different room.

Only filter out words with fixed system meanings:
- verbose, brief, superbrief
- quit, restart, restore, save
- help, about, info, version
- score, inventory, i
- look, l, wait, z
- again, g, undo, oops

Any other word might cause movement in some room (e.g., "jump", "climb", "cross", "launch", "land", "board", "pray", etc.).

## Implementation (Current)

Uses z2js static analysis (zparser.py) - NO dfrotz dependency.

**StaticExitExtractor** analyzes:
1. Dictionary entries - in Infocom games, extra bytes in dictionary entries contain the property number that word maps to for movement
2. Room object properties - single-byte properties pointing to other rooms are exits
3. Fallback: if dictionary has no extra bytes (ZILF games), uses default Infocom property mapping

Works well with:
- Original Infocom games (minizork, zork1, enchanter, etc.)

Does NOT work with:
- ZILF-compiled games (different object/property structure)
