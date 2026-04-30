from collections.abc import Generator
from pathlib import Path
import sqlite3
import time
import zipfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.deps import get_db
from app.main import create_app
from app.modules.auth.service import init_admin_user


@pytest.fixture()
def backup_client(tmp_path, monkeypatch) -> Generator[tuple[TestClient, Path, Path, Path], None, None]:
    """第 12 阶段新增：备份恢复测试使用临时 data 目录，避免污染真实数据。"""

    data_dir = tmp_path / "data"
    uploads_dir = data_dir / "uploads"
    backups_dir = data_dir / "backups"
    uploads_dir.mkdir(parents=True)
    backups_dir.mkdir(parents=True)
    database_path = data_dir / "app.db"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setattr(settings, "data_dir", str(data_dir))
    monkeypatch.setattr(settings, "uploads_dir", str(uploads_dir))
    monkeypatch.setattr(settings, "backups_dir", str(backups_dir))
    monkeypatch.setattr(settings, "database_url", database_url)

    engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestingSessionLocal() as db:
        init_admin_user(db, username="admin", password="admin123456", display_name="系统管理员")

    with TestClient(app) as test_client:
        yield test_client, data_dir, uploads_dir, backups_dir

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def login(client: TestClient, username: str = "admin", password: str = "admin123456") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_backup(client: TestClient, token: str, note: str = "手动备份") -> dict:
    response = client.post("/api/backups", headers=auth_headers(token), json={"note": note})
    assert response.status_code == 200
    return dict(response.json())


def create_normal_user(client: TestClient, admin_token: str) -> str:
    response = client.post(
        "/api/users",
        headers=auth_headers(admin_token),
        json={
            "username": "staff",
            "display_name": "普通用户",
            "password": "staff123456",
            "role": "staff",
            "is_active": True,
            "is_superuser": False,
        },
    )
    assert response.status_code == 200
    return login(client, "staff", "staff123456")


def test_anonymous_user_cannot_access_backup_list(backup_client) -> None:
    client, *_ = backup_client
    response = client.get("/api/backups")
    assert response.status_code == 401


def test_normal_user_cannot_access_backup_api(backup_client) -> None:
    client, *_ = backup_client
    admin_token = login(client)
    staff_token = create_normal_user(client, admin_token)
    response = client.get("/api/backups", headers=auth_headers(staff_token))
    assert response.status_code == 403


def test_superuser_can_create_backup_and_filename_matches_rule(backup_client) -> None:
    client, _, uploads_dir, _ = backup_client
    token = login(client)
    (uploads_dir / "sample.txt").write_text("upload data", encoding="utf-8")
    data = create_backup(client, token)
    assert data["filename"].startswith("mymz-backup-")
    assert data["filename"].endswith(".zip")
    assert data["size"] > 0


def test_backup_zip_contains_manifest_database_and_uploads(backup_client) -> None:
    client, _, uploads_dir, backups_dir = backup_client
    token = login(client)
    (uploads_dir / "nested").mkdir()
    (uploads_dir / "nested" / "file.txt").write_text("upload data", encoding="utf-8")
    data = create_backup(client, token)
    with zipfile.ZipFile(backups_dir / data["filename"]) as zip_file:
        names = set(zip_file.namelist())
    assert "manifest.json" in names
    assert "database/app.db" in names
    assert "uploads/nested/file.txt" in names
    assert not any(name.startswith("backups/") or "data/backups" in name for name in names)


def test_backup_list_orders_by_created_time_desc(backup_client) -> None:
    client, _, _, backups_dir = backup_client
    token = login(client)
    older = create_backup(client, token)["filename"]
    time.sleep(1.1)
    newer = create_backup(client, token)["filename"]
    response = client.get("/api/backups", headers=auth_headers(token))
    assert response.status_code == 200
    items = response.json()
    assert items[0]["filename"] == newer
    assert any(item["filename"] == older for item in items)


def test_can_download_backup(backup_client) -> None:
    client, *_ = backup_client
    token = login(client)
    data = create_backup(client, token)
    response = client.get(f"/api/backups/{data['filename']}/download", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.content.startswith(b"PK")


def test_can_delete_backup_and_missing_returns_404(backup_client) -> None:
    client, *_ = backup_client
    token = login(client)
    data = create_backup(client, token)
    response = client.delete(f"/api/backups/{data['filename']}", headers=auth_headers(token))
    assert response.status_code == 200
    response = client.delete("/api/backups/missing.zip", headers=auth_headers(token))
    assert response.status_code == 404


def test_path_traversal_filename_is_rejected(backup_client) -> None:
    client, *_ = backup_client
    token = login(client)
    response = client.get("/api/backups/..%2Fapp.db/download", headers=auth_headers(token))
    assert response.status_code == 400


def test_non_zip_file_cannot_be_restored(backup_client) -> None:
    client, _, _, backups_dir = backup_client
    token = login(client)
    (backups_dir / "bad.txt").write_text("bad", encoding="utf-8")
    response = client.post("/api/backups/restore", headers=auth_headers(token), json={"filename": "bad.txt"})
    assert response.status_code == 400


def test_zip_missing_manifest_cannot_be_restored(backup_client) -> None:
    client, _, _, backups_dir = backup_client
    token = login(client)
    filename = "missing-manifest.zip"
    with zipfile.ZipFile(backups_dir / filename, "w") as zip_file:
        zip_file.writestr("database/app.db", b"db")
    response = client.post("/api/backups/restore", headers=auth_headers(token), json={"filename": filename})
    assert response.status_code == 400


def test_zip_missing_database_cannot_be_restored(backup_client) -> None:
    client, _, _, backups_dir = backup_client
    token = login(client)
    filename = "missing-db.zip"
    with zipfile.ZipFile(backups_dir / filename, "w") as zip_file:
        zip_file.writestr("manifest.json", "{}")
    response = client.post("/api/backups/restore", headers=auth_headers(token), json={"filename": filename})
    assert response.status_code == 400


def test_restore_creates_safety_backup_and_replaces_database_and_uploads(backup_client) -> None:
    client, data_dir, uploads_dir, backups_dir = backup_client
    token = login(client)
    uploads_original = uploads_dir / "original.txt"
    uploads_original.write_text("old upload", encoding="utf-8")
    data = create_backup(client, token)
    backup_path = backups_dir / data["filename"]

    changed_bytes_marker = (data_dir / "app.db").read_bytes()
    create_normal_user(client, token)
    assert (data_dir / "app.db").read_bytes() != changed_bytes_marker
    uploads_original.unlink()
    (uploads_dir / "changed.txt").write_text("changed upload", encoding="utf-8")

    response = client.post("/api/backups/restore", headers=auth_headers(token), json={"filename": backup_path.name})
    assert response.status_code == 200
    payload = response.json()
    assert payload["restored_filename"] == backup_path.name
    assert payload["safety_backup_filename"].startswith("mymz-before-restore-")
    assert (backups_dir / payload["safety_backup_filename"]).exists()
    with sqlite3.connect(data_dir / "app.db") as connection:
        staff_count = connection.execute("select count(*) from users where username = 'staff'").fetchone()[0]
    assert staff_count == 0
    assert (uploads_dir / "original.txt").read_text(encoding="utf-8") == "old upload"
    assert not (uploads_dir / "changed.txt").exists()


def test_backup_does_not_include_design_files(backup_client) -> None:
    client, data_dir, uploads_dir, backups_dir = backup_client
    token = login(client)
    (data_dir / "design_files").mkdir()
    (data_dir / "design_files" / "secret.html").write_text("do not backup", encoding="utf-8")
    (uploads_dir / "allowed.txt").write_text("allowed", encoding="utf-8")
    data = create_backup(client, token)
    with zipfile.ZipFile(backups_dir / data["filename"]) as zip_file:
        names = zip_file.namelist()
    assert "uploads/allowed.txt" in names
    assert not any("design_files" in name for name in names)
