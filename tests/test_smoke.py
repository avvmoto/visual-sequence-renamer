"""主要機能のスモークテスト（起動・フロー確認は後続で拡張）。"""


def test_app_package_importable() -> None:
    """`app` パッケージがインポートできること。"""
    from app.main import main

    assert callable(main)
