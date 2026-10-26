"""Execute and export the Week 2 notebook using notebook APIs."""
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

ROOT = Path(__file__).resolve().parents[1]
notebook_name = sys.argv[1] if len(sys.argv) > 1 else "02_join_and_aadf_match_audit.ipynb"
path = ROOT / "notebooks" / notebook_name
print("reading notebook", flush=True)
nb = nbformat.read(path, as_version=4)
print("starting kernel", flush=True)
client = NotebookClient(nb, timeout=180, kernel_name="python3", resources={"metadata":{"path":str(ROOT)}})
client.execute(cwd=str(ROOT))
print("writing outputs", flush=True)
nbformat.write(nb, path)
body, _ = HTMLExporter().from_notebook_node(nb)
(ROOT / "reports" / f"{path.stem}.html").write_text(body, encoding="utf-8")
print("executed")
