"""Write SHA-256 checksums for public release files."""
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
NAMES = ("Velune.exe", "Velune-windows-x64.zip", "Velune-source.zip")


def digest(path):
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    lines = [f"{digest(DIST / name)}  {name}" for name in NAMES if (DIST / name).is_file()]
    if not lines:
        raise SystemExit("No release files found in dist")
    (DIST / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")
    print("Checksums ready: dist/SHA256SUMS.txt")


if __name__ == "__main__":
    main()
