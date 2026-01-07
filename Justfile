# Convert and view SPDX file as Mermaid diagram

# Start HTTP server for viewer using flox services
serve:
    flox services start http-server

# Show SPDX file as SVG diagram in browser with zoom
show spdx_file +EXTRA="":
    #!/usr/bin/env bash
    set -euo pipefail
    # Paths
    project_dir="{{justfile_directory()}}"
    temp_base=$(mktemp)
    mmd_file="${temp_base}.mmd"
    mv "$temp_base" "$mmd_file"
    svg_file="$project_dir/diagram.svg"
    viewer_html="$project_dir/viewer.html"
    config_path="$project_dir/mermaid-config.json"

    # Start HTTP server using flox services if not already running
    if ! lsof -i:3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Starting HTTP server via flox services..."
        flox services start http-server
        sleep 1  # Give server time to start
    fi

    # Convert to absolute path (handles relative, absolute, and tilde paths)
    spdx_path=$(cd "{{invocation_directory()}}" && realpath "{{spdx_file}}")

    # Generate mermaid diagram to temp file (mmdc doesn't handle stdin properly)
    uv run spdx-to-mermaid "$spdx_path" {{EXTRA}} > "$mmd_file"

    # Convert to SVG (viewer.html expects diagram.svg in project root)
    mmdc -i "$mmd_file" -o "$svg_file" --configFile "$config_path" -p "$project_dir/puppeteer-config.json"

    # Open viewer in browser via HTTP (avoids CORS issues)
    # Unset CHROME_DEVEL_SANDBOX to avoid Nix sandbox issues on non-NixOS
    CHROME_DEVEL_SANDBOX="" chromium --no-sandbox "http://localhost:3000/viewer.html"

    # Cleanup temp mermaid file only (keep diagram.svg for viewer)
    rm -f "$mmd_file"
