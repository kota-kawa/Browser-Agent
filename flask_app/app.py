from __future__ import annotations

from flask import Flask, Response, request

from .routes import register_routes
from .services.agent_runtime import get_agent_controller
from .webarena import webarena_bp

app = Flask(__name__)
app.json.ensure_ascii = False
app.register_blueprint(webarena_bp)
register_routes(app)


def _get_agent_controller():
	return get_agent_controller()


@app.before_request
def _handle_cors_preflight():
	"""Return an empty response for CORS preflight requests."""

	if request.method == 'OPTIONS':
		response = Response(status=204)
		response.headers['Access-Control-Allow-Origin'] = '*'
		response.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', '*')
		response.headers['Access-Control-Allow-Methods'] = request.headers.get(
			'Access-Control-Request-Method',
			'GET, POST, PUT, PATCH, DELETE, OPTIONS',
		)
		return response


@app.after_request
def _set_cors_headers(response: Response):
	"""Attach permissive CORS headers to all responses."""

	response.headers.setdefault('Access-Control-Allow-Origin', '*')
	response.headers.setdefault(
		'Access-Control-Allow-Headers',
		request.headers.get('Access-Control-Request-Headers', 'Content-Type, Authorization'),
	)
	response.headers.setdefault('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
	return response


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5005)
