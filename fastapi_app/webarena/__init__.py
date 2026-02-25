# JP: WebArena ルートのパッケージ初期化
# EN: Package init for WebArena routes
from fastapi import APIRouter

router = APIRouter()

# JP: ルート登録を遅延インポート
# EN: Import routes to register endpoints
from . import routes
