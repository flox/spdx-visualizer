# SPDX Viewer Environment

A standalone Flox environment for visualizing SPDX files as interactive Mermaid diagrams.

## Features

- **Web-based viewer** with zoom and pan controls
- **Automatic rendering** of SPDX files to SVG diagrams
- **Lightweight** - installs published `spdx-to-mermaid` package from FloxHub
- **Shareable** - push this environment to FloxHub for team use

## Prerequisites

The `spdx-to-mermaid` package must be published to FloxHub first. Once published:

1. Uncomment the package in `.flox/env/manifest.toml`:
   ```toml
   spdx-to-mermaid.pkg-path = "spdx-to-mermaid"
   ```

2. Update the environment:
   ```bash
   flox install
   ```

## Quick Start

### View an SPDX file

```bash
# Activate the environment
flox activate

# View an SPDX file (opens in browser)
just show /path/to/file.spdx.json

# Or manually:
spdx-to-mermaid file.spdx.json > diagram.mmd
mmdc -i diagram.mmd -o diagram.svg --configFile mermaid-config.json
flox services start http-server
chromium http://localhost:3000/viewer.html
```

### Available Commands

- `just show <file>` - Convert and view SPDX file in browser
- `flox services start http-server` - Start the HTTP server manually
- `flox services stop` - Stop all services

## Environment Contents

- **spdx-to-mermaid** - CLI tool for converting SPDX to Mermaid (from FloxHub)
- **mermaid-cli** - Renders Mermaid diagrams to SVG
- **chromium** - Browser for viewing diagrams (Linux only)
- **python3** - HTTP server for serving viewer
- **HTTP server service** - Automatic web server on port 3000

## Sharing on FloxHub

Push this environment to FloxHub to share with your team:

```bash
# Push to your personal FloxHub
flox push

# Or push to an organization
flox push --owner your-org
```

Team members can then pull and use it:

```bash
flox pull owner/spdx-viewer
cd spdx-viewer
flox activate
```

## File Structure

```
spdx-viewer/
├── .flox/              # Flox environment configuration
├── viewer.html         # Interactive diagram viewer
├── mermaid-config.json # Mermaid rendering configuration
├── puppeteer-config.json # Browser automation config
├── Justfile           # Convenience commands
└── README.md          # This file
```

## Differences from Development Environment

This viewer environment is separate from the main development environment:

- **No build tools** - Uses published package instead of building
- **No source code** - Only visualization tools
- **Lightweight** - Faster to set up and share
- **Shareable** - Can be pushed to FloxHub

The main development environment at the repository root includes build configuration, Python source code, and publishing tools.
