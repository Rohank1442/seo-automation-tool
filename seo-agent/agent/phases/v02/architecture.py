"""Public entry point for the v0.2 final site architecture stage."""

from .site_architecture.runner import run_v02_architecture

__all__ = ["run_v02_architecture"]


if __name__ == "__main__":
    run_v02_architecture()
