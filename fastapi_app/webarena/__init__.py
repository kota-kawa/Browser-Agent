# JP: WebArena ルートのパッケージ初期化
# EN: Package init for WebArena routes
from fastapi import APIRouter, Depends

from fastapi_app.routes.admin_auth import require_admin_api_token

router = APIRouter(dependencies=[Depends(require_admin_api_token)])

# JP: ルート登録を遅延インポート
# EN: Import routes to register endpoints
from . import routes as routes
