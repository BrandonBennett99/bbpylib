## Written from repo.ipynb

import tomllib
from pathlib import Path
import subprocess
import os, sys, site
import requests
import re

# Import from process.py in this package
try:
  from .process import run_command
except:
  print("Could not import .process (maybe loaded from a cell)")

try:
  from google.colab import userdata
  GITHUB_TOKEN = userdata.get("GITHUB_TOKEN")
  PIP_API_TOKEN = userdata.get("PIP_API_TOKEN")
except:
  print("Could not get tokens via google.colab.userdata")
  GITHUB_TOKEN = None
  PIP_API_TOKEN = None


class Repo:
  def __init__(self, name, location, user,
               git_token=GITHUB_TOKEN, pip_token = PIP_API_TOKEN):
    self.name = name
    self.location = location
    self.user = user
    self.git_token = git_token
    self.pip_token = pip_token
    self.root =  Path( Path(location)/ name )
    self.src =  Path( self.root, "src", name )
    self.git = GitCommander(self)
    self.version = "batfish"

  def pyproject_toml_pip_version(self):
      with open(self.root/"pyproject.toml", "rb") as f:
          data = tomllib.load(f)
      return data["project"]["version"]

  def published_pip_version(self) -> str | None:
      url = f"https://pypi.org/pypi/{self.name}/json"
      r = requests.get(url, timeout=5)
      if r.status_code != 200:
          return None  # package not found or network error
      data = r.json()
      # 'info' is the metadata for the *latest* release
      return data.get("info", {}).get("version")


  def set_version(self, new_version):
      path = Path(self.root/"pyproject.toml")
      text = path.read_text()
      text, n = re.subn( r'(version\s*=\s*")[^"]+(")',
                        rf'\g<1>{new_version}\g<2>',
                        text, count=1)
      if n != 1:
          raise RuntimeError("Could not uniquely locate version field")
      path.write_text(text)

  def increment_pip_version(self, level="patch"):
      v = self.published_pip_version()
      nv = bump_version(v, level=level)
      print("Incrementing pip version:", v, "->", nv)
      self.set_version(nv)

  def show_config(self):
      with open(self.root/"pyproject.toml", "r") as f:
          print( f.read() )

  def check_repo_files( self ):
      root = self.root
      print("pyproject:", (root/"pyproject.toml").exists())
      print("src dir:", (root/"src").is_dir())
      print("pkg dir:", (root/"src"/self.name).is_dir())
      print("__init__.py:", (root/"src"/self.name/"__init__.py").exists())

  def build_pip(self):
      print(f"Building pip package: {self.name}-{self.pyproject_toml_pip_version()}")
      run_command( ["rm", "-rf", "dist", "build", "*.egg-info"], cwd=self.root, check=True )
      run_command( ["pip", "-q", "install", "build"], check=True)
      run_command( ["python", "-m", "build"], cwd=self.root, check=True)
      run_command( ["ls", "dist"], cwd=self.root, check=True)

  def upload_pip(self):
      print(f"Uploading {self.name}-{self.pyproject_toml_pip_version()} to PyPi ..." )
      env = os.environ.copy()
      env["TWINE_USERNAME"] = "__token__"
      env["TWINE_PASSWORD"] = self.pip_token
      run_command( ["pip", "-q", "install", "twine"], check=True)
      run_command( ["twine", "upload", "dist/*"], cwd=self.root, env=env, check=True)

  def update_pip(self,level="patch", version=None):
      if version:
        print("Setting repo pip version to", version)
        self.set_version(version)
      else:
        self.increment_pip_version(level=level)
      self.build_pip()
      self.upload_pip()

  def install_editable(self):
     install_editable(self.name, self.location)


# This is just a str->str function so not in the class
def bump_version(v, level="patch"):
    major, minor, patch = map(int, v.split("."))
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError("'level' parameter must be 'major', 'minor', or 'patch'")


class GitCommander:
    def __init__(self, repo):
        self.repo = repo
        self.name = repo.name
        self.user = repo.user
        self.token = repo.git_token
        self.url = f"https://{self.user}:{self.token}@github.com/{self.user}/{self.name}.git"

    def git_command(self, *cmd, check=True):
        return run_command(["git", *cmd], cwd=self.repo.root, check=check)

    def status(self):        return self.git_command("status")
    def status_short(self):  return self.git_command("status", "-sb")

    def add(self, *files):
        if files:
           return self.git_command("add", files )
        return self.git_command("add", "-A")

    def commit(self, message="Committing minor updates."):
        if self.git_command( "diff", "--cached", "--quiet", check=False ).returncode == 0:
            print("No changes to commit.")
            return
        return self.git_command("commit", "-m", message)

    def push(self):
        self.git_command( "push", self.url )

    def update(self, message="Committing minor updates."):
        self.add()
        self.commit(message=message)
        self.push()

    def fetch(self):
        return self.git_command( "fetch", self.url )

    def merge(self):
        self.git_command( "merge", "FETCH_HEAD" )

    def pull(self):
        self.fetch()
        self.merge()

    # Don't really need to do this as can pass the token directly
    def set_token_remote(self, remote="origin"):
        return self._git("remote", "set-url", remote, self.url)

    def is_up_to_date(self):
        self.fetch()
        r = self.git_command( "rev-list", "--left-right", "--count", "HEAD...@{u}" )
        ahead, behind = map(int, r.stdout.split())
        return (ahead == 0 and behind == 0)


def pyproject_toml_str(
    package_name: str,
    version: str,
    description: str = "",
    requires_python: str = ">=3.9",
    author_name: str | None = None,
    readme: str | None = "README.md",
    license_text: str | None = "MIT",
) -> str:
    """
    Return a minimal pyproject.toml string suitable for a Hatchling build
    using a standard `src/<package_name>` layout.
    """

    lines = ["# pyproject.toml auto created by BB's pyproject_toml_str function"]

    # --- build system ---
    lines.append("[build-system]")
    lines.append('requires = ["hatchling>=1.25"]')
    lines.append('build-backend = "hatchling.build"')
    lines.append("")

    # --- project metadata ---
    lines.append("[project]")
    lines.append(f'name = "{package_name}"')
    lines.append(f'version = "{version}"')

    if description:
        lines.append(f'description = "{description}"')

    if readme:
        lines.append(f'readme = "{readme}"')

    lines.append(f'requires-python = "{requires_python}"')

    if license_text:
        lines.append(f'license = {{ text = "{license_text}" }}')

    if author_name:
        lines.append("authors = [")
        lines.append(f'  {{ name = "{author_name}" }}')
        lines.append("]")

    lines.append("")

    # --- hatch build config ---
    lines.append("[tool.hatch.build]")
    lines.append('dev-mode-dirs = ["src"]')
    lines.append("")

    lines.append("[tool.hatch.build.targets.wheel]")
    lines.append(f'packages = ["src/{package_name}"]')

    return "\n".join(lines)

def install_editable(repo_name, location, src_subdir="src"):
    """
    Uninstall package_name (if present) and install the repo at repo_path
    in editable mode.
    """
    repo_path = Path(location)/repo_name
    src_path = repo_path / src_subdir
    run_command(["pip", "uninstall", "-y", repo_name])
    run_command(["pip", "install", "-e", str(repo_path)])
    ## It seems you need this to make the -e installed package accessible in Colab
    if src_path.exists():
        site.addsitedir(str(src_path))

def test():
    print("bbpylib.repo.test says: Hello")
