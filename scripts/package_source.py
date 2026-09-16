"""Package only the files intended for the public repository."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = (".github", "browser-extension", "docs", "licenses", "scripts", "static", "tests")


def main():
    target = ROOT / "dist" / "Velune-source.zip"
    target.parent.mkdir(exist_ok=True)
    files = [path for path in ROOT.iterdir() if path.is_file()]
    for folder in FOLDERS:
        files.extend(path for path in (ROOT / folder).rglob("*")
                     if path.is_file() and "__pycache__" not in path.parts
                     and path.suffix not in (".pyc", ".pyo"))
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(f"Source ready: {target}")


if __name__ == "__main__":
    main()
