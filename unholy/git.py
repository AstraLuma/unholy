import io
import os
import subprocess
import tarfile
import tempfile


# This series of functions based on
# https://stackoverflow.com/questions/1125476/retrieve-a-single-file-from-a-repository
def pull_file(
    repo: str, path: str, branch: str | None = None,
    encoding: str | None = 'utf-8'
) -> str | bytes:
    """
    Pull a specific file from a remote repo, without doing a full checkout.
    """
    branch = branch or 'HEAD'
    if 'github.com' in repo:
        # GitHub doesn't support `git archive`, don't bother trying
        raw = _pull_file_github(repo, branch, path)
    try:
        # Try with `git archive`
        raw = _pull_file_archive(repo, branch, path)
    except Exception as exc:
        # Try as github anyway, might be self-hosted or other shenanigans
        try:
            raw = _pull_file_github(repo, branch, path)
        except Exception:
            # That also failed, raise the original exception
            raise exc

    if encoding is not None:
        return raw.decode(encoding)
    else:
        return raw


def _pull_file_archive(repo: str, branch: str, path: str) -> bytes:
    """
    Pull a file from a remote repo using `git-archive`.

    This is currently the most efficient way of doing this.
    """
    # git archive --remote=ssh://host/pathto/repo.git HEAD README.md | tar -x

    # We're buffering instead of streaming so that stuff fails in the correct order.
    # (ie, if git fails, say that instead of giving a tarfile error.)
    proc = subprocess.run(
        ['git', 'archive', f'--remote={repo}', branch, path],
        stdout=subprocess.PIPE, text=False, check=True,
    )
    with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode='r:*') as tf:
        member = tf.getmember(path)
        with tf.extractfile(member) as fobj:
            return fobj.read()


def _pull_file_github(repo: str, branch: str, path: str) -> bytes:
    """
    Pull a file from a remote repo in a github-friendly way.

    This is less efficient, but more compatible.
    """
    # Note: We're not converting the repo into a direct download URL because of
    # auth, in case of private repo. Or if other servers have similar
    # limitations.

    # git clone --no-checkout --depth=1 --no-tags URL
    # git restore --staged DIR-OR-FILE
    # git checkout DIR-OR-FILE
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            ['git', 'clone', '--no-checkout', '--depth=1', '--no-tags', repo, td]
            + (['-b', branch] if branch != 'HEAD' else []),
            check=True,
        )
        subprocess.run(
            ['git', 'restore', '--staged', path],
            check=True, cwd=td,
        )
        subprocess.run(
            ['git', 'checkout', path],
            check=True, cwd=td,
        )
        with open(os.path.join(td, path), 'rb') as f:
            return f.read()


def guess_project_from_url(url) -> str:
    """
    Given a git remote URL, guess the project name.
    """
    end = url.rsplit('/', 1)[-1]
    assert '?' not in end
    assert '#' not in end
    end = end.removesuffix('.git')
    return end
