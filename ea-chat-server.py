#!/usr/bin/env python3
"""EA Chat Server — read-only AI assistant for EA-as-Code repositories.

Connects to a local Ollama instance and uses a text-based tool protocol
(read_request marker) to lazily load catalog data, keeping context lean.

Usage:
    python3 ea-chat-server.py [--port 8765] [--model Qwen3.6:35b] [--repo-path .]
"""

import json
import os
import sys
import argparse
import urllib.request
import urllib.error
import urllib.parse
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import textwrap

# ─── Config ───────────────────────────────────────────────────
REPO_PATH = None
OLLAMA_HOST = "http://localhost:11434"
MODEL = "Qwen3.6:35b"


# ─── Read-Only File Access ────────────────────────────────────
def safe_path(base, *parts):
    path = os.path.normpath(os.path.join(base, *parts))
    if not path.startswith(os.path.normpath(base)):
        return None
    return path


def read_json(relative_path):
    path = safe_path(REPO_PATH, relative_path)
    if not path or not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)


def read_catalog(name):
    name = name.replace("/", "").replace("\\", "")
    return read_json(os.path.join("catalogs", name, f"{name}.json"))


def read_metamodel():
    return read_json("metamodel.json")


def search_entries(query):
    results = []
    catalogs_dir = safe_path(REPO_PATH, "catalogs")
    if not catalogs_dir or not os.path.isdir(catalogs_dir):
        return results
    for entry in sorted(os.listdir(catalogs_dir)):
        subdir = safe_path(catalogs_dir, entry)
        if not subdir or not os.path.isdir(subdir):
            continue
        cat_file = os.path.join(subdir, f"{entry}.json")
        if os.path.isfile(cat_file):
            with open(cat_file) as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue
            for item in data if isinstance(data, list) else []:
                name = (item.get("name") or "")
                desc = (item.get("description") or "")
                if query.lower() in name.lower() or query.lower() in desc.lower():
                    results.append({"catalog": entry, "entry": item})
    return results


def get_entry(entry_id):
    catalogs_dir = safe_path(REPO_PATH, "catalogs")
    if not catalogs_dir or not os.path.isdir(catalogs_dir):
        return None
    for entry in sorted(os.listdir(catalogs_dir)):
        subdir = safe_path(catalogs_dir, entry)
        if not subdir or not os.path.isdir(subdir):
            continue
        cat_file = os.path.join(subdir, f"{entry}.json")
        if os.path.isfile(cat_file):
            with open(cat_file) as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue
            for item in data if isinstance(data, list) else []:
                if item.get("id") == entry_id:
                    return {"catalog": entry, "entry": item}
    return None


def build_catalog_summary():
    """Build a compact summary of all catalogs (just names + IDs, no descriptions)."""
    catalogs_dir = safe_path(REPO_PATH, "catalogs")
    if not catalogs_dir or not os.path.isdir(catalogs_dir):
        return ""
    parts = []
    for entry in sorted(os.listdir(catalogs_dir)):
        subdir = safe_path(catalogs_dir, entry)
        if not subdir or not os.path.isdir(subdir):
            continue
        cat_file = os.path.join(subdir, f"{entry}.json")
        if os.path.isfile(cat_file):
            with open(cat_file) as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue
            if isinstance(data, list):
                entries_part = "  " + "\n  ".join(
                    f"{e.get('id','?')}: {e.get('name','?')}"
                    for e in data
                )
                parts.append(f"[{entry}] ({len(data)} entries)\n{entries_part}")
    return "\n".join(parts)


# ─── System Prompt ────────────────────────────────────────────
def build_system_prompt():
    mm = read_metamodel()
    summary = build_catalog_summary()

    if not mm:
        return "You are an EA repository assistant."

    entities = mm.get("entityTypes", [])
    relationships = mm.get("relationships", [])

    entity_lines = "\n".join(
        f"  - {e['name']} (catalog: {e['catalog']}, domain: {e.get('togafDomain', 'N/A')})"
        for e in entities
    )

    rel_lines = "\n".join(
        f"  - {r['source']} -> {r['target']} via `{r['viaField']}`: {r['description']}"
        for r in relationships
    )

    return textwrap.dedent(f"""\
        You are an Enterprise Architecture repository assistant. You help users understand the EA data in this repository (TOGAF-aligned EA-as-Code).

        Entity Types:
        {entity_lines}

        Relationships:
        {rel_lines}

        Catalog Summary (IDs and names only):
        {summary}

        LAZY DATA RETRIEVAL: If you need the full details (descriptions, fields) of entries in a catalog, output a marker on its own line like:
        [[READ: CatalogName]]

        If you need details on a specific entry by ID, output:
        [[GET: entry-id]]

        If you need to search, output:
        [[SEARCH: query text]]

        I will detect these markers, retrieve the data, and show it to you. Then you can continue your analysis.

        DIAGRAM CONTROL — TWO-STEP COMMAND FLOW:
        You can propose adding or removing entries from the diagram. This requires TWO steps:

        STEP 1 — PROPOSE: When you want to modify the diagram, output a CMD_REQUEST marker:
        [[CMD_REQUEST: <action>|<catalog>|<id1,id2,...>]]

        Where:
        - action = "add" or "remove"
        - catalog = a human-readable name for the catalog (e.g. "InformationFlows")
        - id1,id2,... = comma-separated entry IDs to add or remove

        Example: [[CMD_REQUEST: add|InformationFlows|flow-001,flow-002,flow-012]]
        Example: [[CMD_REQUEST: remove|InformationFlows|flow-003,flow-007]]

        The browser will show the proposed changes with Yes/No buttons for user confirmation.

        IMPORTANT: You must FIRST read the relevant catalogs to find the correct entry IDs before using CMD_REQUEST. Do NOT guess IDs.

        STEP 2 — EXECUTE: After the user approves, I will send you an approval message. Then produce a brief confirmation (e.g. "Adding 5 Information Flows to the diagram...").

        CRITICAL RULES:
        1. Only answer based on data you have read. Do NOT guess.
        2. You are read-only. Do NOT suggest modifications except via CMD_REQUEST.
        3. Cross-reference between catalogs using IDs.
        4. Cite specific entries by name and ID when relevant.
        5. To find common data entities between two applications: first read the ApplicationComponents and InformationFlows catalogs to see which flows connect them and what data entities they carry. Also read the DataEntities catalog to understand what each entity is.
        6. Always request the data you need using [[READ:]], then analyze it.
        7. Always explain what you found (names, IDs) before using CMD_REQUEST so the user knows what they are approving.
        8. For removals, first list the currently-visible entries you propose to remove.
    """)


# ─── Tool Execution (Text-Based Protocol) ─────────────────────
def handle_text_tool(marker):
    """Detect and execute text-based tool markers. Returns (found, response_text)."""
    if marker.startswith("[[READ:"):
        name = marker[7:].strip().rstrip("]").strip()
        data = read_catalog(name)
        if data is not None:
            return (True, json.dumps(data, indent=2))
        return (True, f"Catalog '{name}' not found.")
    if marker.startswith("[[GET:"):
        eid = marker[6:].strip().rstrip("]").strip()
        result = get_entry(eid)
        if result:
            return (True, json.dumps(result, indent=2))
        return (True, f"Entry '{eid}' not found.")
    if marker.startswith("[[SEARCH:"):
        query = marker[9:].strip().rstrip("]").strip()
        results = search_entries(query)
        return (True, json.dumps(results, indent=2))
    return (False, "")


def handle_cmd_request_marker(marker):
    """Detect [[CMD_REQUEST: action|catalog|id1,id2,...]] markers. Returns (found, action, catalog, targets_list)."""
    if not marker.startswith("[[CMD_REQUEST:"):
        return (False, None, None, None)
    inner = marker[len("[[CMD_REQUEST:"):].rstrip("]").strip()
    parts = inner.split("|")
    if len(parts) != 3:
        return (True, None, None, None)  # malformed
    action = parts[0].strip()
    catalog = parts[1].strip()
    targets_str = parts[2].strip()
    if not targets_str:
        return (True, None, None, None)  # no targets
    targets = [t.strip() for t in targets_str.split(",") if t.strip()]
    if not targets:
        return (True, None, None, None)
    return (True, action, catalog, targets)


def handle_approve_marker(marker):
    """Detect [[APPROVE:CMD_REQUEST: ...]] markers. Returns (found, full_marker_string)."""
    if marker.startswith("[[APPROVE:CMD_REQUEST:") and marker.endswith("]]"):
        return (True, marker)
    return (False, "")


def handle_reject_marker(marker):
    """Detect [[REJECT:CMD_REQUEST]] marker. Returns (found, True)."""
    if marker.strip() == "[[REJECT:CMD_REQUEST]]":
        return (True, True)
    return (False, False)


def process_text_tools(text, pending_cmd=None):
    """Process any [[...]] markers in a text. Returns (cleaned_text, should_loop, cmd_request_data, is_approve, is_reject).

    cmd_request_data: None or {"action": str, "catalog": str, "targets": [str]}
    is_approve: True if this is an APPROVE:CMD_REQUEST marker
    is_reject: True if this is a REJECT:CMD_REQUEST marker
    """
    lines = text.split("\n")
    new_lines = []
    should_loop = False
    cmd_request_data = None
    is_approve = False
    is_reject = False

    for line in lines:
        stripped = line.strip()

        # Check for command request
        found, action, catalog, targets = handle_cmd_request_marker(stripped)
        if found:
            if action is None:
                new_lines.append("[Error: malformed CMD_REQUEST — provide action|catalog|id1,id2,...]")
                should_loop = True
            else:
                cmd_request_data = {"action": action, "catalog": catalog, "targets": targets}
                new_lines.append("[Processing command request...]")
                should_loop = True
            continue

        # Check for approval
        found, _ = handle_approve_marker(stripped)
        if found:
            is_approve = True
            new_lines.append("[Command approved — applying...]")
            should_loop = True
            continue

        # Check for rejection
        found, _ = handle_reject_marker(stripped)
        if found:
            is_reject = True
            new_lines.append("[Command cancelled]")
            should_loop = True
            continue

        # Existing text tools
        found, response = handle_text_tool(stripped)
        if found:
            should_loop = True
            new_lines.append(f"[Loaded data for: {stripped}]")
            new_lines.append(response)
        else:
            new_lines.append(line)

    return (
        "\n".join(new_lines),
        should_loop,
        cmd_request_data,
        is_approve,
        is_reject,
    )


# ─── Ollama API ───────────────────────────────────────────────
def call_ollama(messages, stream=True):
    url = f"{OLLAMA_HOST}/api/chat"
    body = json.dumps({
        "model": MODEL,
        "messages": messages,
        "stream": stream,
        "options": {"num_ctx": 131072},
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    return urllib.request.urlopen(req, timeout=300)


def stream_ollama_lines(resp):
    """Yield parsed JSON lines from an Ollama streaming response."""
    while True:
        line = resp.readline()
        if not line:
            break
        line = line.decode("utf-8").strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def parse_approve_marker(marker):
    """Parse [[APPROVE:CMD_REQUEST: action|catalog|targets]] and return (action, catalog, targets_list)."""
    if not marker.startswith("[[APPROVE:CMD_REQUEST:") or not marker.endswith("]]"):
        return (None, None, None)
    inner = marker[len("[[APPROVE:CMD_REQUEST:"):].rstrip("]").strip()
    parts = inner.split("|")
    if len(parts) != 3:
        return (None, None, None)
    action = parts[0].strip()
    catalog = parts[1].strip()
    targets_str = parts[2].strip()
    if not targets_str:
        return (None, None, None)
    targets = [t.strip() for t in targets_str.split(",") if t.strip()]
    if not targets:
        return (None, None, None)
    return (action, catalog, targets)


def chat_loop(messages):
    """
    Run the chat with text-based tool protocol.
    Yields (event_type, data) tuples:
      - ("token", str) — text token
      - ("cmd_request", dict) — command confirmation request to browser
      - ("command", dict) — single command to execute
      - ("done", None) — finished
      - ("error", str) — error message
    """
    max_rounds = 10

    for _ in range(max_rounds):
        try:
            resp = call_ollama(messages, stream=True)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("error", str(e))
            except json.JSONDecodeError:
                msg = err_body or str(e)
            yield ("error", f"Ollama error ({e.code}): {msg}")
            return
        except urllib.error.URLError:
            yield ("error", f"Cannot connect to Ollama at {OLLAMA_HOST}. Is it running?")
            return

        full_content = ""
        try:
            for data in stream_ollama_lines(resp):
                content = data.get("message", {}).get("content", "")
                if content:
                    full_content += content
                    yield ("token", content)
                if data.get("done"):
                    break
        except Exception as e:
            yield ("error", f"Stream error: {str(e)}")
            return

        # Check for markers — detect approval BEFORE process_text_tools rewrites it
        approval_raw = None
        is_approve_early = False
        for line in full_content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("[[APPROVE:CMD_REQUEST:") and stripped.endswith("]]"):
                approval_raw = stripped
                is_approve_early = True
                break

        # Check for rejection BEFORE process_text_tools
        is_reject_early = False
        for line in full_content.split("\n"):
            if line.strip() == "[[REJECT:CMD_REQUEST]]":
                is_reject_early = True
                break

        # Check for cmd_request BEFORE process_text_tools
        cmd_request_raw = None
        for line in full_content.split("\n"):
            if line.strip().startswith("[[CMD_REQUEST:"):
                cmd_request_raw = line.strip()
                break

        # Check for other text tools
        has_other_tool = any(
            line.strip().startswith("[[READ:") or
            line.strip().startswith("[[GET:") or
            line.strip().startswith("[[SEARCH:")
            for line in full_content.split("\n")
        )

        processed, should_loop, cmd_request_data, _, _ = process_text_tools(full_content)

        if is_reject_early:
            messages.append({"role": "assistant", "content": processed})
            messages.append({
                "role": "user",
                "content": "Acknowledge the cancellation."
            })
            continue

        if cmd_request_raw is not None and cmd_request_data is not None:
            # Command request — emit to browser, don't add to messages yet
            messages.append({"role": "assistant", "content": processed})
            yield ("cmd_request", cmd_request_data)
            messages.append({
                "role": "user",
                "content": "Continue. Based on the data above, confirm what you found and ask the user to approve or reject."
            })
            continue

        if is_approve_early and approval_raw:
            action, catalog, targets = parse_approve_marker(approval_raw)
            if targets:
                messages.append({"role": "assistant", "content": processed})
                for target in targets:
                    yield ("command", {"action": action, "target": target})
                messages.append({
                    "role": "user",
                    "content": "Acknowledge the command has been applied."
                })
                continue
            # Fallback: malformed approval
            messages.append({"role": "assistant", "content": processed})
            yield ("token", "[Error: Could not parse approval — please try again]")
            messages.append({"role": "user", "content": "Continue."})
            continue

        if is_reject_early:
            messages.append({"role": "assistant", "content": processed})
            messages.append({
                "role": "user",
                "content": "Acknowledge the cancellation."
            })
            continue

        if should_loop:
            messages.append({"role": "assistant", "content": processed})
            messages.append({
                "role": "user",
                "content": "Continue your analysis with the data above. Provide your answer now."
            })
            continue

        messages.append({"role": "assistant", "content": full_content})
        yield ("done", None)
        return

    yield ("error", "Max rounds reached")


# ─── HTTP Server ──────────────────────────────────────────────
class ChatHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._set_cors()
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self._handle_health()
        elif self.path == "/" or self.path == "":
            self._handle_root()
        elif self.path.startswith("/"):
            self._serve_static(self.path.lstrip("/"))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/chat":
            self._handle_chat()
        else:
            self.send_error(404)

    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _serve_static(self, rel_path):
        rel_path = urllib.parse.unquote(rel_path)
        path = safe_path(REPO_PATH, rel_path)
        if not path or not os.path.isfile(path):
            self.send_error(404)
            return
        ctype, _ = mimetypes.guess_type(path)
        self.send_response(200)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Cache-Control", "no-cache")
        self._set_cors()
        self.end_headers()
        with open(path, "rb") as f:
            self.wfile.write(f.read())

    def _handle_root(self):
        self._serve_static("visualiser.html")

    def _handle_health(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._set_cors()
        self.end_headers()
        status = {"ok": True, "model": MODEL, "repo": REPO_PATH}
        try:
            req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
            resp = urllib.request.urlopen(req, timeout=5)
            tags = json.loads(resp.read())
            status["ollama"] = "connected"
            status["models"] = [t["name"] for t in tags.get("models", [])]
        except Exception:
            status["ollama"] = "disconnected"
        self.wfile.write(json.dumps(status).encode())

    def _handle_chat(self):
        global MODEL
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        messages = data.get("messages", [])
        model = data.get("model", MODEL)

        if model != MODEL:
            MODEL = model

        if not any(m.get("role") == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": build_system_prompt()})

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._set_cors()
        self.end_headers()

        for event_type, data in chat_loop(messages):
            if event_type == "token":
                self._sse_send({"type": "token", "content": data})
            elif event_type == "cmd_request":
                self._sse_send({"type": "cmd_request", "action": data["action"], "catalog": data["catalog"], "targets": data["targets"]})
            elif event_type == "command":
                self._sse_send({"type": "command", "action": data["action"], "target": data["target"]})
            elif event_type == "done":
                self._sse_send({"type": "done"})
                break
            elif event_type == "error":
                self._sse_send({"type": "error", "message": data})
                break

    def _sse_send(self, data):
        try:
            self.wfile.write(f"data: {json.dumps(data)}\n\n".encode())
            self.wfile.flush()
        except BrokenPipeError:
            pass

    def log_message(self, format, *args):
        msg = format % args if args else format
        sys.stderr.write(f"[EA Chat] {msg}\n")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


# ─── Main ─────────────────────────────────────────────────────
def main():
    global REPO_PATH, OLLAMA_HOST, MODEL

    parser = argparse.ArgumentParser(description="EA Chat Server")
    parser.add_argument("--port", type=int, default=8765, help="Server port (default: 8765)")
    parser.add_argument("--model", default="Qwen3.6:35b", help="Ollama model name (default: Qwen3.6:35b)")
    parser.add_argument("--ollama-host", default="http://localhost:11434", help="Ollama API base URL")
    parser.add_argument("--repo-path", default=None, help="Path to repository root (default: auto-detect from CWD)")
    args = parser.parse_args()

    if args.repo_path:
        REPO_PATH = os.path.abspath(args.repo_path)
    else:
        cwd = os.getcwd()
        if os.path.isfile(os.path.join(cwd, "metamodel.json")):
            REPO_PATH = cwd
        else:
            print("Error: metamodel.json not found in current directory.", file=sys.stderr)
            print("Specify repo path with --repo-path", file=sys.stderr)
            sys.exit(1)

    MODEL = args.model
    OLLAMA_HOST = args.ollama_host.rstrip("/")

    print(f"EA Chat Server")
    print(f"  Model: {MODEL}")
    print(f"  Ollama: {OLLAMA_HOST}")
    print(f"  Repo: {REPO_PATH}")
    print(f"  Listening: http://localhost:{args.port}")
    print()

    server = ThreadedHTTPServer(("", args.port), ChatHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
