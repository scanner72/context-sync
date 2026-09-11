"""Intelligent auto-scanner and configuration injector for AI Coding Agents and IDEs."""

import os
import sys
import json
import glob
import shutil
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclass
class AgentTarget:
    name: str
    app_id: str
    config_path: Path
    detection_paths: List[Path] = field(default_factory=list)
    detected: bool = False
    configured: bool = False
    raw_config: Optional[Dict[str, Any]] = None
    note: str = ""


def get_candidate_targets() -> List[AgentTarget]:
    """Find all supported AI coding agents and IDEs on current OS, detecting their installation."""
    home = Path.home()
    is_win = sys.platform.startswith("win")
    is_mac = sys.platform == "darwin"

    app_data = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) if is_win else home
    local_app_data = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local")) if is_win else home

    candidates: List[AgentTarget] = []

    # 1. Claude Desktop (Standard installer or Windows Store / MSIX package)
    claude_config_path = None
    claude_detection_paths = []

    if is_win:
        # Check Windows Store MSIX package first (very common on modern Windows)
        package_pattern = str(local_app_data / "Packages" / "Claude_*" / "LocalCache" / "Roaming" / "Claude")
        matches = glob.glob(package_pattern)
        if matches:
            store_dir = Path(matches[0])
            claude_config_path = store_dir / "claude_desktop_config.json"
            claude_detection_paths.append(store_dir)

        # Standard non-store path
        std_claude_dir = app_data / "Claude"
        claude_detection_paths.append(std_claude_dir)
        if not claude_config_path:
            claude_config_path = std_claude_dir / "claude_desktop_config.json"

    elif is_mac:
        mac_dir = home / "Library" / "Application Support" / "Claude"
        claude_detection_paths.append(mac_dir)
        claude_config_path = mac_dir / "claude_desktop_config.json"
    else:
        linux_dir = home / ".config" / "Claude"
        claude_detection_paths.append(linux_dir)
        claude_config_path = linux_dir / "claude_desktop_config.json"

    candidates.append(
        AgentTarget(
            name="Claude Desktop",
            app_id="claude-desktop",
            config_path=claude_config_path,
            detection_paths=claude_detection_paths,
            note="Официальное десктопное приложение Anthropic",
        )
    )

    # 2. Claude Code CLI (Anthropic's terminal agent)
    claude_code_config = home / ".claude.json"
    claude_code_dir = home / ".claude"
    candidates.append(
        AgentTarget(
            name="Claude Code CLI",
            app_id="claude-code",
            config_path=claude_code_config,
            detection_paths=[claude_code_config, claude_code_dir, app_data / "Claude Code"],
            note="Терминальный агент Claude Code (claude CLI)",
        )
    )

    # 3. Cursor IDE
    cursor_home_dir = home / ".cursor"
    cursor_app_data = app_data / "Cursor"
    cursor_mcp_config = cursor_home_dir / "mcp.json"
    candidates.append(
        AgentTarget(
            name="Cursor IDE",
            app_id="cursor",
            config_path=cursor_mcp_config,
            detection_paths=[cursor_home_dir, cursor_app_data],
            note="ИИ-редактор Cursor (глобальный ~/.cursor/mcp.json)",
        )
    )

    # 4. Antigravity / Gemini CLI
    antigravity_dir = home / ".gemini" / "antigravity"
    antigravity_config = antigravity_dir / "mcp_config.json"
    candidates.append(
        AgentTarget(
            name="Antigravity",
            app_id="antigravity",
            config_path=antigravity_config,
            detection_paths=[antigravity_dir],
            note="Google Antigravity ассистент",
        )
    )

    # 5. Windsurf IDE
    windsurf_home = home / ".codeium"
    windsurf_appdata = app_data / "Windsurf"
    windsurf_config = home / ".codeium" / "windsurf" / "mcp_config.json"
    candidates.append(
        AgentTarget(
            name="Windsurf IDE",
            app_id="windsurf",
            config_path=windsurf_config,
            detection_paths=[windsurf_home, windsurf_appdata],
            note="Codeium Windsurf IDE",
        )
    )

    # 6. Cline (VS Code Extension)
    if is_win:
        cline_settings_dir = app_data / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings"
    elif is_mac:
        cline_settings_dir = home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings"
    else:
        cline_settings_dir = home / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings"

    candidates.append(
        AgentTarget(
            name="Cline (VS Code)",
            app_id="cline",
            config_path=cline_settings_dir / "cline_mcp_settings.json",
            detection_paths=[cline_settings_dir, app_data / "Code"],
            note="Автономный агент Cline в VS Code",
        )
    )

    # 7. Roo Code (VS Code Extension)
    if is_win:
        roo_settings_dir = app_data / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings"
    elif is_mac:
        roo_settings_dir = home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings"
    else:
        roo_settings_dir = home / ".config" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings"

    candidates.append(
        AgentTarget(
            name="Roo Code (VS Code)",
            app_id="roo-code",
            config_path=roo_settings_dir / "cline_mcp_settings.json",
            detection_paths=[roo_settings_dir, app_data / "Code"],
            note="Форк Roo Code в VS Code",
        )
    )

    # 8. Codex (OpenAI Codex CLI & Desktop)
    codex_home_dir = home / ".codex"
    codex_config = codex_home_dir / "config.toml"
    codex_appdata = app_data / "OpenAI" / "Codex"
    candidates.append(
        AgentTarget(
            name="Codex (OpenAI)",
            app_id="codex",
            config_path=codex_config,
            detection_paths=[codex_home_dir, codex_appdata],
            note="OpenAI Codex CLI & Desktop (~/.codex/config.toml)",
        )
    )

    return candidates


def scan_agents() -> List[AgentTarget]:
    """Scan filesystem for installed agents based on app folders and MCP configuration status."""
    targets = get_candidate_targets()
    results = []

    for target in targets:
        # Check if ANY of the app detection paths exist on the machine
        target.detected = any(p.exists() for p in target.detection_paths) or target.config_path.exists()

        if target.config_path.exists():
            try:
                content = target.config_path.read_text(encoding="utf-8").strip()
                if content:
                    if target.config_path.suffix.lower() == ".toml":
                        try:
                            import tomllib
                            data = tomllib.loads(content)
                        except Exception:
                            data = {}
                        mcp_section = data.get("mcp_servers", {}) or data.get("mcpServers", {})
                        target.configured = "remote-context" in mcp_section
                        target.raw_config = data
                    else:
                        data = json.loads(content)
                        target.raw_config = data
                        servers = data.get("mcpServers", {})
                        target.configured = "remote-context" in servers
            except Exception as e:
                logger.warning(f"Error reading config at {target.config_path}: {e}")

        results.append(target)

    return results


def inject_mcp_server(
    target: AgentTarget,
    sse_url: str,
    token: str,
    server_name: str = "remote-context",
    use_command_proxy: bool = False,
) -> bool:
    """Safely inject or update the Remote Context MCP server configuration into an agent config."""
    try:
        # Ensure parent directory exists
        target.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Special handling for TOML configurations (Codex)
        if target.config_path.suffix.lower() == ".toml":
            backup_path = target.config_path.with_suffix(".toml.bak")
            existing_text = ""
            if target.config_path.exists():
                existing_text = target.config_path.read_text(encoding="utf-8")
                shutil.copyfile(target.config_path, backup_path)

            if use_command_proxy:
                toml_block = f"""
[mcp_servers.{server_name}]
command = "npx"
args = ["-y", "mcp-remote", "{sse_url}?token={token}"]
"""
            else:
                toml_block = f"""
[mcp_servers.{server_name}]
url = "{sse_url}"

[mcp_servers.{server_name}.http_headers]
Authorization = "Bearer {token}"
"""
            # If section already exists in toml, don't corrupt it
            if f"[mcp_servers.{server_name}]" not in existing_text:
                with open(target.config_path, "a", encoding="utf-8") as f:
                    f.write("\n" + toml_block.strip() + "\n")

            target.configured = True
            return True

        # Standard JSON configurations
        data: Dict[str, Any] = {}
        if target.config_path.exists():
            content = target.config_path.read_text(encoding="utf-8").strip()
            if content:
                try:
                    data = json.loads(content)
                    # Create a backup
                    backup_path = target.config_path.with_suffix(".json.bak")
                    shutil.copyfile(target.config_path, backup_path)
                except Exception:
                    data = {}

        if "mcpServers" not in data:
            data["mcpServers"] = {}

        # Claude Code CLI prefers specific format (type: "sse" or "stdio")
        if target.app_id == "claude-code":
            data["mcpServers"][server_name] = {
                "type": "sse",
                "url": sse_url,
                "headers": {
                    "Authorization": f"Bearer {token}",
                },
            }
        elif target.app_id == "claude-desktop" or use_command_proxy:
            # Claude Desktop strictly requires stdio command transport
            if sys.platform.startswith("win"):
                data["mcpServers"][server_name] = {
                    "command": "cmd.exe",
                    "args": [
                        "/c",
                        "npx",
                        "-y",
                        "mcp-remote",
                        f"{sse_url}?token={token}",
                    ],
                }
            else:
                data["mcpServers"][server_name] = {
                    "command": "npx",
                    "args": [
                        "-y",
                        "mcp-remote",
                        f"{sse_url}?token={token}",
                    ],
                }
        else:
            # Direct SSE with headers (standard)
            data["mcpServers"][server_name] = {
                "url": sse_url,
                "headers": {
                    "Authorization": f"Bearer {token}",
                },
            }

        with open(target.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        target.configured = True
        return True

    except Exception as e:
        logger.error(f"Failed to inject config into {target.name} ({target.config_path}): {e}")
        return False


def main():
    """CLI runner for discovering agents and injecting configuration."""
    import argparse

    parser = argparse.ArgumentParser(description="Intelligent Auto-scanner and MCP injector for AI Coding Agents")
    parser.add_argument("--url", default="http://localhost:8000/sse", help="Remote Context MCP SSE endpoint URL")
    parser.add_argument("--token", default="", help="Bearer authentication token")
    parser.add_argument("--scan-only", action="store_true", help="Only scan and report detected agents without modifying")
    parser.add_argument("--stdio", action="store_true", help="Use npx mcp-remote instead of direct SSE headers")
    parser.add_argument("--agent", help="Inject into specific agent app_id (or all detected by default)")

    args = parser.parse_args()

    print("\n🔍 Сканирование установленных ИИ-агентов и IDE на компьютере...")
    targets = scan_agents()

    detected_targets = [t for t in targets if t.detected]
    configured_targets = [t for t in targets if t.configured]

    print(f"Всего проверено: {len(targets)} | Установлено агентов: {len(detected_targets)} | Уже подключено: {len(configured_targets)}\n")

    for t in targets:
        if t.detected:
            status_icon = "✓ [УСТАНОВЛЕН]"
            conf_status = " -> ПОДКЛЮЧЕН К CONTEXT SYNC 🟢" if t.configured else " -> ГОТОВ К ПОДКЛЮЧЕНИЮ ⚪"
            print(f"  {status_icon} {t.name:<20} {conf_status}")
            print(f"    Конфиг: {t.config_path}")
        else:
            print(f"  ✗ [НЕ НАЙДЕН]   {t.name:<20} (Путь: {t.config_path})")

    if args.scan_only:
        return

    if not args.token:
        print("\n⚠️  Для автоматической инъекции укажите токен: --token <AUTH_TOKEN>")
        return

    print(f"\n🚀 Внедрение remote-context MCP ({args.url})...")
    modified = 0

    for t in targets:
        if args.agent and t.app_id != args.agent:
            continue

        if t.detected or args.agent:
            success = inject_mcp_server(
                target=t,
                sse_url=args.url,
                token=args.token,
                use_command_proxy=args.stdio,
            )
            if success:
                print(f"  ✅ {t.name}: конфиг успешно обновлён (бэкап сохранён в .bak)")
                modified += 1
            else:
                print(f"  ❌ {t.name}: ошибка записи")

    print(f"\nГотово! Успешно сконфигурировано агентов: {modified}. Перезапустите соответствующие IDE/агенты.")


if __name__ == "__main__":
    main()
