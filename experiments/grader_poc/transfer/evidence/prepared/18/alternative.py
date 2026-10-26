def alternative_18(text: str, substring: str) -> int:
    """Advance one character after a match so overlapping occurrences remain."""
    count, start = 0, 0
    while start <= len(text) - len(substring):
        position = text.find(substring, start)
        if position < 0:
            break
        count += 1
        start = position + 1
    return count

how_many_times = alternative_18
