"""Content merging utilities for spec documentation.

This module provides functionality for intelligently merging markdown content
during spec documentation updates. It handles section detection, conflict
identification, and various merge strategies to preserve important content
while incorporating new changes.
"""

import re
from typing import Any

from ..logging.debug import debug_logger


class ContentMerger:
    """Utilities for merging and combining file content."""

    def __init__(self) -> None:
        """Initialize the content merger with pattern matchers."""
        # Patterns for detecting markdown sections
        self.section_patterns = {
            "heading": re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE),
            "yaml_frontmatter": re.compile(r"^---\n(.+?)\n---", re.DOTALL),
            "code_block": re.compile(
                r"^```([a-z]*)\n(.*?)\n```$", re.MULTILINE | re.DOTALL
            ),
        }

        debug_logger.log("INFO", "ContentMerger initialized")

    def detect_content_sections(self, content: str) -> dict[str, list[dict[str, Any]]]:
        """Detect structured sections in markdown content.

        Args:
            content: Content to analyze

        Returns:
            Dictionary mapping section types to detected sections
        """
        sections: dict[str, list[Any]] = {
            "headings": [],
            "yaml_frontmatter": [],
            "code_blocks": [],
            "paragraphs": [],
        }

        # Detect headings
        for match in self.section_patterns["heading"].finditer(content):
            level = len(match.group(1))
            title = match.group(2).strip()
            start_pos = match.start()
            end_pos = match.end()

            sections["headings"].append(
                {
                    "level": level,
                    "title": title,
                    "start": start_pos,
                    "end": end_pos,
                    "content": match.group(0),
                }
            )

        # Detect YAML frontmatter
        frontmatter_match = self.section_patterns["yaml_frontmatter"].match(content)
        if frontmatter_match:
            sections["yaml_frontmatter"].append(
                {
                    "content": frontmatter_match.group(1),
                    "start": frontmatter_match.start(),
                    "end": frontmatter_match.end(),
                }
            )

        # Detect code blocks
        for match in self.section_patterns["code_block"].finditer(content):
            sections["code_blocks"].append(
                {
                    "language": match.group(1).strip() if match.group(1) else "text",
                    "content": match.group(2),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # Simple paragraph detection (non-empty lines not in other sections)
        lines = content.split("\n")
        in_code_block = False
        current_paragraph: list[str] = []
        line_start = 0

        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block or line.startswith("#") or not line.strip():
                if current_paragraph:
                    sections["paragraphs"].append(
                        {
                            "content": "\n".join(current_paragraph),
                            "start_line": line_start,
                            "end_line": i - 1,
                        }
                    )
                    current_paragraph = []
                continue

            if not current_paragraph:
                line_start = i
            current_paragraph.append(line)

        if current_paragraph:
            sections["paragraphs"].append(
                {
                    "content": "\n".join(current_paragraph),
                    "start_line": line_start,
                    "end_line": len(lines) - 1,
                }
            )

        debug_logger.log(
            "DEBUG",
            "Content sections detected",
            headings=len(sections["headings"]),
            code_blocks=len(sections["code_blocks"]),
            paragraphs=len(sections["paragraphs"]),
        )

        return sections

    def merge_markdown_content(
        self, base_content: str, new_content: str, strategy: str = "intelligent"
    ) -> str:
        """Merge two markdown contents using specified strategy.

        Args:
            base_content: Existing content
            new_content: New content to merge
            strategy: Merge strategy ('intelligent', 'append', 'prepend', 'replace')

        Returns:
            Merged content
        """
        debug_logger.log(
            "INFO",
            "Merging markdown content",
            strategy=strategy,
            base_length=len(base_content),
            new_length=len(new_content),
        )

        if strategy == "replace":
            return new_content
        elif strategy == "append":
            return base_content + "\n\n" + new_content
        elif strategy == "prepend":
            return new_content + "\n\n" + base_content
        elif strategy == "intelligent":
            return self._intelligent_merge(base_content, new_content)
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

    def _intelligent_merge(self, base_content: str, new_content: str) -> str:
        """Perform intelligent merge based on content structure."""
        base_sections = self.detect_content_sections(base_content)
        new_sections = self.detect_content_sections(new_content)

        # Start with base content
        merged_lines = base_content.split("\n")

        # Merge headings intelligently
        base_headings = {h["title"].lower(): h for h in base_sections["headings"]}

        for new_heading in new_sections["headings"]:
            title_lower = new_heading["title"].lower()

            if title_lower not in base_headings:
                # Add new heading
                merged_lines.append("")
                merged_lines.append(new_heading["content"])

                # Find content after this heading in new content
                heading_end = new_heading["end"]
                next_heading_start = len(new_content)

                for other_heading in new_sections["headings"]:
                    if other_heading["start"] > heading_end:
                        next_heading_start = min(
                            next_heading_start, other_heading["start"]
                        )

                if next_heading_start > heading_end:
                    section_content = new_content[
                        heading_end:next_heading_start
                    ].strip()
                    if section_content:
                        merged_lines.append(section_content)

        merged_content = "\n".join(merged_lines)

        debug_logger.log(
            "DEBUG", "Intelligent merge completed", result_length=len(merged_content)
        )

        return merged_content

    def detect_conflicts(
        self, base_content: str, new_content: str
    ) -> list[dict[str, Any]]:
        """Detect potential conflicts between content versions.

        Args:
            base_content: Original content
            new_content: New content

        Returns:
            List of detected conflicts
        """
        conflicts = []

        base_sections = self.detect_content_sections(base_content)
        new_sections = self.detect_content_sections(new_content)

        # Check for heading conflicts
        base_headings = {h["title"].lower(): h for h in base_sections["headings"]}
        new_headings = {h["title"].lower(): h for h in new_sections["headings"]}

        common_headings = set(base_headings.keys()) & set(new_headings.keys())

        for heading_title in common_headings:
            base_heading = base_headings[heading_title]
            new_heading = new_headings[heading_title]

            if base_heading["level"] != new_heading["level"]:
                conflicts.append(
                    {
                        "type": "heading_level_conflict",
                        "heading": heading_title,
                        "base_level": base_heading["level"],
                        "new_level": new_heading["level"],
                        "severity": "medium",
                    }
                )

        # Check for substantial content differences
        base_words = set(re.findall(r"\b\w+\b", base_content.lower()))
        new_words = set(re.findall(r"\b\w+\b", new_content.lower()))

        common_words = base_words & new_words
        total_words = base_words | new_words

        if total_words:
            similarity = len(common_words) / len(total_words)

            if similarity < 0.5:  # Less than 50% similarity
                conflicts.append(
                    {
                        "type": "content_divergence",
                        "similarity": similarity,
                        "severity": "high" if similarity < 0.3 else "medium",
                    }
                )

        debug_logger.log(
            "DEBUG", "Conflict detection completed", conflicts=len(conflicts)
        )

        return conflicts

    def create_merge_preview(
        self, base_content: str, new_content: str, strategy: str
    ) -> dict[str, Any]:
        """Create a preview of what merge would produce.

        Args:
            base_content: Base content
            new_content: New content
            strategy: Merge strategy

        Returns:
            Dictionary with merge preview information
        """
        try:
            merged_content = self.merge_markdown_content(
                base_content, new_content, strategy
            )
            conflicts = self.detect_conflicts(base_content, new_content)

            preview = {
                "strategy": strategy,
                "base_length": len(base_content),
                "new_length": len(new_content),
                "merged_length": len(merged_content),
                "conflicts": conflicts,
                "conflict_count": len(conflicts),
                "has_conflicts": len(conflicts) > 0,
                "merged_preview": merged_content[:500] + "..."
                if len(merged_content) > 500
                else merged_content,
            }

            return preview

        except Exception as e:
            return {
                "strategy": strategy,
                "error": str(e),
                "has_conflicts": True,
            }

    def extract_metadata_diff(
        self, base_content: str, new_content: str
    ) -> dict[str, Any]:
        """Extract differences in metadata between content versions.

        Args:
            base_content: Base content
            new_content: New content

        Returns:
            Dictionary with metadata differences
        """
        base_sections = self.detect_content_sections(base_content)
        new_sections = self.detect_content_sections(new_content)

        diff: dict[str, list[Any]] = {
            "headings_added": [],
            "headings_removed": [],
            "headings_modified": [],
            "structure_changes": [],
        }

        base_heading_titles = {h["title"].lower() for h in base_sections["headings"]}
        new_heading_titles = {h["title"].lower() for h in new_sections["headings"]}

        diff["headings_added"] = list(new_heading_titles - base_heading_titles)
        diff["headings_removed"] = list(base_heading_titles - new_heading_titles)

        # Check for structure changes
        if len(base_sections["headings"]) != len(new_sections["headings"]):
            diff["structure_changes"].append("heading_count_changed")

        if len(base_sections["code_blocks"]) != len(new_sections["code_blocks"]):
            diff["structure_changes"].append("code_block_count_changed")

        return diff
