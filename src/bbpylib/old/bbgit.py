## This is the older one. The one in git.py is better.
import subprocess
from pathlib import Path

# --- core runner -------------------------------------------------------------

def _git(cmd, path):
    r = subprocess.run(
        ["git", *cmd],
        cwd=path,
        text=True,
        capture_output=True
    )
    if r.stdout:
        print(r.stdout, end="")
    if r.stderr:
        print(r.stderr, end="")
    if r.returncode:
        raise subprocess.CalledProcessError(
            r.returncode, r.args, r.stdout, r.stderr
        )

# --- helpers ----------------------------------------------------------------

def git_status(repo, base="/content/drive/MyDrive/GIT-repos"):
    _git(["status"], Path(base) / repo)

def git_status_short(repo, base="/content/drive/MyDrive/GIT-repos"):
    _git(["status", "-sb"], Path(base) / repo)

def git_add(repo, *files, base="/content/drive/MyDrive/GIT-repos"):
    cmd = ["add", "-A"] if not files else ["add", *files]
    _git(cmd, Path(base) / repo)

def git_commit(repo, msg, base="/content/drive/MyDrive/GIT-repos"):
    path = Path(base) / repo
    if subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=path
    ).returncode == 0:
        print("No changes to commit.")
        return
    _git(["commit", "-m", msg], path)

def git_pull(repo, base="/content/drive/MyDrive/GIT-repos"):
    _git(["pull"], Path(base) / repo)

def git_push(repo, base="/content/drive/MyDrive/GIT-repos"):
    _git(["push"], Path(base) / repo)

def git_fetch(repo, base="/content/drive/MyDrive/GIT-repos"):
    _git(["fetch"], Path(base) / repo)
