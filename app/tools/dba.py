from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from app.tools.files import read_file


_IO_FIELD_PATTERNS = {
    "scan_count": re.compile(r"\bScan count\s+(\d+)", re.IGNORECASE),
    "logical_reads": re.compile(r"\blogical reads\s+(\d+)", re.IGNORECASE),
    "physical_reads": re.compile(r"\bphysical reads\s+(\d+)", re.IGNORECASE),
    "read_ahead_reads": re.compile(r"\bread-ahead reads\s+(\d+)", re.IGNORECASE),
}
_TABLE_LINE = re.compile(r"Table\s+'([^']+)'\s*\.(.*)", re.IGNORECASE)
_TIME_LINE = re.compile(
    r"CPU time\s*=\s*(\d+)\s*ms\s*,\s*elapsed time\s*=\s*(\d+)\s*ms",
    re.IGNORECASE,
)


def _source_text(
    *,
    text: str | None,
    relative_path: str | None,
    workspace: Path,
    max_bytes: int,
    allowed_suffixes: set[str] | None = None,
) -> tuple[str, str]:
    has_text = isinstance(text, str) and bool(text.strip())
    has_path = isinstance(relative_path, str) and bool(relative_path.strip())
    if has_text == has_path:
        raise ValueError("Proporciona exactamente uno de text o relative_path")
    if has_text:
        assert text is not None
        size = len(text.encode("utf-8"))
        if size > max_bytes:
            raise ValueError(f"Entrada demasiado grande: {size} bytes (máximo {max_bytes})")
        return text, "text"
    assert relative_path is not None
    if allowed_suffixes and Path(relative_path).suffix.casefold() not in allowed_suffixes:
        allowed = ", ".join(sorted(allowed_suffixes))
        raise ValueError(f"Extensión no permitida; usa: {allowed}")
    return (
        read_file(relative_path, workspace=workspace, max_bytes=max_bytes),
        relative_path,
    )


def analyze_statistics_io(
    text: str | None = None,
    relative_path: str | None = None,
    *,
    workspace: Path,
    max_bytes: int,
) -> str:
    content, source = _source_text(
        text=text,
        relative_path=relative_path,
        workspace=workspace,
        max_bytes=max_bytes,
    )
    tables: list[dict[str, Any]] = []
    for line in content.splitlines():
        match = _TABLE_LINE.search(line)
        if not match:
            continue
        item: dict[str, Any] = {"table": match.group(1)}
        metrics = match.group(2)
        for field, pattern in _IO_FIELD_PATTERNS.items():
            value = pattern.search(metrics)
            if value:
                item[field] = int(value.group(1))
        tables.append(item)
    return json.dumps(
        {
            "source": source,
            "tables": tables,
            "table_count": len(tables),
            "interpretation_constraints": {
                "physical_operator_known": False,
                "requires_execution_plan_for_operator": True,
                "note": (
                    "STATISTICS IO scan count no identifica Table Scan, Index Scan, "
                    "Index Seek ni Key Lookup y no debe parafrasearse como que hubo "
                    "un escaneo; esos operadores requieren evidencia del plan de "
                    "ejecución."
                ),
            },
        },
        ensure_ascii=False,
        indent=2,
    )


def analyze_statistics_time(
    text: str | None = None,
    relative_path: str | None = None,
    *,
    workspace: Path,
    max_bytes: int,
) -> str:
    content, source = _source_text(
        text=text,
        relative_path=relative_path,
        workspace=workspace,
        max_bytes=max_bytes,
    )
    timings = [
        {"cpu_time_ms": int(match.group(1)), "elapsed_time_ms": int(match.group(2))}
        for match in _TIME_LINE.finditer(content)
    ]
    return json.dumps(
        {"source": source, "timings": timings, "sample_count": len(timings)},
        ensure_ascii=False,
        indent=2,
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _safe_xml(content: str) -> ET.Element:
    folded = content.casefold()
    if "<!doctype" in folded or "<!entity" in folded:
        raise ValueError("XML bloqueado: DTD y entidades no están permitidas")
    try:
        return ET.fromstring(content)
    except ET.ParseError as exc:
        raise ValueError(f"XML inválido: {exc}") from exc


def _float_or_text(value: str | None) -> float | str | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return value


def analyze_execution_plan(
    relative_path: str,
    *,
    workspace: Path,
    max_bytes: int,
) -> str:
    content, source = _source_text(
        text=None,
        relative_path=relative_path,
        workspace=workspace,
        max_bytes=max_bytes,
        allowed_suffixes={".sqlplan"},
    )
    root = _safe_xml(content)
    operators: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    missing_indexes: list[dict[str, Any]] = []

    for element in root.iter():
        name = _local_name(element.tag)
        if name == "RelOp":
            operator: dict[str, Any] = {
                "node_id": element.attrib.get("NodeId"),
                "physical_op": element.attrib.get("PhysicalOp"),
                "logical_op": element.attrib.get("LogicalOp"),
                "estimated_rows": _float_or_text(element.attrib.get("EstimateRows")),
                "estimated_total_subtree_cost": _float_or_text(
                    element.attrib.get("EstimatedTotalSubtreeCost")
                ),
            }
            runtime_nodes = [
                child
                for child in element
                if _local_name(child.tag) == "RunTimeInformation"
            ]
            actual_values = [
                int(float(counter.attrib["ActualRows"]))
                for runtime in runtime_nodes
                for counter in runtime.iter()
                if _local_name(counter.tag) == "RunTimeCountersPerThread"
                and counter.attrib.get("ActualRows") is not None
            ]
            if actual_values:
                operator["actual_rows"] = sum(actual_values)
            operators.append({key: value for key, value in operator.items() if value is not None})
        elif name in {
            "Warnings",
            "SpillToTempDb",
            "SpillOccurred",
            "HashSpillDetails",
            "SortSpillDetails",
            "Wait",
        }:
            warnings.append({"type": name, "attributes": dict(element.attrib)})
        elif name == "MissingIndex":
            suggestion: dict[str, Any] = {
                "database": element.attrib.get("Database"),
                "schema": element.attrib.get("Schema"),
                "table": element.attrib.get("Table"),
                "columns": [],
            }
            for group in element:
                if _local_name(group.tag) != "ColumnGroup":
                    continue
                usage = group.attrib.get("Usage")
                for column in group:
                    if _local_name(column.tag) == "Column":
                        suggestion["columns"].append(
                            {"usage": usage, "name": column.attrib.get("Name")}
                        )
            missing_indexes.append(suggestion)

    physical_ops = [str(item.get("physical_op", "")) for item in operators]
    categories = {
        "scans": [op for op in physical_ops if "Scan" in op],
        "seeks": [op for op in physical_ops if "Seek" in op],
        "lookups": [op for op in physical_ops if "Lookup" in op],
        "joins": [
            op
            for op in physical_ops
            if any(join in op for join in ("Nested Loops", "Hash Match", "Merge Join"))
        ],
    }
    return json.dumps(
        {
            "source": source,
            "facts_only": True,
            "operators": operators,
            "operator_categories": categories,
            "warnings": warnings,
            "missing_index_suggestions": missing_indexes,
            "note": "Los operadores y sugerencias requieren interpretación con evidencia de ejecución.",
        },
        ensure_ascii=False,
        indent=2,
    )


def _element_text(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    value = " ".join(part.strip() for part in element.itertext() if part.strip())
    return value or None


def analyze_deadlock_xml(
    relative_path: str,
    *,
    workspace: Path,
    max_bytes: int,
) -> str:
    content, source = _source_text(
        text=None,
        relative_path=relative_path,
        workspace=workspace,
        max_bytes=max_bytes,
        allowed_suffixes={".xml", ".xdl"},
    )
    root = _safe_xml(content)
    victims: list[str] = []
    processes: list[dict[str, Any]] = []
    resources: list[dict[str, Any]] = []

    for element in root.iter():
        name = _local_name(element.tag)
        if name == "victimProcess" and element.attrib.get("id"):
            victims.append(element.attrib["id"])
        elif name == "process":
            input_buffer = next(
                (child for child in element.iter() if _local_name(child.tag) == "inputbuf"),
                None,
            )
            frames = [
                {
                    "procedure": child.attrib.get("procname"),
                    "line": child.attrib.get("line"),
                    "statement": _element_text(child),
                }
                for child in element.iter()
                if _local_name(child.tag) == "frame"
            ]
            processes.append(
                {
                    "id": element.attrib.get("id"),
                    "spid": element.attrib.get("spid"),
                    "database_id": element.attrib.get("currentdb"),
                    "isolation_level": element.attrib.get("isolationlevel"),
                    "wait_resource": element.attrib.get("waitresource"),
                    "lock_mode": element.attrib.get("lockMode"),
                    "input_buffer": _element_text(input_buffer),
                    "execution_stack": frames,
                }
            )

    resource_lists = [
        element for element in root.iter() if _local_name(element.tag) == "resource-list"
    ]
    for resource_list in resource_lists:
        for resource in resource_list:
            owners: list[dict[str, Any]] = []
            waiters: list[dict[str, Any]] = []
            for child in resource.iter():
                child_name = _local_name(child.tag)
                if child_name == "owner":
                    owners.append(dict(child.attrib))
                elif child_name == "waiter":
                    waiters.append(dict(child.attrib))
            resources.append(
                {
                    "type": _local_name(resource.tag),
                    "database_id": resource.attrib.get("dbid"),
                    "object_name": resource.attrib.get("objectname"),
                    "attributes": dict(resource.attrib),
                    "owners": owners,
                    "waiters": waiters,
                }
            )

    return json.dumps(
        {
            "source": source,
            "victims": victims,
            "processes": processes,
            "resources": resources,
            "facts_only": True,
        },
        ensure_ascii=False,
        indent=2,
    )
