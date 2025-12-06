# Z-Machine Version-Specific Encoding Notes

Notes from fixing zilc compiler for V1-V8 support. The JS compiler likely has similar issues.

## V1/V2 Text Encoding

### Z-Character Shift Codes

V1-V2 use DIFFERENT shift codes than V3+:

| Z-char | V1-V2 Meaning | V3+ Meaning |
|--------|---------------|-------------|
| 1 | Newline (V1 only) | Abbreviation table 0 |
| 2 | Temp shift UP (A0→A1, A1→A2, A2→A0) | Abbreviation table 1 |
| 3 | Temp shift DOWN (A0→A2, A1→A0, A2→A1) | Abbreviation table 2 |
| 4 | Shift LOCK up | Temp shift to A1 |
| 5 | Shift LOCK down | Temp shift to A2 |

**Key insight**: V3+ interpreters will misread V1-V2 shift codes as abbreviation references, causing garbled text.

### V1 A2 Alphabet

V1's A2 alphabet is different from V2+:

```
V1 A2: [escape][0][1][2][3][4][5][6][7][8][9][.][,][!][?][_][#][']["][/][\][<][-][:][(][)]
V2+ A2: [escape][newline][0][1][2][3][4][5][6][7][8][9][.][,][!][?][_][#][']["][/][\][-][:][(][)]
```

- **V1 position 7** = digit '0' (NOT newline or '<')
- **V2+ position 7** = newline
- V1 newline is z-char 1, not in any alphabet

This causes off-by-one errors in digit display if not handled correctly.

### Space Character

Z-char 0 is ALWAYS space in any alphabet. Don't try to look it up in alphabet tables.

## V6/V7 Specifics

### File Length Divisor

| Version | Divisor |
|---------|---------|
| V1-V3 | 2 |
| V4-V5 | 4 |
| V6-V8 | 8 |

### Initial PC (Program Counter)

- **V1-V5, V8**: Direct byte address of first routine
- **V6-V7**: Packed routine address (needs routines_offset)

### Routines/Strings Offset

- **V6-V7**: Uses header fields at 0x28 and 0x2A for packed address calculation
- **V8**: Does NOT use these fields (like V5)

### PULL Opcode

The PULL opcode changed significantly:

- **V1-V5, V8**: `pull (variable)` - operand is target variable number, no store byte
- **V6-V7**: `pull stack → (result)` - has store byte, operand defaults to main stack

For V6-7 encoding:
```
0xE9        ; VAR form PULL
0xFF        ; Type byte: all omitted = use main stack
<var_num>   ; Store result here
```

For V1-5, V8 encoding:
```
0xE9        ; VAR form PULL
0x7F        ; Type byte: small constant
<var_num>   ; Target variable number (operand, not store)
```

## V8 Specifics

V8 is essentially V5 with larger address space:
- Uses V5-style Initial PC (direct byte address)
- Uses V5-style PULL (no store byte)
- Does NOT use routines_offset/strings_offset fields
- Uses divisor 8 for file length (like V6-V7)

Only one known V8 game: Anchorhead (special release)

## Testing Commands

```bash
# Compile for specific version
python3 -m zilc.compiler test.zil -o test.z1 -v 1
python3 -m zilc.compiler test.zil -o test.z2 -v 2
python3 -m zilc.compiler test.zil -o test.z3 -v 3

# Test with dfrotz
dfrotz test.z1
```

## Files Modified in zilc

- `zilc/zmachine/text_encoding.py`: V1/V2 alphabet and shift code handling
- `zilc/zmachine/assembler.py`: File length divisor, Initial PC, routines offset
- `zilc/codegen/codegen_improved.py`: PULL opcode encoding per version
