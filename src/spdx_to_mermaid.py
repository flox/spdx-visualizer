#!/usr/bin/env python3
"""
SPDX to Mermaid Converter

This script reads an SPDX file (JSON, YAML, XML, RDF, or tag-value format)
and generates a comprehensive Mermaid tree diagram showing all elements,
relationships, and annotations.
"""

import argparse
import json
import sys
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


def format_node_label(
    element_id: str, element_data: Dict[str, Any], element_type: str
) -> str:
    """
    Format a comprehensive node label showing all available data from the element.
    """
    lines = []

    # Add type header with purpose if available
    if "primaryPackagePurpose" in element_data and element_data["primaryPackagePurpose"]:
        purpose = element_data["primaryPackagePurpose"]
        lines.append(f"[{element_type} - {purpose}]")
    else:
        lines.append(f"[{element_type}]")

    # Add name/ID (highlighted - first)
    if "name" in element_data and element_data["name"]:
        lines.append(f"<b><font size='4' color='#0066cc'>Name:</font></b> {escape_quotes(str(element_data['name']))}")
    else:
        lines.append(f"<b><font size='4' color='#0066cc'>ID:</font></b> {escape_quotes(element_id)}")

    # Add summary if available (highlighted - second)
    if "summary" in element_data and element_data["summary"]:
        summary = escape_quotes(str(element_data["summary"]))
        if len(summary) > 60:
            summary = summary[:57] + "..."
        lines.append(f"<b><font size='4' color='#0066cc'>Summary:</font></b> {summary}")

    # Add version if available (highlighted - second)
    if "version" in element_data and element_data["version"]:
        lines.append(f"<b><font size='4' color='#0066cc'>Version:</font></b> {escape_quotes(str(element_data['version']))}")

    # Add license info (highlighted - third)
    if "licenseConcluded" in element_data and element_data["licenseConcluded"]:
        lines.append(f"<b><font size='4' color='#0066cc'>License:</font></b> {escape_quotes(str(element_data['licenseConcluded']))}")

    # Add license comments if available
    if "licenseComments" in element_data and element_data["licenseComments"]:
        lic_comment = escape_quotes(str(element_data["licenseComments"]))
        if len(lic_comment) > 60:
            lic_comment = lic_comment[:57] + "..."
        lines.append(f"<b>License Note:</b> {lic_comment}")

    # Add download location for packages
    if "downloadLocation" in element_data and element_data["downloadLocation"]:
        download = escape_quotes(str(element_data["downloadLocation"]))
        if len(download) > 50:
            download = download[:47] + "..."
        lines.append(f"<b>Download:</b> {download}")

    # Add supplier if available
    if "supplier" in element_data and element_data["supplier"]:
        lines.append(f"<b>Supplier:</b> {escape_quotes(str(element_data['supplier']))}")

    # Add originator if available
    if "originator" in element_data and element_data["originator"]:
        lines.append(f"<b>Originator:</b> {escape_quotes(str(element_data['originator']))}")

    # Add files analyzed status
    if "filesAnalyzed" in element_data:
        lines.append(f"<b>Files Analyzed:</b> {element_data['filesAnalyzed']}")

    # Add verification code if present
    if "verificationCode" in element_data and element_data["verificationCode"]:
        lines.append(f"<b>Verification:</b> {element_data['verificationCode']}")

    # Add checksums if available
    if "checksums" in element_data and element_data["checksums"]:
        checksums = element_data["checksums"]
        if isinstance(checksums, list) and checksums:
            for checksum in checksums[:2]:  # Limit to first 2 checksums
                if isinstance(checksum, dict):
                    algo = checksum.get("algorithm", "")
                    value = checksum.get("checksumValue", "")[:12]  # Truncate
                    lines.append(f"<b>{algo}:</b> {value}...")

    # Add copyright if available
    if "copyrightText" in element_data and element_data["copyrightText"]:
        copyright_text = escape_quotes(str(element_data["copyrightText"]))
        if len(copyright_text) > 40:
            copyright_text = copyright_text[:37] + "..."
        lines.append(f"<b>Copyright:</b> {copyright_text}")

    # Add comment if present
    if "comment" in element_data and element_data["comment"]:
        comment = escape_quotes(str(element_data["comment"]))
        if len(comment) > 50:
            comment = comment[:47] + "..."
        lines.append(f"<b>Comment:</b> {comment}")

    # Add homepage if available
    if "homepage" in element_data and element_data["homepage"]:
        lines.append(f"<b>Homepage:</b> {escape_quotes(str(element_data['homepage']))}")

    # Add document-specific fields
    if element_type == "Document":
        if "created" in element_data and element_data["created"]:
            lines.append(f"<b>Created:</b> {escape_quotes(str(element_data['created']))}")
        if "creators" in element_data and element_data["creators"]:
            creators_str = ", ".join(element_data["creators"])
            if len(creators_str) > 50:
                creators_str = creators_str[:47] + "..."
            lines.append(f"<b>Creators:</b> {escape_quotes(creators_str)}")
        if "namespace" in element_data and element_data["namespace"]:
            namespace = escape_quotes(str(element_data["namespace"]))
            if len(namespace) > 50:
                namespace = namespace[:47] + "..."
            lines.append(f"<b>Namespace:</b> {namespace}")
        if "dataLicense" in element_data and element_data["dataLicense"]:
            lines.append(f"<b>Data License:</b> {escape_quotes(str(element_data['dataLicense']))}")

    # Add package-specific fields
    if element_type == "Package":
        if "licenseDeclared" in element_data and element_data["licenseDeclared"]:
            lines.append(f"<b>License Declared:</b> {escape_quotes(str(element_data['licenseDeclared']))}")
        if "packageFileName" in element_data and element_data["packageFileName"]:
            pkg_file = escape_quotes(str(element_data["packageFileName"]))
            if len(pkg_file) > 50:
                pkg_file = pkg_file[:47] + "..."
            lines.append(f"<b>Package File:</b> {pkg_file}")
        if "externalRefs" in element_data and element_data["externalRefs"]:
            for ref in element_data["externalRefs"][:2]:  # Limit to first 2
                if isinstance(ref, dict):
                    ref_type = ref.get("referenceType", "")
                    ref_loc = ref.get("referenceLocator", "")
                    if len(ref_loc) > 40:
                        ref_loc = ref_loc[:37] + "..."
                    lines.append(f"<b>{ref_type}:</b> {escape_quotes(ref_loc)}")

    # Join all lines with <br/> for Mermaid
    return "<br/>".join(lines)


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
            if hasattr(package, "license_concluded") and package.license_concluded
            else None,
            "licenseDeclared": str(package.license_declared)
            if hasattr(package, "license_declared") and package.license_declared
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
            if hasattr(file, "license_concluded") and file.license_concluded
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
            if hasattr(snippet, "license_concluded") and snippet.license_concluded
            else None,
            "copyrightText": str(snippet.copyright_text)
            if hasattr(snippet, "copyright_text") and snippet.copyright_text
            else None,
        }
        elements[snippet.spdx_id] = snippet_data

    return elements


def generate_mermaid_diagram(doc: Document) -> str:
    """
    Generate a comprehensive Mermaid diagram from an SPDX document.
    """
    elements = extract_elements_from_document(doc)

    # Start the Mermaid diagram with left-right orientation
    lines = ["graph LR"]

    # Track which nodes we've added to avoid duplicates
    added_nodes: Set[str] = set()

    # Add all element nodes
    for element_id, element_data in elements.items():
        node_id = sanitize_node_id(element_id)
        element_type = element_data["type"]
        label = format_node_label(element_id, element_data, element_type)

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

    args = parser.parse_args()

    # Check if file exists
    if not args.spdx_file.exists():
        print(f"Error: File not found: {args.spdx_file}", file=sys.stderr)
        sys.exit(1)

    try:
        # Parse the SPDX file
        doc = parse_file(str(args.spdx_file))

        # Generate Mermaid diagram
        mermaid = generate_mermaid_diagram(doc)

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
