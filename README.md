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

## Documentation

- [Output, examples and debugging](https://github.com/avwohl/z2pdf/blob/main/docs/usage.md) - the PDF pages, sample runs, diagnostics and troubleshooting steps
- [How z2pdf works](https://github.com/avwohl/z2pdf/blob/main/docs/how_it_works.md) - room detection, exit extraction, layout, architecture, supported versions, limitations, future enhancements

## Contributing

This is a debugging tool for Z-machine game development. Improvements to room/exit detection heuristics are welcome, especially for:
- Non-standard property layouts
- Different game conventions
- Better layout algorithms
- Additional output formats

## Related Projects

- **zorkie** (`~/zorkie`): ZIL/ZILF compiler for Z-machine
- **z2js** (`~/z2js`): Z-machine to JavaScript converter

## License

Part of the Zork toolchain project.
