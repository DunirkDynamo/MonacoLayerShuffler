"""Core parsing and reorder preview logic.

The GUI depends on this module for file interpretation, structure-list
extraction, and preview calculation. Keeping the behavior here makes the UI
thin and keeps the save path consistent with the parser.
"""

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Sequence, cast


DATABASE_ROOT = Path(r"C:\GitHub\MonacoDatabase")
PLAN_FILE_NAMES = ("plan", "plan.txt")


class StructuresNotFoundError(ValueError):
    """Raised when no valid Monaco structure block can be found.

    The parser scans the full input looking for a block that matches the
    expected structure-list shape. When no block satisfies the validation
    rules, callers should treat the file as incompatible with this tool.
    """


@dataclass(frozen=True)
class StructureRecord:
    """Represent one structure entry from a Monaco-style file.

    Attributes:
        name: Human-readable structure name.
        original_layer: One-based layer index from the source file.
        layer_fields: Raw comma-separated fields for the layer row, with the
            final field representing the layer index.

    The record keeps the original CSV fields so save operations can preserve
    the file's existing structure while updating the layer number in place.
    """

    name: str
    original_layer: int
    layer_fields: tuple[str, ...]


@dataclass(frozen=True)
class StructureDocument:
    """Represent the original file and the extracted structure block.

    Attributes:
        records: Parsed structure records in source order.
        source_lines: The full original file split into newline-preserving lines.
        block_start: Zero-based index of the count line that starts the block.
        block_end: Zero-based index of the final line in the block.

    The document object carries enough information to rewrite only the matched
    structure block while leaving unrelated file content untouched.
    """

    records: tuple[StructureRecord, ...]
    source_lines: tuple[str, ...]
    block_start: int
    block_end: int


def _build_layer_fields(record: StructureRecord, layer_index: int) -> tuple[str, ...]:
    """Return the stored CSV fields with the final field replaced by an index."""

    fields = list(record.layer_fields)
    if not fields:
        return (str(layer_index),)

    fields[-1] = str(layer_index)
    return tuple(fields)


def _parse_record(lines: Sequence[str], index: int) -> StructureRecord | None:
    """Parse one two-line structure record starting at ``index``.

    The record must be a non-empty label line followed by a numerical line
    containing exactly five comma-separated fields. The first four fields must
    convert to ``float`` and the fifth field must convert to ``int``.
    """

    value_index = index + 1
    if value_index >= len(lines):
        return None

    label = lines[index].strip()
    value_line = lines[value_index].strip()
    if not label:
        return None

    try:
        parsed_fields = next(csv.reader([value_line]))
    except csv.Error:
        return None

    if len(parsed_fields) != 5:
        return None

    try:
        float(parsed_fields[0].strip())
        float(parsed_fields[1].strip())
        float(parsed_fields[2].strip())
        float(parsed_fields[3].strip())
        structure_id = int(parsed_fields[4].strip())
    except ValueError:
        return None

    return StructureRecord(
        name=label,
        original_layer=structure_id,
        layer_fields=tuple(parsed_fields),
    )


def parse_structure_text(text: str) -> list[StructureRecord]:
    """Locate and extract the validated structure list from a file.

    The extractor scans every possible starting position and applies the
    following checks in order:

    1. The line immediately before the candidate list must be a positive
       integer N.
    2. Exactly N two-line structure records must follow.
    3. Each numerical line must contain exactly five comma-separated fields.
    4. Fields 1-4 must convert to float and field 5 must convert to int.
    5. Structure IDs must be 1, 2, ..., N in sequence.
    6. The two lines immediately after the Nth record must not form another
       valid record.
    """

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for start in range(1, len(lines) - 1):
        count_text = lines[start - 1].strip()
        if not count_text.isdigit():
            continue

        count = int(count_text)
        if count <= 0:
            continue

        structures: list[StructureRecord] = []
        valid = True

        for offset in range(count):
            record_index = start + (2 * offset)
            record = _parse_record(lines, record_index)
            if record is None:
                valid = False
                break

            if record.original_layer != offset + 1:
                valid = False
                break

            structures.append(record)

        if not valid:
            continue

        if len(structures) != count:
            continue

        if structures[-1].original_layer != count:
            continue

        next_record_index = start + (2 * count)
        if _parse_record(lines, next_record_index) is not None:
            continue

        return structures

    raise StructuresNotFoundError("Failed to locate structures")


def _extract_structure_document(text: str) -> StructureDocument:
    """Parse the source text and capture the original file span for the list."""

    source_lines = text.splitlines(keepends=True)
    content_lines = text.splitlines()

    for start in range(1, len(content_lines) - 1):
        count_text = content_lines[start - 1].strip()
        if not count_text.isdigit():
            continue

        count = int(count_text)
        if count <= 0:
            continue

        records: list[StructureRecord] = []
        valid = True

        for offset in range(count):
            record_index = start + (2 * offset)
            record = _parse_record(content_lines, record_index)
            if record is None:
                valid = False
                break

            if record.original_layer != offset + 1:
                valid = False
                break

            records.append(record)

        if not valid:
            continue

        if len(records) != count:
            continue

        if records[-1].original_layer != count:
            continue

        next_record_index = start + (2 * count)
        if _parse_record(content_lines, next_record_index) is not None:
            continue

        block_start = start - 1
        block_end = start + (2 * count) - 1
        return StructureDocument(
            records=tuple(records),
            source_lines=tuple(source_lines),
            block_start=block_start,
            block_end=block_end,
        )

    raise StructuresNotFoundError("Failed to locate structures")


def load_structure_file(file_path: Path) -> StructureDocument:
    """Load and parse a Monaco-style structure file.

    Args:
        file_path: Path to the plan file selected by the GUI.

    Returns:
        A parsed document with the extracted structure rows and original file
        text preserved for later rewrites.
    """

    return _extract_structure_document(file_path.read_text(encoding="utf-8"))


def normalize_mrn(mrn_text: str) -> str:
    """Validate and normalize an MRN entered by the user.

    Args:
        mrn_text: Text typed by the user in the MRN prompt.

    Returns:
        The stripped eight-digit MRN.

    Raises:
        ValueError: If the value is empty, contains non-digits, or is not
            exactly eight characters long.
    """

    normalized_mrn = mrn_text.strip()
    if len(normalized_mrn) != 8 or not normalized_mrn.isdigit():
        raise ValueError("The MRN must be exactly 8 digits.")

    return normalized_mrn


def resolve_mrn_folder(mrn_text: str, database_root: Path = DATABASE_ROOT) -> Path:
    """Resolve the database folder that corresponds to an MRN.

    Args:
        mrn_text: User-entered MRN text.
        database_root: Root folder that contains the numbered MRN folders.

    Returns:
        The resolved ``1~<MRN>`` folder.

    Raises:
        ValueError: If the MRN is malformed or the folder does not exist.
    """

    normalized_mrn = normalize_mrn(mrn_text)
    mrn_folder = database_root / f"1~{normalized_mrn}"
    if not mrn_folder.is_dir():
        raise ValueError(
            f'Could not find the MRN folder "1~{normalized_mrn}" under {database_root}.'
        )

    return mrn_folder


def resolve_plan_file(mrn_folder: Path, plan_name: str) -> Path:
    """Resolve the plan file inside an MRN folder by matching the plan folder name.

    The lookup expects the folder structure ``1~<MRN>/plan/<plan name>/plan``
    or ``1~<MRN>/plan/<plan name>/plan.txt``.
    """

    normalized_plan_name = plan_name.strip()
    if not normalized_plan_name:
        raise ValueError("The plan name cannot be empty.")

    plans_folder = mrn_folder / "plan"
    if not plans_folder.is_dir():
        raise ValueError("No plans available")

    matching_plan_folder = None
    for child in plans_folder.iterdir():
        if child.is_dir() and child.name.casefold() == normalized_plan_name.casefold():
            matching_plan_folder = child
            break

    if matching_plan_folder is None:
        raise ValueError(
            f'No plan named "{normalized_plan_name}" was found under {plans_folder}.'
        )

    plan_file = None
    for plan_file_name in PLAN_FILE_NAMES:
        candidate_plan_file = matching_plan_folder / plan_file_name
        if candidate_plan_file.is_file():
            plan_file = candidate_plan_file
            break

    if plan_file is None:
        raise ValueError(
            f'The file "plan" or "plan.txt" was not found in {matching_plan_folder}.'
        )

    return plan_file


def default_target_layers(records: Sequence[StructureRecord]) -> list[int]:
    """Return the default dropdown values for a fresh file load.

    The UI uses these values to seed each combo box with the current layer
    ordering.
    """

    return [record.original_layer for record in records]


def build_preview_order(
    records: Sequence[StructureRecord], target_layers: Sequence[int]
) -> list[StructureRecord]:
    """Build the reordered preview order from dropdown selections.

    This does not mutate the source records. It returns a new list ordered by
    the target layer numbers so the GUI can show the preview before saving.
    """

    if len(records) != len(target_layers):
        raise ValueError("The number of selected layers does not match the file.")

    layer_count = len(records)
    preview: list[object] = [None] * layer_count
    occupied_layers: set[int] = set()

    for record, target_layer in zip(records, target_layers):
        if target_layer < 1 or target_layer > layer_count:
            raise ValueError(
                f"Layer {target_layer} is out of range for a {layer_count}-layer file."
            )
        if target_layer in occupied_layers:
            raise ValueError(f"Layer {target_layer} was selected more than once.")
        occupied_layers.add(target_layer)
        preview[target_layer - 1] = record

    if any(record is None for record in preview):
        raise ValueError("At least one destination layer was left unassigned.")

    return cast(list[StructureRecord], [record for record in preview if record is not None])


def _line_ending(line: str) -> str:
    """Return the original newline suffix for a source line."""

    return line[len(line.rstrip("\r\n")) :]


def _serialize_structure_block(
    document: StructureDocument, records: Sequence[StructureRecord]
) -> list[str]:
    """Build replacement lines for the extracted structure block.

    The replacement keeps the same number of lines and preserves the original
    line-ending style for each position in the block.
    """

    if len(records) * 2 + 1 != document.block_end - document.block_start + 1:
        raise ValueError("The reordered records do not match the original block size.")

    block_lines = document.source_lines[document.block_start : document.block_end + 1]
    replacement_lines: list[str] = []

    replacement_lines.append(block_lines[0])

    for index, record in enumerate(records, start=0):
        name_line = block_lines[1 + (2 * index)]
        value_line = block_lines[2 + (2 * index)]
        name_ending = _line_ending(name_line)
        value_ending = _line_ending(value_line)

        replacement_lines.append(f"{record.name}{name_ending}")
        replacement_lines.append(",".join(_build_layer_fields(record, record.original_layer)) + value_ending)

    return replacement_lines


def render_structure_document(
    document: StructureDocument, records: Sequence[StructureRecord]
) -> str:
    """Render the full file text with the updated structure block in place.

    The serializer preserves the untouched file text around the matched block
    and only replaces the structure section.
    """

    updated_lines = list(document.source_lines)
    updated_lines[document.block_start : document.block_end + 1] = _serialize_structure_block(
        document, records
    )
    return "".join(updated_lines)


def reindex_structure_records(records: Sequence[StructureRecord]) -> list[StructureRecord]:
    """Return a copy of the records renumbered to match their current order.

    Useful when a reordered preview should become the new persisted order.
    """

    return [
        StructureRecord(
            name=record.name,
            original_layer=layer_index,
            layer_fields=_build_layer_fields(record, layer_index),
        )
        for layer_index, record in enumerate(records, start=1)
    ]


def apply_target_layers(
    records: Sequence[StructureRecord], target_layers: Sequence[int]
) -> list[StructureRecord]:
    """Apply the selected destination layer to each record without reordering.

    This preserves the visual row order but updates each record's layer value
    so later serialization can write the chosen destination numbers back out.
    """

    if len(records) != len(target_layers):
        raise ValueError("The number of selected layers does not match the file.")

    return [
        StructureRecord(
            name=record.name,
            original_layer=target_layer,
            layer_fields=_build_layer_fields(record, target_layer),
        )
        for record, target_layer in zip(records, target_layers)
    ]


def write_structure_file(file_path: Path, records: Sequence[StructureRecord]) -> None:
    """Legacy helper retained for compatibility with older call sites.

    It writes only the structure rows and is kept for backward compatibility.
    The current GUI prefers :func:`write_structure_document`.
    """

    lines: list[str] = []
    for record in records:
        lines.append(record.name)
        lines.append(",".join(_build_layer_fields(record, record.original_layer)))
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_structure_document(
    file_path: Path, document: StructureDocument, records: Sequence[StructureRecord]
) -> None:
    """Write the updated structure block back into the original file text.

    Args:
        file_path: Destination path that should receive the rewritten plan.
        document: Parsed document that still contains the original file text.
        records: Updated records in the order they should be written.
    """

    file_path.write_text(render_structure_document(document, records), encoding="utf-8")