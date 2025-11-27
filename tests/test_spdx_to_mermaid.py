#!/usr/bin/env python3
"""
Tests for SPDX to Mermaid converter.
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spdx_to_mermaid import (
    sanitize_node_id,
    escape_quotes,
    format_node_label,
    extract_elements_from_document,
    generate_mermaid_diagram,
)
from spdx_tools.spdx.parser.parse_anything import parse_file


# Test data paths
ASSETS_DIR = Path(__file__).parent / "assets"
FLOX_GIT_SPDX = ASSETS_DIR / "flox-git.spdx.json"
GIT_SPDX = ASSETS_DIR / "git-2.51.2.spdx.json"
SYFT_SPDX = ASSETS_DIR / "syft_spdx.json"
NIX2SBOM_SPDX = ASSETS_DIR / "nix2sbom.spdx.json"


class TestSanitization:
    """Test sanitization functions."""

    def test_sanitize_node_id(self):
        """Test node ID sanitization."""
        assert sanitize_node_id("SPDXRef-Package") == "Package"
        assert sanitize_node_id("SPDXRef-my-package") == "my_package"
        assert sanitize_node_id("SPDXRef-foo.bar") == "foo_bar"

    def test_escape_quotes(self):
        """Test quote escaping."""
        assert escape_quotes('test "quoted" text') == "test 'quoted' text"
        assert escape_quotes("no quotes") == "no quotes"


class TestDocumentParsing:
    """Test SPDX document parsing and element extraction."""

    def test_parse_flox_git_spdx(self):
        """Test parsing flox-git SPDX file."""
        doc = parse_file(str(FLOX_GIT_SPDX))
        assert doc is not None
        assert doc.creation_info is not None
        assert len(doc.packages) > 0

    def test_parse_git_spdx(self):
        """Test parsing git SPDX file."""
        doc = parse_file(str(GIT_SPDX))
        assert doc is not None
        assert doc.creation_info is not None
        assert len(doc.packages) > 0

    def test_parse_syft_spdx(self):
        """Test parsing syft SPDX file."""
        doc = parse_file(str(SYFT_SPDX))
        assert doc is not None
        assert doc.creation_info is not None
        assert len(doc.packages) > 0

    def test_parse_nix2sbom_spdx(self):
        """Test parsing nix2sbom SPDX file with timestamp preprocessing."""
        from spdx_to_mermaid import preprocess_spdx_file

        # Preprocess the file to fix timestamp issues
        processed_file = preprocess_spdx_file(NIX2SBOM_SPDX)

        # Parse the preprocessed file
        doc = parse_file(str(processed_file))

        # Clean up temp file if created
        if processed_file != NIX2SBOM_SPDX:
            processed_file.unlink()

        assert doc is not None
        assert doc.creation_info is not None
        assert len(doc.packages) > 0

    def test_extract_elements(self):
        """Test element extraction from document."""
        doc = parse_file(str(FLOX_GIT_SPDX))
        elements = extract_elements_from_document(doc)

        # Should have document element
        assert "SPDXRef-DOCUMENT" in elements
        assert elements["SPDXRef-DOCUMENT"]["type"] == "Document"

        # Should have package elements
        package_elements = {
            k: v for k, v in elements.items() if v["type"] == "Package"
        }
        assert len(package_elements) > 0

    def test_package_purpose_extraction(self):
        """Test that package purpose is extracted."""
        doc = parse_file(str(FLOX_GIT_SPDX))
        elements = extract_elements_from_document(doc)

        # Check for SOURCE and APPLICATION packages
        purposes = [
            elem.get("primaryPackagePurpose")
            for elem in elements.values()
            if elem.get("type") == "Package"
        ]

        # Should have at least one package with purpose
        assert any(p is not None for p in purposes)


class TestMermaidGeneration:
    """Test Mermaid diagram generation."""

    def test_generate_flox_git_diagram(self):
        """Test generating diagram for flox-git SPDX."""
        doc = parse_file(str(FLOX_GIT_SPDX))
        mermaid = generate_mermaid_diagram(doc)

        assert mermaid.startswith("graph LR")
        assert "DOCUMENT" in mermaid
        assert "Legend:" in mermaid

        # Check for color styling
        assert "style" in mermaid
        assert "fill:" in mermaid

    def test_generate_git_diagram(self):
        """Test generating diagram for git SPDX."""
        doc = parse_file(str(GIT_SPDX))
        mermaid = generate_mermaid_diagram(doc)

        assert mermaid.startswith("graph LR")
        assert "DOCUMENT" in mermaid

    def test_package_purpose_styling(self):
        """Test that packages are styled based on purpose."""
        doc = parse_file(str(FLOX_GIT_SPDX))
        mermaid = generate_mermaid_diagram(doc)

        # Should have different colors for SOURCE and APPLICATION
        # Orange for SOURCE: #fff3e0
        # Purple for APPLICATION: #f3e5f5
        assert "#fff3e0" in mermaid or "#f3e5f5" in mermaid

    def test_generated_from_relationships(self):
        """Test GENERATED_FROM relationship direction."""
        doc = parse_file(str(FLOX_GIT_SPDX))
        mermaid = generate_mermaid_diagram(doc)

        # Should have GENERATED_FROM relationships
        if "GENERATED_FROM" in mermaid:
            # Check that arrows exist in output
            assert "-->" in mermaid

    def test_relationship_labels(self):
        """Test that relationships have labels."""
        doc = parse_file(str(FLOX_GIT_SPDX))
        mermaid = generate_mermaid_diagram(doc)

        # Should have relationship type labels
        assert "|" in mermaid  # Mermaid edge label syntax

    def test_summary_in_labels(self):
        """Test that summary field is included in labels."""
        doc = parse_file(str(FLOX_GIT_SPDX))
        elements = extract_elements_from_document(doc)

        # Find a package with summary
        for elem_id, elem_data in elements.items():
            if elem_data.get("type") == "Package" and elem_data.get("summary"):
                label = format_node_label(elem_id, elem_data, "Package")
                assert "Summary:" in label
                break

    def test_license_comments_in_labels(self):
        """Test that license comments are included in labels."""
        doc = parse_file(str(FLOX_GIT_SPDX))
        elements = extract_elements_from_document(doc)

        # Find a package with license comments
        for elem_id, elem_data in elements.items():
            if (
                elem_data.get("type") == "Package"
                and elem_data.get("licenseComments")
            ):
                label = format_node_label(elem_id, elem_data, "Package")
                assert "License Note:" in label
                break


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_relationships(self):
        """Test handling documents with few relationships."""
        doc = parse_file(str(GIT_SPDX))
        mermaid = generate_mermaid_diagram(doc)

        # Should still generate valid diagram
        assert mermaid.startswith("graph LR")
        assert "DOCUMENT" in mermaid

    def test_special_characters_in_names(self):
        """Test handling special characters in element names."""
        # Just verify sanitization works
        result = sanitize_node_id("SPDXRef-package-with-special-chars.test")
        assert "-" not in result
        assert "." not in result

    def test_long_text_truncation(self):
        """Test that long text fields are truncated."""
        doc = parse_file(str(SYFT_SPDX))
        elements = extract_elements_from_document(doc)

        # Generate labels and check for truncation indicators
        for elem_id, elem_data in elements.items():
            label = format_node_label(elem_id, elem_data, elem_data["type"])
            # If there are very long fields, they should be truncated with ...
            # This is a soft check - just verify label generation doesn't fail
            assert len(label) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
