from fastapi import APIRouter

from .auth import router as auth_router
from .chat import router as chat_router
from .metrics import router as metrics_router
from .notifications import router as notifications_router

# from .optimization import router as optimization_router  # DEPRECATED: ABTest and OptimizationSuggestion models removed
from .product_tracking import router as product_tracking_router
from .suggestions import router as suggestions_router
from .user_products import router as user_products_router
from .user_settings import router as user_settings_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(user_settings_router, prefix="/user", tags=["user-settings"])
router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
# router.include_router(optimization_router, prefix="/optimization", tags=["optimization"])  # DEPRECATED: ABTest and OptimizationSuggestion models removed
router.include_router(metrics_router, prefix="/metrics", tags=["metrics"])
router.include_router(product_tracking_router, prefix="/tracking", tags=["product-tracking"])
router.include_router(user_products_router, prefix="/user-products", tags=["user-products"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(suggestions_router, prefix="/suggestions", tags=["ai-suggestions"])
