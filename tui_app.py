from textual.app import App, ComposeResult
from textual import work
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, Grid
from textual.widgets import Header, Footer, Input, Button, Label, Static, ListView, ListItem, LoadingIndicator, RadioSet, RadioButton, Markdown, SelectionList
from textual.screen import Screen, ModalScreen
from textual.message import Message
from textual.binding import Binding
from textual.reactive import reactive
from textual.worker import Worker, WorkerState

import os
import sys
import threading
import queue
import time
from datetime import datetime
import logging
import subprocess
import socket

# Configure logging to file
logging.basicConfig(
    filename='tui_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import core Whetstone modules
from core import PhilosopherCore
from symposium import Symposium
from scheduler_service import SocraticScheduler

# --- Widgets ---

class ChatBubble(Vertical):
    """A single chat message bubble."""
    def __init__(self, sender: str, text: str, is_user: bool = False, is_generating: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = sender
        self.text_content = text
        self.is_user = is_user
        self.is_generating = is_generating

    def compose(self) -> ComposeResult:
        yield Label(f"[{self.sender}]", classes="sender-label")
        # Ensure Markdown has content so it renders borders
        content = self.text_content if self.text_content else " "
        yield Markdown(content, classes="message-text")
        if self.is_generating:
             yield LoadingIndicator(classes="compact-loader", id="loader")

    def on_mount(self) -> None:
        if self.is_user:
            self.add_class("user-message")
        else:
            self.add_class("ai-message")

class SymposiumBubble(Vertical):
    """A symposium debate bubble."""
    def __init__(self, sender: str, text: str, side: str = "left", is_generating: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = sender
        self.text_content = text
        self.side = side
        self.is_generating = is_generating

    def compose(self) -> ComposeResult:
        yield Label(f"[{self.sender}]", classes="symp-sender")
        yield Markdown(self.text_content, classes="symp-text")
        if self.is_generating:
            yield LoadingIndicator(classes="compact-loader")

# ... (skipping to generate_ai_response) ...

    @work(exclusive=True, thread=True)
    def generate_ai_response(self, user_text: str, ai_bubble: ChatBubble):
        try:
            logger.info(f"Starting generate_ai_response for: {user_text[:20]}...")
            app = self.app
            full_response = ""
            first_token = True
            
            # Diagnostic: Check if backend is ready
            if not app.core.backend:
                 logger.error("Backend is None!")
            
            for token in app.core.chat(user_text):
                logger.debug(f"Token received: {token[:10]!r}")
                full_response += token
                def update_ui(first, text):
                    if first:
                        try: 
                            # Explicitly log removal attempt
                            logger.debug(f"Bubble children: {ai_bubble.children}")
                            # logger.debug("Removing loading indicator")
                            # ai_bubble.query(LoadingIndicator).remove()
                            ai_bubble.query("#loader").remove()
                        except Exception as e: 
                            logger.error(f"Error removing loader: {e}")
                    
                    # Update Markdown widget
                    try:
                        ai_bubble.query_one(Markdown).update(text)
                    except Exception as e:
                        logger.error(f"Error updating Markdown: {e}")
                        
                    self.query_one("#chat-history", ScrollableContainer).scroll_end(animate=False)
                
                app.call_from_thread(update_ui, first_token, full_response)
                first_token = False

            logger.info(f"Generation complete. First token? {first_token}")

            if first_token:
                 # No tokens received
                 logger.warning("No tokens received from backend.")
                 def show_error():
                     try: ai_bubble.query("#loader").remove()
                     except: pass
                     ai_bubble.query_one(Markdown).update("[Error: No response from AI]")
                 app.call_from_thread(show_error)
        except Exception as e:
            logger.exception("Error in generate_ai_response")
            def show_fatal_error():
                 try: ai_bubble.query("#loader").remove()
                 except: pass
                 ai_bubble.query_one(Markdown).update(f"[System Error: {str(e)}]")
            self.app.call_from_thread(show_fatal_error)

    def on_mount(self) -> None:
        self.add_class(f"symp-{self.side}")

class DreamModal(ModalScreen):
    """Full screen modal for Dream Mode."""
    CSS = """
    DreamModal {
        align: center middle;
        background: $surface 80%;
    }
    #dream-box {
        width: 80%;
        height: 60%;
        background: $panel;
        border: thick $primary;
        padding: 2 4;
        align: center middle;
    }
    #dream-quote {
        text-align: center;
        text-style: italic bold;
        margin-bottom: 2;
        color: $text;
        width: 100%;
        height: 1fr;
        content-align: center middle; 
    }
    #dream-author {
        text-align: center;
        color: $accent;
    }
    """
    
    def __init__(self, author: str, quote: str):
        super().__init__()
        self.author = author
        self.quote = quote

    def compose(self) -> ComposeResult:
        with Vertical(id="dream-box"):
            yield Label(self.quote, id="dream-quote")
            yield Label(f"— {self.author}", id="dream-author")
            yield Button("Wake Up", id="btn-close-dream", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-dream":
            self.dismiss()

# --- Screens ---

class DashboardScreen(Screen):
    """Main Chat Interface."""
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="app-grid"):
            with Vertical(id="sidebar"):
                yield Label("THE WHETSTONE", id="logo")
                
                # --- COMMAND MENU (Top Left) ---
                yield Label("COMMANDS", classes="section-title")
                yield Button("Start Symposium", id="btn-goto-symposium", variant="primary")
                yield Button("Update Personas", id="btn-update-personas", variant="default")
                yield Button("Scheduler Manager", id="btn-goto-scheduler", variant="warning")
                
                # --- Personas (push to bottom or fill remaining) ---
                yield Label("PERSONAS", classes="section-title")
                yield ListView(id="persona-list")
            
            with Vertical(id="main-chat-area"):
                yield ScrollableContainer(id="chat-history")
                with Horizontal(id="input-bar"):
                    yield Input(placeholder="Type your message...", id="chat-input")
                    yield Button("Send", id="btn-send", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        # Populate Persona List
        self.refresh_persona_list()

    def refresh_persona_list(self):
        list_view = self.query_one("#persona-list", ListView)
        list_view.clear()
        personas = self.app.core.get_valid_personas()
        for p in personas:
            list_view.append(ListItem(Label(p['name']), name=p['name']))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-send":
            inp = self.query_one("#chat-input", Input)
            await self.process_user_message(inp.value)
        elif event.button.id == "btn-goto-symposium":
            self.app.push_screen(SymposiumScreen())
        elif event.button.id == "btn-goto-scheduler":
            self.app.push_screen(SchedulerScreen())
        elif event.button.id == "btn-update-personas":
            self.run_update_personas()

    @work(thread=True)
    def run_update_personas(self):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "philosophy_library", "generate_personas.py")
        
        def notify(msg):
             self.app.notify(msg)
        
        self.app.call_from_thread(notify, "Updating personas... this may take a moment.")
        
        try:
             cmd = [sys.executable, script_path]
             subprocess.run(cmd, cwd=os.path.dirname(script_path), check=True)
             self.app.core.refresh_data()
             self.app.call_from_thread(self.refresh_persona_list)
             self.app.call_from_thread(notify, "Personas updated successfully!")
             
        except Exception as e:
             logger.error(f"Failed to update personas: {e}")
             self.app.call_from_thread(notify, f"Error updating personas: {e}")

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        name = event.item.name
        if not name:
            label = event.item.query_one(Label)
            name = str(label.renderable) if hasattr(label, 'renderable') else str(label)
        for p in self.app.core.get_valid_personas():
            if p['name'] == name:
                self.app.core.set_persona(p)
                inp = self.query_one("#chat-input", Input)
                inp.placeholder = f"Chatting with {p['name']}..."
                break

    async def process_user_message(self, text: str):
        if not text.strip(): return
        
        if not self.app.core.current_persona:
            hist = self.query_one("#chat-history", ScrollableContainer)
            hist.mount(ChatBubble("System", "Please select a persona from the sidebar first.", is_user=False))
            return
            
        inp = self.query_one("#chat-input", Input)
        inp.value = ""
        
        history = self.query_one("#chat-history", ScrollableContainer)
        await history.mount(ChatBubble("You", text, is_user=True))
        # Mount AI response bubble
        ai_bubble = ChatBubble(self.app.core.current_persona['name'], "", is_user=False, is_generating=True)
        history.mount(ai_bubble)
        history.scroll_end(animate=False)
        
        self.generate_ai_response(text, ai_bubble)

    @work(exclusive=True, thread=True)
    def generate_ai_response(self, user_text: str, ai_bubble: ChatBubble):
        try:
            logger.info(f"Starting generate_ai_response for: {user_text[:20]}...")
            app = self.app
            full_response = ""
            first_token = True
            
            # Diagnostic: Check if backend is ready
            if not app.core.backend:
                 logger.error("Backend is None!")
            
            for token in app.core.chat(user_text):
                logger.debug(f"Token received: {token[:10]!r}")
                full_response += token
                def update_ui(first, text):
                    if first:
                        try: 
                            # Explicitly log removal attempt
                            # logger.debug("Removing loading indicator")
                            ai_bubble.query(LoadingIndicator).remove()
                        except Exception as e: 
                            logger.error(f"Error removing loader: {e}")
                    ai_bubble.query_one(".message-text").update(text)
                    self.query_one("#chat-history", ScrollableContainer).scroll_end(animate=False)
                
                app.call_from_thread(update_ui, first_token, full_response)
                first_token = False

            logger.info(f"Generation complete. First token? {first_token}")

            if first_token:
                 # No tokens received
                 logger.warning("No tokens received from backend.")
                 def show_error():
                     ai_bubble.query(LoadingIndicator).remove()
                     ai_bubble.query_one(".message-text").update("[Error: No response from AI]")
                 app.call_from_thread(show_error)
        except Exception as e:
            logger.exception("Error in generate_ai_response")
            def show_fatal_error():
                 try: ai_bubble.query(LoadingIndicator).remove()
                 except: pass
                 ai_bubble.query_one(".message-text").update(f"[System Error: {str(e)}]")
            self.app.call_from_thread(show_fatal_error)

class SchedulerScreen(Screen):
    """Screen for managing Scheduled Tasks."""
    CSS = """
    #sched-container { layout: grid; grid-size: 2; grid-columns: 1fr 1fr; }
    .col { padding: 1; border: solid $secondary; height: 100%; }
    .sec-title { text-align: center; text-style: bold; background: $accent; color: $text; margin-bottom: 1;}
    .task-item { padding: 1; border-bottom: solid $surface; }
    #new-task-form { layout: vertical; }
    .form-label { margin-top: 1; }
    """
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        with Header():
             yield Button("← Back", id="btn-back", variant="error", classes="header-back-btn")
        
        with Container(id="sched-container"):
            # Left: Task List
            with Vertical(classes="col"):
                yield Label("Active Tasks", classes="sec-title")
                yield ScrollableContainer(id="task-list")
                yield Button("Start Scheduler Service", id="btn-service-toggle", variant="success")
            
            # Right: Task Builder
            with Vertical(classes="col", id="new-task-form"):
                yield Label("Task Builder", classes="sec-title")
                
                yield Label("Task Name", classes="form-label")
                yield Input(placeholder="e.g. Morning Wakeup", id="in-task-name")
                
                yield Label("Interval (Minutes)", classes="form-label")
                yield Input(placeholder="1", value="1", id="in-interval", type="integer")
                
                yield Label("Action Type", classes="form-label")
                with RadioSet(id="radio-action"):
                    yield RadioButton("Toast Notification", value=True, id="toast")
                    yield RadioButton("Audio Alert", id="audio")
                    yield RadioButton("Dream Mode Modal", id="dream_mode")
                
                yield Label("Target Persona", classes="form-label")
                with RadioSet(id="radio-persona"):
                    yield RadioButton("Random Persona", value=True, id="Random")
                    yield RadioButton("Specific (Current)", id="Specific")
                
                yield Label("Topic (Optional)", classes="form-label")
                yield Input(placeholder="e.g. Failure, Hope", id="in-topic")
                
                yield Button("Create Task", id="btn-create-task", variant="primary", classes="form-label")
                
                yield Label("--- Quick Actions ---", classes="form-label")
                yield Button("Add 'Dream Mode' (1 min)", id="btn-add-dream", variant="primary")

    async def on_mount(self):
        await self.mount_task_list()
        self.update_service_button()

    def update_service_button(self):
        btn = self.query_one("#btn-service-toggle", Button)
        if self.app.scheduler.running:
            btn.label = "Stop Scheduler Service"
            btn.variant = "error"
        else:
            btn.label = "Start Scheduler Service"
            btn.variant = "success"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()
            
        elif event.button.id == "btn-service-toggle":
            if self.app.scheduler.running:
                self.app.scheduler.stop()
            else:
                self.app.scheduler.start()
            self.update_service_button()
            
        elif event.button.id == "btn-add-dream":
            self.app.scheduler.add_task("Dream Mode", 1, "dream_mode", "Random", "Philosophy")
            self.app.notify("Dream Mode task added!")
            await self.mount_task_list()
            
        elif event.button.id == "btn-create-task":
            name = self.query_one("#in-task-name", Input).value or "New Task"
            try:
                interval = int(self.query_one("#in-interval", Input).value)
            except: interval = 1
            
            # Get Action
            action_radio = self.query_one("#radio-action", RadioSet)
            if action_radio.pressed_button:
                 action = action_radio.pressed_button.id 
            else: action = "toast"
            
            # Get Persona
            p_radio = self.query_one("#radio-persona", RadioSet)
            is_random = True
            if p_radio.pressed_button and p_radio.pressed_button.id == "Specific":
                 is_random = False
            
            p_name = "Random"
            if not is_random:
                 if self.app.core.current_persona:
                      p_name = self.app.core.current_persona['name']
                 else:
                      self.app.notify("No current persona selected! using Random.")
            
            topic = self.query_one("#in-topic", Input).value
            
            self.app.scheduler.add_task(name, interval, action, p_name, topic)
            self.app.notify(f"Task '{name}' created!")
            await self.mount_task_list()
            
        elif event.button.id and event.button.id.startswith("del-"):
            task_id = event.button.id.split("-")[1]
            self.app.scheduler.remove_task(task_id)
            await self.mount_task_list()

    async def mount_task_list(self):
        cont = self.query_one("#task-list", ScrollableContainer)
        await cont.remove_children() 
        for task in self.app.scheduler.tasks:
            lbl = Label(f"[{task.interval_minutes}m] {task.name} ({task.action_type})")
            lbl.styles.width = "1fr"
            lbl.styles.margin_top = 1
            
            crow = Horizontal(
                lbl,
                Button("Del", id=f"del-{task.id}", variant="error"),
                classes="task-item"
            )
            crow.styles.height = "auto"
            crow.styles.margin_bottom = 1
            await cont.mount(crow)


class SymposiumScreen(Screen):
    """Split Screen Debate."""
    
    BINDINGS = [("escape", "app.pop_screen", "Back to Chat")]

    def compose(self) -> ComposeResult:
        with Header():
            yield Button("← Back", id="btn-symp-back", variant="error", classes="header-back-btn")
        
        with Container(id="symp-header-controls"):
            yield Label("Topic:")
            yield Input(placeholder="Enter topic (e.g. Justice)", id="symp-topic")
            yield Button("P1: Select", id="btn-p1-cycle")
            yield Button("P2: Select", id="btn-p2-cycle")
            yield Button("Start Debate", id="btn-symp-start", variant="success")

        with Container(id="symp-container"):
             # Split View
            with Horizontal(id="debate-stage"):
                with Vertical(id="stage-left", classes="stage-col"):
                    yield Label("PLATO", id="label-p1", classes="stage-name")
                    yield ScrollableContainer(id="chat-left")
                with Vertical(id="stage-right", classes="stage-col"):
                    yield Label("NIETZSCHE", id="label-p2", classes="stage-name")
                    yield ScrollableContainer(id="chat-right")
            
    def on_mount(self):
        # Initialize default selections
        self.personas = self.app.core.get_valid_personas()
        self.p1_idx = 0
        self.p2_idx = 1 if len(self.personas) > 1 else 0
        self.update_persona_labels()

    def update_persona_labels(self):
        if not self.personas: return
        p1 = self.personas[self.p1_idx]
        p2 = self.personas[self.p2_idx]
        
        self.query_one("#btn-p1-cycle", Button).label = f"P1: {p1['name']}"
        self.query_one("#btn-p2-cycle", Button).label = f"P2: {p2['name']}"
        self.query_one("#label-p1", Label).update(p1['name'].upper())
        self.query_one("#label-p2", Label).update(p2['name'].upper())

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-symp-back":
            self.app.pop_screen()
        elif event.button.id == "btn-p1-cycle":
            self.p1_idx = (self.p1_idx + 1) % len(self.personas)
            self.update_persona_labels()
        elif event.button.id == "btn-p2-cycle":
            self.p2_idx = (self.p2_idx + 1) % len(self.personas)
            self.update_persona_labels()
        elif event.button.id == "btn-symp-start":
            topic = self.query_one("#symp-topic", Input).value
            if not topic: topic = "Philosophy" # default
            self.start_debate_logic(topic)

    @work(thread=True)
    def start_debate_logic(self, topic: str):
        try:
            app = self.app
            # Initialize Symposium Logic
            p1 = self.personas[self.p1_idx]
            p2 = self.personas[self.p2_idx]
            
            symposium = Symposium(app.core, p1, p2, topic)
            
            # Clear previous chat
            def clear_ui():
                self.query_one("#chat-left", ScrollableContainer).remove_children()
                self.query_one("#chat-right", ScrollableContainer).remove_children()
            app.call_from_thread(clear_ui)
            
            # Run loop (e.g. 4 rounds)
            for _ in range(4):
                # Predict speaker
                if symposium.turn_count % 2 == 0:
                    s_name = p1['name']
                    side = "left"
                else:
                    s_name = p2['name']
                    side = "right"

                # Mount Loading Bubble
                async def mount_bubble(s_side, s_name):
                     container_id = "#chat-left" if s_side == "left" else "#chat-right"
                     cont = self.query_one(container_id, ScrollableContainer)
                     b = SymposiumBubble(s_name, "", s_side, is_generating=True)
                     await cont.mount(b)
                     cont.scroll_end()
                
                app.call_from_thread(mount_bubble, side, s_name)
                
                full_turn_text = ""
                first_token = True
                
                for token_obj in symposium.next_turn():
                    if token_obj['type'] == 'token':
                        content = token_obj['content']
                        full_turn_text += content
                        
                        # Update UI
                        def update_text(text, first, s_side):
                            container_id = "#chat-left" if s_side == "left" else "#chat-right"
                            cont = self.query_one(container_id, ScrollableContainer)
                            if not cont.children: return
                            bubble = cont.children[-1]
                            
                            if first:
                                # Remove by Type to avoid ID errors
                                bubble.query(LoadingIndicator).remove()
                            
                            bubble.query_one(".symp-text").update(text)
                            cont.scroll_end(animate=False)
                            
                        app.call_from_thread(update_text, full_turn_text, first_token, side)
                        first_token = False
                
                # Use `first_token` flag to check if we received anything
                if first_token:
                     # Loop finished but `first_token` is still True => No tokens yielded
                     def show_error(s_side):
                          container_id = "#chat-left" if s_side == "left" else "#chat-right"
                          cont = self.query_one(container_id, ScrollableContainer)
                          if cont.children:
                              bubble = cont.children[-1]
                              bubble.query(LoadingIndicator).remove()
                              bubble.query_one(".symp-text").update("[Error: No response from AI]")
                     app.call_from_thread(show_error, side)
                
                # Short pause between turns
                time.sleep(1)
        except Exception as e:
            logger.exception("Error in start_debate_logic")


class WhetstoneTUI(App):
    """The Whetstone Terminal App."""
    CSS_PATH = "tui.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_deep", "Toggle Deep Mode"),
        ("p", "toggle_privacy", "Toggle Privacy"),
    ]

    def on_mount(self) -> None:
        self.title = "The Whetstone"
        self.core = PhilosopherCore()
        self.scheduler = SocraticScheduler(self.core)
        
        # Register Callback for Scheduler
        self.scheduler.set_ui_callback(self.dispatch_scheduler_action)
        
        personas = self.core.get_valid_personas()
        if personas:
            self.core.set_persona(personas[0])
        
        self.push_screen(DashboardScreen())

    def dispatch_scheduler_action(self, title, message, type):
        """Bridge between background thread callback and Textual UI."""
        self.call_from_thread(self.handle_scheduler_event, title, message, type)

    def handle_scheduler_event(self, title, message, type):
        """Run on main thread to update UI."""
        if type == "dream_mode":
             # Push Modal screen
             self.push_screen(DreamModal(title, message))
        elif type == "toast":
             self.notify(message, title=title, timeout=10)
        else:
             # Audio (fallback to print/notify for now)
             self.notify(f"[AUDIO] {message}", title=title)
             
    def action_toggle_deep(self):
        new_state = not self.core.deep_mode
        self.core.set_deep_mode(new_state)
        status = "ON" if new_state else "OFF"
        self.notify(f"Deep Mode is now {status}")

    def action_toggle_privacy(self):
        # Toggle logic: If logging enabled, disable (Privacy ON). If disabled, enable (Privacy OFF).
        new_logging_state = not self.core.db.logging_enabled
        self.core.set_logging(new_logging_state)
        privacy_status = "OFF" if new_logging_state else "ON"
        self.notify(f"Privacy Mode is now {privacy_status}")

# --- Ollama Server Auto-Launch (Helper) ---
def is_ollama_running(host="127.0.0.1", port=11434):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False

def launch_ollama_server():
    print("[INFO] Ollama server not detected. Launching 'ollama serve' with 16k context window...")
    env = os.environ.copy()
    env["OLLAMA_CONTEXT_LENGTH"] = "16384"
    if sys.platform.startswith("win"):
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(["ollama", "serve"], creationflags=DETACHED_PROCESS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    else:
        subprocess.Popen(["ollama", "serve"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    
    for _ in range(30):
        if is_ollama_running():
            print("[INFO] Ollama server is now running.")
            return
        time.sleep(1)
    print("[ERROR] Ollama server did not start within 30 seconds.")

if __name__ == "__main__":
    if os.getenv("WHETSTONE_BACKEND", "ollama") == "ollama":
        if not is_ollama_running():
            launch_ollama_server()
    app = WhetstoneTUI()
    app.run()
