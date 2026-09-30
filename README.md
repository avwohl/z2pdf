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

- Python 3.8+
- reportlab 3.5.0 or newer
- z2js 0.2.3 or newer, which supplies the Z-machine parser (`zparser`)

pip installs both libraries as dependencies.

### Setup

```bash
pip install z2pdf        # from PyPI
pip install .            # or from a checkout of this repository
```

Either one puts a `z2pdf` command on the PATH. The `z2pdf` script at the top of
the repository runs the same code without installing the package, but still
needs reportlab and z2js installed.

## Usage

Basic usage:

```bash
z2pdf <input.z3> [output.pdf]
```

Examples:

```bash
# Generate map for minizork
z2pdf minizork.z3

# Specify output filename
z2pdf zork1.z3 zork1-map.pdf

# Process any Z-machine version
z2pdf game.z5 game-map.pdf
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
- **z2js** ([avwohl/z2js](https://github.com/avwohl/z2js)): Z-machine to JavaScript converter, and the source of the parser z2pdf uses

## License

Part of the Zork toolchain project.
