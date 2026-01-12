# Pending Git Changes Summary

## Modified Files (from previous sessions)

### Core Application Changes
- `core.py` - Privacy & persistence features
- `database.py` - User settings and journey memory
- `tui_app.py` - TUI symposium updates
- `philosopher_app.py` - CLI mode restoration

### Philosophy Library
- 170+ `.txt` files - Auto-curator added `---BEGIN/END AUTHOR TEXT---` markers
- Deleted: `pg_browser.py`, `watch_library.py`, `auto_curator_codex.py` (moved to codepax-cli)
- Deleted: `openapi.json`

## Untracked Files (never committed)

### Application Code
- `main.py` - New unified entry point
- `utils.py` - Shared utilities

### Static Assets
- `static/favicon.svg` - Custom "crossed swords" icon
- `static/manifest.json` - PWA configuration

### External/Ignore
- `codepax-cli/` - External repo (should .gitignore)
- `codex-library/` - External repo (should .gitignore)
- `msi.komodo-city.ts.net.crt` - SSL cert (SECURITY RISK - do NOT commit)
- `msi.komodo-city.ts.net.key` - SSL key (SECURITY RISK - do NOT commit)
- `philosophy_library/.metadata/` - Auto-curator cache (should .gitignore)
- `A_Treatise_on_Good_Works.codex` - Test file

## Recommended Actions

1. **Ignore security-sensitive files**:
   ```
   *.crt
   *.key
   codepax-cli/
   codex-library/
   philosophy_library/.metadata*/
   *.codex
   ```

2. **Commit application features** (separate commits):
   - Privacy/persistence (core.py, database.py)
   - PWA support (favicon, manifest, main.py)
   - TUI updates (tui_app.py, philosopher_app.py)

3. **Philosophy library changes**: Decide later (many files changed)
