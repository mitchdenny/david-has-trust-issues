"""Exercise the real .NET template engine without changing the user's template hive."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".validation"
TEMPLATE = json.loads((ROOT / ".template.config/template.json").read_text())
DEFAULT_VERSION = TEMPLATE["symbols"]["AspireVersion"]["defaultValue"]
DEFAULT_FEED = TEMPLATE["symbols"]["AspireNuGetSource"]["defaultValue"]


def run(*args):
    subprocess.run(
        ["dotnet", "new", *args, "--debug:custom-hive", str(OUTPUT / "hive")],
        cwd=ROOT,
        check=True,
        timeout=120,
    )


def check(name, folder, version=DEFAULT_VERSION, feed=DEFAULT_FEED, overrides=False):
    destination = OUTPUT / folder
    if destination.exists():
        shutil.rmtree(destination)
    args = [
        "david-has-trust-issues", "--name", name,
        "--output", str(destination),
    ]
    if overrides:
        args += ["--AspireVersion", version, "--AspireNuGetSource", feed]
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
    nuget = ET.parse(destination / "NuGet.config").getroot()
    sources = {item.attrib["key"]: item.attrib["value"] for item in nuget.findall("packageSources/add")}
    assert sources["aspire-template"] == feed
    for mapping in nuget.findall("packageSourceMapping/packageSource"):
        assert mapping.attrib["key"] in sources
    apphost = (destination / "apphost.mts").read_text()
    assert '"./api"' in apphost and '"./frontend"' in apphost
    assert (destination / "api/src/index.ts").is_file()
    assert (destination / "frontend/src/App.tsx").is_file()
    forbidden = {".git", ".github", ".vscode", ".template.config", ".aspire", ".azure",
                 "node_modules", "bin", "obj", "dist", "tests", ".validation"}
    for path in destination.rglob("*"):
        relative = path.relative_to(destination)
        assert not forbidden.intersection(relative.parts), relative
        if path.is_file() and path.suffix in {".json", ".mts", ".ts", ".tsx", ".html"}:
            text = path.read_text()
            assert "TemplateApp" not in text and "__npm_name__" not in text, relative
    assert not (destination / "README.md").exists()
    print(f"PASS {name}: versions, feed, names, locks, paths, exclusions")


OUTPUT.mkdir(exist_ok=True)
run("install", str(ROOT), "--force")
check("david-has-trust-issues", "david-has-trust-issues")
check("Contoso.Inventory", "Contoso.Inventory")
check("Override.App", "override", "99.0.0-preview.42",
      'https://example.invalid/v3/index.json?channel=daily&label="test"<value>', True)
check("Local.Feed", "local-feed", "99.0.0-preview.43",
      '/tmp/local feed "quoted" & packages', True)
