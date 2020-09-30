def to_boolean(value):
    """Convert a number to a boolean value

    Args:
        value (float): value

    Returns:
        bool: boolean transformation
    """
    return value > 0.0


def to_boolean_int(value):
    """Convert a number to a boolean value but using int as the return type

    Args:
        value (float): value

    Returns:
        int: boolean transformation
    """
    return 1 if value > 0.0 else 0



