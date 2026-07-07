"""アプリ起動・主要ページの疎通テスト。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from work_dashboard.database import get_db
from work_dashboard.main import app
from work_dashboard.models import Base


@pytest.fixture()
def client() -> TestClient:
    """インメモリ SQLite を使ったテストクライアント。

    StaticPool により全接続で同一のインメモリ DB を共有する。
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():  # noqa: ANN202
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


# ---------------------------------------------------------------------------
# 基本ページ疎通
# ---------------------------------------------------------------------------


def test_dashboard(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "ダッシュボード" in res.text


def test_member_list(client: TestClient) -> None:
    res = client.get("/members")
    assert res.status_code == 200


def test_task_list(client: TestClient) -> None:
    res = client.get("/tasks")
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# タスク CRUD
# ---------------------------------------------------------------------------


def test_create_and_complete_task(client: TestClient) -> None:
    # メンバー作成
    res = client.post("/members", data={"name": "テストユーザー", "is_self": "1"})
    assert res.status_code == 200

    # タスク作成
    res = client.post(
        "/tasks",
        data={"name": "テストタスク", "member_id": "1", "deadline": "2099-12-31"},
    )
    assert res.status_code == 200

    # タスク一覧に表示される
    res = client.get("/tasks")
    assert "テストタスク" in res.text

    # 完了
    res = client.post("/tasks/1/done")
    assert res.status_code == 200

    # 未完了フィルタ（デフォルト）では非表示
    res = client.get("/tasks")
    assert "テストタスク" not in res.text


def test_task_member_filter(client: TestClient) -> None:
    """メンバーフィルタが機能する。"""
    # 2メンバー作成
    client.post("/members", data={"name": "メンバーA"})
    client.post("/members", data={"name": "メンバーB"})

    # 各メンバーにタスクを作成
    client.post("/tasks", data={"name": "AのタスクX", "member_id": "1", "deadline": "2099-01-01"})
    client.post("/tasks", data={"name": "BのタスクY", "member_id": "2", "deadline": "2099-01-01"})

    # メンバーA でフィルタ
    res = client.get("/tasks?member_id=1")
    assert "AのタスクX" in res.text
    assert "BのタスクY" not in res.text


# ---------------------------------------------------------------------------
# WCM / Must CRUD
# ---------------------------------------------------------------------------


def test_wcm_lifecycle(client: TestClient) -> None:
    """WCM 作成 → Will/Can 保存 → Must 追加 → 編集 → 削除。"""
    # メンバー作成
    client.post("/members", data={"name": "山田 太郎", "is_self": "1"})

    # メンバー詳細ページが表示される（WCM 未作成）
    res = client.get("/members/1")
    assert res.status_code == 200

    # WCM 初期化
    res = client.post("/members/1/wcm/init", data={"period": "FY202504"})
    assert res.status_code == 200

    # Will/Can 保存
    res = client.post(
        "/members/1/wcm/1/will-can",
        data={"will": "リーダーになりたい", "can": "Pythonが得意"},
    )
    assert res.status_code == 200

    # メンバー詳細に反映
    res = client.get("/members/1?period=FY202504")
    assert "リーダーになりたい" in res.text
    assert "Pythonが得意" in res.text

    # Must 追加
    res = client.post(
        "/members/1/wcm/1/musts",
        data={
            "theme": "品質向上",
            "sub_theme": "テスト整備",
            "mission": "カバレッジ 80% 達成",
            "criteria": "coverage report で確認",
            "progress": "現在 60%",
        },
    )
    assert res.status_code == 200

    # Must が一覧に表示される
    res = client.get("/members/1?period=FY202504")
    assert "カバレッジ 80% 達成" in res.text

    # Must 編集
    res = client.post(
        "/members/1/wcm/1/musts/1/edit",
        data={
            "theme": "品質向上",
            "sub_theme": "テスト整備",
            "mission": "カバレッジ 90% 達成",
            "criteria": "",
            "progress": "現在 70%",
        },
    )
    assert res.status_code == 200
    res = client.get("/members/1?period=FY202504")
    assert "カバレッジ 90% 達成" in res.text

    # Must 削除
    res = client.post("/members/1/wcm/1/musts/1/delete")
    assert res.status_code == 200
    res = client.get("/members/1?period=FY202504")
    assert "カバレッジ 90% 達成" not in res.text


def test_must_reorder(client: TestClient) -> None:
    """Must の並び替えが機能する。"""
    client.post("/members", data={"name": "鈴木"})
    client.post("/members/1/wcm/init", data={"period": "FY202504"})

    # 3件追加
    for i in range(1, 4):
        client.post(
            "/members/1/wcm/1/musts",
            data={"theme": f"テーマ{i}", "mission": f"ミッション{i}"},
        )

    # 2番目を上へ移動 → 1番目と入れ替わる
    res = client.post("/members/1/wcm/1/musts/2/move", data={"direction": "up"})
    assert res.status_code == 200
