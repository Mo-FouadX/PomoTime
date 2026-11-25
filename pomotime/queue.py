"""
Session Queue management for PomoTime.

Multi-block session planner: build a custom sequence of focus blocks and
breaks, advance through every step automatically, and track completion.
"""

from __future__ import annotations

from typing import Optional


class SessionQueue:
    """Holds the ordered list of session blocks and the active index.

    Each block is a dict: {"kind": "focus"|"short_break"|"long_break",
                           "minutes": int, "task": str}
    """

    def __init__(self):
        self.blocks: list[dict] = []
        self.index = 0
        self.mode = False  # whether queue mode is active

    @property
    def is_empty(self) -> bool:
        return len(self.blocks) == 0

    @property
    def is_complete(self) -> bool:
        return self.index >= len(self.blocks)

    def current_block(self) -> Optional[dict]:
        if self.is_empty or self.index >= len(self.blocks):
            return None
        return self.blocks[self.index]

    def next_block(self) -> Optional[dict]:
        if self.index + 1 >= len(self.blocks):
            return None
        return self.blocks[self.index + 1]

    def add_block(self, kind: str, minutes: int, task: str = "") -> None:
        if kind not in ("focus", "short_break", "long_break"):
            kind = "focus"
        self.blocks.append(
            {"kind": kind, "minutes": max(1, min(180, int(minutes))), "task": task or ""}
        )

    def add_quick_cycle(self, focus_minutes: int, long_break_minutes: int) -> None:
        """Append 2 focus blocks followed by a long break."""
        for _ in range(2):
            self.add_block("focus", focus_minutes)
        self.add_block("long_break", long_break_minutes)

    def add_extra_cycle(self, focus_minutes: int, short_break_minutes: int) -> None:
        """Append one focus block followed by a short break."""
        self.add_block("focus", focus_minutes)
        self.add_block("short_break", short_break_minutes)

    def move_up(self, row: int) -> bool:
        if row <= 0 or row >= len(self.blocks):
            return False
        self.blocks[row - 1], self.blocks[row] = self.blocks[row], self.blocks[row - 1]
        return True

    def move_down(self, row: int) -> bool:
        if row < 0 or row >= len(self.blocks) - 1:
            return False
        self.blocks[row + 1], self.blocks[row] = self.blocks[row], self.blocks[row + 1]
        return True

    def delete_block(self, row: int) -> bool:
        if row < 0 or row >= len(self.blocks):
            return False
        del self.blocks[row]
        return True

    def clear(self) -> None:
        self.blocks = []
        self.index = 0
        self.mode = False

    def advance(self) -> None:
        """Move to the next block index."""
        self.index += 1

    def restart(self) -> None:
        """Restart the queue from the first block."""
        self.index = 0
        self.mode = bool(self.blocks)

    def load_step(self, index: int) -> Optional[dict]:
        """Load a block into the timer engine and return it."""
        if self.is_empty:
            return None
        index = max(0, min(index, len(self.blocks) - 1))
        self.index = index
        return self.blocks[index]

    def __len__(self) -> int:
        return len(self.blocks)

    def __iter__(self):
        return iter(self.blocks)
