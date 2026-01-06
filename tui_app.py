from textual.app import App, ComposeResult
from textual import work
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Input, Button, Label, ListView, ListItem, Switch
from textual.screen import Screen
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

# Import core Whetstone modules
from core import PhilosopherCore
from symposium import Symposium
from scheduler_service import SocraticScheduler

# --- Widgets ---

class ChatBubble(Vertical):
    """A single chat message bubble."""
    def __init__(self, sender: str, text: str, is_user: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = sender
        self.text_content = text
        self.is_user = is_user

    def compose(self) -> ComposeResult:
        yield Label(f"[{self.sender}]", classes="sender-label")
        yield Label(self.text_content, classes="message-text")

    def on_mount(self) -> None:
        if self.is_user:
            self.add_class("user-message")
        else:
            self.add_class("ai-message")

class SymposiumBubble(Vertical):
    """A symposium debate bubble."""
    def __init__(self, sender: str, text: str, side: str = "left", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = sender
        self.text_content = text
        self.side = side

    def compose(self) -> ComposeResult:
        yield Label(f"[{self.sender}]", classes="symp-sender")
        yield Label(self.text_content, classes="symp-text")

    def on_mount(self) -> None:
        self.add_class(f"symp-{self.side}")

# --- Screens ---

class DashboardScreen(Screen):
    """Main Chat Interface."""
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="app-grid"):
            with Vertical(id="sidebar"):
                yield Label("THE WHETSTONE", id="logo")
                yield Label("Personas", classes="section-title")
                yield ListView(id="persona-list")
                yield Label("Settings", classes="section-title")
                with Horizontal(classes="setting-row"):
                    yield Label("Deep Mode")
                    yield Switch(id="sw-deep")
                with Horizontal(classes="setting-row"):
                    yield Label("Privacy")
                    yield Switch(id="sw-privacy")
                yield Button("Scheduler: OFF", id="btn-scheduler", variant="warning")
                yield Button("Start Symposium", id="btn-goto-symposium", variant="primary")
            
            with Vertical(id="main-chat-area"):
                yield ScrollableContainer(id="chat-history")
                with Horizontal(id="input-bar"):
                    yield Input(placeholder="Type your message...", id="chat-input")
                    yield Button("Send", id="btn-send", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        # Populate Persona List
        list_view = self.query_one("#persona-list", ListView)
        personas = self.app.core.get_valid_personas()
        for p in personas:
            list_view.append(ListItem(Label(p['name']), name=p['name']))

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        await self.process_user_message(message.value)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-send":
            inp = self.query_one("#chat-input", Input)
            await self.process_user_message(inp.value)
        elif event.button.id == "btn-goto-symposium":
            self.app.push_screen(SymposiumScreen())

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle persona selection from sidebar."""
        # Find the persona by name
        # We assigned the name to the ListItem when creating it
        name = event.item.name
        if not name:
            # Fallback for safety
            label = event.item.query_one(Label)
            name = str(label.renderable) if hasattr(label, 'renderable') else str(label)
        for p in self.app.core.get_valid_personas():
            if p['name'] == name:
                self.app.core.set_persona(p)
                # Show feedback (optional, maybe in input placeholder or a toast)
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
        
        # 1. Mount User Bubble
        await history.mount(ChatBubble("You", text, is_user=True))
        
        # 2. Mount AI Bubble (Empty placeholder)
        ai_bubble = ChatBubble(self.app.core.current_persona['name'], "...", is_user=False)
        await history.mount(ai_bubble)
        history.scroll_end(animate=False)

        # 3. Start Background Worker
        self.generate_ai_response(text, ai_bubble)

    @work(exclusive=True, thread=True)
    def generate_ai_response(self, user_text: str, ai_bubble: ChatBubble):
        app = self.app
        full_response = ""
        
        # Stream response
        for token in app.core.chat(user_text):
            full_response += token
            
            # Define update callback
            def update_ui():
                ai_bubble.query_one(".message-text").update(full_response)
                self.query_one("#chat-history", ScrollableContainer).scroll_end(animate=False)
            
            # Schedule update on main thread
            app.call_from_thread(update_ui)

class SymposiumScreen(Screen):
    """Split Screen Debate."""
    
    BINDINGS = [("escape", "app.pop_screen", "Back to Chat")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="symp-container"):
            yield Label("Select two philosophers from Dashboard to begin (Mockup: Defaulting to Plato vs Nietzsche)", id="symp-status")
             # Split View
            with Horizontal(id="debate-stage"):
                with Vertical(id="stage-left", classes="stage-col"):
                    yield Label("PLATO", classes="stage-name")
                    yield ScrollableContainer(id="chat-left")
                with Vertical(id="stage-right", classes="stage-col"):
                    yield Label("NIETZSCHE", classes="stage-name")
                    yield ScrollableContainer(id="chat-right")
            
            with Horizontal(id="symp-controls"):
                yield Button("Start Round", id="btn-symp-start")
                yield Button("Interject", id="btn-symp-interject")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-symp-start":
            self.run_worker(self.run_demo_round(), thread=True)

    def run_demo_round(self):
        # This is a stub to demonstrate the UI capabilities
        # In real impl, this would call symposium.next_turn()
        
        # P1 Speaks
        self.app.call_from_thread(self.add_bubble, "Plato", "Justice is the harmony of the soul.", "left")
        time.sleep(1)
        
        # P2 Speaks
        self.app.call_from_thread(self.add_bubble, "Nietzsche", "Harmony? Or merely the suppression of the dangerous passions?", "right")

    def add_bubble(self, sender, text, side):
        container_id = "#chat-left" if side == "left" else "#chat-right"
        container = self.query_one(container_id, ScrollableContainer)
        container.mount(SymposiumBubble(sender, text, side))
        container.scroll_end()


class WhetstoneTUI(App):
    """The Whetstone Terminal App."""
    CSS_PATH = "tui.css"
    BINDINGS = [("q", "quit", "Quit")]

    def on_mount(self) -> None:
        self.title = "The Whetstone"
        # Init Core
        self.core = PhilosopherCore()
        
        # Set default persona so it's not None on start
        personas = self.core.get_valid_personas()
        if personas:
            self.core.set_persona(personas[0])
        
        # Push Main Screen
        self.push_screen(DashboardScreen())

if __name__ == "__main__":
    app = WhetstoneTUI()
    app.run()
