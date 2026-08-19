"""Tests for nowhere.health — Card 29 health check module.

Tests:
  1. health.py runs without crashing (smoke test)
  2. Report is generated with expected structure
  3. A known failure appears in report (mock one)
"""
from __future__ import annotations

import pathlib
import sys
import textwrap
from unittest import mock

import pytest

# Ensure repo root is on path
_REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

from nowhere.health import (
    Finding,
    SectionResult,
    _generate_report,
    _print_console_summary,
)


# ═══════════════════════════════════════════════════════════════════════
# Test 1: Module imports and data structures work
# ═══════════════════════════════════════════════════════════════════════

class TestImports:
    """Smoke test: the module imports and core structures work."""

    def test_finding_creation(self):
        f = Finding(id="TEST-001", source="tests", level="pass", phenomenon="ok")
        assert f.symbol == "✓"
        assert f.level == "pass"

    def test_finding_fail_symbol(self):
        f = Finding(id="TEST-002", source="tests", level="fail", phenomenon="broken")
        assert f.symbol == "✗"

    def test_finding_skip_symbol(self):
        f = Finding(id="TEST-003", source="tests", level="skip", phenomenon="skipped")
        assert f.symbol == "S"

    def test_section_result_counts(self):
        s = SectionResult(source="test", elapsed=1.0, findings=[
            Finding(id="A", source="test", level="pass", phenomenon=""),
            Finding(id="B", source="test", level="fail", phenomenon=""),
            Finding(id="C", source="test", level="pass", phenomenon=""),
        ])
        assert s.pass_count == 2
        assert s.fail_count == 1
        assert s.skip_count == 0
        assert len(s.findings) == 3


# ═══════════════════════════════════════════════════════════════════════
# Test 2: Report generation produces valid markdown
# ═══════════════════════════════════════════════════════════════════════

class TestReportGeneration:
    """Test that _generate_report produces valid markdown."""

    def test_report_has_header(self):
        sections = [
            SectionResult(source="geocode", elapsed=1.0, findings=[
                Finding(id="GEO-001", source="geocode", level="pass",
                        phenomenon="all good"),
            ]),
        ]
        report = _generate_report(sections, 5.0)
        assert "# Nowhere Health Report" in report
        assert "Generated" in report
        assert "Total items" in report

    def test_report_has_all_sources(self):
        sections = [
            SectionResult(source="geocode", elapsed=1.0, findings=[]),
            SectionResult(source="probe", elapsed=2.0, findings=[]),
            SectionResult(source="alignment", elapsed=3.0, findings=[]),
            SectionResult(source="lqa", elapsed=4.0, findings=[]),
            SectionResult(source="tests", elapsed=5.0, findings=[]),
        ]
        report = _generate_report(sections, 15.0)
        for src in ["geocode", "probe", "alignment", "lqa", "tests"]:
            assert src.upper() in report or src in report.lower()

    def test_report_shows_failures(self):
        sections = [
            SectionResult(source="geocode", elapsed=0.5, findings=[
                Finding(id="GEO-001", source="geocode", level="fail",
                        phenomenon="wrong country code",
                        reproduction="trace_lookup('Paris')"),
            ]),
        ]
        report = _generate_report(sections, 1.0)
        assert "wrong country code" in report
        assert "trace_lookup" in report
        assert "✗" in report

    def test_report_summary_table(self):
        sections = [
            SectionResult(source="geocode", elapsed=1.0, findings=[
                Finding(id="GEO-001", source="geocode", level="pass", phenomenon="ok"),
                Finding(id="GEO-002", source="geocode", level="fail", phenomenon="bad"),
            ]),
        ]
        report = _generate_report(sections, 2.0)
        assert "| geocode |" in report
        assert "| 2 |" in report  # total items


# ═══════════════════════════════════════════════════════════════════════
# Test 3: Known failure appears in report (mock one)
# ═══════════════════════════════════════════════════════════════════════

class TestKnownFailure:
    """Test that injecting a known failure produces it in the report."""

    def test_mock_failure_in_report(self):
        """Simulate a known failure and verify it appears in the report."""
        mock_findings = [
            Finding(
                id="MOCK-001",
                source="probe",
                level="fail",
                phenomenon="温度 30 度但文本说「寒风」",
                reproduction="place=北京, action=walk_1, temp=30",
                detail="温度数据与文本体感矛盾",
            ),
            Finding(
                id="MOCK-002",
                source="geocode",
                level="pass",
                phenomenon="全部 84 城市国家码正确",
            ),
        ]

        sections = [
            SectionResult(source="probe", elapsed=0.5, findings=[mock_findings[0]]),
            SectionResult(source="geocode", elapsed=0.3, findings=[mock_findings[1]]),
        ]

        report = _generate_report(sections, 0.8)

        # The mock failure must appear
        assert "MOCK-001" in report
        assert "温度 30 度" in report
        assert "寒风" in report
        assert "✗" in report

        # The mock pass must also appear
        assert "MOCK-002" in report
        assert "✓" in report

        # Counts should be correct
        assert "**Pass**: 1" in report

    def test_console_summary_shows_failures(self, capsys):
        """Test that console summary prints failure details."""
        sections = [
            SectionResult(source="alignment", elapsed=0.1, findings=[
                Finding(id="ALN-BAD", source="alignment", level="fail",
                        phenomenon="some bug found",
                        reproduction="run this"),
            ]),
        ]
        _print_console_summary(sections, 0.1)
        captured = capsys.readouterr()
        assert "FAIL" in captured.out
        assert "ALN-BAD" in captured.out
        assert "some bug found" in captured.out


# ═══════════════════════════════════════════════════════════════════════
# Test 4: Empty sections produce valid report
# ═══════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge case: empty results, no findings."""

    def test_empty_sections(self):
        sections = []
        report = _generate_report(sections, 0.0)
        assert "# Nowhere Health Report" in report
        assert "Total items**: 0" in report

    def test_all_pass(self):
        sections = [
            SectionResult(source="geocode", elapsed=0.1, findings=[
                Finding(id="GEO-001", source="geocode", level="pass", phenomenon="ok"),
            ]),
            SectionResult(source="probe", elapsed=0.1, findings=[
                Finding(id="PRB-001", source="probe", level="pass", phenomenon="ok"),
            ]),
        ]
        report = _generate_report(sections, 0.2)
        assert "Fail**: 0" in report
        assert "Pass**: 2" in report


# ═══════════════════════════════════════════════════════════════════════
# Test 5: Individual runners can be called without crash (integration)
# ═══════════════════════════════════════════════════════════════════════

class TestRunners:
    """Integration tests for individual runners (may be slow)."""

    @pytest.mark.slow
    def test_run_geocode_returns_section(self):
        from nowhere.health import _run_geocode
        result = _run_geocode()
        assert isinstance(result, SectionResult)
        assert result.source == "geocode"
        assert len(result.findings) > 0

    @pytest.mark.slow
    def test_run_alignment_returns_section(self):
        from nowhere.health import _run_alignment
        result = _run_alignment()
        assert isinstance(result, SectionResult)
        assert result.source == "alignment"
        assert len(result.findings) > 0
