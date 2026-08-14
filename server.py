#!/usr/bin/env python3
"""Local static server for the WIGAnimation Shotlist UI + OpenRouter + vault search."""
from __future__ import annotations

import argparse
import base64
import functools
import hashlib
import hmac
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import http.client
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

# The shotlist used to dump full state into chunked cookies. Browsers then send
# one Cookie header larger than CPython's 64KiB line cap → HTTP 431 "Line too long".
http.client._MAXLINE = 1024 * 1024
http.client._MAXHEADERS = 400

ROOT = Path(__file__).resolve().parent
VAULT_ROOT = ROOT.parents[1]  # .../secondbrain
DEFAULT_PORT = 8765
DEFAULT_HOST = "127.0.0.1"

DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY_VAULT = os.environ.get("AZURE_KEY_VAULT", "dp-kv-deliverypilot")
KEY_SECRET = os.environ.get("OPENROUTER_SECRET_NAME", "OPENROUTER-API-KEY")
STORAGE_SECRET = os.environ.get("AZURE_STORAGE_SECRET_NAME", "AZURE-STORAGE-CONN-STR")
STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER", "projects")
STORAGE_PREFIX = os.environ.get("AZURE_STORAGE_PREFIX", "aug-video-animation-1/shotlist")
STORAGE_LATEST = f"{STORAGE_PREFIX}/latest.json"
BLOB_API_VERSION = "2021-08-06"

INDEX_EXTS = {".md", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".canvas", ".pdf"}
SKIP_DIR_NAMES = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", ".obsidian",
    "Notion", "_assets", "site-packages", ".trash",
}

_api_key_cache: str | None = None
_vault_index: list[str] = []
_vault_index_built_at = 0.0
_vault_index_lock = threading.Lock()
_INDEX_TTL = 300  # seconds


def get_openrouter_key() -> str:
    global _api_key_cache
    if _api_key_cache:
        return _api_key_cache
    env_key = (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_KEY") or "").strip()
    if env_key:
        _api_key_cache = env_key
        return env_key
    try:
        out = subprocess.check_output(
            [
                "az", "keyvault", "secret", "show",
                "--vault-name", KEY_VAULT, "--name", KEY_SECRET,
                "--query", "value", "-o", "tsv",
            ],
            stderr=subprocess.STDOUT, text=True, timeout=45,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            f"Could not load OpenRouter key from Key Vault secret {KEY_SECRET} in {KEY_VAULT}: {exc}"
        ) from exc
    if not out:
        raise RuntimeError(f"Key Vault secret {KEY_SECRET} is empty")
    _api_key_cache = out
    return out


def kv_secret(name: str) -> str:
    try:
        out = subprocess.check_output(
            [
                "az", "keyvault", "secret", "show",
                "--vault-name", KEY_VAULT, "--name", name,
                "--query", "value", "-o", "tsv",
            ],
            stderr=subprocess.STDOUT, text=True, timeout=45,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            f"Could not load Key Vault secret {name} in {KEY_VAULT}: {exc}"
        ) from exc
    if not out:
        raise RuntimeError(f"Key Vault secret {name} is empty")
    return out


_storage_conn_cache: str | None = None
_storage_account_cache: tuple[str, str, str] | None = None


def get_storage_conn() -> str:
    global _storage_conn_cache
    if _storage_conn_cache:
        return _storage_conn_cache
    env = (
        os.environ.get("AZURE_STORAGE_CONN_STR")
        or os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        or ""
    ).strip()
    if env:
        _storage_conn_cache = env
        return env
    _storage_conn_cache = kv_secret(STORAGE_SECRET)
    return _storage_conn_cache


def parse_storage_conn(conn: str) -> tuple[str, str, str]:
    parts = {}
    for item in conn.split(";"):
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        parts[k] = v
    account = parts.get("AccountName") or ""
    key = parts.get("AccountKey") or ""
    suffix = parts.get("EndpointSuffix") or "core.windows.net"
    if not account or not key:
        raise RuntimeError("Azure storage connection string is missing AccountName or AccountKey")
    return account, key, suffix


def storage_account() -> tuple[str, str, str]:
    global _storage_account_cache
    if _storage_account_cache:
        return _storage_account_cache
    _storage_account_cache = parse_storage_conn(get_storage_conn())
    return _storage_account_cache


def _utc_rfc1123() -> str:
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def _sign_blob(method: str, account: str, key: str, path_and_query: str, headers: dict[str, str], content_len: int) -> str:
    content_type = headers.get("Content-Type", "")
    length_field = "" if content_len == 0 else str(content_len)
    canon_headers = "".join(
        f"{k.lower()}:{headers[k].strip()}\n"
        for k in sorted(headers, key=str.lower)
        if k.lower().startswith("x-ms-")
    )
    resource_path, _, query = path_and_query.partition("?")
    canon_resource = f"/{account}{resource_path}"
    if query:
        params: dict[str, list[str]] = {}
        for pair in query.split("&"):
            if not pair:
                continue
            nk, _, nv = pair.partition("=")
            params.setdefault(urllib.parse.unquote(nk), []).append(urllib.parse.unquote(nv))
        for name in sorted(params):
            canon_resource += f"\n{name}:" + ",".join(sorted(params[name]))
    string_to_sign = (
        f"{method}\n\n\n{length_field}\n\n{content_type}\n\n\n\n\n\n\n"
        f"{canon_headers}{canon_resource}"
    )
    digest = hmac.new(base64.b64decode(key), string_to_sign.encode("utf-8"), hashlib.sha256).digest()
    return "SharedKey " + account + ":" + base64.b64encode(digest).decode("ascii")


def blob_request(method: str, blob_path: str, body: bytes | None = None, query: str = "") -> tuple[int, dict[str, str], bytes]:
    account, key, suffix = storage_account()
    body = body or b""
    quoted = "/".join(urllib.parse.quote(p, safe="") for p in blob_path.split("/") if p)
    path = f"/{STORAGE_CONTAINER}/{quoted}" if quoted else f"/{STORAGE_CONTAINER}"
    if query:
        path_and_query = path + "?" + query
    else:
        path_and_query = path
    date = _utc_rfc1123()
    headers = {
        "x-ms-date": date,
        "x-ms-version": BLOB_API_VERSION,
    }
    if method == "PUT" and not query:
        headers["x-ms-blob-type"] = "BlockBlob"
        headers["Content-Type"] = "application/json; charset=utf-8"
    req_headers = dict(headers)
    req_headers["Authorization"] = _sign_blob(method, account, key, path_and_query, headers, len(body))
    req_headers["Content-Length"] = str(len(body))
    url = f"https://{account}.blob.{suffix}{path_and_query}"
    req = urllib.request.Request(url, data=body if method in ("PUT", "POST") else None, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, dict(resp.headers.items()), resp.read()
    except urllib.error.HTTPError as exc:
        err_body = exc.read()
        return exc.code, dict(exc.headers.items()) if exc.headers else {}, err_body


def save_shotlist_state(payload: dict[str, Any], backup: bool = True) -> dict[str, Any]:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    status, _, body = blob_request("PUT", STORAGE_LATEST, raw)
    if status not in (200, 201):
        raise RuntimeError(f"Azure blob save failed HTTP {status}: {body[:400].decode('utf-8', 'replace')}")
    backup_name = ""
    if backup:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        backup_name = f"{STORAGE_PREFIX}/backups/{stamp}.json"
        b_status, _, b_body = blob_request("PUT", backup_name, raw)
        if b_status not in (200, 201):
            raise RuntimeError(f"Azure blob backup failed HTTP {b_status}: {b_body[:400].decode('utf-8', 'replace')}")
    return {
        "ok": True,
        "container": STORAGE_CONTAINER,
        "latest": STORAGE_LATEST,
        "backup": backup_name,
        "bytes": len(raw),
        "savedAt": payload.get("savedAt"),
    }


def load_shotlist_state(blob_path: str | None = None) -> dict[str, Any]:
    name = blob_path or STORAGE_LATEST
    if ".." in name or name.startswith("/"):
        raise ValueError("invalid blob path")
    if not name.startswith(STORAGE_PREFIX + "/"):
        name = f"{STORAGE_PREFIX}/{name.lstrip('/')}"
    status, headers, body = blob_request("GET", name)
    if status == 404:
        return {"ok": True, "found": False, "blob": name}
    if status != 200:
        raise RuntimeError(f"Azure blob load failed HTTP {status}: {body[:400].decode('utf-8', 'replace')}")
    try:
        data = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Azure blob is not valid JSON: {exc}") from exc
    return {
        "ok": True,
        "found": True,
        "blob": name,
        "bytes": len(body),
        "etag": headers.get("ETag") or headers.get("etag") or "",
        "lastModified": headers.get("Last-Modified") or headers.get("last-modified") or "",
        "state": data,
    }


def list_shotlist_backups(limit: int = 20) -> dict[str, Any]:
    prefix = STORAGE_PREFIX + "/"
    query = "restype=container&comp=list&prefix=" + urllib.parse.quote(prefix)
    status, _, body = blob_request("GET", "", query=query)
    if status != 200:
        raise RuntimeError(f"Azure blob list failed HTTP {status}: {body[:400].decode('utf-8', 'replace')}")
    root = ET.fromstring(body)
    items = []
    for blob in root.findall(".//Blob"):
        name = (blob.findtext("Name") or "").strip()
        props = blob.find("Properties")
        items.append({
            "name": name,
            "latest": name == STORAGE_LATEST,
            "bytes": int((props.findtext("Content-Length") if props is not None else None) or 0),
            "lastModified": (props.findtext("Last-Modified") if props is not None else "") or "",
        })
    items.sort(key=lambda x: x.get("lastModified") or "", reverse=True)
    return {
        "ok": True,
        "container": STORAGE_CONTAINER,
        "prefix": STORAGE_PREFIX,
        "count": len(items),
        "blobs": items[: max(1, min(limit, 50))],
    }


def build_messages(action: str, text: str) -> list[dict[str, str]]:
    text = (text or "").strip()
    if action == "grammar":
        system = (
            "You are a precise copy editor for spoken video voiceover. "
            "Fix grammar, spelling, punctuation, and capitalization only. "
            "Keep the original meaning, tone, and approximate length. "
            "Do not add marketing fluff or stage directions. "
            "Return ONLY the corrected voiceover text — no quotes, no preamble."
        )
        user = f"Fix grammar in this voiceover:\n\n{text}"
    elif action == "rewrite":
        system = (
            "You rewrite spoken video voiceover to be clearer and tighter. "
            "Keep the same meaning and facts. Prefer short sentences that sound natural when spoken. "
            "Do not invent new claims. "
            "Return ONLY the rewritten voiceover text — no quotes, no preamble."
        )
        user = f"Rewrite this voiceover for clarity and spoken flow:\n\n{text}"
    else:
        raise ValueError(f"Unknown action: {action}")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def openrouter_complete(action: str, text: str, model: str | None = None) -> str:
    if not (text or "").strip():
        return ""
    key = get_openrouter_key()
    model = model or DEFAULT_MODEL
    payload = {
        "model": model,
        "messages": build_messages(action, text),
        "temperature": 0.2 if action == "grammar" else 0.5,
        "max_tokens": 1200,
    }
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8765/research.html",
            "X-Title": "WIGAnimation Shotlist",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {err_body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter network error: {exc}") from exc
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected OpenRouter response: {str(body)[:500]}") from exc
    out = (content or "").strip()
    if len(out) >= 2 and ((out[0] == out[-1] == '"') or (out[0] == out[-1] == "'")):
        out = out[1:-1].strip()
    return out


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.startswith(".")


def build_vault_index(force: bool = False) -> list[str]:
    global _vault_index, _vault_index_built_at
    with _vault_index_lock:
        now = time.time()
        if not force and _vault_index and (now - _vault_index_built_at) < _INDEX_TTL:
            return _vault_index
        paths: list[str] = []
        root = VAULT_ROOT
        if not root.is_dir():
            _vault_index = []
            _vault_index_built_at = now
            return _vault_index
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
            # skip deep Notion dumps and similar by path fragment
            rel_dir = Path(dirpath).relative_to(root).as_posix()
            if "/Notion/" in f"/{rel_dir}/" or rel_dir.startswith("4_Archieve/Notion"):
                dirnames[:] = []
                continue
            for fn in filenames:
                ext = Path(fn).suffix.lower()
                if ext not in INDEX_EXTS:
                    continue
                rel = (Path(dirpath) / fn).relative_to(root).as_posix()
                paths.append(rel)
                if len(paths) >= 25000:
                    dirnames[:] = []
                    break
            if len(paths) >= 25000:
                break
        paths.sort()
        _vault_index = paths
        _vault_index_built_at = now
        return _vault_index


def vault_search(query: str, limit: int = 20) -> list[dict[str, str]]:
    q = (query or "").strip().lower().replace("[[", "").replace("]]", "")
    if not q:
        return []
    index = build_vault_index()
    scored: list[tuple[int, str]] = []
    for p in index:
        pl = p.lower()
        base = Path(p).name.lower()
        if q in base:
            score = 0 if base.startswith(q) else 1
        elif q in pl:
            score = 2
        else:
            # fuzzy-ish: all tokens present
            toks = [t for t in re_split_tokens(q) if t]
            if toks and all(t in pl for t in toks):
                score = 3
            else:
                continue
        scored.append((score, p))
    scored.sort(key=lambda x: (x[0], len(x[1]), x[1]))
    out = []
    for score, p in scored[:limit]:
        out.append({"path": p, "name": Path(p).name, "score": score})
    return out


def re_split_tokens(q: str) -> list[str]:
    import re
    return re.split(r"[^a-z0-9]+", q)


class ShotlistHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **getattr(SimpleHTTPRequestHandler, "extensions_map", {}),
        ".html": "text/html; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".md": "text/markdown; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".yaml": "text/yaml; charset=utf-8",
        ".yml": "text/yaml; charset=utf-8",
        ".csv": "text/csv; charset=utf-8",
        ".edl": "text/plain; charset=utf-8",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
    }

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=str(directory or ROOT), **kwargs)

    def end_headers(self):
        path = self.path.split("?", 1)[0]
        if path == "/" or path.endswith((".html", ".js")):
            self.send_header("Cache-Control", "no-store")
            self._expire_state_cookies()
        if path.startswith("/api/"):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        if not path.startswith("/api/"):
            self.send_error(404, "Not found")
            return
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _expire_state_cookies(self):
        """Drop leftover wiganimation_state_* cookies so the next request stays under the header cap."""
        raw = self.headers.get("Cookie") or ""
        if "wiganimation_state" not in raw:
            return
        seen = set()
        for part in raw.split(";"):
            name = part.strip().split("=", 1)[0]
            if name.startswith("wiganimation_state") and name not in seen:
                seen.add(name)
                self.send_header("Set-Cookie", f"{name}=; Path=/; Max-Age=0; SameSite=Lax")

    def log_message(self, fmt, *args):
        sys.stderr.write("[shotlist] %s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, status: int, obj: Any) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON body: {exc}") from exc

    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        # Error pages / copy-paste sometimes append the 431 body onto the URL.
        if path.startswith("/research.html") and path != "/research.html":
            self.path = "/research.html"
            path = "/research.html"
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if path == "/api/health":
            storage_ok = False
            storage_err = ""
            try:
                acc, _, _ = storage_account()
                storage_ok = True
                account_name = acc
            except Exception as exc:  # noqa: BLE001
                account_name = ""
                storage_err = str(exc)
            self._send_json(200, {
                "ok": True,
                "model": DEFAULT_MODEL,
                "vault": str(VAULT_ROOT),
                "index_size": len(_vault_index),
                "openrouter_key_configured": bool(
                    os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_KEY") or _api_key_cache
                ),
                "azure": {
                    "ok": storage_ok,
                    "account": account_name,
                    "container": STORAGE_CONTAINER,
                    "prefix": STORAGE_PREFIX,
                    "secret": STORAGE_SECRET,
                    "error": storage_err,
                },
            })
            return
        if path == "/api/state":
            blob = (qs.get("blob") or [""])[0]
            try:
                self._send_json(200, load_shotlist_state(blob or None))
            except Exception as exc:  # noqa: BLE001
                self._send_json(502, {"ok": False, "error": str(exc)})
            return
        if path == "/api/state/list":
            try:
                limit = int((qs.get("limit") or ["20"])[0] or 20)
                self._send_json(200, list_shotlist_backups(limit=limit))
            except Exception as exc:  # noqa: BLE001
                self._send_json(502, {"ok": False, "error": str(exc)})
            return
        if path == "/api/vault-search":
            q = (qs.get("q") or [""])[0]
            limit = int((qs.get("limit") or ["20"])[0] or 20)
            try:
                results = vault_search(q, limit=max(1, min(limit, 50)))
                self._send_json(200, {"ok": True, "query": q, "results": results, "index_size": len(_vault_index) or len(build_vault_index())})
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"ok": False, "error": str(exc)})
            return
        if path == "/api/vault-index":
            try:
                force = (qs.get("force") or ["0"])[0] == "1"
                idx = build_vault_index(force=force)
                self._send_json(200, {"ok": True, "count": len(idx), "sample": idx[:5]})
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"ok": False, "error": str(exc)})
            return
        return super().do_GET()

    def do_POST(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path not in ("/api/text", "/api/vo-edit", "/api/state"):
            self.send_error(404, "Not found")
            return
        try:
            body = self._read_json_body()
            if path == "/api/state":
                state = body.get("state") if isinstance(body.get("state"), dict) else body
                if not isinstance(state, dict) or not state:
                    self._send_json(400, {"ok": False, "error": "state object is empty"})
                    return
                backup = body.get("backup", True) is not False
                result = save_shotlist_state(state, backup=backup)
                self._send_json(200, result)
                return
            action = (body.get("action") or "").strip().lower()
            text = body.get("text") or ""
            model = body.get("model") or None
            if action not in ("grammar", "rewrite"):
                self._send_json(400, {"ok": False, "error": "action must be 'grammar' or 'rewrite'"})
                return
            if not str(text).strip():
                self._send_json(400, {"ok": False, "error": "text is empty"})
                return
            result = openrouter_complete(action, str(text), model=model)
            self._send_json(200, {"ok": True, "action": action, "text": result, "model": model or DEFAULT_MODEL})
        except ValueError as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
        except RuntimeError as exc:
            self._send_json(502, {"ok": False, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": f"Server error: {exc}"})


def open_server(host: str, port: int, handler):
    last_err = None
    for candidate in range(port, port + 10):
        try:
            return ThreadingHTTPServer((host, candidate), handler), candidate
        except OSError as exc:
            last_err = exc
    raise SystemExit(f"Could not bind {host}:{port}-{port + 9}: {last_err}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Serve WIGAnimation Shotlist on localhost")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--preload-key", action="store_true")
    parser.add_argument("--index-vault", action="store_true", help="Build vault path index at startup")
    args = parser.parse_args(argv)

    os.chdir(ROOT)
    if args.preload_key:
        try:
            get_openrouter_key()
            print(f"OpenRouter key loaded (model={DEFAULT_MODEL})")
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: could not preload OpenRouter key: {exc}", file=sys.stderr)
    if args.index_vault:
        idx = build_vault_index(force=True)
        print(f"Vault index: {len(idx)} paths under {VAULT_ROOT}")

    handler = functools.partial(ShotlistHandler, directory=ROOT)
    httpd, port = open_server(args.host, args.port, handler)
    # warm index in background
    threading.Thread(target=lambda: build_vault_index(force=False), daemon=True).start()

    url = f"http://{args.host}:{port}/research.html"
    if port != args.port:
        print(f"Port {args.port} busy — using {port}")
    print(f"Shotlist server root: {ROOT}")
    print(f"Vault root: {VAULT_ROOT}")
    print(f"Open: {url}")
    print(f"API text: POST /api/text  |  vault search: GET /api/vault-search?q=")
    print(f"Model: {DEFAULT_MODEL}")
    print("Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
