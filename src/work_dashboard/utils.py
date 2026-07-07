"""共通ユーティリティ。"""

from datetime import date


def current_period(today: date | None = None) -> str:
    """現在の期を返す（FY202504 形式）。

    会社の半期: 4月〜9月 = FY{YYYY}04, 10月〜3月 = FY{YYYY}10
    """
    d = today or date.today()
    if d.month < 4:
        return f"FY{d.year - 1}10"
    elif d.month < 10:
        return f"FY{d.year}04"
    else:
        return f"FY{d.year}10"


def period_label(period: str) -> str:
    """FY202504 → '2025年度 前期（4月〜9月）' のような表示用ラベルを返す。"""
    year = period[2:6]
    month = period[6:8]
    if month == "04":
        return f"{year}年度 前期（4〜9月）"
    else:
        return f"{year}年度 後期（10〜3月）"
