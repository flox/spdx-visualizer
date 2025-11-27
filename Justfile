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
    mmd_file=$(mktemp --suffix=.mmd)
    svg_file="$project_dir/diagram.svg"
    viewer_html="$project_dir/viewer.html"
    config_path="$project_dir/mermaid-config.json"

    # Start HTTP server using flox services if not already running
    if ! lsof -i:3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Starting HTTP server via flox services..."
        flox services start http-server
        sleep 1  # Give server time to start
    fi

    # Convert relative path to absolute from invocation directory
    spdx_path=$(realpath "{{invocation_directory()}}/{{spdx_file}}")

    # Generate mermaid diagram to temp file (mmdc doesn't handle stdin properly)
    uv run spdx-to-mermaid "$spdx_path" {{EXTRA}} > "$mmd_file"

    # Convert to SVG (viewer.html expects diagram.svg in project root)
    mmdc -i "$mmd_file" -o "$svg_file" --configFile "$config_path"

    # Open viewer in browser via HTTP (avoids CORS issues)
    xdg-open "http://localhost:3000/viewer.html"

    # Cleanup temp mermaid file only (keep diagram.svg for viewer)
    rm -f "$mmd_file"
