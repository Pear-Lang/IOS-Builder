#!/usr/bin/env python3
import sys
import subprocess
import time
import platform
import argparse
import shutil
import os
import textwrap
import requests
import zipfile
import io

from colorama import init, Fore, Style
from termcolor import colored

init(autoreset=True)

def print_ascii_art():
    ascii_art = [
        " __  __           _        ____              _       _ _             ",
        "|  \\/  | __ _  __| | ___  | __ ) _   _      | |_   _| (_) __ _ _ __  ",
        "| |\\/| |/ _` |/ _` |/ _ \\ |  _ \\| | | |  _  | | | | | | |/ _` | '_ \\ ",
        "| |  | | (_| | (_| |  __/ | |_) | |_| | | |_| | |_| | | | (_| | | | |",
        "|_|  |_|\\__,_|\\__,_|\\___| |____/ \\__, |  \\___/ \\__,_|_|_|\\__,_|_| |_|",
        "                                 |___/                               ",
    ]

    rainbow_colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]

    for line in ascii_art:
        rainbow_line = ''
        for i, char in enumerate(line):
            if char != ' ':
                color = rainbow_colors[i % len(rainbow_colors)]
                rainbow_line += color + char
            else:
                rainbow_line += ' '
        print(rainbow_line + Style.RESET_ALL)

    print('\n')

def run_command(command, cwd=None, verbose=True, check=True):
    if verbose:
        print(Fore.LIGHTBLUE_EX + f"➤ Running command: {command}")
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        stdout = ''
        while True:
            line = process.stdout.readline()
            if not line:
                break
            stdout += line
            if verbose:
                print(Fore.WHITE + line.strip())
        returncode = process.wait()
        if returncode != 0 and check:
            print(Fore.RED + f"✘ Command '{command}' failed with return code {returncode}.")
            sys.exit(1)
        return returncode, stdout, ''
    except subprocess.CalledProcessError as e:
        if check:
            print(Fore.RED + f"✘ Error executing: {command}")
            sys.exit(1)
        else:
            return e.returncode, e.output, ''

def open_new_window_and_run(command):
    current_os = platform.system()
    if current_os == "Windows":
        subprocess.run(f'start cmd /c "{command}"', shell=True)
    else:
        subprocess.run(f'{command}', shell=True)

def install_python_packages(verbose=False):
    required_packages = ['PyGithub', 'requests', 'colorama', 'termcolor']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(Fore.YELLOW + f"Installing missing Python package: {package}")
            if sys.argv[0].endswith('.exe'):
                print(Fore.YELLOW + f"Running as .exe. Opening new Python window to install {package}...")
                python_path = shutil.which("python") or "python"
                open_new_window_and_run(f'{python_path} -m pip install {package}')
                print(Fore.YELLOW + "Relaunching the script with the same arguments...")
                subprocess.run([sys.executable] + sys.argv)
                sys.exit(0)
            else:
                run_command(f"{sys.executable} -m pip install {package}", verbose=verbose)

def install_with_chocolatey(package, verbose=False):
    try:
        subprocess.run(
            "choco -v",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except subprocess.CalledProcessError:
        print(Fore.RED + "✘ Chocolatey is not installed. Please install Chocolatey.")
        sys.exit(1)

    print(Fore.YELLOW + f"Installing {package} with Chocolatey...")
    run_command(f"choco install {package} -y", verbose=verbose)

def install_with_apt(package, verbose=False):
    try:
        run_command("sudo apt-get update", verbose=verbose)
        run_command(f"sudo apt-get install -y {package}", verbose=verbose)
    except:
        print(Fore.RED + f"✘ Error installing {package} with apt. Please install manually.")
        sys.exit(1)

def install_with_homebrew(package, verbose=False):
    try:
        subprocess.run(
            "brew --version",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except subprocess.CalledProcessError:
        print(Fore.RED + "✘ Homebrew is not installed. Please install Homebrew.")
        sys.exit(1)

    print(Fore.YELLOW + f"Installing {package} with Homebrew...")
    run_command(f"brew install {package}", verbose=verbose)

def install_git(verbose=False):
    current_os = platform.system()
    if current_os == "Windows":
        install_with_chocolatey("git", verbose=verbose)
    elif current_os == "Linux":
        install_with_apt("git", verbose=verbose)
    elif current_os == "Darwin":
        install_with_homebrew("git", verbose=verbose)
    else:
        print(Fore.RED + "✘ Git installation not supported automatically. Install manually.")
        sys.exit(1)

def check_and_install_git(verbose=False):
    try:
        run_command("git --version", verbose=verbose)
        print(Fore.GREEN + "✔ Git is installed.")
    except:
        print(Fore.YELLOW + "Git is not installed. Installing now...")
        if platform.system() == "Windows":
            open_new_window_and_run('choco install git -y')
            run_command("git --version", verbose=verbose)
            print(Fore.GREEN + "✔ Git installed from new window.")
        else:
            install_git(verbose=verbose)
    run_command('git config --global user.email "you@example.com"', verbose=verbose)
    run_command('git config --global user.name "Your Name"', verbose=verbose)
    print(Fore.GREEN + "✔ Global Git user identity set to you@example.com / Your Name.")

def install_gh(verbose=False):
    current_os = platform.system()
    if current_os == "Windows":
        install_with_chocolatey("gh", verbose=verbose)
    elif current_os == "Linux":
        install_with_apt("gh", verbose=verbose)
    elif current_os == "Darwin":
        install_with_homebrew("gh", verbose=verbose)
    else:
        print(Fore.RED + "✘ Installing GitHub CLI not supported automatically. Install manually.")
        sys.exit(1)

    print(Fore.YELLOW + "GitHub CLI (gh) installed. Opening new window for `gh auth login`...")
    if platform.system() == "Windows":
        open_new_window_and_run('gh auth login')
        open_new_window_and_run('gh auth setup-git')
    else:
        run_command("gh auth login", verbose=verbose)
        run_command("gh auth setup-git", verbose=verbose)

def check_and_install_gh(verbose=False):
    try:
        run_command("gh --version", verbose=verbose)
        print(Fore.GREEN + "✔ GitHub CLI (gh) is installed.")
        _, auth_status, _ = run_command("gh auth status", verbose=verbose)
        if "not logged into any GitHub hosts" in auth_status:
            print(Fore.YELLOW + "GitHub CLI not authenticated. Please authenticate.")
            if platform.system() == "Windows":
                open_new_window_and_run('gh auth login')
                open_new_window_and_run('gh auth setup-git')
            else:
                run_command("gh auth login", verbose=verbose)
                run_command("gh auth setup-git", verbose=verbose)
    except:
        print(Fore.YELLOW + "GitHub CLI (gh) not installed.")
        if platform.system() == "Windows":
            open_new_window_and_run('choco install gh -y')
            run_command("gh --version", verbose=verbose)
            print(Fore.GREEN + "✔ GitHub CLI installed from new window.")
            open_new_window_and_run('gh auth login')
            open_new_window_and_run('gh auth setup-git')
        else:
            install_gh(verbose=verbose)

def get_github_token(args):
    token = args.token or os.getenv('GITHUB_TOKEN')
    if not token:
        token = input(Fore.CYAN + "Please enter your GitHub Personal Access Token: ").strip()
    if not token:
        print(Fore.RED + "✘ GitHub Token is required.")
        sys.exit(1)
    return token

def create_repo(repo_name, github_token, verbose=False):
    from github import Github, GithubException

    g = Github(github_token)
    user = g.get_user()

    # Check if repo exists first
    try:
        existing_repo = g.get_repo(f"{user.login}/{repo_name}")
        # If we get here, the repo already exists
        print(Fore.YELLOW + f"Repository '{repo_name}' already exists.")
        use_existing = input("Do you want to use the existing repository instead? (y/n): ").strip().lower()
        if use_existing == 'y':
            print(Fore.GREEN + f"✔ Using existing repository '{repo_name}'.")
            return existing_repo
        else:
            print(Fore.RED + "✘ Repository already exists. Exiting.")
            sys.exit(1)
    except GithubException:
        # Repo does not exist, create it
        pass

    try:
        repo = user.create_repo(repo_name, private=False, auto_init=False)
        print(Fore.GREEN + f"✔ Repository '{repo_name}' successfully created.")
        return repo
    except GithubException as e:
        print(Fore.RED + f"✘ Error creating the repository: {e.data['message']}")
        sys.exit(1)

def upload_project(repo_name, github_token, project_path, verbose=False):
    from github import Github

    if not os.path.isdir(os.path.join(project_path, ".git")):
        print(Fore.YELLOW + "Initializing Git repository...")
        run_command("git init", cwd=project_path, verbose=verbose)

    github_username = get_github_username(github_token)
    remote_url = f"https://github.com/{github_username}/{repo_name}.git"
    print(Fore.YELLOW + f"Setting remote 'origin' to {remote_url}")
    run_command("git remote remove origin", cwd=project_path, verbose=verbose, check=False)
    run_command(f"git remote add origin {remote_url}", cwd=project_path, verbose=verbose)

    print(Fore.YELLOW + "Adding files to Git...")
    run_command("git add .", cwd=project_path, verbose=verbose)
    commit_message = "Initial commit"
    returncode, stdout, _ = run_command(f'git commit -m "{commit_message}"', cwd=project_path, verbose=verbose, check=False)
    commit_output = stdout.lower() if stdout else ''
    if returncode != 0:
        if "nothing to commit" in commit_output or "working tree clean" in commit_output:
            print(Fore.YELLOW + "Nothing to commit. Skipping commit step.")
        else:
            print(Fore.RED + f"✘ Error during git commit:\n{stdout}")
            sys.exit(1)
    else:
        print(Fore.GREEN + "✔ Commit created.")

    print(Fore.YELLOW + "Pushing files to GitHub...")
    # Pushing may fail if GitHub push protection detects a secret.
    try:
        run_command("git branch -M main", cwd=project_path, verbose=verbose)
        run_command("git push -u origin main -f", cwd=project_path, verbose=verbose)
    except SystemExit:
        # If push fails due to GH push protection, instruct user to fix
        print(Fore.RED + "✘ Push failed due to repository rule violations (e.g., secret scanning).")
        print(Fore.RED + "Please remove any secrets from your files and commit again, or follow GitHub's instructions.")
        sys.exit(1)

    print(Fore.GREEN + f"✔ Project successfully uploaded to repository '{repo_name}'.")

def get_github_username(github_token):
    from github import Github
    g = Github(github_token)
    user = g.get_user()
    return user.login

def add_github_actions_workflow(workflow_content, project_path, verbose=False):
    workflow_dir = os.path.join(project_path, '.github', 'workflows')

    if os.path.exists(workflow_dir):
        for filename in os.listdir(workflow_dir):
            file_path = os.path.join(workflow_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                if verbose:
                    print(Fore.YELLOW + f"Removed old workflow file: {file_path}")
    else:
        os.makedirs(workflow_dir, exist_ok=True)

    workflow_path = os.path.join(workflow_dir, 'build_ios.yml')
    with open(workflow_path, 'w', encoding='utf-8') as f:
        f.write(workflow_content)
    print(Fore.GREEN + "✔ GitHub Actions workflow file successfully created locally.")

    run_command(f"git add {workflow_dir}", cwd=project_path, verbose=verbose)
    commit_message = "Update GitHub Actions workflow for iOS build"
    returncode, stdout, _ = run_command(f'git commit -m "{commit_message}"', cwd=project_path, verbose=verbose, check=False)
    commit_output = stdout.lower() if stdout else ''
    if returncode != 0:
        if "nothing to commit" in commit_output or "working tree clean" in commit_output:
            print(Fore.YELLOW + "Workflow file already committed or no changes. Skipping commit step.")
        else:
            print(Fore.RED + f"✘ Error during git commit:\n{stdout}")
            sys.exit(1)
    else:
        print(Fore.GREEN + "✔ Workflow commit created.")

    print(Fore.YELLOW + "Pushing workflow to GitHub...")
    try:
        run_command("git push", cwd=project_path, verbose=verbose)
    except SystemExit:
        print(Fore.RED + "✘ Push failed due to repository rule violations. Please fix the issue and try again.")
        sys.exit(1)
    print(Fore.GREEN + "✔ GitHub Actions workflow file successfully pushed to repository.")
    print(Fore.YELLOW + "Waiting for GitHub to recognize the workflow...")
    time.sleep(20)

def set_workflow_permissions(repo_name, github_token, verbose=False):
    print(Fore.YELLOW + "Setting GitHub Actions permissions to 'Read and write'...")
    owner = get_github_username(github_token)
    url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/permissions"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "enabled": True,
        "allowed_actions": "all",
        "permissions": {
            "contents": "write"
        }
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code in [200, 204]:
        print(Fore.GREEN + "✔ GitHub Actions permissions successfully set to 'Read and write'.")
    else:
        print(Fore.RED + f"✘ Failed to set GitHub Actions permissions: {response.status_code} - {response.text}")
        sys.exit(1)

def trigger_workflow_dispatch(repo_name, github_token, verbose=False):
    print(Fore.YELLOW + "Triggering GitHub Actions workflow via API...")
    owner = get_github_username(github_token)
    url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/workflows/build_ios.yml/dispatches"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"ref": "main"}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code in [204]:
        print(Fore.GREEN + "✔ Workflow dispatch event triggered successfully.")
    else:
        print(Fore.RED + f"✘ Failed to trigger workflow dispatch: {response.status_code} - {response.text}")
        sys.exit(1)

def wait_for_workflow_completion(repo, github_token, build_timeout, poll_interval, verbose=False):
    from github import Github
    g = Github(github_token)
    user = g.get_user()
    repository = g.get_repo(f"{user.login}/{repo.name}")
    print(Fore.YELLOW + "Waiting for the GitHub Actions workflow to start...")
    start_time = time.time()
    workflow_run = None
    while time.time() - start_time < build_timeout:
        workflows = repository.get_workflows()
        if workflows.totalCount == 0:
            print(Fore.YELLOW + "No workflows found. Waiting...")
            time.sleep(poll_interval)
            continue

        workflow = next((wf for wf in workflows if wf.name == "iOS Build"), None)
        if not workflow:
            print(Fore.YELLOW + "Workflow 'iOS Build' not found. Waiting...")
            time.sleep(poll_interval)
            continue

        runs = workflow.get_runs(branch="main")
        if runs.totalCount == 0:
            print(Fore.YELLOW + "No workflow runs found. Waiting...")
            time.sleep(poll_interval)
            continue

        workflow_run = runs[0]
        if workflow_run.status != "completed":
            print(Fore.YELLOW + f"Workflow run {workflow_run.id} is '{workflow_run.status}'. Waiting...")
            time.sleep(poll_interval)
        else:
            if workflow_run.conclusion == "success":
                print(Fore.GREEN + "✔ GitHub Actions workflow completed successfully.")
                if verbose:
                    download_and_display_workflow_logs(repository, workflow_run.id, github_token)
                return
            else:
                print(Fore.RED + f"✘ GitHub Actions workflow failed: {workflow_run.conclusion}")
                if verbose:
                    download_and_display_workflow_logs(repository, workflow_run.id, github_token)
                sys.exit(1)
    print(Fore.RED + "✘ Timeout reached. Workflow did not complete in time.")
    sys.exit(1)

def download_and_display_workflow_logs(repository, run_id, github_token):
    print(Fore.YELLOW + "Downloading workflow logs...")
    logs_url = f"https://api.github.com/repos/{repository.full_name}/actions/runs/{run_id}/logs"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(logs_url, headers=headers)
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as thezip:
            for zipinfo in thezip.infolist():
                with thezip.open(zipinfo) as thefile:
                    print(Fore.CYAN + f"\n--- Log file: {zipinfo.filename} ---")
                    log_content = thefile.read().decode('utf-8', errors='ignore')
                    print(Fore.WHITE + log_content)
    else:
        print(Fore.RED + f"✘ Failed to download workflow logs: {response.status_code} - {response.text}")

def download_ipa(repo, builds_dir, ipa_name, verbose=False):
    print(Fore.YELLOW + "Fetching the latest release...")
    releases = repo.get_releases()
    if releases.totalCount == 0:
        print(Fore.RED + "✘ No releases found.")
        sys.exit(1)
    latest_release = releases[0]
    assets = latest_release.get_assets()
    ipa_asset = next((asset for asset in assets if asset.name.endswith(".ipa")), None)
    if not ipa_asset:
        print(Fore.RED + "✘ No IPA file found in the latest release.")
        sys.exit(1)
    download_url = ipa_asset.browser_download_url
    print(Fore.GREEN + f"✔ IPA download URL: {download_url}")
    os.makedirs(builds_dir, exist_ok=True)
    ipa_path = os.path.join(builds_dir, ipa_name)
    print(Fore.YELLOW + f"Downloading the IPA file to '{ipa_path}'...")
    try:
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(ipa_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(Fore.GREEN + f"✔ IPA successfully downloaded to '{ipa_path}'.")
    except Exception as e:
        print(Fore.RED + f"✘ Error downloading the IPA: {e}")
        sys.exit(1)

def get_workflow_yaml(ipa_name):
    yaml_content = f"""
    name: iOS Build

    on:
      workflow_dispatch:

    permissions:
      contents: write

    jobs:
      build-ios:
        name: iOS Build
        runs-on: macos-latest
        steps:
          - uses: actions/checkout@v3
          - uses: subosito/flutter-action@v2
            with:
              channel: 'stable'
              architecture: x64
          - run: flutter pub get
          - run: pod repo update
            working-directory: ios
          - run: flutter build ios --release --no-codesign
          - run: mkdir Payload
            working-directory: build/ios/iphoneos
          - run: mv Runner.app/ Payload
            working-directory: build/ios/iphoneos
          - name: Zip output
            run: zip -qq -r -9 {ipa_name} Payload
            working-directory: build/ios/iphoneos
          - name: Upload binaries to release
            uses: svenstaro/upload-release-action@v2
            with:
              repo_token: ${{{{ secrets.GITHUB_TOKEN }}}}
              file: build/ios/iphoneos/{ipa_name}
              tag: v1.0
              overwrite: true
              body: "This is first release"
    """
    return textwrap.dedent(yaml_content)

def check_and_install_dependencies(verbose=False):
    check_and_install_git(verbose=verbose)
    check_and_install_gh(verbose=verbose)
    install_python_packages(verbose=verbose)

def delete_old_workflow_runs(repo, github_token, verbose=False):
    from github import Github

    print(Fore.YELLOW + "Deleting old workflow runs...")
    g = Github(github_token)
    user = g.get_user()
    repository = g.get_repo(f"{user.login}/{repo.name}")
    workflows = repository.get_workflows()

    for workflow in workflows:
        runs = workflow.get_runs()
        for run in runs:
            try:
                run.delete()
                if verbose:
                    print(Fore.YELLOW + f"Deleted workflow run {run.id} for '{workflow.name}'.")
            except Exception as e:
                print(Fore.RED + f"✘ Failed to delete workflow run {run.id}: {e}")
    print(Fore.GREEN + "✔ All old workflow runs deleted.")

def main():
    print_ascii_art()
    parser = argparse.ArgumentParser(
        description="Automates creation and management of GitHub repositories for Flutter iOS projects."
    )
    parser.add_argument('--token', '-t', type=str, help='GitHub Personal Access Token.')
    parser.add_argument('--action', '-a', choices=['createrepo', 'repo'], required=True, help="Action: 'createrepo' or 'repo'")
    parser.add_argument('--repo', '-r', type=str, required=True, help='GitHub repository name.')
    parser.add_argument('--ipa-name', type=str, default='FlutterIpaExport.ipa', help='Name of the IPA file.')
    parser.add_argument('--build-dir', type=str, default='builds', help='Directory to store builds.')
    parser.add_argument('--project-path', '-p', type=str, default='.', help='Path to Flutter project.')
    parser.add_argument('--skip-dependencies', action='store_true', help='Skip installing dependencies.')
    parser.add_argument('--skip-build', action='store_true', help='Skip build and IPA download.')
    parser.add_argument('--skip-upload', action='store_true', help='Skip uploading project to GitHub.')
    parser.add_argument('--build-timeout', type=int, default=1800, help='Build timeout in seconds.')
    parser.add_argument('--poll-interval', type=int, default=30, help='Polling interval in seconds.')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output.')

    args = parser.parse_args()
    BUILD_TIMEOUT = args.build_timeout
    POLL_INTERVAL = args.poll_interval
    BUILD_DIR = args.build_dir
    IPA_NAME = args.ipa_name
    PROJECT_PATH = args.project_path

    github_token = get_github_token(args)

    if not args.skip_dependencies:
        check_and_install_dependencies(verbose=args.verbose)
    else:
        print(Fore.YELLOW + "Skipping dependency checks.")

    from github import Github, GithubException
    g = Github(github_token)
    user = g.get_user()

    repo_name = args.repo
    action = args.action

    if action == "createrepo":
        repo = create_repo(repo_name, github_token, verbose=args.verbose)
        set_workflow_permissions(repo_name, github_token, verbose=args.verbose)
        if not args.skip_upload:
            upload_project(repo_name, github_token, project_path=PROJECT_PATH, verbose=args.verbose)
        else:
            print(Fore.YELLOW + "Skipping project upload.")
    elif action == "repo":
        try:
            repo = g.get_repo(f"{user.login}/{repo_name}")
            print(Fore.GREEN + f"✔ Repository '{repo_name}' found.")
            set_workflow_permissions(repo_name, github_token, verbose=args.verbose)
            delete_old_workflow_runs(repo, github_token, verbose=args.verbose)
        except GithubException:
            print(Fore.RED + f"✘ Repository '{repo_name}' not found.")
            sys.exit(1)

        if not args.skip_upload:
            upload_project(repo_name, github_token, project_path=PROJECT_PATH, verbose=args.verbose)
        else:
            print(Fore.YELLOW + "Skipping project upload.")

    workflow_yaml = get_workflow_yaml(IPA_NAME)
    add_github_actions_workflow(workflow_yaml, project_path=PROJECT_PATH, verbose=args.verbose)

    if not args.skip_build:
        trigger_workflow_dispatch(repo_name, github_token, verbose=args.verbose)
        wait_for_workflow_completion(repo, github_token, BUILD_TIMEOUT, POLL_INTERVAL, verbose=args.verbose)
        download_ipa(repo, BUILD_DIR, IPA_NAME, verbose=args.verbose)
    else:
        print(Fore.YELLOW + "Skipping build and download steps.")

if __name__ == "__main__":
    main()
