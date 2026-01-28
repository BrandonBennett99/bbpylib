## Written from repo.ipynb

import tomllib
from pathlib import Path
import re
import subprocess

from .process import run_command

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
    self.version = "orange"

  def pip_version(self):
      with open(self.root/"pyproject.toml", "rb") as f:
          data = tomllib.load(f)
      return data["project"]["version"]

  def set_version(self, new_version):
      path = Path(self.root/"pyproject.toml")
      text = path.read_text()
      text, n = re.subn( r'(version\s*=\s*")[^"]+(")',
                        rf'\1{new_version}\2',
                        text, count=1)
      if n != 1:
          raise RuntimeError("Could not uniquely locate version field")
      path.write_text(text)

  def increment_pip_version(self, part="patch"):
      v = self.pip_version()
      nv = bump_version(v, part=part)
      print("Incrementing pip version:", v, "->", nv)
      self.set_version(nv, self)

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
      print(f"Building pip package: {self.name}-{self.version()}")
      run_command( "pip", "-q", "install", "build", check=True)
      run_command( "python", "-m", "build", cwd=self.root, check=True)
      run_command( "ls", "dist", cwd=self.root, check=True)
  
  def upload_pip(self):
      print(f"Uploading {self.name}-{self.version()} to PyPi ..." )
      env = os.environ.copy()
      env["TWINE_USERNAME"] = "__token__"
      env["TWINE_PASSWORD"] = self.pip_token
      run_command( "pip", "-q", "install", "twine", check=True)
      run_command( "twine", "upload", "dist/*", cwd=self.root, env=env, check=True)

  def update_pip(self):
      self.increment_pip_version()
      self.build_pip()
      self.upoad_pip()





# This is just a str->str function so not in the class
def bump_version(v, part="patch"):
    major, minor, patch = map(int, v.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError("part must be 'major', 'minor', or 'patch'")





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
