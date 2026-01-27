import os
import subprocess
from pathlib import Path
from google.colab import userdata

def bump_version(v, part="patch"):
    major, minor, patch = map(int, v.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError("part must be 'major', 'minor', or 'patch'")

def set_version(new_version, repo):
    path = Path( repo.root / "pyproject.toml" )
    text = path.read_text()


    text, n = re.subn( r'(version\s*=\s*")[^"]+(")',
                       rf'\1{new_version}\2',
                       text, count=1 )
    if n != 1:
        raise RuntimeError("Could not uniquely locate version field")
    path.write_text(text)



def build_and_upload_pypi(repo, base="/content/drive/MyDrive/GIT-repos"):
    path = Path(base) / repo
    if not path.is_dir():
        raise FileNotFoundError(path)

    token = userdata.get("PIP_API_TOKEN")
    if not token:
        raise RuntimeError("PIP_API_TOKEN not found in Colab userdata")

    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = token

    subprocess.run(["pip", "-q", "install", "build"], check=True)
    subprocess.run(["python", "-m", "build"], cwd=path, check=True)
    subprocess.run(["ls", "dist"], cwd=path, check=True)

    subprocess.run(["pip", "-q", "install", "twine"], check=True)
    subprocess.run(["twine", "upload", "dist/*"], cwd=path, env=env, check=True)
