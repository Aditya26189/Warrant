def alternative_57(values: list) -> bool:
    """Track direction; equality behavior is a predeclared out-of-scope assumption."""
    rising, falling = False, False
    for index in range(1, len(values)):
        rising = rising or values[index] > values[index - 1]
        falling = falling or values[index] < values[index - 1]
        if rising and falling:
            return False
    return True

monotonic = alternative_57
