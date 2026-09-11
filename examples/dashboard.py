"""Timers, background threads and a scrolling log.

Run with: uv run examples/dashboard.py
"""

import random
import threading
import time

from pytui import App, Box, Checkbox, ProgressBar, Row, Text


def main() -> None:
    clock = Text("", text_align="right", flex_grow=1)
    cpu = ProgressBar(flex_grow=1)
    memory = ProgressBar(flex_grow=1, fg="yellow")
    paused = Checkbox("Pause log")
    log = Box(overflow="scroll", flex_grow=1, border="single", title="log", focusable=True)

    root = Box(
        Row(Text("dashboard", bold=True), clock, padding=(0, 1), bg="blue", fg="bright_white"),
        Row(Text("cpu", width=4), cpu, gap=1, padding=(0, 1)),
        Row(Text("mem", width=4), memory, gap=1, padding=(0, 1)),
        Row(paused, padding=(0, 1)),
        log,
        Text(
            "Focus the log and use arrows/PageUp/PageDown, or the mouse wheel. Ctrl+C quits.",
            dim=True,
            padding=(0, 1),
        ),
    )
    app = App(root)

    def tick() -> None:
        clock.text = time.strftime("%H:%M:%S")
        cpu.value = random.random()
        memory.value = (memory.value + 0.02) % 1

    def add_line(line: str) -> None:
        if paused.checked:
            return
        follow = log.scroll_y >= log.max_scroll_y
        log.mount(Text(line))
        if len(log.children) > 500:
            log.children[0].remove()
        if follow:
            log.scroll_y = log.virtual_height + 1  # clamped to the bottom on next layout

    def worker() -> None:
        count = 0
        while True:
            time.sleep(random.uniform(0.1, 0.8))
            count += 1
            app.call_from_thread(add_line, f"{time.strftime('%H:%M:%S')}  event #{count}")

    tick()
    app.set_interval(0.5, tick)
    threading.Thread(target=worker, daemon=True).start()
    app.run()


if __name__ == "__main__":
    main()
