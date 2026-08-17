import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DiffLine:
    origin: str  # ' ' (context), '+' (added), '-' (deleted), '@' (header)
    content: str
    old_line_no: Optional[int] = None
    new_line_no: Optional[int] = None

    @property
    def is_addition(self) -> bool:
        return self.origin == "+"

    @property
    def is_deletion(self) -> bool:
        return self.origin == "-"

    @property
    def is_context(self) -> bool:
        return self.origin == " "


@dataclass
class DiffHunk:
    header: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine] = field(default_factory=list)


@dataclass
class FileDiff:
    old_path: str
    new_path: str
    is_new: bool = False
    is_deleted: bool = False
    is_renamed: bool = False
    hunks: List[DiffHunk] = field(default_factory=list)

    @property
    def display_path(self) -> str:
        if self.new_path and self.new_path != "/dev/null":
            return self.new_path
        return self.old_path

    @property
    def all_lines(self) -> List[DiffLine]:
        lines: List[DiffLine] = []
        for hunk in self.hunks:
            lines.append(DiffLine(origin="@", content=hunk.header))
            lines.extend(hunk.lines)
        return lines


HUNK_HEADER_REGEX = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


class UnifiedDiffParser:
    """Parses standard unified diff output into structured file diffs and hunks."""

    @classmethod
    def parse(cls, diff_text: str) -> List[FileDiff]:
        if not diff_text or not diff_text.strip():
            return []

        file_diffs: List[FileDiff] = []
        current_file: Optional[FileDiff] = None
        current_hunk: Optional[DiffHunk] = None
        old_line_counter = 0
        new_line_counter = 0

        lines = diff_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]

            if line.startswith("diff --git "):
                # Finish previous hunk and file
                if current_hunk and current_file:
                    current_file.hunks.append(current_hunk)
                    current_hunk = None
                if current_file:
                    file_diffs.append(current_file)

                # Parse paths: diff --git a/path/to/file b/path/to/file
                parts = line.split(" ")
                old_p = parts[2][2:] if len(parts) > 2 and parts[2].startswith("a/") else ""
                new_p = parts[3][2:] if len(parts) > 3 and parts[3].startswith("b/") else ""
                current_file = FileDiff(old_path=old_p, new_path=new_p)
                i += 1
                continue

            if not current_file:
                i += 1
                continue

            if line.startswith("new file mode "):
                current_file.is_new = True
            elif line.startswith("deleted file mode "):
                current_file.is_deleted = True
            elif line.startswith("similarity index ") or line.startswith("rename from "):
                current_file.is_renamed = True
            elif line.startswith("--- "):
                path_part = line[4:].strip()
                if path_part.startswith("a/"):
                    current_file.old_path = path_part[2:]
                elif path_part == "/dev/null":
                    current_file.old_path = "/dev/null"
                    current_file.is_new = True
            elif line.startswith("+++ "):
                path_part = line[4:].strip()
                if path_part.startswith("b/"):
                    current_file.new_path = path_part[2:]
                elif path_part == "/dev/null":
                    current_file.new_path = "/dev/null"
                    current_file.is_deleted = True
            elif line.startswith("@@ "):
                match = HUNK_HEADER_REGEX.match(line)
                if match:
                    if current_hunk:
                        current_file.hunks.append(current_hunk)

                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) is not None else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) is not None else 1

                    current_hunk = DiffHunk(
                        header=line,
                        old_start=old_start,
                        old_count=old_count,
                        new_start=new_start,
                        new_count=new_count,
                    )
                    old_line_counter = old_start
                    new_line_counter = new_start
            elif current_hunk:
                if line.startswith("+"):
                    diff_line = DiffLine(
                        origin="+",
                        content=line[1:],
                        old_line_no=None,
                        new_line_no=new_line_counter,
                    )
                    new_line_counter += 1
                    current_hunk.lines.append(diff_line)
                elif line.startswith("-"):
                    diff_line = DiffLine(
                        origin="-",
                        content=line[1:],
                        old_line_no=old_line_counter,
                        new_line_no=None,
                    )
                    old_line_counter += 1
                    current_hunk.lines.append(diff_line)
                elif line.startswith(" ") or line == "":
                    content = line[1:] if line.startswith(" ") else line
                    diff_line = DiffLine(
                        origin=" ",
                        content=content,
                        old_line_no=old_line_counter,
                        new_line_no=new_line_counter,
                    )
                    old_line_counter += 1
                    new_line_counter += 1
                    current_hunk.lines.append(diff_line)
                elif line.startswith("\\ No newline at end of file"):
                    pass

            i += 1

        if current_hunk and current_file:
            current_file.hunks.append(current_hunk)
        if current_file:
            file_diffs.append(current_file)

        return file_diffs
