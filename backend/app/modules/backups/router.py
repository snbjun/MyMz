from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse

from app.core.deps import get_db, require_superuser
from app.modules.audit_logs.service import record_audit_log
from app.modules.backups.schemas import (
    BackupCreate,
    BackupCreateResponse,
    BackupItem,
    BackupRestoreRequest,
    BackupRestoreResponse,
    SuccessResponse,
)
from app.modules.backups.service import BackupService
from app.modules.users.model import User
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/backups", response_model=list[BackupItem])
def list_backups(current_user: User = Depends(require_superuser)) -> list[BackupItem]:
    return BackupService().list_backups()


@router.post("/backups", response_model=BackupCreateResponse)
def create_backup(
    payload: BackupCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> BackupCreateResponse:
    result = BackupService().create_backup(note=payload.note)
    record_audit_log(
        db,
        current_user,
        module="backups",
        action="create",
        target_type="backup",
        target_label=result.filename,
        summary=f"创建备份：{result.filename}",
        request=request,
    )
    return result


@router.get("/backups/{filename:path}/download")
def download_backup(
    filename: str,
    current_user: User = Depends(require_superuser),
) -> FileResponse:
    path = BackupService().get_download_path(filename)
    return FileResponse(path=path, filename=path.name, media_type="application/zip")


@router.delete("/backups/{filename:path}", response_model=SuccessResponse)
def delete_backup(
    filename: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> SuccessResponse:
    BackupService().delete_backup(filename)
    record_audit_log(
        db,
        current_user,
        module="backups",
        action="delete",
        target_type="backup",
        target_label=filename,
        summary=f"删除备份：{filename}",
        request=request,
    )
    return SuccessResponse()


@router.post("/backups/restore", response_model=BackupRestoreResponse)
def restore_backup(
    payload: BackupRestoreRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> BackupRestoreResponse:
    result = BackupService().restore_backup(payload.filename)
    record_audit_log(
        db,
        current_user,
        module="backups",
        action="restore",
        target_type="backup",
        target_label=result.restored_filename,
        summary=f"恢复备份：{result.restored_filename}",
        request=request,
    )
    return result
