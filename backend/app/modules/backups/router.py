from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.core.deps import require_superuser
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

router = APIRouter()


@router.get("/backups", response_model=list[BackupItem])
def list_backups(current_user: User = Depends(require_superuser)) -> list[BackupItem]:
    return BackupService().list_backups()


@router.post("/backups", response_model=BackupCreateResponse)
def create_backup(
    payload: BackupCreate,
    current_user: User = Depends(require_superuser),
) -> BackupCreateResponse:
    return BackupService().create_backup(note=payload.note)


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
    current_user: User = Depends(require_superuser),
) -> SuccessResponse:
    BackupService().delete_backup(filename)
    return SuccessResponse()


@router.post("/backups/restore", response_model=BackupRestoreResponse)
def restore_backup(
    payload: BackupRestoreRequest,
    current_user: User = Depends(require_superuser),
) -> BackupRestoreResponse:
    return BackupService().restore_backup(payload.filename)
