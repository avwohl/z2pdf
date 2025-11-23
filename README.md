# z2pdf - Z-Machine to PDF Debugging Tool

A tool for extracting and visualizing debugging information from Z-machine game files (.z1 through .z8). It works best on traditional infocom games compiled by the infocom compiler.  It gets less info about the directions for moves between rooms when a game is compiled with zorkie (our zil/zilf compiler).

## Features

- **Room Map Visualization**: Automatically generates a map showing all rooms/locations with their connections
- **Directional Connections**: Shows movement directions (north, south, east, west, up, down, etc.) between rooms
- **Vocabulary Extraction**: Lists all input vocabulary words from the game dictionary
- **Takable Objects**: Identifies and lists all objects that can be picked up in the game
- **Multi-page Support**: Handles large games across multiple PDF pages

## Installation

### Requirements

- Python 3.7+
- reportlab library

### Setup

```bash
pip install reportlab
```

The tool also depends on the Z-machine parser from the z2js project at `~/z2js/zparser.py`.

## Usage

Basic usage:

```bash
python3 z2pdf <input.z3> [output.pdf]
```

Examples:

```bash
# Generate map for minizork
python3 z2pdf minizork.z3

# Specify output filename
python3 z2pdf zork1.z3 zork1-map.pdf

# Process any Z-machine version
python3 z2pdf game.z5 game-map.pdf
```

## Output

The generated PDF includes:

1. **Title Page**: Game name and metadata
2. **Map Pages**: Visual representation of rooms and their connections
   - Rooms shown as labeled boxes
   - Direction labels on connection lines
   - Automatic layout based on directional relationships
3. **Vocabulary Page**: All input words recognized by the game
4. **Objects Page**: List of takable items

## How It Works

### Room Detection

The tool uses heuristics to identify rooms in the Z-machine object table:
- Objects with no parent or special parent relationships
- Objects with multiple properties (typically exits)
- Objects appearing early in the object table

### Exit Extraction

Directional exits are extracted from object properties:
- Properties 1-12 are typically directions in Infocom games
- Property values pointing to other room objects are treated as exits
- Common directions: north, south, east, west, northeast, northwest, southeast, southwest, up, down, in, out

### Layout Algorithm

Rooms are positioned using a force-directed layout:
- Starting from the first room
- Positioning connected rooms based on their directional relationship
- Unconnected rooms are placed separately

## Supported Z-Machine Versions

- Version 1-3: Classic Infocom games (Zork, Planetfall, etc.)
- Version 4-5: Extended features
- Version 6-8: Modern games

Tested with:
- Zork I (v3)
- Minizork (v3)
- Enchanter (v3)
- Planetfall (v3)

## Limitations

- Exit detection is heuristic-based and may not catch all connections
- Property-to-direction mapping is based on common Infocom conventions
- Very large maps may require manual adjustment of layout parameters
- Some games use non-standard property layouts that may not be fully detected

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

## Architecture

The tool consists of several components:

- **ZParser** (from z2js): Low-level Z-machine file parser
- **ZMapExtractor**: Extracts rooms, objects, and connections
- **MapLayoutEngine**: Calculates 2D positions for room layout
- **PDFGenerator**: Creates the final PDF output using ReportLab

## Related Projects

- **zorkie** (`~/zorkie`): ZIL/ZILF compiler for Z-machine
- **z2js** (`~/z2js`): Z-machine to JavaScript converter

## Future Enhancements

Possible improvements:
- Interactive HTML output
- Better heuristics for room/object detection
- Analysis of game logic and puzzles
- Graphviz output option
- Command-line options for layout customization
- Property number to direction mapping configuration

## License

Part of the Zork toolchain project.

## Debugging

The tool prints diagnostic information:
- Z-machine version and metadata
- Number of rooms found
- Number of objects found
- Number of dictionary words

If you encounter issues:
1. Check that the input file is a valid Z-machine file
2. Verify that z2js/zparser.py is available
3. Ensure reportlab is installed
4. Try with known-good files like minizork.z3

## Contributing

This is a debugging tool for Z-machine game development. Improvements to room/exit detection heuristics are welcome, especially for:
- Non-standard property layouts
- Different game conventions
- Better layout algorithms
- Additional output formats
# z2pdf
