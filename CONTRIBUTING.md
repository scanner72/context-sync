# Contributing to Context Sync

Thank you for your interest in contributing to **Context Sync**! We welcome contributions of all kinds — from bug fixes and documentation improvements to new agent adapters and embedding providers.

---

## 🚀 Quick Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/context-sync.git
   cd context-sync
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate    # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your desired settings
   ```

4. **Run with Docker Compose (Recommended)**:
   ```bash
   docker compose up -d --build
   ```

5. **Run test suite**:
   ```bash
   python -m pytest tests/ -v
   ```

---

## 📐 Architecture Guidelines

Context Sync is organized around four core pillars:
- **`src/context_store.py`**: PostgreSQL 16 + pgvector storage abstraction with FastEmbed ONNX runtime.
- **`src/mcp_server.py`**: Model Context Protocol (MCP) server implementing SSE (`GET /sse`, `POST /messages`, `POST /mcp`) and JSON-RPC 2.0 tools.
- **`src/scanner.py`**: Intelligent auto-discovery and configuration injector for local AI IDEs and coding agents.
- **`src/syncer/`**: Continuous background collectors (`CodexCollector`, `CursorCollector`, `ClaudeCollector`, `AntigravityCollector`) and non-destructive project digest injectors.

When adding new agents:
1. Add target paths and detection heuristic in `src/scanner.py` -> `get_candidate_targets()`.
2. Implement chat/history collector in `src/syncer/collectors.py` inheriting from base extractor patterns.
3. Add unit test coverage in `tests/`.

---

## 🧪 Testing Policy

- All PRs must pass the test suite:
  ```bash
  python -m pytest tests/ -v
  ```
- Any new features or bug fixes must include corresponding tests in `tests/`.
- Ensure async tests utilize `pytest-asyncio` markers (`@pytest.mark.asyncio`).

---

## 📦 Pull Request Process

1. Fork the repo and create your feature branch:
   ```bash
   git checkout -b feature/amazing-new-agent
   ```
2. Commit your changes following Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
3. Ensure code formatting is clean and all tests pass.
4. Push to your branch and open a Pull Request against `main`.
5. Clearly describe the problem solved or feature added in the PR description.

Thank you for helping make multi-agent AI development seamless and unified!
