"""period 計算のユニットテスト。"""

from datetime import date

from work_dashboard.utils import current_period


def test_period_april() -> None:
    assert current_period(date(2025, 4, 1)) == "FY202504"


def test_period_september() -> None:
    assert current_period(date(2025, 9, 30)) == "FY202504"


def test_period_october() -> None:
    assert current_period(date(2025, 10, 1)) == "FY202510"


def test_period_march_next_year() -> None:
    """3月は前年の10月期になる。"""
    assert current_period(date(2026, 3, 31)) == "FY202510"
