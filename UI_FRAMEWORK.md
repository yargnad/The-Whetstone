# UI Framework Specification

**Component Status:** 📋 Specification Phase  
**Target Platform:** E-ink display on Radxa Rock 5B+  
**Purpose:** Define user interface states, transitions, and visual design for The Whetstone

---

## Overview

The Whetstone's UI is designed for an e-ink display with the following constraints and principles:

**Design Constraints:**
- Grayscale only (typically 2-bit or 4-bit)
- Slow refresh rate (1-2 seconds full, 200-500ms partial)
- Limited resolution (likely 400x300 or 800x480 pixels)
- No touch input (button navigation only)

**Design Principles:**
- **Text-first** - Reading experience is primary use case
- **Minimal transitions** - Avoid unnecessary screen changes (save refresh budget)
- **Clear state** - User should always know what mode they're in
- **Graceful degradation** - Long text wraps/scrolls rather than truncating

---

## UI State Machine

### States and Transitions

```
                     ┌─────────────────┐
                     │   BOOT SCREEN   │
                     │ (splash screen)  │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ PERSONA SELECT  │◄──────┐
                     │  (main menu)     │       │
                     └────────┬─────────┘       │
                              │                 │
                    SELECT pressed              │
                              │                 │
                              ▼                 │
                     ┌─────────────────┐        │
                     │  CONVERSATION   │        │
                     │   (main mode)    │        │
                     └────────┬─────────┘        │
                              │                 │
                    LEFT pressed (back)         │
                              │                 │
                              └─────────────────┘
                              
                              
    CONVERSATION mode can enter sub-states:
    
    ┌─────────────────┐
    │  CONVERSATION   │
    └────────┬─────────┘
             │
             ├──► [LISTENING] (PTT held)
             │
             ├──► [THINKING] (AI processing)
             │
             ├──► [SPEAKING] (TTS playing)
             │
             └──► [POWER MENU] (SELECT long press)
```

---

## Screen Layouts

### 1. Boot Screen (Splash)

**Purpose:** Display during system initialization (1-2 seconds)

**Layout:**
```
┌────────────────────────────────────┐
│                                    │
│                                    │
│          THE WHETSTONE             │
│                                    │
│        Learning to think again     │
│                                    │
│           Initializing...          │
│                                    │
│                                    │
└────────────────────────────────────┘
```

**Components:**
- **Title:** Large, centered text ("THE WHETSTONE")
- **Tagline:** Smaller, centered text ("Learning to think again")
- **Status:** Loading message ("Initializing...")

**Rendering:**
- Full refresh on boot (acceptable delay)
- Remains on screen until system ready (~2-5 seconds)

---

### 2. Persona Selection Screen

**Purpose:** Allow user to choose philosophical persona for the session

**Layout (4.2" display, ~400x300px):**
```
┌────────────────────────────────────┐
│  THE WHETSTONE                     │
│  Select Your Interlocutor:         │
│                                    │
│  ┌────────────────────────────┐   │
│  │ Benevolent Absurdist       │   │
│  └────────────────────────────┘   │
│                                    │
│  ► Socratic Inquirer               │
│                                    │
│    Stoic Guide                     │
│                                    │
│    Plato                           │
│                                    │
│    Nietzsche                       │
│                                    │
│  UP/DOWN to select, SELECT to begin│
└────────────────────────────────────┘
```

**Layout (7.5" display, ~800x480px):**
```
┌──────────────────────────────────────────────────────────┐
│  THE WHETSTONE                                           │
│  Select Your Philosophical Interlocutor:                 │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Benevolent Absurdist                             │   │
│  │ Empathy, reason, and existential acceptance      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ► Socratic Inquirer                                     │
│    Rigorous questioning for definitional clarity         │
│                                                          │
│    Stoic Guide                                           │
│    Dichotomy of control, virtue ethics                   │
│                                                          │
│    Plato                                                 │
│    Direct dialogue as Plato would speak                  │
│                                                          │
│    Nietzsche                                             │
│    Provocative, aphoristic challenges                    │
│                                                          │
│  UP/DOWN to navigate  •  SELECT to begin  •  Hold SELECT for settings │
└──────────────────────────────────────────────────────────┘
```

**Components:**
- **Header:** "THE WHETSTONE" (static)
- **Subheader:** "Select Your Interlocutor" (static)
- **Persona List:** 
  - Each persona on separate line
  - Selected persona highlighted with `►` or inverted background
  - Optional: Brief description (1 line) for each persona
- **Footer:** Button hints (static)

**Interactions:**
- **UP button:** Move selection up (wrap to bottom if at top)
- **DOWN button:** Move selection down (wrap to top if at bottom)
- **SELECT button:** Confirm selection, transition to Conversation screen

**Rendering Strategy:**
- Initial render: Full refresh
- Selection change: Partial refresh (highlight + arrow only)
- After 5 selections: Full refresh to clear ghosting

---

### 3. Conversation Screen (Main Mode)

**Purpose:** Display ongoing philosophical dialogue

**Layout (4.2" display, ~400x300px):**
```
┌────────────────────────────────────┐
│ Socratic Inquirer          [12:34] │
├────────────────────────────────────┤
│ You: What is justice?              │
│                                    │
│ AI: Before we can explore justice, │
│ we must first clarify what you     │
│ mean. When you say "justice," do   │
│ you refer to a quality within an   │
│ individual, or to the proper       │
│ ordering of a society?             │
│                                    │
│ You: I mean justice in society.    │
│                                    │
│ AI: Very well. And when you speak  │
│ of the "proper" ordering of        │
│ society, by what standard do you   │
│ judge what is proper?              │
│                                    │
│ [▲▼ Scroll • LEFT Back • PTT Talk] │
└────────────────────────────────────┘
```

**Layout (7.5" display, ~800x480px):**
```
┌──────────────────────────────────────────────────────────────────┐
│ Socratic Inquirer                                  Session: 14:27 │
├──────────────────────────────────────────────────────────────────┤
│ You: What is justice?                                            │
│                                                                  │
│ AI: Before we can explore the nature of justice, we must first  │
│ clarify what you mean by the term. When you say "justice," do   │
│ you refer to a quality or virtue that exists within an           │
│ individual person, or are you speaking of the proper ordering    │
│ and governance of a society as a whole?                          │
│                                                                  │
│ You: I mean justice in society—how a society should be organized.│
│                                                                  │
│ AI: Very well. And when you speak of the "proper" ordering of    │
│ a society, by what standard do you judge what is proper? Do you  │
│ appeal to convention, to nature, to divine command, or to some   │
│ other criterion?                                                 │
│                                                                  │
│ You: I think justice is whatever benefits the most people.       │
│                                                                  │
│ AI: Ah, so you invoke a kind of utilitarianism. But tell me:     │
│ if benefiting the most people is the measure of justice, would   │
│ it be just to enslave a minority if doing so brought great       │
│ happiness to the majority?                                       │
│                                                                  │
│                                                                  │
│ [▲▼ Scroll • ◀ Back to Menu • PTT Hold to Speak • SELECT Settings]│
└──────────────────────────────────────────────────────────────────┘
```

**Components:**
- **Header:** 
  - Persona name (left-aligned)
  - Session time or message count (right-aligned, optional)
  - Separator line
- **Conversation Area:**
  - Alternating "You:" and "AI:" messages
  - Word-wrapped text
  - Scrollable (UP/DOWN buttons)
  - Auto-scroll to bottom when new message arrives
- **Footer:**
  - Button hints (static or context-aware)

**Rendering Strategy:**
- **New message arrives:** Partial refresh (conversation area only)
- **Scroll:** Partial refresh (shift viewport)
- **Full refresh:** Every 15 messages or when returning from sleep

---

### 4. Listening State (Voice Input Active)

**Purpose:** Visual feedback that system is recording voice

**Layout:**
```
┌────────────────────────────────────┐
│ Socratic Inquirer          [12:34] │
├────────────────────────────────────┤
│ You: What is justice?              │
│                                    │
│ AI: Before we can explore justice, │
│ we must first clarify...           │
│                                    │
│                                    │
│         ╔═══════════════╗          │
│         ║   LISTENING   ║          │
│         ║      🎤       ║          │
│         ║   ● ● ● ● ●   ║          │
│         ╚═══════════════╝          │
│                                    │
│                                    │
│ Release PTT to send                │
└────────────────────────────────────┘
```

**Components:**
- **Overlay box:** Centered, draws attention
- **Microphone icon:** Visual indicator (or text "🎤" if no icon support)
- **Audio level indicator:** 5 dots that fill based on input volume (optional, may be too complex for e-ink)
- **Instruction:** "Release PTT to send"

**Rendering:**
- **PTT pressed:** Partial refresh to show overlay
- **PTT released:** Partial refresh to remove overlay, show "Thinking..."

**Alternative (Simpler):**
If overlay is too complex for e-ink refresh rates, use footer status instead:
```
│ [LISTENING... Release PTT to send] │
```

---

### 5. Thinking State (AI Processing)

**Purpose:** Indicate that AI is processing user's query

**Layout:**
```
┌────────────────────────────────────┐
│ Socratic Inquirer          [12:34] │
├────────────────────────────────────┤
│ You: I think justice is whatever   │
│ benefits the most people.          │
│                                    │
│                                    │
│         ╔═══════════════╗          │
│         ║   THINKING    ║          │
│         ║      ⚙        ║          │
│         ║   • • • • •   ║          │
│         ╚═══════════════╝          │
│                                    │
│                                    │
│ Formulating response...            │
└────────────────────────────────────┘
```

**Components:**
- **Overlay box:** "THINKING" label
- **Gear icon or dots:** Static (no animation due to e-ink refresh limits)
- **Status text:** "Formulating response..."

**Rendering:**
- **Triggered by:** Voice input complete OR text query submitted
- **Duration:** Remains until AI response ready (~2-10 seconds)
- **Refresh:** Single partial refresh to display, single to remove

---

### 6. Speaking State (TTS Playing)

**Purpose:** Indicate that AI is speaking response aloud

**Layout:**
```
┌────────────────────────────────────┐
│ Socratic Inquirer          [12:34] │
├────────────────────────────────────┤
│ You: I think justice is whatever   │
│ benefits the most people.          │
│                                    │
│ AI: Ah, so you invoke a kind of    │
│ utilitarianism. But tell me: if    │
│ benefiting the most people is the  │
│ measure of justice, would it be    │
│ just to enslave a minority if      │
│ doing so brought great happiness   │
│ to the majority?                   │
│                                    │
│                                    │
│ [🔊 Speaking... UP/DOWN for volume]│
└────────────────────────────────────┘
```

**Components:**
- **Conversation area:** Shows AI's full response text (scrollable)
- **Footer status:** "🔊 Speaking..." + volume hint

**Interactions:**
- **UP button:** Volume up
- **DOWN button:** Volume down
- **LEFT button:** Cancel/stop playback
- **Text displays:** Even while speaking (user can read along)

**Rendering:**
- **TTS starts:** Partial refresh to show text + update footer
- **TTS completes:** Partial refresh to clear status

---

### 7. Power Menu

**Purpose:** Allow user to sleep or shutdown device

**Layout:**
```
┌────────────────────────────────────┐
│                                    │
│                                    │
│         ╔═══════════════╗          │
│         ║  POWER MENU   ║          │
│         ╠═══════════════╣          │
│         ║ ► Sleep       ║          │
│         ║   Shutdown    ║          │
│         ║   Cancel      ║          │
│         ╚═══════════════╝          │
│                                    │
│ UP/DOWN select  •  SELECT confirm  │
│                                    │
└────────────────────────────────────┘
```

**Components:**
- **Overlay menu:** Centered modal
- **Options:**
  - **Sleep:** Enter low-power mode (wake on button press)
  - **Shutdown:** Full system shutdown
  - **Cancel:** Return to conversation
- **Instructions:** Footer hints

**Interactions:**
- **UP/DOWN:** Navigate options
- **SELECT:** Confirm selection
- **LEFT:** Cancel (same as selecting "Cancel")

**Rendering:**
- **Triggered by:** SELECT long press (> 1 second)
- **Refresh:** Full refresh (modal overlay requires clear background)

---

## Typography Specifications

### Font Selection

**Primary Font:** DejaVu Sans Mono (monospace, open-source, highly readable)

**Font Sizes (4.2" display, 400x300px):**
- **Header (Persona name):** 14pt Bold
- **Body (Conversation text):** 11pt Regular
- **Footer (Button hints):** 9pt Regular
- **Overlay titles ("LISTENING"):** 16pt Bold

**Font Sizes (7.5" display, 800x480px):**
- **Header:** 18pt Bold
- **Body:** 13pt Regular
- **Footer:** 11pt Regular
- **Overlay titles:** 20pt Bold

**Line Spacing:**
- 1.2x font size (e.g., 11pt font → 13px line height)

---

### Text Wrapping Rules

1. **Word boundaries:** Break lines at spaces, not mid-word
2. **Hyphenation:** Not implemented (adds complexity)
3. **Long words:** If single word exceeds line width, force break (rare case)
4. **Indentation:** None (flush left for all text)

**Example Text Wrap (40 characters/line):**
```
AI: Before we can explore the nature
of justice, we must first clarify
what you mean by the term.
```

---

## Color Palette (Grayscale)

**4-bit Grayscale (16 levels):**
- **0 (Black):** Primary text
- **15 (White):** Background
- **8 (Mid-gray):** Separator lines
- **12 (Light gray):** Footer hints, timestamps
- **3 (Dark gray):** Overlay box borders

**2-bit Grayscale (4 levels - fallback):**
- **0 (Black):** All text
- **3 (White):** Background
- **1 (Dark gray):** Separator lines
- **2 (Light gray):** Highlights, less important text

**Note:** Actual grayscale support depends on e-ink display model. Optimize after hardware testing.

---

## Accessibility Considerations

### High Contrast Mode (Future Enhancement)
- Option to disable gray tones (pure black on white)
- Larger font sizes (e.g., 14pt body text instead of 11pt)

### Screen Reader Support (Future Enhancement)
- TTS can read all on-screen text aloud
- Audio feedback for button presses ("Button: UP")

### Low Vision Adaptations
- Minimum font size: 11pt (tested for readability at arm's length)
- Clear spacing between UI elements (minimum 10px padding)

---

## Error States

### 1. Voice Input Error

**Trigger:** Whisper STT fails to transcribe, or no audio detected

**Display:**
```
┌────────────────────────────────────┐
│         ╔═══════════════╗          │
│         ║   ⚠ ERROR     ║          │
│         ╠═══════════════╣          │
│         ║ Could not     ║          │
│         ║ understand    ║          │
│         ║ audio input   ║          │
│         ╚═══════════════╝          │
│                                    │
│ Press PTT to try again             │
└────────────────────────────────────┘
```

**Recovery:** Auto-dismiss after 3 seconds, or on button press

---

### 2. AI Response Error

**Trigger:** Ollama fails to generate response (model crash, timeout, etc.)

**Display:**
```
┌────────────────────────────────────┐
│ Socratic Inquirer          [12:34] │
├────────────────────────────────────┤
│ You: I think justice is whatever   │
│ benefits the most people.          │
│                                    │
│ [Error: AI failed to respond.      │
│  Please try rephrasing your        │
│  question.]                        │
│                                    │
│ Press PTT to retry                 │
└────────────────────────────────────┘
```

**Recovery:** User can retry input, or press LEFT to return to persona selection

---

### 3. Low Battery Warning (Future)

**Trigger:** Battery level < 15%

**Display:**
```
│ [⚠ Low Battery: 12% remaining]     │
```

**Placement:** Footer status area

---

## Animation Constraints

**E-ink displays cannot smoothly animate.** Any "animation" must be achieved through:

1. **Static frames:** Display different static images in sequence (e.g., dots: `•  ` → `• •` → `• • •`)
2. **Slow transitions:** Acceptable delay of 200-500ms between frames (partial refresh)
3. **Minimal use:** Animations reserved for critical feedback (e.g., "LISTENING" state)

**Recommendation:** Avoid animation entirely. Use static indicators for all states.

---

## Development Roadmap

### Phase 1: Static Layouts ✅ Target
- [ ] Design persona selection screen mockup
- [ ] Design conversation screen mockup
- [ ] Choose fonts and test readability on target display
- [ ] Create PIL-based rendering functions for each layout

### Phase 2: State Transitions
- [ ] Implement state machine (enum + transition logic)
- [ ] Test screen transitions (persona select → conversation)
- [ ] Verify partial refresh works for state changes

### Phase 3: Dynamic Content
- [ ] Implement scrollable conversation buffer
- [ ] Test word wrapping algorithm
- [ ] Add timestamp/session info to header

### Phase 4: Overlays & Modals
- [ ] Implement "LISTENING" overlay
- [ ] Implement "THINKING" overlay
- [ ] Implement power menu modal

### Phase 5: Error Handling
- [ ] Add error state screens
- [ ] Test recovery workflows
- [ ] Add timeout logic (e.g., "THINKING" state max 30s)

---

## Testing Checklist

### Visual Tests
- [ ] All text readable at arm's length (typical reading distance)
- [ ] No text truncation (all wraps correctly)
- [ ] Separator lines visible but not distracting
- [ ] Overlays clearly distinct from background content

### Functional Tests
- [ ] Persona selection highlights correctly
- [ ] Conversation scrolls smoothly (no jumps or artifacts)
- [ ] Status changes (LISTENING → THINKING → SPEAKING) display correctly
- [ ] Power menu appears on SELECT long press

### Rendering Tests
- [ ] Partial refresh doesn't cause excessive ghosting
- [ ] Full refresh clears all artifacts
- [ ] Transition from persona select → conversation is smooth (< 2s)

---

## Resources

### Design Tools
- **Mockups:** Figma, Inkscape, or simple ASCII art (this document)
- **Font preview:** https://www.programmingfonts.org/
- **Grayscale simulator:** ImageMagick `convert -colorspace Gray` to preview designs

### Inspiration
- **Remarkable 2 tablet UI** (excellent e-ink UX reference)
- **Kindle interface** (proven text-first design)
- **Terminal UIs** (ncurses, vim) for button-based navigation patterns

---

## Notes for Future Improvement

**After Phase 1:**
- Take photos of actual display with rendered screens
- Adjust font sizes based on real-world readability
- Document optimal line length (characters per line)

**After Phase 3:**
- Consider adding "breadcrumbs" (e.g., "Message 5 of 12" in footer)
- Explore highlighting key terms (e.g., philosophical concepts in bold)

**After Phase 5:**
- Add battery indicator to header (if battery-powered build)
- Consider "night mode" (inverted colors: white text on black background)

---

**Last Updated:** November 9, 2025  
**Status:** Specification complete, awaiting display hardware  
**Next Steps:** Create mockup images, test font rendering with PIL
