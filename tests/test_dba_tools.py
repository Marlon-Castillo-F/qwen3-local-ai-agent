import json
from pathlib import Path

import pytest

from app.tools.dba import (
    analyze_deadlock_xml,
    analyze_execution_plan,
    analyze_statistics_io,
    analyze_statistics_time,
)


SQLPLAN = """<?xml version="1.0" encoding="utf-8"?>
<ShowPlanXML xmlns="http://schemas.microsoft.com/sqlserver/2004/07/showplan">
  <BatchSequence><Batch><Statements><StmtSimple StatementText="SELECT * FROM dbo.Orders">
    <QueryPlan>
      <MissingIndexes><MissingIndexGroup Impact="42.5"><MissingIndex Database="[Lab]" Schema="[dbo]" Table="[Orders]"><ColumnGroup Usage="EQUALITY"><Column Name="[CustomerId]" /></ColumnGroup></MissingIndex></MissingIndexGroup></MissingIndexes>
      <RelOp NodeId="0" PhysicalOp="Nested Loops" LogicalOp="Inner Join" EstimateRows="10" EstimatedTotalSubtreeCost="1.25">
        <RunTimeInformation><RunTimeCountersPerThread Thread="0" ActualRows="200" /></RunTimeInformation>
        <Warnings><SpillToTempDb SpillLevel="1" /></Warnings>
        <RelOp NodeId="1" PhysicalOp="Index Scan" LogicalOp="Index Scan" EstimateRows="200" />
        <RelOp NodeId="2" PhysicalOp="Key Lookup" LogicalOp="Key Lookup" EstimateRows="10" />
      </RelOp>
    </QueryPlan>
  </StmtSimple></Statements></Batch></BatchSequence>
</ShowPlanXML>
"""

DEADLOCK = """<deadlock-list><deadlock>
  <victim-list><victimProcess id="process1" /></victim-list>
  <process-list>
    <process id="process1" spid="51" currentdb="7" isolationlevel="read committed" waitresource="KEY: 7:1" lockMode="S">
      <executionStack><frame procname="Lab.dbo.p1" line="12">UPDATE dbo.A SET x=1</frame></executionStack>
      <inputbuf>EXEC dbo.p1</inputbuf>
    </process>
    <process id="process2" spid="52" currentdb="7" isolationlevel="read committed" />
  </process-list>
  <resource-list><keylock dbid="7" objectname="Lab.dbo.A"><owner-list><owner id="process2" mode="X" /></owner-list><waiter-list><waiter id="process1" mode="S" /></waiter-list></keylock></resource-list>
</deadlock></deadlock-list>"""


def test_statistics_io_parsing(tmp_path: Path):
    result = json.loads(
        analyze_statistics_io(
            "Table 'Orders'. Scan count 1, logical reads 120, physical reads 2, read-ahead reads 8.",
            workspace=tmp_path,
            max_bytes=1024,
        )
    )
    assert result["tables"] == [
        {
            "table": "Orders",
            "scan_count": 1,
            "logical_reads": 120,
            "physical_reads": 2,
            "read_ahead_reads": 8,
        }
    ]


def test_statistics_io_does_not_invent_missing_fields(tmp_path: Path):
    result = json.loads(
        analyze_statistics_io(
            "Table 'Small'. logical reads 4.", workspace=tmp_path, max_bytes=1024
        )
    )
    assert result["tables"] == [{"table": "Small", "logical_reads": 4}]


def test_statistics_time_parsing_from_file(tmp_path: Path):
    (tmp_path / "time.txt").write_text(
        "SQL Server Execution Times: CPU time = 8000 ms, elapsed time = 2500 ms.",
        encoding="utf-8",
    )
    result = json.loads(
        analyze_statistics_time(
            relative_path="time.txt", workspace=tmp_path, max_bytes=1024
        )
    )
    assert result["timings"] == [{"cpu_time_ms": 8000, "elapsed_time_ms": 2500}]


def test_text_or_path_is_required_exclusively(tmp_path: Path):
    with pytest.raises(ValueError, match="exactamente uno"):
        analyze_statistics_io(workspace=tmp_path, max_bytes=1024)
    with pytest.raises(ValueError, match="exactamente uno"):
        analyze_statistics_io(
            "text", "file.txt", workspace=tmp_path, max_bytes=1024
        )


def test_valid_sqlplan_returns_facts(tmp_path: Path):
    (tmp_path / "plan.sqlplan").write_text(SQLPLAN, encoding="utf-8")
    result = json.loads(
        analyze_execution_plan("plan.sqlplan", workspace=tmp_path, max_bytes=100_000)
    )
    assert result["facts_only"] is True
    assert result["operators"][0]["actual_rows"] == 200
    assert "Index Scan" in result["operator_categories"]["scans"]
    assert "Key Lookup" in result["operator_categories"]["lookups"]
    assert result["missing_index_suggestions"][0]["table"] == "[Orders]"
    assert any(item["type"] == "SpillToTempDb" for item in result["warnings"])


@pytest.mark.parametrize(
    "filename,content",
    [("bad.sqlplan", "<broken>"), ("bad.sqlplan", "<!DOCTYPE x><x />")],
)
def test_invalid_or_unsafe_sqlplan_is_rejected(tmp_path: Path, filename, content):
    (tmp_path / filename).write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        analyze_execution_plan(filename, workspace=tmp_path, max_bytes=1024)


def test_valid_deadlock_xml_returns_facts(tmp_path: Path):
    (tmp_path / "deadlock.xml").write_text(DEADLOCK, encoding="utf-8")
    result = json.loads(
        analyze_deadlock_xml("deadlock.xml", workspace=tmp_path, max_bytes=100_000)
    )
    assert result["victims"] == ["process1"]
    assert {process["spid"] for process in result["processes"]} == {"51", "52"}
    assert result["resources"][0]["type"] == "keylock"
    assert result["resources"][0]["waiters"][0]["id"] == "process1"


def test_invalid_deadlock_xml_is_rejected(tmp_path: Path):
    (tmp_path / "deadlock.xml").write_text("not xml", encoding="utf-8")
    with pytest.raises(ValueError, match="XML inválido"):
        analyze_deadlock_xml("deadlock.xml", workspace=tmp_path, max_bytes=1024)


@pytest.mark.parametrize("path", ["../../plan.sqlplan", "/tmp/plan.sqlplan"])
def test_dba_path_traversal_is_blocked(tmp_path: Path, path: str):
    with pytest.raises(PermissionError):
        analyze_execution_plan(path, workspace=tmp_path, max_bytes=1024)


def test_dba_large_file_is_blocked(tmp_path: Path):
    (tmp_path / "large.sqlplan").write_text("x" * 50, encoding="utf-8")
    with pytest.raises(ValueError, match="demasiado grande"):
        analyze_execution_plan("large.sqlplan", workspace=tmp_path, max_bytes=10)


def test_dba_symlink_escape_is_blocked(tmp_path: Path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (outside / "plan.sqlplan").write_text(SQLPLAN, encoding="utf-8")
    try:
        (workspace / "escape").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("El sistema no permite crear symlinks")
    with pytest.raises(PermissionError):
        analyze_execution_plan(
            "escape/plan.sqlplan", workspace=workspace, max_bytes=100_000
        )
