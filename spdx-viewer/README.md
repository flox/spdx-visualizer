# SPDX Viewer Environment

A standalone Flox environment for visualizing SPDX files as interactive Mermaid diagrams.

## Features

- **Web-based viewer** with zoom and pan controls
- **Automatic rendering** of SPDX files to SVG diagrams
- **Lightweight** - installs published `spdx-to-mermaid` package from FloxHub
- **Shareable** - push this environment to FloxHub for team use

## Quick Start

### View an SPDX file

```bash
# Activate the environment
flox activate

# View an SPDX file (opens in browser)
spdx-show /path/to/file.spdx.json

# View with options
spdx-show /path/to/file.spdx.json --compact --max-packages 20
```

### Available Commands

When you activate the environment, these bash functions are available:

- **`spdx-show <file> [options]`** - Convert and view SPDX file in browser
- **`spdx-svg <file> [output.svg] [options]`** - Convert SPDX to SVG file
- **`spdx-to-mermaid <file> [options]`** - Convert SPDX to Mermaid diagram (stdout)
- **`spdx-serve`** - Start the HTTP server manually
- **`spdx-stop`** - Stop all services

#### Examples

```bash
# Basic visualization
spdx-show myfile.spdx.json

# Compact view with limited packages
spdx-show myfile.spdx.json --compact --max-packages 10

# Create SVG file
spdx-svg myfile.spdx.json output.svg

# Create Mermaid markdown
spdx-to-mermaid myfile.spdx.json > diagram.md
```

## Environment Contents

### Packages
- **spdx-to-mermaid** - CLI tool for converting SPDX to Mermaid (from flox/spdx-to-mermaid)
- **mermaid-cli** - Renders Mermaid diagrams to SVG
- **chromium** - Browser for viewing diagrams (Linux only)
- **python3** - HTTP server for serving viewer

### Services
- **http-server** - Web server on port 3000 for viewing diagrams

### Shell Functions
The environment provides convenient bash functions (defined in the profile):
- `spdx-show` - Interactive viewer
- `spdx-svg` - SVG conversion
- `spdx-serve` - Start server
- `spdx-stop` - Stop services

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
│   └── env/
│       └── manifest.toml # Includes bash functions + asset files
├── viewer.html         # Created on activation from manifest
├── mermaid-config.json # Created on activation from manifest
├── puppeteer-config.json # Created on activation from manifest
└── README.md          # This file
```

**Note:** The viewer assets (viewer.html, mermaid-config.json, puppeteer-config.json) are embedded in the manifest and written to the project directory on first activation. This makes the environment fully self-contained when pushed to FloxHub.

## Differences from Development Environment

This viewer environment is separate from the main development environment:

- **No build tools** - Uses published `flox/spdx-to-mermaid` package
- **No source code** - Only visualization tools
- **Lightweight** - Minimal dependencies (no `just`, `uv`, or dev tools)
- **Self-contained** - All commands are bash functions in the environment profile
- **Shareable** - Can be pushed to FloxHub for team use

The main development environment at the repository root includes build configuration, Python source code, `uv`, and publishing tools.
