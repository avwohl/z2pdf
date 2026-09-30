# How z2pdf Works

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

## Architecture

The tool consists of several components:

- **ZParser** (from z2js): Low-level Z-machine file parser
- **ZMapExtractor**: Extracts rooms, objects, and connections
- **MapLayoutEngine**: Calculates 2D positions for room layout
- **PDFGenerator**: Creates the final PDF output using ReportLab

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

## Future Enhancements

Possible improvements:
- Interactive HTML output
- Better heuristics for room/object detection
- Analysis of game logic and puzzles
- Graphviz output option
- Command-line options for layout customization
- Property number to direction mapping configuration
