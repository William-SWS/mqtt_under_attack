from pathlib import Path

from nbclient import NotebookClient
import nbformat

NOTEBOOK_PATH = Path(__file__).resolve().parents[1] / "notebooks" / "training.ipynb"


def test_training_notebook_runs_from_top_to_bottom():
    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=120,
        kernel_name="python3",
        resources={"metadata": {"path": str(NOTEBOOK_PATH.parent)}},
    )

    client.execute()
