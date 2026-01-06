from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import APP_STATIC_DIR
from .routes import register_routes
from .services.agent_runtime import get_agent_controller
from .webarena import router as webarena_router

app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_methods=['*'],
	allow_headers=['*'],
)
app.mount('/static', StaticFiles(directory=str(APP_STATIC_DIR)), name='static')
app.include_router(webarena_router)
register_routes(app)


def _get_agent_controller():
	return get_agent_controller()


app.state.get_agent_controller = _get_agent_controller


if __name__ == '__main__':
	import uvicorn

	uvicorn.run('flask_app.app:app', host='0.0.0.0', port=5005, reload=False)
