# Changelog

All notable changes to z2pdf are documented here.

## [0.1.1] - 2026-08-20

No change to z2pdf's own code. Everything below is packaging and repository
state: the source that 0.1.0 already shipped is now committed to git, the
project URLs in the package metadata are corrected, and the `z2js` floor moves
up. The floor is not cosmetic. On an environment still holding z2js 0.1.0, the
upgrade drags it forward to a parser that decodes digits and punctuation
correctly, and the text in the generated PDF changes with it. Where z2js had
already resolved to 0.2.x, the output is unchanged and only the GitHub links
differ.

### Added
- The package source is now in the repository. 0.1.0 was uploaded to PyPI on
  2025-11-27 from a working tree that was never committed: at the newest
  commit at that point (`6c9eadd`, 2025-11-23) the repo held a standalone
  `z2pdf` script, a README, a LICENSE, a `.gitignore` and a docs note — no
  `pyproject.toml` and no `src/` at all. Commit `38ff577` ("found") added
  `pyproject.toml`, `src/z2pdf/__init__.py` and `src/z2pdf/main.py` after the
  fact, and those three files are identical to the ones inside the published
  `z2pdf-0.1.0.tar.gz`. So the diff since 0.1.0 looks like the whole package
  was written in this cycle only because git had never seen it — not because
  anything about how the tool parses a Z-machine file, lays out the map or
  draws the PDF has changed.
- `.github/workflows/publish.yml`, which builds an sdist and wheel and uploads
  them to PyPI through trusted publishing when a GitHub release is published, or
  on a manual `workflow_dispatch`. Repository infrastructure; it is not part of
  the installed package.
- `z-machine-version-notes.md`, reference notes carried over from work on the
  `zilc` compiler: V1/V2 Z-character shift codes, the V1 A2 alphabet, the V6/V7
  packed-address offsets and PULL opcode, V8 specifics, and a dfrotz test
  recipe. It is documentation only — not included in the sdist, and no code
  reads it.

### Changed
- The `z2js` requirement moves from `>=0.1.0` to `>=0.2.3`. z2pdf takes its
  whole Z-machine front end from that package via `from zparser import ZParser,
  ZObject`, and every member it touches — `get_object`, `get_object_name`,
  `get_dictionary_words`, `read_byte`, `read_word`, the raw `data` buffer, and
  `header.version` / `release` / `serial` / `dictionary` — already exists in
  z2js 0.1.0. The call sites in `src/z2pdf/main.py` are unchanged, so this floor
  is not about an API z2pdf newly needs. What it does decide is which text
  decoder produces the strings on the page: every room name, object name and
  vocabulary word in the generated PDF is whatever `zparser` handed back. The
  z2js 0.1.0 decoder indexed its A2 alphabet one place short, so letters came
  out right but every digit and punctuation mark decoded as the entry before it
  — `1` printed as `0`, `.` as `9`, `:` as `-` — and `)`, the last entry, fell
  off the end and printed as nothing; the 10-bit ZSCII escape was an empty
  branch, so an escaped character turned into two spurious letters. z2js 0.2.0
  rewrote `decode_zstring` and fixed all of that. `>=0.1.0` merely allowed the
  corrected parser; `>=0.2.3` requires it.
- `.gitignore` now covers the Python build artifacts (`dist/`, `build/`,
  `*.egg-info/`, `__pycache__/`), virtualenv directories and editor droppings,
  none of which it listed before the repo had a build to produce them.

### Fixed
- The GitHub URLs in the package metadata named the wrong account.
  `Homepage`, `Repository` and `Issues` in `pyproject.toml` all read
  `github.com/awohl/z2pdf`; the maintainer's account is `avwohl`. `awohl` is
  not a typo that lands nowhere — it is a real GitHub account, registered in
  February 2014, dormant since 2015, holding a single forked repository
  unrelated to this project. `awohl/z2pdf` does not exist, so all three URLs are
  404s today, but they point into a namespace this project does not control, and
  they would silently start resolving to whatever appeared there if a repository
  of that name were ever created. These three keys ship as `Project-URL` core
  metadata and are the sidebar links on the PyPI page, so on the 0.1.0 page the
  entire route from PyPI to the source and to the issue tracker is broken. Now
  `github.com/avwohl/z2pdf`. (The commit that made the correction, `9a6273b`,
  describes `awohl` as "no such account"; that part of the message is wrong.)

Earlier history is in the git log.
