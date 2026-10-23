"""Exercise the real .NET template engine without changing the user's template hive."""

import json
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".validation"
TEMPLATE = json.loads((ROOT / ".template.config/template.json").read_text())
DEFAULT_VERSION = TEMPLATE["symbols"]["AspireVersion"]["defaultValue"]
assert "AspireNuGetSource" not in TEMPLATE["symbols"]


def run(*args):
    subprocess.run(
        ["dotnet", "new", *args, "--debug:custom-hive", str(OUTPUT / "hive")],
        cwd=ROOT,
        check=True,
        timeout=120,
    )


def check(name, folder, version=DEFAULT_VERSION):
    destination = OUTPUT / folder
    if destination.exists():
        shutil.rmtree(destination)
    args = [
        "david-has-trust-issues", "--name", name,
        "--output", str(destination),
    ]
    if version != DEFAULT_VERSION:
        args += ["--AspireVersion", version]
    run(*args)
    config = json.loads((destination / "aspire.config.json").read_text())
    assert config["appHost"]["path"] == "apphost.mts"
    assert config["sdk"]["version"] == version
    assert config["packages"] == {"Aspire.Hosting.JavaScript": version}
    npm_name = re.sub(r"[^a-z0-9._-]+", "-", name.lower()).lstrip("._-")
    for package_dir, expected in [("", npm_name), ("api", npm_name + "-api"), ("frontend", "frontend")]:
        manifest = json.loads((destination / package_dir / "package.json").read_text())
        assert manifest["name"] == expected
        lock_path = destination / package_dir / "package-lock.json"
        if lock_path.exists():
            lock = json.loads(lock_path.read_text())
            assert lock["name"] == expected
            assert lock["packages"][""]["name"] == expected
    apphost = (destination / "apphost.mts").read_text()
    assert '"./api"' in apphost and '"./frontend"' in apphost
    assert (destination / "api/src/index.ts").is_file()
    assert (destination / "frontend/src/App.tsx").is_file()
    forbidden = {".git", ".github", ".vscode", ".template.config", ".aspire", ".azure",
                 "node_modules", "bin", "obj", "dist", "tests", ".validation"}
    for path in destination.rglob("*"):
        relative = path.relative_to(destination)
        assert path.name.lower() != "nuget.config", relative
        assert not forbidden.intersection(relative.parts), relative
        if path.is_file() and path.suffix in {".json", ".mts", ".ts", ".tsx", ".html"}:
            text = path.read_text()
            assert "TemplateApp" not in text and "__npm_name__" not in text, relative
    assert not (destination / "README.md").exists()
    print(f"PASS {name}: versions, names, locks, paths, exclusions, no NuGet.config")


OUTPUT.mkdir(exist_ok=True)
run("install", str(ROOT), "--force")
check("david-has-trust-issues", "david-has-trust-issues")
check("Contoso.Inventory", "Contoso.Inventory")
check("Override.App", "override", "99.0.0-preview.42")
