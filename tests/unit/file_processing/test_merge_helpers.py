"""Tests for content merging functionality."""

import pytest

from spec_cli.file_processing.merge_helpers import ContentMerger


class TestContentMerger:
    """Test ContentMerger class."""

    @pytest.fixture
    def content_merger(self) -> ContentMerger:
        """Create ContentMerger instance."""
        return ContentMerger()

    def test_content_section_detection(self, content_merger: ContentMerger) -> None:
        """Test detection of content sections in markdown."""
        content = """# Main Title

Some introductory text here.

## Section One

Content for section one.

### Subsection

More detailed content.

```python
def hello():
    print("Hello, World!")
```

Another paragraph here.

## Section Two

More content.
"""

        sections = content_merger.detect_content_sections(content)

        # Check headings detection
        assert len(sections["headings"]) == 4
        headings = {h["title"]: h["level"] for h in sections["headings"]}
        assert headings["Main Title"] == 1
        assert headings["Section One"] == 2
        assert headings["Subsection"] == 3
        assert headings["Section Two"] == 2

        # Check code blocks detection
        assert len(sections["code_blocks"]) == 1
        code_block = sections["code_blocks"][0]
        assert "def hello():" in code_block["content"]
        assert code_block["language"] == "python"

        # Check paragraphs detection
        assert len(sections["paragraphs"]) >= 2
        paragraph_texts = [p["content"] for p in sections["paragraphs"]]
        assert any("introductory text" in text for text in paragraph_texts)

    def test_content_section_detection_yaml_frontmatter(
        self, content_merger: ContentMerger
    ) -> None:
        """Test detection of YAML frontmatter."""
        content = """---
title: Test Document
author: Test Author
date: 2024-01-01
---

# Document Content

Regular content here.
"""

        sections = content_merger.detect_content_sections(content)

        assert len(sections["yaml_frontmatter"]) == 1
        frontmatter = sections["yaml_frontmatter"][0]
        assert "title: Test Document" in frontmatter["content"]
        assert "author: Test Author" in frontmatter["content"]

    def test_markdown_content_merging_strategies(
        self, content_merger: ContentMerger
    ) -> None:
        """Test different content merging strategies."""
        base_content = "# Original Title\n\nOriginal content here."
        new_content = "# New Title\n\nNew content here."

        # Test replace strategy
        result = content_merger.merge_markdown_content(
            base_content, new_content, "replace"
        )
        assert result == new_content

        # Test append strategy
        result = content_merger.merge_markdown_content(
            base_content, new_content, "append"
        )
        expected = base_content + "\n\n" + new_content
        assert result == expected

        # Test prepend strategy
        result = content_merger.merge_markdown_content(
            base_content, new_content, "prepend"
        )
        expected = new_content + "\n\n" + base_content
        assert result == expected

        # Test invalid strategy
        with pytest.raises(ValueError, match="Unknown merge strategy"):
            content_merger.merge_markdown_content(base_content, new_content, "invalid")

    def test_intelligent_merge_strategy(self, content_merger: ContentMerger) -> None:
        """Test intelligent merging based on content structure."""
        base_content = """# Documentation

## Overview
This is the original overview.

## Usage
Original usage instructions.
"""

        new_content = """# Documentation

## Overview
This is an updated overview.

## Installation
New installation section.

## Advanced Usage
Advanced usage examples.
"""

        result = content_merger.merge_markdown_content(
            base_content, new_content, "intelligent"
        )

        # Should contain base content plus new sections
        assert "original overview" in result.lower()
        assert "installation" in result.lower()
        assert "advanced usage" in result.lower()

        # Should have more content than either original
        assert len(result) > len(base_content)
        assert len(result) > len(new_content)

    def test_conflict_detection_in_content(self, content_merger: ContentMerger) -> None:
        """Test detection of conflicts between content versions."""
        # Test heading level conflicts
        base_content = """# Main Title

## Section One
Content here.
"""

        new_content = """# Main Title

### Section One
Different content here.
"""

        conflicts = content_merger.detect_conflicts(base_content, new_content)

        # Should detect heading level conflict
        heading_conflicts = [
            c for c in conflicts if c["type"] == "heading_level_conflict"
        ]
        assert len(heading_conflicts) == 1
        assert heading_conflicts[0]["heading"] == "section one"
        assert heading_conflicts[0]["base_level"] == 2
        assert heading_conflicts[0]["new_level"] == 3
        assert heading_conflicts[0]["severity"] == "medium"

    def test_conflict_detection_content_divergence(
        self, content_merger: ContentMerger
    ) -> None:
        """Test detection of content divergence conflicts."""
        base_content = "This is about cats and dogs and pets in general."
        new_content = "This discusses cars and trucks and vehicles overall."

        conflicts = content_merger.detect_conflicts(base_content, new_content)

        # Should detect content divergence
        divergence_conflicts = [
            c for c in conflicts if c["type"] == "content_divergence"
        ]
        assert len(divergence_conflicts) == 1

        conflict = divergence_conflicts[0]
        assert conflict["similarity"] < 0.5
        assert conflict["severity"] in ["medium", "high"]

    def test_merge_preview_generation(self, content_merger: ContentMerger) -> None:
        """Test creation of merge previews."""
        base_content = """# Title

## Section A
Base content A.
"""

        new_content = """# Title

## Section B
New content B.
"""

        # Test successful preview
        preview = content_merger.create_merge_preview(
            base_content, new_content, "intelligent"
        )

        assert preview["strategy"] == "intelligent"
        assert preview["base_length"] == len(base_content)
        assert preview["new_length"] == len(new_content)
        assert preview["merged_length"] > 0
        assert "conflicts" in preview
        assert "has_conflicts" in preview
        assert "merged_preview" in preview

        # Test preview with error
        error_preview = content_merger.create_merge_preview(
            base_content, new_content, "invalid_strategy"
        )
        assert "error" in error_preview
        assert error_preview["has_conflicts"] is True
        assert "Unknown merge strategy" in error_preview["error"]

    def test_metadata_diff_extraction(self, content_merger: ContentMerger) -> None:
        """Test extraction of metadata differences."""
        base_content = """# Document

## Introduction
Intro content.

## Methods
Method content.

```python
code here
```
"""

        new_content = """# Document

## Introduction
Updated intro content.

## Results
New results section.

## Conclusion
New conclusion section.

```python
updated code
```

```bash
new bash code
```
"""

        diff = content_merger.extract_metadata_diff(base_content, new_content)

        # Check heading changes
        assert "results" in [h.lower() for h in diff["headings_added"]]
        assert "conclusion" in [h.lower() for h in diff["headings_added"]]
        assert "methods" in [h.lower() for h in diff["headings_removed"]]

        # Check structure changes
        assert "code_block_count_changed" in diff["structure_changes"]

    def test_complex_content_section_detection(
        self, content_merger: ContentMerger
    ) -> None:
        """Test section detection with complex markdown."""
        content = """---
title: Complex Document
---

# Main Document

Regular paragraph with some text.

## Code Examples

Here's some Python:

```python
def complex_function():
    return "complex"
```

And some shell commands:

```bash
echo "hello world"
ls -la
```

### Nested Section

More content here.

#### Deep Nesting

Even deeper content.

## Another Section

Final content.
"""

        sections = content_merger.detect_content_sections(content)

        # Verify comprehensive detection
        assert len(sections["yaml_frontmatter"]) == 1
        assert len(sections["headings"]) == 5  # 5 headings of different levels
        assert len(sections["code_blocks"]) == 2  # Python and bash
        assert len(sections["paragraphs"]) >= 3  # Multiple paragraphs

        # Check heading levels
        heading_levels = [h["level"] for h in sections["headings"]]
        assert 1 in heading_levels  # H1
        assert 2 in heading_levels  # H2
        assert 3 in heading_levels  # H3
        assert 4 in heading_levels  # H4

        # Check code block languages
        languages = {cb["language"] for cb in sections["code_blocks"]}
        assert "python" in languages
        assert "bash" in languages

    def test_merge_with_empty_content(self, content_merger: ContentMerger) -> None:
        """Test merging with empty or minimal content."""
        base_content = ""
        new_content = "# New Content\n\nSome text."

        # Replace with empty base
        result = content_merger.merge_markdown_content(
            base_content, new_content, "replace"
        )
        assert result == new_content

        # Append to empty base
        result = content_merger.merge_markdown_content(
            base_content, new_content, "append"
        )
        assert result == "\n\n" + new_content

        # Intelligent merge with empty base
        result = content_merger.merge_markdown_content(
            base_content, new_content, "intelligent"
        )
        assert "New Content" in result

    def test_merge_preview_error_handling(self, content_merger: ContentMerger) -> None:
        """Test merge preview error handling."""
        base_content = "# Test"
        new_content = "# Test"

        # Force an error by patching the merge method
        import unittest.mock

        with unittest.mock.patch.object(
            content_merger,
            "merge_markdown_content",
            side_effect=Exception("Merge error"),
        ):
            preview = content_merger.create_merge_preview(
                base_content, new_content, "intelligent"
            )

            assert preview["strategy"] == "intelligent"
            assert "error" in preview
            assert preview["has_conflicts"] is True
            assert "Merge error" in preview["error"]

    def test_content_similarity_calculation(
        self, content_merger: ContentMerger
    ) -> None:
        """Test content similarity calculation in conflict detection."""
        # Very similar content
        similar_base = "The quick brown fox jumps over the lazy dog"
        similar_new = "The quick brown fox leaps over the lazy dog"

        conflicts = content_merger.detect_conflicts(similar_base, similar_new)

        # Should not detect significant divergence for similar content
        divergence_conflicts = [
            c for c in conflicts if c["type"] == "content_divergence"
        ]
        if divergence_conflicts:
            assert divergence_conflicts[0]["similarity"] > 0.7

        # Very different content
        different_base = "This is about programming and software development"
        different_new = "This discusses cooking and recipe preparation techniques"

        conflicts = content_merger.detect_conflicts(different_base, different_new)

        # Should detect significant divergence
        divergence_conflicts = [
            c for c in conflicts if c["type"] == "content_divergence"
        ]
        assert len(divergence_conflicts) == 1
        assert divergence_conflicts[0]["similarity"] < 0.3
