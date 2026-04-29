from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """骨架阶段新增：供本地开发、Docker 和测试使用的健康检查。"""

    return {"status": "ok", "service": "mymz-backend"}
