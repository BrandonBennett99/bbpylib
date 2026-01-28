import subprocess

def run_command(cmd, *, cwd=None, env=None, check=True):
    """
    Run an external command, echo stdout/stderr, and raise on failure.

    Parameters
    ----------
    cmd : list[str]           Command and arguments.
    cwd : Path | str | None   Directory to run in.
    check : Bool
    Raises
    ------
    subprocess.CalledProcessError
        If check=True and the command exits with a non-zero status.
    """
    r = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True
    )
    if r.stdout: print(r.stdout, end="")
    if r.stderr: print(r.stderr, end="")
    if check and r.returncode:
        raise subprocess.CalledProcessError(
            r.returncode, r.args, r.stdout, r.stderr)
    return r
