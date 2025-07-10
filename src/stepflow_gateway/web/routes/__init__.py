"""
Web 路由包
"""

from .users import router as users_router
from .apis import router as apis_router
from .endpoints import router as endpoints_router
from .auth import router as auth_router
from .calls import router as calls_router
from .stats import router as stats_router
from .resources import router as resources_router
from .templates import router as templates_router

__all__ = [
    'users_router',
    'apis_router',
    'endpoints_router', 
    'auth_router',
    'calls_router',
    'stats_router',
    'resources_router',
    'templates_router'
] 