"""Pipeline entry points with lazy imports for optional runtime dependencies."""


def run_corruption_flow() -> None:
    from .corruption_flow import main

    main()


def run_phase1() -> None:
    from .phase1 import main

    main()


__all__ = ["run_corruption_flow", "run_phase1"]
