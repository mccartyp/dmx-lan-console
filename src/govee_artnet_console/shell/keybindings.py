"""Key bindings configuration for the Govee ArtNet shell.

This module handles all keyboard shortcuts and key bindings for the
interactive shell interface.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings

if TYPE_CHECKING:
    from .core import GoveeShell


class KeyBindingManager:
    """Manages key bindings for the shell."""

    def __init__(self, shell: GoveeShell):
        """
        Initialize the key binding manager.

        Args:
            shell: Reference to the GoveeShell instance
        """
        self.shell = shell

    def create_key_bindings(self) -> KeyBindings:
        """
        Create and configure all key bindings for the shell.

        Returns:
            Configured KeyBindings instance
        """
        kb = KeyBindings()

        # Basic shell keybindings
        @kb.add('c-c')
        def _(event):
            """Handle Ctrl+C - clear input or show message."""
            if self.shell.input_buffer.text:
                self.shell.input_buffer.reset()
            else:
                self.shell._append_output("\n[yellow]Use 'exit' or Ctrl+D to quit.[/]\n")

        @kb.add('c-d')
        def _(event):
            """Handle Ctrl+D - exit shell."""
            event.app.exit(result=True)

        @kb.add('c-l')
        def _(event):
            """Handle Ctrl+L - clear screen."""
            self.shell.output_buffer.set_document(Document(""), bypass_readonly=True)
            event.app.invalidate()

        @kb.add('c-t')
        def _(event):
            """Handle Ctrl+T - toggle follow-tail mode."""
            self.shell.follow_tail = not self.shell.follow_tail
            status = "enabled" if self.shell.follow_tail else "disabled"
            self.shell._append_output(f"\n[dim]Follow-tail {status}[/]\n")

        @kb.add('pageup')
        def _(event):
            """Handle Page Up - scroll output and disable follow-tail."""
            # Disable follow-tail when manually scrolling
            self.shell.follow_tail = False
            # Scroll output buffer up by one page
            rows = event.app.output.get_size().rows - 4  # Account for input and toolbar
            new_pos = max(0, self.shell.output_buffer.cursor_position - rows * 80)  # Approximate line length
            self.shell.output_buffer.cursor_position = new_pos
            event.app.invalidate()

        @kb.add('pagedown')
        def _(event):
            """Handle Page Down - scroll output down."""
            # Scroll output buffer down by one page
            rows = event.app.output.get_size().rows - 4  # Account for input and toolbar
            new_pos = min(len(self.shell.output_buffer.text), self.shell.output_buffer.cursor_position + rows * 80)
            self.shell.output_buffer.cursor_position = new_pos
            # If we're at the bottom, re-enable follow-tail
            if self.shell.output_buffer.cursor_position >= len(self.shell.output_buffer.text) - 10:
                self.shell.follow_tail = True
            event.app.invalidate()

        # Log tail mode keybindings
        @kb.add('escape', filter=Condition(lambda: self.shell.in_log_tail_mode))
        def _(event):
            """Handle Escape in log tail mode - exit to normal view."""
            asyncio.create_task(self.shell._exit_log_tail_mode())

        @kb.add('q', filter=Condition(lambda: self.shell.in_log_tail_mode))
        def _(event):
            """Handle 'q' in log tail mode - exit to normal view."""
            asyncio.create_task(self.shell._exit_log_tail_mode())

        @kb.add('end', filter=Condition(lambda: self.shell.in_log_tail_mode))
        def _(event):
            """Handle End in log tail mode - jump to bottom and enable follow-tail."""
            if self.shell.log_tail_controller:
                self.shell.log_tail_controller.enable_follow_tail()
                event.app.invalidate()

        @kb.add('f', filter=Condition(lambda: self.shell.in_log_tail_mode))
        def _(event):
            """Handle 'f' in log tail mode - open filter prompt."""
            # For now, show a message (we can implement a filter input dialog later)
            self.shell.log_tail_buffer.insert_text(
                "\033[33m[Filter UI not yet implemented - use 'logs tail --level LEVEL --logger LOGGER' to set filters]\033[0m\n"
            )
            event.app.invalidate()

        # Watch mode keybindings
        @kb.add('escape', filter=Condition(lambda: self.shell.in_watch_mode))
        def _(event):
            """Handle Escape in watch mode - exit to normal view."""
            asyncio.create_task(self.shell._exit_watch_mode())

        @kb.add('q', filter=Condition(lambda: self.shell.in_watch_mode))
        def _(event):
            """Handle 'q' in watch mode - exit to normal view."""
            asyncio.create_task(self.shell._exit_watch_mode())

        @kb.add('+', filter=Condition(lambda: self.shell.in_watch_mode))
        def _(event):
            """Handle '+' in watch mode - decrease refresh interval (faster)."""
            if self.shell.watch_controller:
                new_interval = max(0.5, self.shell.watch_controller.refresh_interval - 0.5)
                self.shell.watch_controller.set_interval(new_interval)
                event.app.invalidate()

        @kb.add('-', filter=Condition(lambda: self.shell.in_watch_mode))
        def _(event):
            """Handle '-' in watch mode - increase refresh interval (slower)."""
            if self.shell.watch_controller:
                new_interval = self.shell.watch_controller.refresh_interval + 0.5
                self.shell.watch_controller.set_interval(new_interval)
                event.app.invalidate()

        # Log view mode keybindings
        @kb.add('escape', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle Escape in log view mode - exit to normal view."""
            asyncio.create_task(self.shell._exit_log_view_mode())

        @kb.add('q', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle 'q' in log view mode - exit to normal view."""
            asyncio.create_task(self.shell._exit_log_view_mode())

        @kb.add('pageup', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle Page Up in log view mode - previous page."""
            if self.shell.log_view_controller:
                self.shell.log_view_controller.navigate_page("prev")
                asyncio.create_task(self.shell.log_view_controller.refresh())

        @kb.add('pagedown', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle Page Down in log view mode - next page."""
            if self.shell.log_view_controller:
                self.shell.log_view_controller.navigate_page("next")
                asyncio.create_task(self.shell.log_view_controller.refresh())

        @kb.add('home', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle Home in log view mode - first page."""
            if self.shell.log_view_controller:
                self.shell.log_view_controller.navigate_page("first")
                asyncio.create_task(self.shell.log_view_controller.refresh())

        @kb.add('end', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle End in log view mode - last page."""
            if self.shell.log_view_controller:
                self.shell.log_view_controller.navigate_page("last")
                asyncio.create_task(self.shell.log_view_controller.refresh())

        @kb.add('l', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle 'l' in log view mode - cycle log level filter."""
            if self.shell.log_view_controller:
                self.shell.log_view_controller.cycle_level_filter()
                asyncio.create_task(self.shell.log_view_controller.refresh())

        @kb.add('c', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle 'c' in log view mode - clear logger filter."""
            if self.shell.log_view_controller:
                self.shell.log_view_controller.set_logger_filter(None)
                asyncio.create_task(self.shell.log_view_controller.refresh())

        @kb.add('r', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle 'r' in log view mode - manual refresh."""
            if self.shell.log_view_controller:
                asyncio.create_task(self.shell.log_view_controller.refresh())

        @kb.add('space', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle Space in log view mode - toggle follow mode."""
            if self.shell.log_view_controller:
                self.shell.log_view_controller.toggle_follow_mode()
                asyncio.create_task(self.shell.log_view_controller.refresh())

        @kb.add('f', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle 'f' in log view mode - set logger filter (modal prompt)."""
            # TODO: Implement modal input dialog for logger filter
            # For now, show placeholder message
            pass

        @kb.add('/', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle '/' in log view mode - edit search pattern (modal prompt)."""
            # TODO: Implement modal input dialog for search pattern
            # For now, show placeholder message
            pass

        @kb.add('?', filter=Condition(lambda: self.shell.in_log_view_mode))
        def _(event):
            """Handle '?' in log view mode - show help modal."""
            # TODO: Implement help modal
            # For now, show placeholder message
            pass

        return kb
