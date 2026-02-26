# JP: WebArena ルートのパッケージ初期化
# EN: Package init for WebArena routes
from fastapi import APIRouter

# EN: Assign value to router.
# JP: router に値を代入する。
router = APIRouter()

# JP: ルート登録を遅延インポート
# EN: Import routes to register endpoints
from . import routes
