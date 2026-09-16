"""Create a release bundle including all required notices and LGPL source."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def main():
    exe = ROOT / "dist" / "Velune.exe"
    if not exe.is_file():
        raise SystemExit("Build dist/Velune.exe first")
    target = ROOT / "dist" / "Velune-windows-x64.zip"
    top_level = [exe, ROOT / "README.md", ROOT / "SECURITY.md", ROOT / "LICENSE",
                 ROOT / "THIRD_PARTY_NOTICES.md"]
    files = list(top_level)
    files.append(ROOT / "docs" / "SIGNING-AND-ANTIVIRUS.md")
    files += sorted(path for path in (ROOT / "licenses").rglob("*") if path.is_file())
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path in files:
            name = path.name if path in top_level else path.relative_to(ROOT).as_posix()
            archive.write(path, name)
    print(f"Release ready: {target}")


if __name__ == "__main__":
    main()
