from datetime import date

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.modules.audit_logs.model import AuditLog
from app.modules.audit_logs.repository import AuditLogRepository
from app.modules.audit_logs.schemas import AuditLogListResponse, AuditLogRead
from app.modules.users.model import User


class AuditLogService:
    """第 13 阶段新增：操作日志记录失败不影响主业务。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuditLogRepository(db)

    def list_logs(
        self,
        keyword: str | None,
        user_id: int | None,
        module: str | None,
        action: str | None,
        target_type: str | None,
        start_date: date | None,
        end_date: date | None,
        page: int,
        page_size: int,
    ) -> AuditLogListResponse:
        logs, total = self.repo.list_logs(keyword, user_id, module, action, target_type, start_date, end_date, page, page_size)
        return AuditLogListResponse(items=[AuditLogRead.model_validate(log) for log in logs], total=total, page=page, page_size=page_size)

    def get_log(self, log_id: int) -> AuditLogRead:
        log = self.repo.get(log_id)
        if log is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="操作日志不存在")
        return AuditLogRead.model_validate(log)

    def record(
        self,
        user: User | None,
        module: str,
        action: str,
        summary: str,
        target_type: str | None = None,
        target_id: int | str | None = None,
        target_label: str | None = None,
        request: Request | None = None,
    ) -> None:
        try:
            log = AuditLog(
                user_id=user.id if user else None,
                username=user.username if user else None,
                module=module,
                action=action,
                target_type=target_type,
                target_id=str(target_id) if target_id is not None else None,
                target_label=target_label,
                method=request.method if request else None,
                path=str(request.url.path) if request else None,
                ip_address=request.client.host if request and request.client else None,
                user_agent=request.headers.get("user-agent") if request else None,
                summary=summary,
            )
            self.repo.create(log)
            self.db.commit()
        except Exception:
            self.db.rollback()


def record_audit_log(
    db: Session,
    user: User | None,
    module: str,
    action: str,
    summary: str,
    target_type: str | None = None,
    target_id: int | str | None = None,
    target_label: str | None = None,
    request: Request | None = None,
) -> None:
    AuditLogService(db).record(user, module, action, summary, target_type, target_id, target_label, request)
