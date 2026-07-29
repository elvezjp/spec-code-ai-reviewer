"""safe_filename のテスト（パストラバーサル対策）。"""

import os
import tempfile
from pathlib import Path

import pytest

from app.safe_path import safe_filename


class TestSafeFilename:
    """通常のファイル名は保持し、パス成分は除去する。"""

    def test_plain_filename_is_kept(self):
        assert safe_filename("report.xlsx") == "report.xlsx"

    def test_japanese_filename_is_kept(self):
        assert safe_filename("設計書.xlsx") == "設計書.xlsx"

    @pytest.mark.parametrize(
        "given,expected",
        [
            ("/etc/passwd", "passwd"),
            ("../../etc/passwd", "passwd"),
            ("dir/sub/report.xlsx", "report.xlsx"),
            ("/opt/app/backend/app/routers/split.py", "split.py"),
            ("C:\\Windows\\System32\\evil.xlsx", "evil.xlsx"),
        ],
    )
    def test_path_components_are_stripped(self, given, expected):
        assert safe_filename(given) == expected

    @pytest.mark.parametrize("given", [None, "", "   ", ".", "..", "/", "../"])
    def test_empty_or_dot_names_fall_back_to_default(self, given):
        assert safe_filename(given) == "input"

    def test_custom_default(self):
        assert safe_filename(None, "input.md") == "input.md"


class TestJoinIsContained:
    """サニタイズ後の結合先が必ず基準ディレクトリ配下になること。"""

    @pytest.mark.parametrize(
        "attack",
        [
            "/etc/evil.conf",
            "../../../../etc/evil.conf",
            "/opt/app/backend/app/main.py",
        ],
    )
    def test_os_path_join_stays_inside(self, attack):
        with tempfile.TemporaryDirectory() as tmpdir:
            joined = os.path.join(tmpdir, safe_filename(attack))
            assert Path(joined).resolve().parent == Path(tmpdir).resolve()

    @pytest.mark.parametrize("attack", ["/etc/evil.xlsx", "../../evil.xlsx"])
    def test_pathlib_join_stays_inside(self, attack):
        with tempfile.TemporaryDirectory() as tmpdir:
            joined = Path(tmpdir) / safe_filename(attack)
            assert joined.resolve().parent == Path(tmpdir).resolve()

    def test_unsanitized_join_would_escape(self):
        """サニタイズしない場合は脱出できることを確認（回帰検知用）。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            escaped = os.path.join(tmpdir, "/etc/evil.conf")
            # Windows では join 結果にドライブ文字が付くため、厳密一致は POSIX のみ検証
            if os.name != "nt":
                assert escaped == "/etc/evil.conf"
            assert Path(escaped).resolve().parent != Path(tmpdir).resolve()
