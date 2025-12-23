# Browser-Agent

<p align="center">
  <img src="static/Browser-Agent-Icon.png" width="400" alt="Browser-Agent Icon">
</p>

A powerful browser automation agent with a Flask-based web interface, powered by modern LLMs. This project allows you to control a browser using natural language, visualize the execution in real-time, and even run benchmarks like WebArena.

## 🚀 Overview

`Browser-Agent` integrates the `browser_use` library with a robust Flask backend to provide:
- **Natural Language Control**: Instruct the browser to perform tasks like "Search for the cheapest flight to Tokyo" or "Log into my account and check messages".
- **Real-time Visualization**: Watch the agent's actions live via a noVNC stream and see step-by-step logs in the UI.
- **Multi-LLM Support**: Compatible with Gemini, OpenAI, Anthropic, DeepSeek, and more.
- **WebArena Benchmarking**: Built-in tools to run and evaluate standard browser automation benchmarks.

## ✨ Key Features

- **Web Interface**: A clean, responsive UI to interact with the agent, view the browser screen, and monitor execution logs.
- **Live Streaming**: Real-time feedback using Server-Sent Events (SSE) and VNC for browser visibility.
- **Scratchpad**: A dedicated memory space for the agent to store and structure extracted data (e.g., prices, names, reviews) during tasks.
- **Conversation Analysis**: An API endpoint (`/api/check-conversation-history`) to analyze chat history and determine if browser action is required.
- **Docker Ready**: Fully containerized setup for easy deployment using Docker Compose.
- **Extensible Architecture**: Modular design separating the core agent (`browser_use`), API services (`flask_app`), and UI.

## 🛠️ Installation

### Prerequisites
- **Python 3.11+**
- **Docker & Docker Compose** (recommended for full stack)
- **uv** (recommended for local Python management)
- **Google Chrome** (if running locally without Docker)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/browser-agent.git
cd browser-agent
```

### 2. Environment Setup
Copy the example secrets file and configure your API keys.
```bash
cp secrets.env.example secrets.env
```
Edit `secrets.env` and add your LLM provider keys (e.g., `GOOGLE_API_KEY`, `OPENAI_API_KEY`).

### 3. Run with Docker (Recommended)
This will start the Flask app, a Chrome instance, and the VNC server.
```bash
docker-compose up --build
```
Access the UI at: http://localhost:5005

### 4. Run Locally
If you prefer running without Docker:

**Install Dependencies:**
```bash
# Using uv (recommended)
./bin/setup.sh

# Or using pip
pip install -r flask_app/requirements.txt
```

**Start the Application:**
Make sure you have a Chrome instance running with remote debugging enabled, or set `BROWSER_USE_CDP_URL` to a remote CDP endpoint.
```bash
uv run flask run --host 0.0.0.0 --port 5005
```

## 📖 Usage

### Web UI
1. Open http://localhost:5005 in your browser.
2. Type your instruction in the chat box (e.g., "Go to amazon.com and find a good mechanical keyboard").
3. The agent will start executing the task. You can see the browser view on the left and the logs/chat on the right.

### WebArena Benchmarks
Navigate to the "WebArena" tab in the UI or use the API to run standard benchmark tasks to evaluate the agent's performance.

### API Endpoints
- `POST /api/chat`: Send a task to the agent.
- `GET /api/stream`: Subscribe to the event stream for logs.
- `POST /api/check-conversation-history`: Analyze chat context for actionable tasks.
- `POST /webarena/run`: Run a specific WebArena task.

## 📂 Project Structure

```
/
├── browser_use/       # Core agent logic, DOM manipulation, tools
├── flask_app/         # Flask web server, API routes, UI templates
│   ├── core/          # Config and environment setup
│   ├── services/      # Business logic (Agent Controller, History)
│   ├── routes/        # API endpoints
│   └── templates/     # HTML frontend
├── docker-compose.yml # Container orchestration
└── secrets.env        # API keys and configuration
```

## 🧪 Development

### Running Tests
```bash
./bin/test.sh
```

### Linting
```bash
./bin/lint.sh
```

## 📄 License

See [LICENSE.md](LICENSE.md) for details.
