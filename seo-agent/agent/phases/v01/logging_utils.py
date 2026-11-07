"""Small console helpers shared by the synchronous v0.1 research stages."""


def print_separator(char: str = "─", length: int = 50) -> None:
    """Print a visual section divider in the worker logs."""
    print(char * length)
