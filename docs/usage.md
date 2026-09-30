# Output, Examples and Debugging

## Output

The generated PDF includes:

1. **Title Page**: Game name and metadata
2. **Map Pages**: Visual representation of rooms and their connections
   - Rooms shown as labeled boxes
   - Direction labels on connection lines
   - Automatic layout based on directional relationships
3. **Vocabulary Page**: All input words recognized by the game
4. **Objects Page**: List of takable items

## Examples

Generate maps for sample games:

```bash
# Minizork - small test game
python3 z2pdf ~/z2js/docs/minizork.z3
# Output: Found 143 rooms and 87 objects

# Zork I - full game
python3 z2pdf ~/zorkie/zork1-final.z3
# Output: Found 247 rooms and 1 objects

# Enchanter
python3 z2pdf ~/zorkie/enchanter-test.z3
# Output: Found 251 rooms and 0 objects
```

## Debugging

The tool prints diagnostic information:
- Z-machine version and metadata
- Number of rooms found
- Number of objects found
- Number of dictionary words

If you encounter issues:
1. Check that the input file is a valid Z-machine file
2. Verify that the z2js package is installed, version 0.2.3 or newer (`pip show z2js`)
3. Ensure reportlab is installed
4. Try with known-good files like minizork.z3
