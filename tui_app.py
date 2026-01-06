from textual.app import App, ComposeResult
from textual import work
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Input, Button, Label, ListView, ListItem, Switch, LoadingIndicator
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
    def __init__(self, sender: str, text: str, is_user: bool = False, loading: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = sender
        self.text_content = text
        self.is_user = is_user
        self.loading = loading

    def compose(self) -> ComposeResult:
        yield Label(f"[{self.sender}]", classes="sender-label")
        yield Label(self.text_content, classes="message-text")
        if self.loading:
            yield LoadingIndicator(id="msg-loader", classes="compact-loader")

    def on_mount(self) -> None:
        if self.is_user:
            self.add_class("user-message")
        else:
            self.add_class("ai-message")

class SymposiumBubble(Vertical):
    """A symposium debate bubble."""
    def __init__(self, sender: str, text: str, side: str = "left", loading: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = sender
        self.text_content = text
        self.side = side
        self.loading = loading

    def compose(self) -> ComposeResult:
        yield Label(f"[{self.sender}]", classes="symp-sender")
        yield Label(self.text_content, classes="symp-text")
        if self.loading:
            yield LoadingIndicator(id="symp-loader", classes="compact-loader")

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
        
        # 2. Mount AI Bubble with Loading Indicator
        ai_bubble = ChatBubble(self.app.core.current_persona['name'], "", is_user=False, loading=True)
        await history.mount(ai_bubble)
        history.scroll_end(animate=False)

        # 3. Start Background Worker
        self.generate_ai_response(text, ai_bubble)

    @work(exclusive=True, thread=True)
    def generate_ai_response(self, user_text: str, ai_bubble: ChatBubble):
        app = self.app
        full_response = ""
        first_token = True
        
        # Stream response
        for token in app.core.chat(user_text):
            full_response += token
            
            # Helper to update UI
            def update_ui(first, text):
                if first:
                    try:
                        ai_bubble.query(LoadingIndicator).remove()
                    except: pass
                ai_bubble.query_one(".message-text").update(text)
                self.query_one("#chat-history", ScrollableContainer).scroll_end(animate=False)
            
            # Schedule update on main thread
            app.call_from_thread(update_ui, first_token, full_response)
            first_token = False

        if first_token:
             # No tokens received
             def show_error():
                 try: ai_bubble.query_one("#msg-loader").remove()
                 except: pass
                 ai_bubble.query_one(".message-text").update("[Error: No response from AI]")
             app.call_from_thread(show_error)

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
            def mount_bubble(s_side, s_name):
                 container_id = "#chat-left" if s_side == "left" else "#chat-right"
                 cont = self.query_one(container_id, ScrollableContainer)
                 b = SymposiumBubble(s_name, "", s_side, loading=True)
                 cont.mount(b)
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
                            try: bubble.query_one("#symp-loader").remove()
                            except: pass
                        
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
                          try: bubble.query_one("#symp-loader").remove()
                          except: pass
                          bubble.query_one(".symp-text").update("[Error: No response from AI]")
                 app.call_from_thread(show_error, side)
            
            # Short pause between turns
            time.sleep(1)


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
