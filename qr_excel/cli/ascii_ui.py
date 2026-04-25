"""Terminal UI styling components (Vite-style dots, ASCII art, select components)."""

from __future__ import annotations

from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style


# ASCII_LOGO = r"""
#  ░██████░   █████████              ██████████  ██      ██  ████████  ██████████  ██
# ██      ██  ██      ██             ██           ██    ██  ██      ██ ██          ██
# ██      ██  ██      ██             ██            ██  ██   ██         ██          ██
# ██      ██  █████████     ██████   ████████       ████    ██         ████████    ██
# ██      ██  ██    ██               ██            ██  ██   ██         ██          ██
# ██      ██  ██     ██              ██           ██    ██  ██      ██ ██          ██
#  ░██████░   ██      ██             ██████████  ██      ██  ████████  ██████████  █████████
#         ░█
#          ░██
# """

ASCII_LOGO = """ 
  ░██████   ░█████████                ░██████████ ░██    ░██   ░██████  ░██████████ ░██         
 ░██   ░██  ░██     ░██               ░██          ░██  ░██   ░██   ░██ ░██         ░██         
░██     ░██ ░██     ░██               ░██           ░██░██   ░██        ░██         ░██         
░██     ░██ ░█████████     ░██████    ░█████████     ░███    ░██        ░█████████  ░██         
░██     ░██ ░██   ░██                 ░██           ░██░██   ░██        ░██         ░██         
 ░██   ░██  ░██    ░██                ░██          ░██  ░██   ░██   ░██ ░██         ░██         
  ░██████   ░██     ░██               ░██████████ ░██    ░██   ░██████  ░██████████ ░██████████ 
       ░██                                                                                     
        ░██                                                                                     
""" 

BOOT_STEPS = [
    (20, "[bold yellow][LOAD][/] [white]Scanning environment variables...[/]"),
    (45, "[bold yellow][LOAD][/] [white]Initializing Excel processing engine...[/]"),
    (70, "[bold yellow][LOAD][/] [white]Loading QR generation modules...[/]"),
    (90, "[bold yellow][LOAD][/] [white]Establishing SQLite session link...[/]"),
    (100, "[bold green][OK][/]   [white]Core system safely online.[/]"),
]

def ascii_select(title: str, options: list[tuple[str, str]], default_index: int = 0) -> str:
    """
    Vite-style inline select with dot highlighter.
    Returns the value (key) of the selected option.
    options: list of (value, label) tuples
    """
    state = {"idx": default_index}

    def get_tokens() -> list[tuple[str, str]]:
        lines: list[tuple[str, str]] = []
        lines.append(("class:title", f"\n  {title}\n\n"))
        for i, (_, label) in enumerate(options):
            if i == state["idx"]:
                lines.append(("class:pointer", "  > "))
                lines.append(("class:selected", f"{label}\n"))
            else:
                lines.append(("", f"    {label}\n"))
        lines.append(("class:hint", "\n  [Up/Down/j/k to move, Enter to select]\n"))
        return lines

    kb = KeyBindings()

    @kb.add("up")
    def _up(event) -> None:
        state["idx"] = (state["idx"] - 1) % len(options)

    @kb.add("down")
    def _down(event) -> None:
        state["idx"] = (state["idx"] + 1) % len(options)

    @kb.add("k")
    def _k(event) -> None:
        state["idx"] = (state["idx"] - 1) % len(options)

    @kb.add("j")
    def _j(event) -> None:
        state["idx"] = (state["idx"] + 1) % len(options)

    @kb.add("enter")
    def _enter(event) -> None:
        event.app.exit()

    @kb.add("c-c")
    def _ctrlc(event) -> None:
        event.app.exit(exception=KeyboardInterrupt())

    layout = Layout(
        Window(content=FormattedTextControl(get_tokens, focusable=True, show_cursor=False))
    )
    style = Style.from_dict({
        'title': 'bold ansicyan',
        'pointer': 'bold ansigreen',
        'selected': 'bold',
        'hint': 'ansigray',
    })
    application = Application(layout=layout, key_bindings=kb, full_screen=False, style=style)
    application.run()
    return options[state["idx"]][0]
