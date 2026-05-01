from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: int
    user_id: int | None = None
    username: str | None = None
    module: str
    action: str
    target_type: str | None = None
    target_id: str | None = None
    target_label: str | None = None
    method: str | None = None
    path: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    total: int
    page: int
    page_size: int
