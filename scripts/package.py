#!/usr/bin/env python3
"""Create a runtime source bundle for Docker/uv; this is no Shopware plugin."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tarfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    version = project["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SystemExit("Expected a stable three-part backend version")
    if os.environ.get("GITHUB_REF_TYPE") == "tag":
        if os.environ.get("GITHUB_REF_NAME") != "v" + version:
            raise SystemExit("Tag does not match pyproject.toml")
    output = Path(os.environ.get("RELEASE_OUTPUT", ROOT / "dist")).resolve()
    output.mkdir(parents=True, exist_ok=True)
    prefix = f"shopware-ollama-mcp-{version}"
    archive = output / f"{prefix}.tar.gz"
    paths = [ROOT / p for p in ("app.py", "shopware_mcp_server.py", "Dockerfile",
                               ".dockerignore", "compose.yaml", "pyproject.toml",
                               "uv.lock", "README.md", "CHANGELOG.md")]
    paths += sorted((ROOT / "backend").rglob("*.py"))
    paths += sorted((ROOT / "backend/data").rglob("*.json"))
    paths += [ROOT / "scripts/rebuild_ollama_aliases.sh", ROOT / "docs/release.md"]
    contents = {}
    for path in paths:
        relative = path.relative_to(ROOT)
        if any((ROOT.joinpath(*relative.parts[:i])).is_symlink()
               for i in range(1, len(relative.parts) + 1)):
            raise SystemExit(f"Refusing symlink: {relative}")
        contents[str(relative)] = path.read_bytes()
    info = {"project": project["name"], "version": version,
            "source_sha256": {p: hashlib.sha256(data).hexdigest() for p, data in contents.items()}}
    contents["BUILD-INFO.json"] = (json.dumps(info, indent=2) + "\n").encode()
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as bundle:
                for name, data in sorted(contents.items()):
                    item = tarfile.TarInfo(f"{prefix}/{name}")
                    item.size = len(data)
                    item.mode = 0o755 if name.endswith(".sh") else 0o644
                    bundle.addfile(item, io.BytesIO(data))
    with tarfile.open(archive) as bundle:
        assert all(m.isfile() and m.name.startswith(prefix + "/") for m in bundle)
        assert json.loads(bundle.extractfile(prefix + "/BUILD-INFO.json").read())["version"] == version
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".gz.sha256").write_text(f"{digest}  {archive.name}\n")
    print(f"Built and checked: {archive}")


if __name__ == "__main__":
    main()
