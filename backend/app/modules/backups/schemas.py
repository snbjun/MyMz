from datetime import datetime

from pydantic import BaseModel, Field


class BackupCreate(BaseModel):
    note: str | None = None


class BackupItem(BaseModel):
    filename: str
    size: int
    created_at: datetime
    kind: str


class BackupCreateResponse(BackupItem):
    pass


class BackupRestoreRequest(BaseModel):
    filename: str = Field(min_length=1)


class BackupRestoreResponse(BaseModel):
    restored_filename: str
    safety_backup_filename: str
    message: str


class SuccessResponse(BaseModel):
    success: bool = True
