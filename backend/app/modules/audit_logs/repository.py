from datetime import date, time

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.modules.audit_logs.model import AuditLog


class AuditLogRepository:
    """第 13 阶段新增：操作日志查询和写入集中在 repository。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, log: AuditLog) -> AuditLog:
        self.db.add(log)
        self.db.flush()
        return log

    def get(self, log_id: int) -> AuditLog | None:
        return self.db.get(AuditLog, log_id)

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
    ) -> tuple[list[AuditLog], int]:
        filters = []
        if keyword:
            like_keyword = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    AuditLog.username.like(like_keyword),
                    AuditLog.summary.like(like_keyword),
                    AuditLog.target_label.like(like_keyword),
                    AuditLog.path.like(like_keyword),
                )
            )
        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)
        if module:
            filters.append(AuditLog.module == module)
        if action:
            filters.append(AuditLog.action == action)
        if target_type:
            filters.append(AuditLog.target_type == target_type)
        if start_date:
            filters.append(AuditLog.created_at >= start_date)
        if end_date:
            filters.append(AuditLog.created_at <= end_date)
        where_clause = and_(*filters) if filters else True
        total = int(self.db.scalar(select(func.count()).select_from(AuditLog).where(where_clause)) or 0)
        stmt = (
            select(AuditLog)
            .where(where_clause)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total
