## the git_is_up_to_date function at the end needs to be integrated into the class.

import subprocess
from pathlib import Path
from google.colab import userdata

class GitRepo:
    def __init__(self, repo, base="/content/drive/MyDrive/GIT-repos"):
        self.path = Path(base) / repo
        if not self.path.is_dir():
            raise FileNotFoundError(self.path)

    def _git(self, *cmd, check=True):
        r = subprocess.run(["git", *cmd], cwd=self.path, text=True, capture_output=True)
        if r.stdout: print(r.stdout, end="")
        if r.stderr: print(r.stderr, end="")
        if check and r.returncode:
            raise subprocess.CalledProcessError(r.returncode, r.args, r.stdout, r.stderr)
        return r

    def status(self):        return self._git("status")
    def status_short(self):  return self._git("status", "-sb")
    def fetch(self):         return self._git("fetch")
    def pull(self):          return self._git("pull")
    def push(self):          return self._git("push")

    def add(self, *files):
        return self._git("add", "-A" if not files else None, *files) if files else self._git("add", "-A")

    def commit(self, msg):
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=self.path).returncode == 0:
            print("No changes to commit.")
            return
        return self._git("commit", "-m", msg)

    def set_token_remote(self, user, token_key="GITHUB_TOKEN", remote="origin"):
        token = userdata.get(token_key)
        if not token:
            raise RuntimeError(f"{token_key} not found in Colab userdata")
        url = f"https://{user}:{token}@github.com/{user}/{self.path.name}.git"
        return self._git("remote", "set-url", remote, url)


def git_is_up_to_date(repo, base="/content/drive/MyDrive/GIT-repos"):
    path = Path(base) / repo
    subprocess.run(["git", "fetch"], cwd=path, check=True)

    r = subprocess.run(
        ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"],
        cwd=path,
        capture_output=True,
        text=True,
        check=True
    )
    ahead, behind = map(int, r.stdout.split())
    return ahead == 0 and behind == 0

