# Security Policy

The Context Sync team takes the security and privacy of developer workflows very seriously. Because Context Sync manages AI coding agent context, code excerpts, and architecture decisions across multiple tools, maintaining strict isolation and authentication is paramount.

---

## 🔒 Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## 🛡️ Security Best Practices for Deployments

1. **Authentication Tokens**:
   - Always change the default `AUTH_TOKEN` in `.env` before exposing Context Sync beyond `localhost`.
   - Generate a cryptographically secure token:
     ```bash
     openssl rand -hex 32
     ```
2. **Network Isolation**:
   - By default, bind `HOST=127.0.0.1` unless running on a trusted private LAN or behind a reverse proxy (Nginx / Caddy / Cloudflare Tunnel) with TLS termination.
3. **Database Credentials**:
   - Use strong passwords for `POSTGRES_PASSWORD`. The internal Docker network isolates database communication, but external port mapping (`5445`) should be firewalled if exposed on public IPs.

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability within Context Sync, please **do not open a public GitHub issue**.

Instead, please report security issues privately via:
- GitHub Private Vulnerability Reporting on this repository
- Or email the maintainers directly at `security@context-sync.dev`

Please provide:
- A detailed description of the vulnerability.
- Steps or proof-of-concept to reproduce the behavior.
- Affected components (e.g. MCP SSE handler, scanner injection, REST API).

You will receive an acknowledgment within 24 hours, followed by regular updates until a fix is published.
