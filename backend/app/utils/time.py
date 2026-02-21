from __future__ import annotations


def seconds_to_game_clock(seconds: int) -> str:
    """Convert seconds remaining in a quarter to MM:SS display string."""
    minutes, secs = divmod(max(0, seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


def game_clock_to_seconds(clock_str: str) -> int:
    """Convert 'MM:SS' game clock string to seconds integer."""
    parts = clock_str.split(":")
    if len(parts) != 2:
        return 0
    try:
        return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        return 0
