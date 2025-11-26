# Convert and view SPDX file as Mermaid diagram

# Show SPDX file as SVG diagram in Chrome
show spdx_file:
    #!/usr/bin/env bash
    set -euo pipefail
    tmpfile=$(mktemp --suffix=.svg)
    flox activate -- sh -c "uv run spdx-to-mermaid {{spdx_file}} | mmdc -i - -o $tmpfile"
    google-chrome $tmpfile
