def alternative_87(rows: list, target: int) -> list:
    """Construct the required ordering directly without sorting coordinates."""
    found = []
    for row_index, row in enumerate(rows):
        for column in reversed(range(len(row))):
            if row[column] == target:
                found.append((row_index, column))
    return found

get_row = alternative_87
