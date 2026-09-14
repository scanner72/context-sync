"""MCP Protocol Server handler for Remote Context Store."""

import json
import logging
from typing import Any, Dict, List, Optional
from src.context_store import context_store
from src.facts import fact_store
from src.skills import skills_store
from src.mcp_registry import mcp_registry

logger = logging.getLogger(__name__)

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "remote-context-store"
SERVER_VERSION = "0.1.0"

# Tool definitions adhering to MCP specification
TOOLS = [
    {
        "name": "context_save",
        "description": (
            "Save or update an architectural decision, design pattern, gotcha, or context summary "
            "to the shared remote context store across all devices."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Descriptive title of the context or architectural decision.",
                },
                "content": {
                    "type": "string",
                    "description": "Full Markdown content, code snippets, gotchas, or reasoning.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags for filtering (e.g. ['auth', 'fastapi', 'docker']).",
                },
                "project": {
                    "type": "string",
                    "description": "Project identifier (e.g. 'my-app' or 'global' for cross-project). Defaults to 'global'.",
                    "default": "global",
                },
                "metadata": {
                    "type": "object",
                    "description": "Arbitrary metadata key-values (source files, commit hashes, etc.).",
                },
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "context_search",
        "description": (
            "Perform semantic vector search on the shared context base to find relevant architectural "
            "decisions, conventions, or solutions from previous sessions or other devices."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query describing what context or solution you need.",
                },
                "project": {
                    "type": "string",
                    "description": "Filter by project name. Omit to search across all projects.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 5).",
                    "default": 5,
                },
                "min_score": {
                    "type": "number",
                    "description": "Minimum similarity score between 0.0 and 1.0 (default 0.25).",
                    "default": 0.25,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "context_get",
        "description": (
            "Retrieve full details of a specific context document by its UUID or exact title."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "context_id": {
                    "type": "string",
                    "description": "UUID or exact title of the context item to fetch.",
                }
            },
            "required": ["context_id"],
        },
    },
    {
        "name": "context_list",
        "description": "List recent context notes and decisions across devices.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Filter by project name.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of items to return (default 10).",
                    "default": 10,
                },
            },
        },
    },
    {
        "name": "context_delete",
        "description": "Delete an outdated context document by ID or exact title.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "context_id": {
                    "type": "string",
                    "description": "UUID or exact title of the context document to delete.",
                }
            },
            "required": ["context_id"],
        },
    },
    {
        "name": "fact_set",
        "description": (
            "Store or update an atomic project fact (e.g. backend.port=8200, db.type=postgres) "
            "with versioning and conflict resolution across all AI agents."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "description": "Entity name (e.g. 'backend', 'database', 'auth', 'frontend').",
                },
                "attribute": {
                    "type": "string",
                    "description": "Attribute or property (e.g. 'port', 'type', 'jwt_algorithm').",
                },
                "value": {
                    "description": "The atomic value (number, string, boolean, or json object).",
                },
                "project": {
                    "type": "string",
                    "description": "Project identifier. Defaults to 'global'.",
                    "default": "global",
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence score between 0.0 and 1.0 (default 1.0).",
                    "default": 1.0,
                },
                "policy": {
                    "type": "string",
                    "description": "Conflict resolution policy: 'lww' (Last-Write-Wins) or 'authority'. Default is 'lww'.",
                    "enum": ["lww", "authority"],
                    "default": "lww",
                },
            },
            "required": ["entity", "attribute", "value"],
        },
    },
    {
        "name": "fact_get",
        "description": "Retrieve the current active fact for a given entity and attribute.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "description": "Entity name.",
                },
                "attribute": {
                    "type": "string",
                    "description": "Attribute name.",
                },
                "project": {
                    "type": "string",
                    "description": "Project identifier. Defaults to 'global'.",
                    "default": "global",
                },
            },
            "required": ["entity", "attribute"],
        },
    },
    {
        "name": "fact_list",
        "description": "List all active atomic facts and conventions for a project (Truth-Table).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project identifier. Defaults to 'global'.",
                    "default": "global",
                },
                "entity": {
                    "type": "string",
                    "description": "Optional entity name to filter by.",
                },
            },
        },
    },
    {
        "name": "fact_history",
        "description": "Retrieve the audit and version history of an atomic fact to track past changes and conflicts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "description": "Entity name.",
                },
                "attribute": {
                    "type": "string",
                    "description": "Attribute name.",
                },
                "project": {
                    "type": "string",
                    "description": "Project identifier. Defaults to 'global'.",
                    "default": "global",
                },
            },
            "required": ["entity", "attribute"],
        },
    },
    {
        "name": "skill_publish",
        "description": (
            "Publish or update an AI agent skill (SKILL.md instructions, triggers, and bundled scripts) "
            "into the centralized fleet repository for cross-agent reuse."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique identifier of the skill (e.g. 'docker-deploy', 'git-workflow').",
                },
                "content_md": {
                    "type": "string",
                    "description": "Full Markdown content of the SKILL.md file.",
                },
                "description": {
                    "type": "string",
                    "description": "Short summary of what this skill enables.",
                },
                "version": {
                    "type": "string",
                    "description": "Semantic version string (default '1.0.0').",
                    "default": "1.0.0",
                },
                "files_bundle": {
                    "type": "object",
                    "description": "Optional mapping of relative filepaths to file content (scripts, templates).",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags for filtering (e.g. ['docker', 'devops']).",
                },
            },
            "required": ["name", "content_md"],
        },
    },
    {
        "name": "skill_list",
        "description": "Browse and search available skills across the AI agent fleet.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Keyword to search in skill name or description.",
                },
                "tag": {
                    "type": "string",
                    "description": "Filter by specific tag.",
                },
            },
        },
    },
    {
        "name": "skill_get",
        "description": "Fetch the complete specification, instructions, and bundled files of a skill.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill to fetch.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "skill_install",
        "description": (
            "Install a skill directly into an agent's local filesystem "
            "(supports 'cursor', 'claude', 'antigravity', 'codex', 'windsurf', or 'all')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill to install.",
                },
                "target_agent": {
                    "type": "string",
                    "description": "Target agent ID ('cursor', 'claude', 'antigravity', 'codex', 'windsurf', or 'all').",
                    "default": "all",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "mcp_server_publish",
        "description": (
            "Register or share an external MCP server configuration (command, args, env, or sse url) "
            "into the fleet registry so all agents can use it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique name of the MCP server (e.g. 'github', 'postgres', 'filesystem').",
                },
                "transport": {
                    "type": "string",
                    "enum": ["stdio", "sse"],
                    "description": "Transport mechanism: 'stdio' (CLI process) or 'sse' (remote URL).",
                },
                "config": {
                    "type": "object",
                    "description": "Configuration object: {command, args, env} for stdio, or {url, headers} for sse.",
                },
            },
            "required": ["name", "transport", "config"],
        },
    },
    {
        "name": "mcp_server_list",
        "description": "List all validated external MCP servers available in the fleet registry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "only_active": {
                    "type": "boolean",
                    "description": "Whether to return only active servers (default true).",
                    "default": True,
                },

            },
        },
    },
    {
        "name": "mcp_server_install",
        "description": "Inject an MCP server from the registry into local agent config files (or all detected agents).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the MCP server to install.",
                },
                "target_agent": {
                    "type": "string",
                    "description": "Target agent app ID ('cursor', 'claude-desktop', 'claude-code', 'antigravity', etc., or 'all').",
                    "default": "all",
                },
            },
            "required": ["name"],
        },
    },
]



RESOURCES = [
    {
        "uri": "context://recent",
        "name": "Recent Architectural Contexts",
        "description": "A feed of the most recently updated architectural notes and decisions.",
        "mimeType": "application/json",
    }
]


class MCPServerHandler:
    """Processes MCP JSON-RPC 2.0 messages."""

    async def handle_request(self, message: Dict[str, Any], client_info: Optional[str] = None) -> Optional[Dict[str, Any]]:
        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})

        if not method:
            return self._error_response(msg_id, -32600, "Invalid Request: method is required")

        try:
            if method == "initialize":
                return self._success_response(msg_id, {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                })

            elif method == "notifications/initialized":
                # Client acknowledging initialization, no response needed for notifications
                return None

            elif method == "ping":
                return self._success_response(msg_id, {})

            elif method == "tools/list":
                return self._success_response(msg_id, {"tools": TOOLS})

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result_text = await self._dispatch_tool(tool_name, arguments, client_info)
                return self._success_response(msg_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text,
                        }
                    ]
                })

            elif method == "resources/list":
                return self._success_response(msg_id, {"resources": RESOURCES})

            elif method == "resources/read":
                uri = params.get("uri")
                if uri == "context://recent":
                    items = await context_store.list_all(limit=10)
                    return self._success_response(msg_id, {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": json.dumps(items, ensure_ascii=False, indent=2),
                            }
                        ]
                    })
                return self._error_response(msg_id, -32602, f"Resource not found: {uri}")

            else:
                return self._error_response(msg_id, -32601, f"Method not found: {method}")

        except Exception as exc:
            logger.exception(f"Error handling MCP method {method}")
            return self._error_response(msg_id, -32603, f"Internal server error: {str(exc)}")

    async def _dispatch_tool(self, name: str, args: Dict[str, Any], client_info: Optional[str]) -> str:
        if name == "context_save":
            title = args.get("title")
            content = args.get("content")
            tags = args.get("tags") or []
            project = args.get("project") or "global"
            metadata = args.get("metadata") or {}

            if not title or not content:
                raise ValueError("Both 'title' and 'content' are required for context_save")

            res = await context_store.save(
                title=title,
                content=content,
                tags=tags,
                project=project,
                author_device=client_info,
                metadata=metadata,
            )
            return json.dumps({
                "status": "success",
                "action": res.get("action"),
                "id": res.get("id"),
                "title": res.get("title"),
                "project": res.get("project"),
                "tags": res.get("tags"),
                "message": f"Successfully saved context '{title}' [id={res.get('id')}].",
            }, ensure_ascii=False, indent=2)

        elif name == "context_search":
            query = args.get("query")
            if not query:
                raise ValueError("'query' is required for context_search")
            
            project = args.get("project")
            tags = args.get("tags")
            limit = int(args.get("limit", 5))
            min_score = float(args.get("min_score", 0.25))

            results = await context_store.search(
                query=query,
                project=project,
                tags=tags,
                limit=limit,
                min_score=min_score,
            )
            return json.dumps({
                "query": query,
                "count": len(results),
                "results": results,
            }, ensure_ascii=False, indent=2)

        elif name == "context_get":
            context_id = args.get("context_id")
            if not context_id:
                raise ValueError("'context_id' is required for context_get")
            
            doc = await context_store.get(context_id)
            if not doc:
                return json.dumps({"status": "not_found", "message": f"Context '{context_id}' not found."}, indent=2)
            return json.dumps(doc, ensure_ascii=False, indent=2)

        elif name == "context_list":
            project = args.get("project")
            limit = int(args.get("limit", 10))
            docs = await context_store.list_all(project=project, limit=limit)
            return json.dumps({
                "count": len(docs),
                "contexts": [
                    {
                        "id": d["id"],
                        "title": d["title"],
                        "project": d["project"],
                        "tags": d["tags"],
                        "updated_at": d["updated_at"],
                    }
                    for d in docs
                ],
            }, ensure_ascii=False, indent=2)

        elif name == "context_delete":
            context_id = args.get("context_id")
            if not context_id:
                raise ValueError("'context_id' is required for context_delete")
            
            deleted = await context_store.delete(context_id)
            return json.dumps({
                "status": "success" if deleted else "not_found",
                "deleted": deleted,
                "message": f"Context '{context_id}' {'deleted' if deleted else 'not found'}.",
            }, indent=2)

        elif name == "fact_set":
            entity = args.get("entity")
            attribute = args.get("attribute")
            value = args.get("value")
            project = args.get("project") or "global"
            confidence = float(args.get("confidence", 1.0))
            policy = args.get("policy", "lww")
            source_agent = client_info or "unknown"

            if not entity or not attribute:
                raise ValueError("Both 'entity' and 'attribute' are required for fact_set")

            fact = await fact_store.set_fact(
                entity=entity,
                attribute=attribute,
                value=value,
                project=project,
                source_agent=source_agent,
                confidence=confidence,
                policy=policy,
            )
            return json.dumps({
                "status": "success",
                "action": fact.get("action"),
                "conflict_detected": fact.get("conflict_detected"),
                "fact": fact,
            }, ensure_ascii=False, indent=2)

        elif name == "fact_get":
            entity = args.get("entity")
            attribute = args.get("attribute")
            project = args.get("project") or "global"

            if not entity or not attribute:
                raise ValueError("Both 'entity' and 'attribute' are required for fact_get")

            fact = await fact_store.get_fact(entity=entity, attribute=attribute, project=project)
            if not fact:
                return json.dumps({
                    "status": "not_found",
                    "message": f"No active fact found for entity '{entity}' and attribute '{attribute}' in project '{project}'.",
                }, indent=2)
            return json.dumps({"status": "success", "fact": fact}, ensure_ascii=False, indent=2)

        elif name == "fact_list":
            project = args.get("project") or "global"
            entity = args.get("entity")

            facts = await fact_store.list_facts(project=project, entity=entity, only_active=True)
            return json.dumps({
                "status": "success",
                "count": len(facts),
                "project": project,
                "facts": facts,
            }, ensure_ascii=False, indent=2)

        elif name == "fact_history":
            entity = args.get("entity")
            attribute = args.get("attribute")
            project = args.get("project") or "global"

            if not entity or not attribute:
                raise ValueError("Both 'entity' and 'attribute' are required for fact_history")

            history = await fact_store.get_fact_history(entity=entity, attribute=attribute, project=project)
            return json.dumps({
                "status": "success",
                "count": len(history),
                "history": history,
            }, ensure_ascii=False, indent=2)

        elif name == "skill_publish":
            s_name = args.get("name")
            content_md = args.get("content_md")
            desc = args.get("description")
            version = args.get("version", "1.0.0")
            files_bundle = args.get("files_bundle") or {}
            tags = args.get("tags") or []
            source_agent = client_info or "unknown"

            if not s_name or not content_md:
                raise ValueError("Both 'name' and 'content_md' are required for skill_publish")

            res = await skills_store.publish_skill(
                name=s_name,
                content_md=content_md,
                description=desc,
                version=version,
                files_bundle=files_bundle,
                source_agent=source_agent,
                tags=tags,
            )
            return json.dumps({
                "status": "success",
                "action": res.get("action"),
                "skill": res,
                "message": f"Successfully published skill '{s_name}' (v{version}).",
            }, ensure_ascii=False, indent=2)

        elif name == "skill_list":
            search = args.get("search")
            tag = args.get("tag")
            skills = await skills_store.list_skills(tag=tag, search=search)
            return json.dumps({
                "status": "success",
                "count": len(skills),
                "skills": skills,
            }, ensure_ascii=False, indent=2)

        elif name == "skill_get":
            s_name = args.get("name")
            if not s_name:
                raise ValueError("'name' is required for skill_get")
            skill = await skills_store.get_skill(s_name)
            if not skill:
                return json.dumps({"status": "not_found", "message": f"Skill '{s_name}' not found."}, indent=2)
            return json.dumps({"status": "success", "skill": skill}, ensure_ascii=False, indent=2)

        elif name == "skill_install":
            s_name = args.get("name")
            target = args.get("target_agent", "all")
            if not s_name:
                raise ValueError("'name' is required for skill_install")

            if target == "all":
                res = await skills_store.install_to_all_agents(s_name)
            else:
                res = await skills_store.install_skill(s_name, target)

            return json.dumps({"status": "success", "result": res}, ensure_ascii=False, indent=2)

        elif name == "mcp_server_publish":
            srv_name = args.get("name")
            transport = args.get("transport")
            config = args.get("config")
            source_agent = client_info or "unknown"

            if not srv_name or not transport or not config:
                raise ValueError("'name', 'transport', and 'config' are required for mcp_server_publish")

            res = await mcp_registry.register_server(
                name=srv_name,
                transport=transport,
                config=config,
                source_agent=source_agent,
            )
            return json.dumps({
                "status": "success",
                "action": res.get("action"),
                "server": res,
                "message": f"Successfully registered MCP server '{srv_name}'.",
            }, ensure_ascii=False, indent=2)

        elif name == "mcp_server_list":
            only_active = bool(args.get("only_active", True))
            servers = await mcp_registry.list_servers(only_active=only_active)
            return json.dumps({
                "status": "success",
                "count": len(servers),
                "servers": servers,
            }, ensure_ascii=False, indent=2)

        elif name == "mcp_server_install":
            srv_name = args.get("name")
            target = args.get("target_agent", "all")
            if not srv_name:
                raise ValueError("'name' is required for mcp_server_install")

            if target == "all":
                res = await mcp_registry.install_to_all_detected(srv_name)
            else:
                res = await mcp_registry.install_server(srv_name, target)

            return json.dumps({"status": "success", "result": res}, ensure_ascii=False, indent=2)

        else:
            raise ValueError(f"Unknown tool: {name}")



    def _success_response(self, msg_id: Any, result: Any) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result,
        }

    def _error_response(self, msg_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": code,
                "message": message,
            },
        }


mcp_handler = MCPServerHandler()
