"""Evaluation entry points with lazy imports for optional RAG dependencies."""


def build_test_set(*args, **kwargs):
    from .testset import build_test_set as implementation

    return implementation(*args, **kwargs)


def evaluate_pipeline(*args, **kwargs):
    from .metrics import evaluate_pipeline as implementation

    return implementation(*args, **kwargs)


__all__ = ["build_test_set", "evaluate_pipeline"]
