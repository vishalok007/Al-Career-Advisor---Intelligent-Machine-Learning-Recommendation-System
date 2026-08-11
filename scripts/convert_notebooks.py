"""Convert all .ipynb notebooks in notebook/ into executable .py Python scripts."""
from __future__ import annotations
import json
from pathlib import Path

def convert_notebooks():
    notebook_dir = Path(__file__).resolve().parent.parent / "notebook"
    print(f"[*] Processing notebooks in {notebook_dir} ...")

    for ipynb_path in sorted(notebook_dir.glob("*.ipynb")):
        py_path = ipynb_path.with_suffix(".py")
        print(f"  -> Converting {ipynb_path.name} ...")
        
        try:
            with open(ipynb_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    print(f"     [!] {ipynb_path.name} is empty, creating empty .py file.")
                    py_path.write_text("# Empty notebook\n", encoding="utf-8")
                    continue
                nb = json.loads(content)
        except Exception as e:
            print(f"     [!] Failed to parse JSON for {ipynb_path.name}: {e}")
            continue

        parts = [f"# Converted from {ipynb_path.name}\n"]
        for cell in nb.get("cells", []):
            cell_type = cell.get("cell_type")
            source = "".join(cell.get("source", []))
            if not source.strip():
                continue

            if cell_type == "markdown":
                md_comment = "\n".join("# " + line for line in source.splitlines())
                parts.append(f"\n{md_comment}\n")
            elif cell_type == "code":
                code_lines = []
                for line in source.splitlines():
                    if line.strip().startswith("%") or line.strip().startswith("!"):
                        code_lines.append(f"# {line}")
                    else:
                        code_lines.append(line)
                parts.append("\n".join(code_lines))

        py_content = "\n\n".join(parts)
        with open(py_path, "w", encoding="utf-8") as f:
            f.write(py_content + "\n")
        print(f"     [OK] Saved {py_path.name} ({len(py_content):,} bytes)")

if __name__ == "__main__":
    convert_notebooks()
