from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.permissions import Permission, require_permission
from app.modules.audit_logs.schemas import AuditLogListResponse, AuditLogRead
from app.modules.audit_logs.service import AuditLogService
from app.modules.users.model import User

router = APIRouter(prefix="/audit-logs")


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    keyword: str | None = None,
    user_id: int | None = None,
    module: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AUDIT_LOGS_VIEW)),
) -> AuditLogListResponse:
    return AuditLogService(db).list_logs(keyword, user_id, module, action, target_type, start_date, end_date, page, page_size)


@router.get("/{log_id}", response_model=AuditLogRead)
def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AUDIT_LOGS_VIEW)),
) -> AuditLogRead:
    return AuditLogService(db).get_log(log_id)
