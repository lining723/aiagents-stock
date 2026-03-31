from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings
from backend.schemas.response import SuccessResponse, ErrorResponse, HealthCheckResponse
from backend.api.v1 import stock_router, longhubang_router, monitor_router, analysis_router
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 80)
    logger.info(f"{settings.PROJECT_NAME} 启动")
    logger.info(f"版本: {settings.VERSION}")
    logger.info("=" * 80)
    yield
    logger.info(f"{settings.PROJECT_NAME} 关闭")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(stock_router, prefix=settings.API_V1_STR)
app.include_router(longhubang_router, prefix=settings.API_V1_STR)
app.include_router(monitor_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    error_response = ErrorResponse.error(
        code=500,
        message="服务器内部错误",
        errors=[str(exc)]
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


@app.get("/health", tags=["健康检查"], response_model=HealthCheckResponse)
async def health_check():
    return HealthCheckResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
    )


@app.get("/", tags=["根路径"], response_model=SuccessResponse[dict])
async def root():
    return SuccessResponse.success(
        data={
            "message": "Welcome to AI Agents Stock API",
            "docs": "/docs",
        },
        message="服务运行正常"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
