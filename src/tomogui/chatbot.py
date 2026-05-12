"""
Claude-powered chatbot dialog for tomogui.

Floating QDialog with a persistent QThread worker that calls the Anthropic
SDK. Streaming text comes back to the UI via Qt signals. The system prompt
(tomocupy parameter reference) lives in chatbot_knowledge.md and is cached
via Anthropic's prompt caching so repeat questions are cheap.

Credential discovery (returns api_key + optional base_url):
    1. ANTHROPIC_API_KEY env var (base_url from env or Claude settings.json)
    2. ~/.claude/settings.json — Claude Code's config:
         - "apiKeyHelper": shell command whose stdout is the API key
           (this is the Argonne-style flow: a helper script that mints
           short-lived tokens, used together with a custom base_url)
         - "env.ANTHROPIC_BASE_URL": custom Claude proxy endpoint
    3. ~/.config/tomogui/api_key (mode 0600, written by first-run dialog)
    4. ~/.claude/credentials.json (legacy fallback)
"""

import functools
import json
import os
import subprocess
from pathlib import Path

from PyQt5.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
)


KNOWLEDGE_PATH = Path(__file__).parent / "chatbot_knowledge.md"
SETTINGS_PATH = Path.home() / ".config" / "tomogui" / "api_key"
MODEL = "claude-opus-4-7"


@functools.lru_cache(maxsize=1)
def _load_knowledge() -> str:
    if KNOWLEDGE_PATH.exists():
        return KNOWLEDGE_PATH.read_text(encoding="utf-8")
    return (
        "You are a helpful assistant for tomogui, a PyQt5 GUI for tomocupy "
        "tomographic reconstruction. Answer questions about reconstruction "
        "parameters concisely and accurately."
    )


def _check_anthropic_installed():
    """Return (ok, error_message). Soft import — never raises."""
    try:
        import anthropic  # noqa: F401
        return True, ""
    except ImportError:
        return False, (
            "The 'anthropic' package is not installed.\n\n"
            "Install with:\n    pip install anthropic"
        )


CLAUDE_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def _load_claude_settings() -> dict:
    """Load Claude Code's settings.json (or {} on error)."""
    if not CLAUDE_SETTINGS_PATH.exists():
        return {}
    try:
        return json.loads(CLAUDE_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _run_api_key_helper(cmd: str) -> str:
    """Run a shell command and return its stripped stdout. Empty on failure."""
    try:
        result = subprocess.run(
            cmd, shell=True, check=True,
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def _find_credentials() -> tuple[str | None, str | None]:
    """Return (api_key, base_url) using the discovery order in the module docstring.

    Either field may be None. The caller is responsible for prompting the user
    (first-run paste dialog) when api_key comes back None.
    """
    settings = _load_claude_settings()
    settings_env = settings.get("env", {}) if isinstance(settings.get("env"), dict) else {}

    # base_url: env wins; otherwise pull from Claude settings.json env block
    base_url = (
        os.environ.get("ANTHROPIC_BASE_URL", "").strip()
        or settings_env.get("ANTHROPIC_BASE_URL", "").strip()
        or None
    )

    # 1. Plain env var
    env_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if env_key:
        return env_key, base_url

    # 2. Claude Code's apiKeyHelper (Argonne-style flow)
    helper = settings.get("apiKeyHelper")
    if isinstance(helper, str) and helper.strip():
        v = _run_api_key_helper(helper.strip())
        if v:
            return v, base_url

    # 3. Tomogui's own settings file
    if SETTINGS_PATH.exists():
        try:
            v = SETTINGS_PATH.read_text(encoding="utf-8").strip()
            if v.startswith("sk-ant-"):
                return v, base_url
        except OSError:
            pass

    # 4. Legacy Claude credentials.json
    cc = Path.home() / ".claude" / "credentials.json"
    if cc.exists():
        try:
            data = json.loads(cc.read_text(encoding="utf-8"))
            for field in ("api_key", "anthropic_api_key", "key"):
                v = data.get(field, "")
                if isinstance(v, str) and v.startswith("sk-ant-"):
                    return v, base_url
        except (OSError, json.JSONDecodeError):
            pass

    return None, base_url


def _find_api_key():
    """Backward-compatible alias for callers that only need the key."""
    return _find_credentials()[0]


def _save_api_key(key: str) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(key.strip(), encoding="utf-8")
    try:
        os.chmod(SETTINGS_PATH, 0o600)
    except OSError:
        pass


class ChatWorker(QObject):
    """Runs Claude streaming requests on a worker thread.

    Lives on its own QThread (moved via moveToThread). The dialog emits
    submit_request → worker.submit; worker emits chunk/done/error back.
    """

    started_response = pyqtSignal()
    chunk = pyqtSignal(str)
    done = pyqtSignal(object)   # the final Message object
    cancelled = pyqtSignal()    # user hit Stop mid-stream
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._client = None
        self._cancel = False
        self._api_key = None
        self._base_url = None

    def set_credentials(self, key: str, base_url: str | None) -> None:
        if key != self._api_key or base_url != self._base_url:
            self._api_key = key
            self._base_url = base_url
            self._client = None  # force rebuild

    def cancel(self) -> None:
        self._cancel = True

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        import anthropic
        kwargs = {"api_key": self._api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        self._client = anthropic.Anthropic(**kwargs)
        return self._client

    def submit(self, messages: list, system_blocks: list) -> None:
        self._cancel = False
        try:
            import anthropic
        except ImportError as e:
            self.error.emit(f"anthropic SDK not available: {e}")
            return

        try:
            client = self._ensure_client()
        except Exception as e:
            self.error.emit(f"Could not create Anthropic client: {e}")
            return

        try:
            self.started_response.emit()
            with client.messages.stream(
                model=MODEL,
                max_tokens=64000,
                system=system_blocks,
                messages=messages,
                output_config={"effort": "medium"},
            ) as stream:
                for text in stream.text_stream:
                    if self._cancel:
                        break
                    self.chunk.emit(text)
                if self._cancel:
                    # Don't call get_final_message — it would block waiting
                    # for the rest of the response. Exiting the with-block
                    # closes the HTTP stream.
                    self.cancelled.emit()
                    return
                final = stream.get_final_message()
            self.done.emit(final)

        except anthropic.AuthenticationError:
            self.error.emit(
                "Invalid API key (401). Click 'Edit key' to update."
            )
        except anthropic.APIConnectionError as e:
            self.error.emit(
                "Cannot reach Claude.\n\n"
                "If you're on a restricted network (e.g. beamline), set "
                "ANTHROPIC_BASE_URL or HTTPS_PROXY to route through your SSH "
                f"tunnel before launching tomogui.\n\nDetails: {e}"
            )
        except anthropic.RateLimitError:
            self.error.emit("Rate limited (429). Please wait and try again.")
        except anthropic.APIStatusError as e:
            if getattr(e, "status_code", 0) == 529:
                self.error.emit("Claude is overloaded (529). Please retry.")
            else:
                self.error.emit(
                    f"API error {getattr(e, 'status_code', '?')}: "
                    f"{getattr(e, 'message', str(e))}"
                )
        except Exception as e:
            self.error.emit(f"Unexpected error: {e}")


class ChatBotDialog(QDialog):
    """Floating Q&A dialog backed by Claude.

    Non-modal — the user can keep working in the main GUI while the dialog
    is open. Conversation history is held here in self.messages; a worker
    on a persistent QThread does the actual API streaming.
    """

    submit_request = pyqtSignal(list, list)

    USER_BUBBLE_LIGHT = "#E3F2FD"
    USER_BUBBLE_DARK = "#1565C0"
    ASSISTANT_BUBBLE_LIGHT = "#F1F8E9"
    ASSISTANT_BUBBLE_DARK = "#2E7D32"
    ERROR_COLOR = "#c62828"

    def __init__(self, parent=None, theme_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Ask Claude — tomogui assistant")
        self.setWindowFlags(Qt.Window)  # independent window with min/max/close
        self.resize(700, 600)

        self.theme_manager = theme_manager
        self.messages: list = []
        self._current_assistant_text = ""
        self._busy = False
        self._cached_key: str | None = None
        self._cached_base_url: str | None = None

        self._build_ui()
        self._setup_worker()

        if self.theme_manager is not None:
            self.theme_manager.register_callback(self._on_theme_changed)
        self._apply_theme()

    # ---------- UI construction ----------

    def _build_ui(self):
        outer = QVBoxLayout(self)

        header = QHBoxLayout()
        header_label = QLabel(
            "Ask about tomocupy parameters, GUI workflow, or reconstruction concepts."
        )
        header_label.setWordWrap(True)
        header.addWidget(header_label, 1)
        self.new_chat_btn = QPushButton("New chat")
        self.new_chat_btn.setToolTip("Clear the conversation history")
        self.new_chat_btn.clicked.connect(self._on_new_chat)
        header.addWidget(self.new_chat_btn)
        outer.addLayout(header)

        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setStyleSheet("QTextEdit { font-size: 11pt; }")
        outer.addWidget(self.transcript, 1)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-style: italic;")
        outer.addWidget(self.status_label)

        bottom = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText(
            "Type your question and press Enter..."
        )
        self.input_box.setStyleSheet("QLineEdit { font-size: 11pt; padding: 6px; }")
        self.input_box.returnPressed.connect(self._on_send)
        bottom.addWidget(self.input_box, 1)
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet(
            "QPushButton { font-size: 11pt; padding: 6px 18px; }"
        )
        self.send_btn.clicked.connect(self._on_send)
        bottom.addWidget(self.send_btn)
        outer.addLayout(bottom)

    def _setup_worker(self):
        self._thread = QThread(self)
        self._worker = ChatWorker()
        self._worker.moveToThread(self._thread)
        self._thread.start()

        # Cross-thread signals are auto-queued by Qt
        self.submit_request.connect(self._worker.submit)
        self._worker.started_response.connect(self._on_started_response)
        self._worker.chunk.connect(self._on_chunk)
        self._worker.done.connect(self._on_done)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.error.connect(self._on_error)

    # ---------- Theme integration ----------

    def _on_theme_changed(self, _theme_name: str) -> None:
        self._apply_theme()

    def _apply_theme(self):
        # Re-render the whole transcript to swap bubble colors.
        # (Cheap because it only happens on theme toggle, not per token.)
        self.transcript.clear()
        for m in self.messages:
            role = m.get("role")
            content = m.get("content", "")
            if isinstance(content, list):
                content = "".join(
                    b.get("text", "") for b in content if isinstance(b, dict)
                )
            if role == "user":
                self._append_user_bubble(content)
            elif role == "assistant":
                self._start_assistant_bubble()
                cursor = self.transcript.textCursor()
                cursor.movePosition(QTextCursor.End)
                cursor.insertText(content)
                self._finalize_assistant_bubble()

    def _is_dark(self) -> bool:
        return (
            self.theme_manager is not None
            and self.theme_manager.get_current_theme() == "dark"
        )

    def _bubble_colors(self):
        if self._is_dark():
            return self.USER_BUBBLE_DARK, self.ASSISTANT_BUBBLE_DARK
        return self.USER_BUBBLE_LIGHT, self.ASSISTANT_BUBBLE_LIGHT

    # ---------- Sending / streaming ----------

    def _on_send(self):
        # When busy the Send button doubles as Stop.
        if self._busy:
            self._worker.cancel()
            self.status_label.setText("Stopping…")
            self.send_btn.setEnabled(False)  # one-shot — don't accept repeats
            return
        text = self.input_box.text().strip()
        if not text:
            return

        # Lazy install / key checks
        ok, msg = _check_anthropic_installed()
        if not ok:
            QMessageBox.warning(self, "anthropic SDK missing", msg)
            return

        # Cache credentials per-dialog so we discover (and run apiKeyHelper)
        # only once per session — not on every send.
        if self._cached_key is None:
            key, base_url = _find_credentials()
            if key is None:
                key = self._prompt_for_key()
                if not key:
                    return
                # _prompt_for_key persists to ~/.config/tomogui/api_key;
                # next discovery would find it, but cache here too.
            self._cached_key = key
            self._cached_base_url = base_url
            src = self._describe_credential_source()
            self.status_label.setText(
                f"credentials: {src}"
                + (f" → {self._cached_base_url}" if self._cached_base_url else "")
            )
        self._worker.set_credentials(self._cached_key, self._cached_base_url)

        self.input_box.clear()
        self._append_user_bubble(text)
        self.messages.append({"role": "user", "content": text})

        system_blocks = [{
            "type": "text",
            "text": _load_knowledge(),
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }]
        self._set_busy(True)
        self.submit_request.emit(list(self.messages), system_blocks)

    def _on_started_response(self):
        self._current_assistant_text = ""
        self._start_assistant_bubble()

    def _on_chunk(self, text: str):
        self._current_assistant_text += text
        cursor = self.transcript.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.transcript.setTextCursor(cursor)
        self.transcript.ensureCursorVisible()

    def _on_done(self, final_message):
        self._finalize_assistant_bubble()
        # Persist the assistant turn so the next request includes it.
        # We store text only — preserves multi-turn context without dragging
        # along thinking blocks (which we have disabled anyway).
        self.messages.append({
            "role": "assistant",
            "content": self._current_assistant_text,
        })
        self._current_assistant_text = ""
        self._set_busy(False)

        # Surface cache effectiveness in the status bar (helpful while tuning).
        try:
            usage = final_message.usage
            cached = getattr(usage, "cache_read_input_tokens", 0) or 0
            written = getattr(usage, "cache_creation_input_tokens", 0) or 0
            uncached = getattr(usage, "input_tokens", 0) or 0
            self.status_label.setText(
                f"tokens — cached: {cached}, written: {written}, "
                f"uncached: {uncached}, output: {usage.output_tokens}"
            )
        except AttributeError:
            self.status_label.setText("")

    def _on_error(self, msg: str):
        self._finalize_assistant_bubble()
        cursor = self.transcript.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(
            f'<div style="color:{self.ERROR_COLOR}; padding:6px;">'
            f'<b>Error:</b> {msg.replace(chr(10), "<br>")}</div><br>'
        )
        self.transcript.setTextCursor(cursor)
        self.transcript.ensureCursorVisible()
        self._set_busy(False)

    def _on_cancelled(self):
        self._finalize_assistant_bubble()
        cursor = self.transcript.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(
            '<div style="color:#888; font-style:italic; padding:4px;">'
            '— stopped —</div><br>'
        )
        # Persist whatever partial text we received so the next turn has
        # context. Better than discarding the half-answer.
        if self._current_assistant_text:
            self.messages.append({
                "role": "assistant",
                "content": self._current_assistant_text,
            })
        self._current_assistant_text = ""
        self.status_label.setText("Stopped.")
        self._set_busy(False)

    # ---------- New chat / key edit ----------

    def _on_new_chat(self):
        if self._busy:
            return
        self.messages = []
        self._current_assistant_text = ""
        self.transcript.clear()
        self.status_label.setText("")

    def _describe_credential_source(self) -> str:
        """Best-guess label for which discovery branch succeeded.

        Used only for the status bar — not load-bearing.
        """
        if os.environ.get("ANTHROPIC_API_KEY", "").strip():
            return "ANTHROPIC_API_KEY env var"
        settings = _load_claude_settings()
        if isinstance(settings.get("apiKeyHelper"), str) and settings["apiKeyHelper"].strip():
            return "Claude Code apiKeyHelper"
        if SETTINGS_PATH.exists():
            return f"{SETTINGS_PATH}"
        if (Path.home() / ".claude" / "credentials.json").exists():
            return "~/.claude/credentials.json"
        return "first-run paste dialog"

    def _prompt_for_key(self) -> str:
        key, ok = QInputDialog.getText(
            self,
            "Enter Claude API key",
            "Paste your Anthropic API key (starts with sk-ant-…).\n"
            "It will be saved to ~/.config/tomogui/api_key with mode 0600.",
            QLineEdit.Password,
        )
        if not ok:
            return ""
        key = key.strip()
        if not key.startswith("sk-ant-"):
            QMessageBox.warning(
                self,
                "Invalid key",
                "API keys start with 'sk-ant-'. Nothing was saved.",
            )
            return ""
        try:
            _save_api_key(key)
        except OSError as e:
            QMessageBox.warning(
                self, "Could not save key",
                f"The key will still work for this session, but couldn't be "
                f"persisted:\n\n{e}",
            )
        return key

    # ---------- Busy state ----------

    def _set_busy(self, busy: bool):
        self._busy = busy
        self.input_box.setEnabled(not busy)
        # Send button stays enabled while busy — it doubles as Stop.
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Stop" if busy else "Send")
        self.new_chat_btn.setEnabled(not busy)
        if busy:
            self.status_label.setText("Thinking… (click Stop to interrupt)")
        if not busy:
            self.input_box.setFocus()

    # ---------- Bubble rendering ----------

    def _append_user_bubble(self, text: str):
        user_bg, _ = self._bubble_colors()
        cursor = self.transcript.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(
            f'<div style="background:{user_bg}; padding:8px; '
            f'border-radius:6px; margin:4px 40px 4px 0;">'
            f'<b>You:</b><br>{self._escape(text)}</div><br>'
        )

    def _start_assistant_bubble(self):
        _, asst_bg = self._bubble_colors()
        cursor = self.transcript.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(
            f'<div style="background:{asst_bg}; padding:8px; '
            f'border-radius:6px; margin:4px 0 4px 40px;">'
            f'<b>Claude:</b><br>'
        )
        # Move cursor inside the open div so subsequent insertText lands there.
        cursor.movePosition(QTextCursor.End)
        self.transcript.setTextCursor(cursor)

    def _finalize_assistant_bubble(self):
        cursor = self.transcript.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml("</div><br>")

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>")
        )

    # ---------- Lifecycle ----------

    def closeEvent(self, event):
        try:
            self._worker.cancel()
            self._thread.quit()
            self._thread.wait(2000)
        except Exception:
            pass
        super().closeEvent(event)
