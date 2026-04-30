from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from fastapi import HTTPException, status
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.modules.backups.schemas import BackupCreateResponse, BackupItem, BackupRestoreResponse

BACKUP_VERSION = "1"


class BackupService:
    """第 12 阶段新增：本地 SQLite 和 uploads 目录备份恢复服务。"""

    def __init__(
        self,
        data_dir: str | Path | None = None,
        uploads_dir: str | Path | None = None,
        backups_dir: str | Path | None = None,
        database_url: str | None = None,
    ) -> None:
        self.data_dir = self._resolve_path(data_dir or settings.data_dir)
        self.uploads_dir = self._resolve_path(uploads_dir or settings.uploads_dir)
        self.backups_dir = self._resolve_path(backups_dir or settings.backups_dir)
        self.database_path = self._database_path(database_url or settings.database_url)
        self._ensure_inside(self.uploads_dir, self.data_dir, "上传目录必须位于数据目录内")
        self._ensure_inside(self.backups_dir, self.data_dir, "备份目录必须位于数据目录内")

    def list_backups(self) -> list[BackupItem]:
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        items = [self._to_item(path) for path in self.backups_dir.glob("*.zip") if path.is_file()]
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def create_backup(self, note: str | None = None, *, before_restore: bool = False) -> BackupCreateResponse:
        self._ensure_database_exists()
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        filename = self._new_filename(before_restore)
        target = self._backup_path(filename)
        manifest = {
            "app_name": settings.app_name,
            "backup_version": BACKUP_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database_filename": "app.db",
            "includes_uploads": True,
            "note": note or ("恢复前安全备份" if before_restore else "手动备份"),
        }
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            zip_file.write(self.database_path, "database/app.db")
            zip_file.writestr("uploads/", "")
            for file_path in self.uploads_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                self._ensure_inside(file_path.resolve(), self.uploads_dir, "上传文件路径非法")
                arcname = PurePosixPath("uploads") / file_path.relative_to(self.uploads_dir).as_posix()
                self._validate_zip_member(str(arcname))
                zip_file.write(file_path, str(arcname))
        item = self._to_item(target)
        return BackupCreateResponse(**item.model_dump())

    def get_download_path(self, filename: str) -> Path:
        path = self._backup_path(filename)
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备份文件不存在")
        return path

    def delete_backup(self, filename: str) -> None:
        path = self.get_download_path(filename)
        path.unlink()

    def restore_backup(self, filename: str) -> BackupRestoreResponse:
        source = self.get_download_path(filename)
        self._validate_restore_zip(source)
        safety_backup = self.create_backup(before_restore=True)
        try:
            with TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                uploads_temp = temp_path / "uploads"
                uploads_temp.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(source) as zip_file:
                    database_bytes = zip_file.read("database/app.db")
                    (temp_path / "app.db").write_bytes(database_bytes)
                    for member in zip_file.infolist():
                        name = member.filename
                        if name == "uploads/" or not name.startswith("uploads/") or member.is_dir():
                            continue
                        relative = PurePosixPath(name).relative_to("uploads")
                        target = uploads_temp / Path(*relative.parts)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(zip_file.read(member))
                self.database_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(temp_path / "app.db", self.database_path)
                if self.uploads_dir.exists():
                    shutil.rmtree(self.uploads_dir)
                shutil.copytree(uploads_temp, self.uploads_dir)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"恢复失败，已保留安全备份：{safety_backup.filename}") from exc
        return BackupRestoreResponse(
            restored_filename=source.name,
            safety_backup_filename=safety_backup.filename,
            message="恢复完成，建议重启后端服务",
        )

    def _validate_restore_zip(self, path: Path) -> None:
        if path.suffix.lower() != ".zip":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能恢复 zip 备份文件")
        try:
            with zipfile.ZipFile(path) as zip_file:
                names = zip_file.namelist()
                for name in names:
                    self._validate_zip_member(name)
                if "manifest.json" not in names:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="备份缺少 manifest.json")
                if "database/app.db" not in names:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="备份缺少 database/app.db")
                json.loads(zip_file.read("manifest.json").decode("utf-8"))
        except zipfile.BadZipFile as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="备份文件格式无效") from exc

    def _backup_path(self, filename: str) -> Path:
        if Path(filename).name != filename or Path(filename).suffix.lower() != ".zip":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="备份文件名非法")
        path = (self.backups_dir / filename).resolve()
        self._ensure_inside(path, self.backups_dir, "备份文件路径非法")
        return path

    def _validate_zip_member(self, name: str) -> None:
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts or (pure.parts and ":" in pure.parts[0]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="备份文件包含非法路径")

    def _database_path(self, database_url: str) -> Path:
        url = make_url(database_url)
        if url.drivername != "sqlite" or not url.database or url.database == ":memory:":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持文件型 SQLite 数据库备份")
        return self._resolve_path(url.database)

    def _resolve_path(self, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()

    def _ensure_database_exists(self) -> None:
        if not self.database_path.exists() or not self.database_path.is_file():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="数据库文件不存在，无法创建备份")

    def _ensure_inside(self, path: Path, parent: Path, message: str) -> None:
        try:
            path.relative_to(parent)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    def _new_filename(self, before_restore: bool) -> str:
        prefix = "mymz-before-restore" if before_restore else "mymz-backup"
        return f"{prefix}-{datetime.now():%Y%m%d-%H%M%S}.zip"

    def _to_item(self, path: Path) -> BackupItem:
        stat = path.stat()
        if path.name.startswith("mymz-backup-"):
            kind = "manual"
        elif path.name.startswith("mymz-before-restore-"):
            kind = "before_restore"
        else:
            kind = "unknown"
        return BackupItem(
            filename=path.name,
            size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            kind=kind,
        )
