"""Core parsing and reorder preview logic.

The GUI depends on this module for file interpretation, structure-list
extraction, and preview calculation. Keeping the behavior here makes the UI
thin and keeps the save path consistent with the parser.
"""

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Sequence, cast


class StructuresNotFoundError(ValueError):
    """Raised when no valid structure list can be found in the input text."""


@dataclass(frozen=True)
class StructureRecord:
    """Represent one structure entry from a Monaco-style file.

    Attributes:
        name: Human-readable structure name.
        original_layer: One-based layer index from the source file.
        layer_fields: Raw comma-separated fields for the layer row, with the
            final field representing the layer index.
    """

    name: str
    original_layer: int
    layer_fields: tuple[str, ...]


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


def load_structure_file(file_path: Path) -> list[StructureRecord]:
    """Load and parse a Monaco-style structure file."""

    return parse_structure_text(file_path.read_text(encoding="utf-8"))


def default_target_layers(records: Sequence[StructureRecord]) -> list[int]:
    """Return the default dropdown values for a fresh file load."""

    return [record.original_layer for record in records]


def build_preview_order(
    records: Sequence[StructureRecord], target_layers: Sequence[int]
) -> list[StructureRecord]:
    """Build the reordered preview order from dropdown selections."""

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


def serialize_structure_records(records: Sequence[StructureRecord]) -> str:
    """Serialize ordered structures back into Monaco-style text."""

    lines: list[str] = []
    for record in records:
        lines.append(record.name)
        lines.append(",".join(_build_layer_fields(record, record.original_layer)))
    return "\n".join(lines) + "\n"


def reindex_structure_records(records: Sequence[StructureRecord]) -> list[StructureRecord]:
    """Return a copy of the records renumbered to match their current order."""

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
    """Apply the selected destination layer to each record without reordering."""

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
    """Write ordered structure records to a Monaco-style text file."""

    file_path.write_text(serialize_structure_records(records), encoding="utf-8")