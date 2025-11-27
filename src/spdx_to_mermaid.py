#!/usr/bin/env python3
"""
SPDX to Mermaid Converter

This script reads an SPDX file (JSON, YAML, XML, RDF, or tag-value format)
and generates a comprehensive Mermaid tree diagram showing all elements,
relationships, and annotations.
"""

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Set
from spdx_tools.spdx.parser.parse_anything import parse_file
from spdx_tools.spdx.model.document import Document
from spdx_tools.spdx.model.package import Package
from spdx_tools.spdx.model.file import File
from spdx_tools.spdx.model.snippet import Snippet
from spdx_tools.spdx.model.relationship import Relationship


def sanitize_node_id(spdx_id) -> str:
    """
    Convert SPDX ID to a valid Mermaid node ID.
    Replace special characters with underscores.
    Handles both string IDs and special SPDX objects like SpdxNoAssertion.
    """
    # Convert to string first to handle special SPDX objects
    spdx_id_str = str(spdx_id)
    return spdx_id_str.replace("SPDXRef-", "").replace("-", "_").replace(".", "_")


def escape_quotes(text: str) -> str:
    """Escape quotes in text for Mermaid."""
    return text.replace('"', "'")


def preprocess_spdx_file(file_path: Path) -> Path:
    """
    Preprocess SPDX JSON file to fix common compatibility issues.

    Fixes:
    - Timestamps missing 'Z' suffix (e.g., "2025-11-27T15:17:19" -> "2025-11-27T15:17:19Z")

    Args:
        file_path: Path to the original SPDX file

    Returns:
        Path to the preprocessed file (may be original or temp file)
    """
    # Only preprocess JSON files
    if file_path.suffix.lower() != '.json':
        return file_path

    try:
        # Read the file
        content = file_path.read_text()

        # Check if we need to fix timestamps
        # Pattern: ISO 8601 timestamp without timezone (missing Z)
        # Example: "2025-11-27T15:17:19" should be "2025-11-27T15:17:19Z"
        needs_fix = False

        # Look for timestamps that are missing the Z suffix
        # Match: "2025-11-27T15:17:19" but not "2025-11-27T15:17:19Z"
        timestamp_pattern = r'"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"(?!Z)'

        if re.search(timestamp_pattern, content):
            needs_fix = True

        if not needs_fix:
            return file_path

        # Fix timestamps by adding Z suffix
        fixed_content = re.sub(
            timestamp_pattern,
            r'"\1Z"',
            content
        )

        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            prefix='spdx_preprocessed_'
        ) as tmp:
            tmp.write(fixed_content)
            tmp_path = Path(tmp.name)

        return tmp_path

    except Exception as e:
        # If preprocessing fails, return original file
        print(f"Warning: Could not preprocess file: {e}", file=sys.stderr)
        return file_path


def format_node_label(
    element_id: str, element_data: Dict[str, Any], element_type: str, compact: bool = False, exclude_external_refs: bool = False
) -> str:
    """
    Format a comprehensive node label showing all available data from the element.

    NOTE: This function generates PLAIN TEXT labels only (no HTML formatting).
    HTML tags like <b>, <font>, and <br/> are NOT supported when mermaid's
    htmlLabels config is set to false. Using HTML in labels causes mmdc to fail
    with "UnknownDiagramError: No diagram type detected".

    We use newlines (\n) instead of <br/> for line breaks in plain text mode.

    FORMATTING LOST by not using HTML:
    - Bold text for field labels (was: <b>Label:</b>)
    - Colored/sized headers for key fields like Name, Version (was: <font size='4' color='#0066cc'>)
    - All text is now uniform weight and color

    Args:
        element_id: The SPDX element ID
        element_data: Dictionary containing element data
        element_type: Type of the element (Document, Package, File, Snippet)
        compact: If True, only show essential fields
        exclude_external_refs: If True, skip external references (CPE, PURL)
    """
    lines = []

    # Add type header with purpose if available
    if "primaryPackagePurpose" in element_data and element_data["primaryPackagePurpose"]:
        purpose = element_data["primaryPackagePurpose"]
        lines.append(f"[{element_type} - {purpose}]")
    else:
        lines.append(f"[{element_type}]")

    # Add name/ID (plain text - no HTML formatting)
    if "name" in element_data and element_data["name"]:
        lines.append(f"Name: {escape_quotes(str(element_data['name']))}")
    else:
        lines.append(f"ID: {escape_quotes(element_id)}")

    # Add summary if available (plain text - no HTML formatting)
    if "summary" in element_data and element_data["summary"]:
        summary = escape_quotes(str(element_data["summary"]))
        if len(summary) > 60:
            summary = summary[:57] + "..."
        lines.append(f"Summary: {summary}")

    # Add version if available (plain text - no HTML formatting)
    if "version" in element_data and element_data["version"]:
        lines.append(f"Version: {escape_quotes(str(element_data['version']))}")

    # Add license info (plain text - no HTML formatting)
    if "licenseConcluded" in element_data and element_data["licenseConcluded"]:
        lines.append(f"License: {escape_quotes(str(element_data['licenseConcluded']))}")

    # Add license comments if available
    if "licenseComments" in element_data and element_data["licenseComments"]:
        lic_comment = escape_quotes(str(element_data["licenseComments"]))
        if len(lic_comment) > 60:
            lic_comment = lic_comment[:57] + "..."
        lines.append(f"License Note: {lic_comment}")

    # In compact mode, skip optional fields
    if not compact:
        # Add download location for packages (plain text - no HTML formatting)
        if "downloadLocation" in element_data and element_data["downloadLocation"]:
            download = escape_quotes(str(element_data["downloadLocation"]))
            if len(download) > 50:
                download = download[:47] + "..."
            lines.append(f"Download: {download}")

        # Add supplier if available (plain text - no HTML formatting)
        if "supplier" in element_data and element_data["supplier"]:
            lines.append(f"Supplier: {escape_quotes(str(element_data['supplier']))}")

        # Add originator if available (plain text - no HTML formatting)
        if "originator" in element_data and element_data["originator"]:
            lines.append(f"Originator: {escape_quotes(str(element_data['originator']))}")

        # Add files analyzed status (plain text - no HTML formatting)
        if "filesAnalyzed" in element_data:
            lines.append(f"Files Analyzed: {element_data['filesAnalyzed']}")

        # Add verification code if present (plain text - no HTML formatting)
        if "verificationCode" in element_data and element_data["verificationCode"]:
            lines.append(f"Verification: {element_data['verificationCode']}")

        # Add checksums if available (plain text - no HTML formatting)
        if "checksums" in element_data and element_data["checksums"]:
            checksums = element_data["checksums"]
            if isinstance(checksums, list) and checksums:
                for checksum in checksums[:2]:  # Limit to first 2 checksums
                    if isinstance(checksum, dict):
                        algo = checksum.get("algorithm", "")
                        value = checksum.get("checksumValue", "")[:12]  # Truncate
                        lines.append(f"{algo}: {value}...")

        # Add copyright if available (plain text - no HTML formatting)
        if "copyrightText" in element_data and element_data["copyrightText"]:
            copyright_text = escape_quotes(str(element_data["copyrightText"]))
            if len(copyright_text) > 40:
                copyright_text = copyright_text[:37] + "..."
            lines.append(f"Copyright: {copyright_text}")

        # Add comment if present (plain text - no HTML formatting)
        if "comment" in element_data and element_data["comment"]:
            comment = escape_quotes(str(element_data["comment"]))
            if len(comment) > 50:
                comment = comment[:47] + "..."
            lines.append(f"Comment: {comment}")

        # Add homepage if available (plain text - no HTML formatting)
        if "homepage" in element_data and element_data["homepage"]:
            lines.append(f"Homepage: {escape_quotes(str(element_data['homepage']))}")

    # Add document-specific fields (plain text - no HTML formatting)
    if element_type == "Document" and not compact:
        if "created" in element_data and element_data["created"]:
            lines.append(f"Created: {escape_quotes(str(element_data['created']))}")
        if "creators" in element_data and element_data["creators"]:
            creators_str = ", ".join(element_data["creators"])
            if len(creators_str) > 50:
                creators_str = creators_str[:47] + "..."
            lines.append(f"Creators: {escape_quotes(creators_str)}")
        if "namespace" in element_data and element_data["namespace"]:
            namespace = escape_quotes(str(element_data["namespace"]))
            if len(namespace) > 50:
                namespace = namespace[:47] + "..."
            lines.append(f"Namespace: {namespace}")
        if "dataLicense" in element_data and element_data["dataLicense"]:
            lines.append(f"Data License: {escape_quotes(str(element_data['dataLicense']))}")

    # Add package-specific fields (plain text - no HTML formatting)
    if element_type == "Package":
        if not compact and "licenseDeclared" in element_data and element_data["licenseDeclared"]:
            lines.append(f"License Declared: {escape_quotes(str(element_data['licenseDeclared']))}")
        if not compact and "packageFileName" in element_data and element_data["packageFileName"]:
            pkg_file = escape_quotes(str(element_data["packageFileName"]))
            if len(pkg_file) > 50:
                pkg_file = pkg_file[:47] + "..."
            lines.append(f"Package File: {pkg_file}")
        # Only show external refs if not excluded (plain text - no HTML formatting)
        if not exclude_external_refs and "externalRefs" in element_data and element_data["externalRefs"]:
            limit = 1 if compact else 2  # Show fewer in compact mode
            for ref in element_data["externalRefs"][:limit]:
                if isinstance(ref, dict):
                    ref_type = ref.get("referenceType", "")
                    ref_loc = ref.get("referenceLocator", "")
                    if len(ref_loc) > 40:
                        ref_loc = ref_loc[:37] + "..."
                    lines.append(f"{ref_type}: {escape_quotes(ref_loc)}")

    # Join all lines with actual newlines for plain text labels
    # NOTE: When htmlLabels is false, we need ACTUAL newline characters, not escape sequences
    # The escape sequence "\n" renders as literal \n text when htmlLabels: false
    return "\n".join(lines)


def extract_elements_from_document(doc: Document) -> Dict[str, Dict[str, Any]]:
    """
    Extract all elements (packages, files, snippets) from the SPDX document.
    """
    elements = {}

    # Add document itself
    elements["SPDXRef-DOCUMENT"] = {
        "type": "Document",
        "name": doc.creation_info.name
        if hasattr(doc.creation_info, "name")
        else doc.name,
        "version": doc.creation_info.spdx_version
        if hasattr(doc.creation_info, "spdx_version")
        else None,
        "namespace": doc.creation_info.document_namespace
        if hasattr(doc.creation_info, "document_namespace")
        else None,
        "created": str(doc.creation_info.created)
        if hasattr(doc.creation_info, "created")
        else None,
        "creators": [str(c) for c in doc.creation_info.creators]
        if hasattr(doc.creation_info, "creators")
        else [],
        "dataLicense": doc.creation_info.data_license
        if hasattr(doc.creation_info, "data_license")
        else None,
    }

    # Add packages
    for package in doc.packages:
        pkg_data = {
            "type": "Package",
            "name": package.name,
            "version": package.version
            if hasattr(package, "version") and package.version
            else None,
            "downloadLocation": str(package.download_location)
            if hasattr(package, "download_location")
            else None,
            "filesAnalyzed": package.files_analyzed
            if hasattr(package, "files_analyzed")
            else None,
            "supplier": str(package.supplier)
            if hasattr(package, "supplier") and package.supplier
            else None,
            "originator": str(package.originator)
            if hasattr(package, "originator") and package.originator
            else None,
            "homepage": str(package.homepage)
            if hasattr(package, "homepage") and package.homepage
            else None,
            "licenseConcluded": str(package.license_concluded)
            if hasattr(package, "license_concluded") and package.license_concluded is not None
            else None,
            "licenseDeclared": str(package.license_declared)
            if hasattr(package, "license_declared") and package.license_declared is not None
            else None,
            "licenseComments": package.license_comment
            if hasattr(package, "license_comment") and package.license_comment
            else None,
            "copyrightText": str(package.copyright_text)
            if hasattr(package, "copyright_text") and package.copyright_text
            else None,
            "comment": package.comment
            if hasattr(package, "comment") and package.comment
            else None,
            "summary": package.summary
            if hasattr(package, "summary") and package.summary
            else None,
            "primaryPackagePurpose": str(package.primary_package_purpose)
            if hasattr(package, "primary_package_purpose") and package.primary_package_purpose
            else None,
            "checksums": [
                {"algorithm": str(c.algorithm), "checksumValue": c.value}
                for c in package.checksums
            ]
            if hasattr(package, "checksums") and package.checksums
            else [],
            "verificationCode": str(package.verification_code.value)
            if hasattr(package, "verification_code") and package.verification_code
            else None,
            "packageFileName": package.file_name
            if hasattr(package, "file_name") and package.file_name
            else None,
            "externalRefs": [
                {
                    "referenceType": str(ref.reference_type) if hasattr(ref, 'reference_type') else str(ref.category),
                    "referenceLocator": ref.locator if hasattr(ref, 'locator') else str(ref),
                    "referenceCategory": str(ref.category) if hasattr(ref, 'category') else ""
                }
                for ref in package.external_references
            ]
            if hasattr(package, "external_references") and package.external_references
            else [],
        }
        elements[package.spdx_id] = pkg_data

    # Add files
    for file in doc.files:
        file_data = {
            "type": "File",
            "name": file.name,
            "licenseConcluded": str(file.license_concluded)
            if hasattr(file, "license_concluded") and file.license_concluded is not None
            else None,
            "copyrightText": str(file.copyright_text)
            if hasattr(file, "copyright_text") and file.copyright_text
            else None,
            "comment": file.comment
            if hasattr(file, "comment") and file.comment
            else None,
            "checksums": [
                {"algorithm": str(c.algorithm), "checksumValue": c.value}
                for c in file.checksums
            ]
            if hasattr(file, "checksums") and file.checksums
            else [],
        }
        elements[file.spdx_id] = file_data

    # Add snippets
    for snippet in doc.snippets:
        snippet_data = {
            "type": "Snippet",
            "name": snippet.name
            if hasattr(snippet, "name") and snippet.name
            else snippet.spdx_id,
            "comment": snippet.comment
            if hasattr(snippet, "comment") and snippet.comment
            else None,
            "licenseConcluded": str(snippet.license_concluded)
            if hasattr(snippet, "license_concluded") and snippet.license_concluded is not None
            else None,
            "copyrightText": str(snippet.copyright_text)
            if hasattr(snippet, "copyright_text") and snippet.copyright_text
            else None,
        }
        elements[snippet.spdx_id] = snippet_data

    return elements


def generate_mermaid_diagram(doc: Document, compact: bool = False, max_packages: int = None, exclude_external_refs: bool = False) -> str:
    """
    Generate a comprehensive Mermaid diagram from an SPDX document.

    Args:
        doc: The SPDX document to visualize
        compact: If True, generate compact output with fewer fields
        max_packages: Maximum number of packages to include (None for all)
        exclude_external_refs: If True, exclude external references from labels
    """
    elements = extract_elements_from_document(doc)

    # Limit packages if requested
    if max_packages is not None:
        package_elements = {k: v for k, v in elements.items() if v["type"] == "Package"}
        if len(package_elements) > max_packages:
            # Keep document element and limit packages
            limited_packages = dict(list(package_elements.items())[:max_packages])
            elements = {k: v for k, v in elements.items() if v["type"] != "Package"}
            elements.update(limited_packages)

    # Start the Mermaid diagram with left-right orientation
    lines = ["graph LR"]

    # Track which nodes we've added to avoid duplicates
    added_nodes: Set[str] = set()

    # Add all element nodes
    for element_id, element_data in elements.items():
        node_id = sanitize_node_id(element_id)
        element_type = element_data["type"]
        label = format_node_label(element_id, element_data, element_type, compact=compact, exclude_external_refs=exclude_external_refs)

        # Use different shapes for different element types
        if element_type == "Document":
            lines.append(f'    {node_id}["{label}"]')
            lines.append(
                f"    style {node_id} fill:#e1f5ff,stroke:#01579b,stroke-width:3px"
            )
        elif element_type == "Package":
            lines.append(f'    {node_id}["{label}"]')
            # Color code based on package purpose
            purpose = element_data.get("primaryPackagePurpose")
            if purpose and "SOURCE" in str(purpose):
                # Orange/amber for SOURCE packages (build specifications)
                lines.append(
                    f"    style {node_id} fill:#fff3e0,stroke:#e65100,stroke-width:2px"
                )
            elif purpose and "APPLICATION" in str(purpose):
                # Purple for APPLICATION packages (runtime artifacts)
                lines.append(
                    f"    style {node_id} fill:#f3e5f5,stroke:#4a148c,stroke-width:2px"
                )
            else:
                # Default purple for packages without purpose specified
                lines.append(
                    f"    style {node_id} fill:#f3e5f5,stroke:#4a148c,stroke-width:2px"
                )
        elif element_type == "File":
            lines.append(f'    {node_id}["{label}"]')
            lines.append(
                f"    style {node_id} fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px"
            )
        elif element_type == "Snippet":
            lines.append(f'    {node_id}["{label}"]')
            lines.append(
                f"    style {node_id} fill:#fff3e0,stroke:#e65100,stroke-width:2px"
            )

        added_nodes.add(node_id)

    # Add relationships with full annotations
    for relationship in doc.relationships:
        source_id = sanitize_node_id(relationship.spdx_element_id)
        target_id = sanitize_node_id(relationship.related_spdx_element_id)
        # Get just the enum name, not the full "RelationshipType.VALUE" string
        rel_type = relationship.relationship_type.name if hasattr(relationship.relationship_type, 'name') else str(relationship.relationship_type)

        # Add comment to relationship if present
        if hasattr(relationship, "comment") and relationship.comment:
            comment = escape_quotes(relationship.comment)
            edge_label = f"{rel_type}<br/>{comment}"
        else:
            edge_label = rel_type

        # Create the edge with label
        # For GENERATED_FROM: keep natural direction (generated element points to source)
        lines.append(f'    {source_id} -->|"{edge_label}"| {target_id}')

    # Add legend
    lines.append("")
    lines.append("    %% Legend")
    lines.append(
        '    legend["Legend:<br/>Blue = Document<br/>Purple = Package (APPLICATION)<br/>Orange = Package (SOURCE)<br/>Green = File<br/>Orange = Snippet"]'
    )
    lines.append(
        "    style legend fill:#fafafa,stroke:#666,stroke-width:1px,stroke-dasharray: 5 5"
    )

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert SPDX files to Mermaid tree diagrams with comprehensive element data"
    )
    parser.add_argument(
        "spdx_file",
        type=Path,
        help="Path to the SPDX file (JSON, YAML, XML, RDF, or tag-value format)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output markdown file (default: stdout)"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Generate compact output (fewer fields, shorter labels)",
    )
    parser.add_argument(
        "--max-packages",
        type=int,
        help="Limit the number of packages to include in the diagram",
    )
    parser.add_argument(
        "--exclude-external-refs",
        action="store_true",
        help="Exclude external references (CPE, PURL) from labels",
    )

    args = parser.parse_args()

    # Check if file exists
    if not args.spdx_file.exists():
        print(f"Error: File not found: {args.spdx_file}", file=sys.stderr)
        sys.exit(1)

    try:
        # Preprocess the file to fix common issues
        processed_file = preprocess_spdx_file(args.spdx_file)

        # Parse the SPDX file
        doc = parse_file(str(processed_file))

        # Clean up temp file if one was created
        if processed_file != args.spdx_file:
            try:
                processed_file.unlink()
            except:
                pass

        # Generate Mermaid diagram
        mermaid = generate_mermaid_diagram(
            doc,
            compact=args.compact,
            max_packages=args.max_packages,
            exclude_external_refs=args.exclude_external_refs
        )

        # Output to file or stdout
        if args.output:
            args.output.write_text(mermaid)
            print(f"Diagram written to {args.output}")
        else:
            print(mermaid)

    except Exception as e:
        print(f"Error processing SPDX file: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
