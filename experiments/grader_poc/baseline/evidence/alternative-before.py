from bisect import bisect_left, insort
def alternative(numbers: list[float], threshold: float) -> bool:
    """Check each inserted value's neighbors without sorting the input in bulk."""
    seen: list[float] = []
    for value in numbers:
        position = bisect_left(seen, value)
        if position and value - seen[position - 1] < threshold:
            return True
        if position < len(seen) and seen[position] - value < threshold:
            return True
        insort(seen, value)
    return False

has_close_elements = alternative
