import importlib


def test_package_imports():
    """The package installs and imports under its new name."""
    module = importlib.import_module("hiring_pipeline")
    assert module.__name__ == "hiring_pipeline"
