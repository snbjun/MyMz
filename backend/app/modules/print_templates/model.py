from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PrintSetting(Base):
    """第 11 阶段新增：销售单/采购单浏览器打印配置。"""

    __tablename__ = "print_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    doc_type: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    template_name: Mapped[str] = mapped_column(String(64), nullable=False, default="标准模板")
    paper_size: Mapped[str] = mapped_column(String(16), nullable=False, default="A4")
    show_company_name: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    company_name: Mapped[str | None] = mapped_column(String(128))
    show_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contact_text: Mapped[str | None] = mapped_column(String(255))
    show_amount: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_unit_price: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_discount: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_remark: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_signature: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    footer_text: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (Index("ix_print_settings_doc_type", "doc_type"),)

