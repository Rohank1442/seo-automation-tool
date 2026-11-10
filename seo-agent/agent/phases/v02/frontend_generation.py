"""Compatibility entry point for v0.2 frontend scaffold generation."""

from pathlib import Path

from .frontend_scaffold import run_frontend_scaffold


def main(project_outputs: Path | None = None, base_url: str | None = None) -> dict:
    """Run the scaffold stage for an explicitly supplied project output root."""
    if project_outputs is None:
        raise ValueError("Pass the project's outputs directory to generate its frontend.")
    return run_frontend_scaffold(project_outputs, base_url)


if __name__ == "__main__":
    raise SystemExit("Call main(project_outputs, base_url) with a project output directory.")
