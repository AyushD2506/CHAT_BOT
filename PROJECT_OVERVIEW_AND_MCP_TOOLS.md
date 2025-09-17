# Project Overview and MCP Tools Guide

This guide explains how the project works end-to-end and how to configure and use MCP Tools, including sending payloads to POST APIs.

## Contents
- Project architecture at a glance
- Data flow: auth → sessions → documents → chat → tools
- MCP Tools: model, creation, update, deletion
- How API tools send data (GET vs POST/PUT/PATCH/DELETE)
- How to pass payloads to POST tools from chat
- Examples (UI and API)
- Troubleshooting tips

---

## Project architecture at a glance

- **Frontend (React + TypeScript)**
  - Location: `front_end/`
  - Key page for session admins: `src/pages/SessionAdminDashboard.tsx`
  - API client: `src/services/api.ts`
  - UI components: e.g., `src/components/RowActionBar.tsx`

- **Backend (FastAPI + SQLAlchemy Async)**
  - Location: `backend/`
  - Routers:
    - Admin routes: `backend/routers/admin.py`
    - Session-admin routes: `backend/routers/session_admin.py`
    - Chat routes: `backend/routers/chat.py`
  - RAG Service: `backend/rag_service.py` (retrieval, tool execution, internet search orchestration)
  - Schemas: `backend/schemas.py`
  - Models: `backend/models.py`

- **Storage**
  - Document uploads live under `storage/uploads/`
  - Vector store under `storage/vectorstores/`

- **Internet search**
  - `backend/search_service.py` uses DuckDuckGo for instant answers and HTML web search parsing.

---

## Data flow

1. **Auth**
   - Frontend stores `access_token` in `localStorage` and attaches it as `Authorization: Bearer <token>` to API requests (see `api.ts`).

2. **Sessions**
   - Global Admin creates and manages sessions (`/admin/sessions`).
   - Session Admin sees and manages only their sessions (`/session-admin/sessions`).

3. **Documents**
   - PDFs uploaded per-session (multipart/form-data).
   - Processed by RAG to chunk and index for retrieval.

4. **Chat**
   - Messages go to `/chat/message` or `/chat/stream`.
   - RAG pipeline can route to tools, internet search, and/or retrieval.

5. **MCP Tools**
   - Tools are attached per-session.
   - Types: `api` or `python_function`.
   - During chat, tools can be executed heuristically ("run <tool_name>") or via the auto-router.

---

## MCP Tools: model and endpoints

- Schema: `schemas.py`
  - Create/update payload fields:
    - **name**: string (unique-ish per session)
    - **tool_type**: `api` | `python_function`
    - **api_url**: string (required for `api` type)
    - **http_method**: string (default `GET`)
    - **function_code**: string (for `python_function` type)
    - **description**: string (human-facing)
    - **params_docstring**: string (document expected parameters)
    - **returns_docstring**: string (document expected return)

- Session Admin routes (require session admin or global admin):
  - POST `/session-admin/sessions/{session_id}/mcp/tools`
  - GET `/session-admin/sessions/{session_id}/mcp/tools`
  - PUT `/session-admin/sessions/{session_id}/mcp/tools/{tool_id}`
  - DELETE `/session-admin/sessions/{session_id}/mcp/tools/{tool_id}`

- Admin equivalents under `/admin/sessions/{session_id}/mcp/tools` (and `/admin/mcp/tools/{tool_id}` for updates/deletes).

---

## How API tools send data

Implementation reference: `backend/rag_service.py`.

- For `tool_type = 'api'`:
  - Method is read from `http_method` and normalized to uppercase.
  - Headers include `Accept: application/json, text/plain;q=0.9`.
  - If method is `GET` and a payload exists: payload is encoded into the URL query string.
  - If method is not `GET` (POST/PUT/PATCH/DELETE) and a payload exists:
    - `Content-Type: application/json`
    - Payload is serialized with `JSON.stringify` (Python-side `json.dumps`) and sent as the request body.

Summary:
- **GET** → payload becomes query string parameters.
- **POST/PUT/PATCH/DELETE** → payload becomes JSON body.

---

## How to pass payloads to POST tools from chat

There are two ways tools get arguments:

1. **Heuristic trigger in your message**
   - Format: `run <tool_name> with {json}`
   - Example:
     - "run weather_api with {\n  \"city\": \"London\",\n  \"units\": \"metric\"\n}"
   - The JSON after the word `with` is extracted and passed as the tool payload.

2. **Auto router (LLM decides)**
   - The system builds a tool catalog and asks the LLM to select a tool and provide `args`.
   - If the LLM decides to use your tool, it supplies a JSON `args` object which is sent using the rules above (GET→query, others→JSON body).

Important:
- Ensure your tool’s `description` and `params_docstring` clearly describe required fields so the auto-router can infer correct `args`.

---

## Examples

### A) Create a POST API tool (Session Admin)

- Use UI: Session Admin Dashboard → Actions → Tools → Create Tool
  - Example configuration:
    - **name**: httpbin_post
    - **tool_type**: api
    - **api_url**: https://httpbin.org/post
    - **http_method**: POST
    - **description**: Demo POST that echoes JSON
    - **params_docstring**: { "message": string, "count": number }
    - **returns_docstring**: JSON echo from httpbin

- Or via REST (cURL):

```bash
curl -X POST \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "httpbin_post",
    "tool_type": "api",
    "api_url": "https://httpbin.org/post",
    "http_method": "POST",
    "description": "Demo POST that echoes JSON",
    "params_docstring": "{ \"message\": string, \"count\": number }",
    "returns_docstring": "JSON echo from httpbin"
  }' \
  http://localhost:8000/session-admin/sessions/<SESSION_ID>/mcp/tools
```

### B) Run the tool with a JSON body from chat

Message example:

```
run httpbin_post with {"message": "hello", "count": 2}
```

Behavior:
- Since method is POST, the payload is sent as JSON body.
- Response preview (first ~2000 chars) is returned to chat.

### C) Create a GET API tool with query params

- Config:
  - name: httpbin_get
  - tool_type: api
  - api_url: https://httpbin.org/get
  - http_method: GET
  - params_docstring: { "q": string }

Run from chat:

```
run httpbin_get with {"q": "ping"}
```

Behavior:
- Payload becomes `?q=ping` on the URL.

### D) Programmatically create a tool from the frontend

```ts
// front_end/src/services/api.ts
await api.sessionAdmin.createTool(sessionId, {
  name: 'httpbin_post',
  tool_type: 'api',
  api_url: 'https://httpbin.org/post',
  http_method: 'POST',
  description: 'Demo POST',
  params_docstring: '{ "message": string }',
});
```

---

## Troubleshooting tips

- Tool not running from chat?
  - Ensure your message matches `run <tool_name>` or includes the exact tool name.
  - Try the explicit format with JSON: `run <tool_name> with { ... }`.

- POST payload not showing on the server?
  - Confirm `http_method` is not `GET`.
  - Confirm the JSON is valid and the UI/auto-router is passing a dictionary object.

- CORS/auth issues when calling external APIs
  - The backend makes the HTTP call server-side; external API CORS won’t affect the backend.
  - Some external APIs require auth headers; currently only `Accept` and `Content-Type` (for non-GET) are sent. If you need custom headers, extend `rag_service.py` to include them or encode tokens in the URL (only for testing).

- Large responses
  - Only the first ~2000 characters are returned as a preview in chat.

---

## Notes

- For best assistance, consider generating `.zencoder/rules/repo.md` so tooling has a repository summary available for future changes.

If you want, I can add support for custom headers on API tools (e.g., Authorization) and a simple key-value UI for default args. Let me know.