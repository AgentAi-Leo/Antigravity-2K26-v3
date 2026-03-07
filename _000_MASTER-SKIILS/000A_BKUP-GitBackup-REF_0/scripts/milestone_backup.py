import os
import sys
import subprocess
import argparse
from datetime import datetime

DEFAULT_REMOTE = "https://github.com/AgentAi-Leo/Antigravity-2K26-v2.git"
MILESTONE_TAG = "REF_0"

def _run(cmd: list, cwd: str, dry_run: bool = False) -> tuple[int, str, str]:
    if dry_run:
        print(f"  [DRY-RUN] {' '.join(cmd)}")
        return 0, "", ""
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def _git(args: list, cwd: str, dry_run: bool = False) -> tuple[int, str, str]:
    return _run(["git"] + args, cwd, dry_run)

def _inject_token(url: str) -> str:
    """Inject GITHUB_TOKEN into HTTPS remote URL if available."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if token and url.startswith("https://"):
        url = url.replace("https://", f"https://{token}@")
    return url

def milestone_backup(target_dir: str, remote_url: str, branch: str, message: str, dry_run: bool) -> None:
    cwd = os.path.abspath(target_dir)
    print(f"{'[DRY-RUN] ' if dry_run else ''}Milestone Backup ({MILESTONE_TAG}): {cwd}")
    print(f"  Remote : {remote_url}")
    print(f"  Branch : {branch}")
    print(f"  Message: {MILESTONE_TAG}: {message}\n")

    # 1. Verify Git Repo
    git_dir = os.path.join(cwd, ".git")
    if not os.path.isdir(git_dir):
        print("Error: Target directory is not a git repository.")
        sys.exit(1)

    # 2. Stage all
    print("Staging all changes...")
    _git(["add", "-A"], cwd, dry_run)

    # 3. Commit
    print("Committing milestone...")
    full_message = f"{MILESTONE_TAG}: {message}"
    code, _, err = _git(["commit", "-m", full_message], cwd, dry_run)
    # Be lenient: if there's nothing new to commit, we still might want to move the tag.
    if code != 0 and not dry_run:
        if "nothing to commit" in err or "working tree clean" in err:
            print("  (Nothing new to commit, proceeding to tagging...)")
        else:
            print(f"Error: commit failed — {err}")
            sys.exit(1)

    # 4. Handle Tag Locally
    print(f"Updating local tag '{MILESTONE_TAG}'...")
    # Delete local if exists to ensure it points to the NEW head
    _git(["tag", "-d", MILESTONE_TAG], cwd, dry_run)
    code, _, err = _git(["tag", MILESTONE_TAG], cwd, dry_run)
    if code != 0 and not dry_run:
        print(f"Error: tagging failed — {err}")
        sys.exit(1)

    # 5. Push Branch
    push_url = _inject_token(remote_url)
    print(f"Pushing branch '{branch}' to remote...")
    code, out, err = _git(["push", push_url, branch], cwd, dry_run)
    if code != 0 and not dry_run:
        print(f"Error: branch push failed — {err}")
        sys.exit(1)

    # 6. Push Tag (Force)
    print(f"Pushing tag '{MILESTONE_TAG}' to remote (force)...")
    code, out, err = _git(["push", push_url, MILESTONE_TAG, "--force"], cwd, dry_run)
    if code != 0 and not dry_run:
        print(f"Error: tag push failed — {err}")
        sys.exit(1)

    if not dry_run:
        print(f"\n✅ Milestone complete! {MILESTONE_TAG} updated locally and on remote.")
        print(f"   URL: {remote_url}/tree/{MILESTONE_TAG}")
    else:
        print("\n[DRY-RUN] Milestone logic previewed successfully.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Stage, commit, and update the REF_0 milestone tag.")
    parser.add_argument("--dir",     default=".",              help="Directory to backup (default: .)")
    parser.add_argument("--remote",  default=DEFAULT_REMOTE,   help="GitHub remote URL")
    parser.add_argument("--branch",  default="main",           help="Target branch (default: main)")
    parser.add_argument("--message", default=None,             help="Commit message (prefixed with REF_0:)")
    parser.add_argument("--dry-run", action="store_true",      help="Preview without committing or pushing")
    args = parser.parse_args()

    message = args.message or f"Release {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    milestone_backup(args.dir, args.remote, args.branch, message, args.dry_run)

if __name__ == "__main__":
    main()
