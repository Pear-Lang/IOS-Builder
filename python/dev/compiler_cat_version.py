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
import json
import hashlib

from colorama import init, Fore, Style
from termcolor import colored
from tqdm import tqdm

from github import Github, GithubException

init(autoreset=True)


def print_ascii_art():
    print(r"""              
                                           \`*-.                   
                                            )  _`-.                
                                            .  : `. .               
                                            : _   '  \              
                                            ; *` _.   `*-._         
                                            `-.-'          `-.      
                                              ;       `       `.    
                                              :.       .        \   
                                              . \  .   :   .-'   .  
                                              '  `+.;  ;  '      :  
                                              :  '  |    ;       ;-.
                                              ; '   : :`-:     _.`* ;
                                           .*' /  .*' ; .*`- +'  `*'
                                           `*-*   `*-*  `*-*'          
    """)
    print('\n')


def run_command(command, cwd=None, verbose=True, check=True, use_tqdm=False):
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
        if use_tqdm:
            for line in tqdm(iter(process.stdout.readline, ''), desc=command, unit='line'):
                if line:
                    stdout += line
                    if verbose:
                        print(Fore.WHITE + line.strip())
        else:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                stdout += line
                if verbose:
                    print(Fore.WHITE + line.strip())
        returncode = process.wait()
        if returncode != 0 and check:
            print(Fore.RED + f"Command '{command}' failed with return code {returncode}.")
            sys.exit(1)
        return returncode, stdout, ''
    except subprocess.CalledProcessError as e:
        if check:
            print(Fore.RED + f"Error executing: {command}")
            sys.exit(1)
        else:
            return e.returncode, e.output, ''


def open_new_window_and_run(command):
    current_os = platform.system()
    if current_os == "Windows":
        subprocess.run(f'start cmd /c "{command}"', shell=True)
    elif current_os == "Darwin":  # macOS
        subprocess.run(f'osascript -e \'tell application "Terminal" to do script "{command}"\'', shell=True)
    else:
        subprocess.run(f'{command}', shell=True)


def install_python_packages(package_versions=None, verbose=False):
    required_packages = {
        'PyGithub': 'PyGithub',
        'requests': 'requests',
        'colorama': 'colorama',
        'termcolor': 'termcolor',
        'tqdm': 'tqdm'
    }
    if package_versions:
        required_packages.update(package_versions)
    for package, spec in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            print(Fore.YELLOW + f"Installing missing Python package: {package}")
            if sys.argv[0].endswith('.exe'):
                print(Fore.YELLOW + f"Running as .exe. Opening new Python window to install {package}...")
                python_path = shutil.which("python") or "python"
                open_new_window_and_run(f'{python_path} -m pip install {spec}')
                print(Fore.YELLOW + "Relaunching the script with the same arguments...")
                subprocess.run([sys.executable] + sys.argv)
                sys.exit(0)
            else:
                run_command(f"{sys.executable} -m pip install {spec}", verbose=verbose)


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
        print(Fore.RED + "Chocolatey is not installed. Please install Chocolatey.")
        sys.exit(1)

    print(Fore.YELLOW + f"Installing {package} with Chocolatey...")
    run_command(f"choco install {package} -y", verbose=verbose)


def install_with_apt(package, verbose=False):
    try:
        run_command("sudo apt-get update", verbose=verbose)
        run_command(f"sudo apt-get install -y {package}", verbose=verbose)
    except:
        print(Fore.RED + f"Error installing {package} with apt. Please install manually.")
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
        print(Fore.RED + "Homebrew is not installed. Please install Homebrew.")
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
        print(Fore.RED + "Git installation not supported automatically. Install manually.")
        sys.exit(1)


def check_and_install_git(verbose=False):
    try:
        returncode, stdout, _ = run_command("git --version", verbose=verbose, check=False)
        if returncode == 0:
            print(Fore.GREEN + "Git is installed.")
            return
    except:
        pass
    print(Fore.YELLOW + "Git is not installed. Installing now...")
    install_git(verbose=verbose)
    run_command("git --version", verbose=verbose)


def install_gh(verbose=False):
    current_os = platform.system()
    if current_os == "Windows":
        install_with_chocolatey("gh", verbose=verbose)
    elif current_os == "Linux":
        install_with_apt("gh", verbose=verbose)
    elif current_os == "Darwin":
        install_with_homebrew("gh", verbose=verbose)
    else:
        print(Fore.RED + "Installing GitHub CLI not supported automatically. Install manually.")
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
        returncode, stdout, _ = run_command("gh --version", verbose=verbose, check=False)
        if returncode == 0:
            print(Fore.GREEN + "GitHub CLI (gh) is installed.")
            _, auth_status, _ = run_command("gh auth status", verbose=verbose, check=False)
            if "not logged into any GitHub hosts" in auth_status:
                print(Fore.YELLOW + "GitHub CLI not authenticated. Please authenticate.")
                if platform.system() == "Windows":
                    open_new_window_and_run('gh auth login')
                    open_new_window_and_run('gh auth setup-git')
                else:
                    run_command("gh auth login", verbose=verbose)
                    run_command("gh auth setup-git", verbose=verbose)
            return
    except:
        pass
    print(Fore.YELLOW + "GitHub CLI (gh) not installed.")
    install_gh(verbose=verbose)


def get_github_token(args):
    token = args.token or os.getenv('GITHUB_TOKEN')
    if not token:
        token = input(Fore.CYAN + "Please enter your GitHub Personal Access Token: ").strip()
    if not token:
        print(Fore.RED + "GitHub Token is required.")
        sys.exit(1)
    return token


def create_repo(repo_name, github_token, verbose=False):
    g = Github(github_token)
    user = g.get_user()

    # Check if repo exists first
    try:
        existing_repo = g.get_repo(f"{user.login}/{repo_name}")
        # If we get here, the repo already exists
        print(Fore.YELLOW + f"Repository '{repo_name}' already exists.")
        use_existing = input("Do you want to use the existing repository instead? (y/n): ").strip().lower()
        if use_existing == 'y':
            print(Fore.GREEN + f"Using existing repository '{repo_name}'.")
            return existing_repo
        else:
            print(Fore.RED + "Repository already exists. Exiting.")
            sys.exit(1)
    except GithubException as e:
        if e.status != 404:
            print(Fore.RED + f"Error checking repository existence: {e.data['message']}")
            sys.exit(1)
        # Repo does not exist, proceed to create it

    try:
        repo = user.create_repo(repo_name, private=False, auto_init=False)
        print(Fore.GREEN + f"Repository '{repo_name}' successfully created.")
        return repo
    except GithubException as e:
        print(Fore.RED + f"Error creating the repository: {e.data.get('message', 'Unknown error')}")
        sys.exit(1)


def upload_project(repo_name, github_token, project_path, branch, ipa_name, apk_name,
                  include_patterns=None, exclude_patterns=None, remotes=None, verbose=False):
    if not os.path.isdir(os.path.join(project_path, ".git")):
        print(Fore.YELLOW + "Initializing Git repository...")
        run_command("git init", cwd=project_path, verbose=verbose)

    github_username = get_github_username(github_token)
    remote_urls = []
    if remotes:
        for remote in remotes:
            remote_url = f"https://github.com/{remote}/{repo_name}.git"
            remote_urls.append(remote_url)
    else:
        remote_url = f"https://github.com/{github_username}/{repo_name}.git"
        remote_urls.append(remote_url)

    for remote_url in remote_urls:
        remote_hash = hashlib.md5(remote_url.encode()).hexdigest()[:6]
        remote_name = f"origin_{remote_hash}"
        print(Fore.YELLOW + f"Adding remote '{remote_name}' to {remote_url}")
        run_command(f"git remote add {remote_name} {remote_url}", cwd=project_path, verbose=verbose, check=False)

    print(Fore.YELLOW + "Adding files to Git...")
    add_command = "git add ."
    if include_patterns:
        include_str = ' '.join(include_patterns)
        add_command = f"git add {include_str}"
    if exclude_patterns:
        print(Fore.YELLOW + "Excluding specified patterns from git add.")
        for pattern in exclude_patterns:
            run_command(f"git rm -r --cached {pattern}", cwd=project_path, verbose=verbose, check=False)
    run_command(add_command, cwd=project_path, verbose=verbose)

    commit_message = "Initial commit"
    returncode, stdout, _ = run_command(f'git commit -m "{commit_message}"', cwd=project_path, verbose=verbose, check=False)
    commit_output = stdout.lower() if stdout else ''
    if returncode != 0:
        if "nothing to commit" in commit_output or "working tree clean" in commit_output:
            print(Fore.YELLOW + "Nothing to commit. Skipping commit step.")
        else:
            print(Fore.RED + f"Error during git commit:\n{stdout}")
            sys.exit(1)
    else:
        print(Fore.GREEN + "Commit created.")

    # Push to all remotes
    for remote_url in remote_urls:
        remote_hash = hashlib.md5(remote_url.encode()).hexdigest()[:6]
        remote_name = f"origin_{remote_hash}"
        try:
            run_command(f"git branch -M {branch}", cwd=project_path, verbose=verbose)
            run_command(f"git push -u {remote_name} {branch} -f", cwd=project_path, verbose=verbose)
            print(Fore.GREEN + f"Project successfully uploaded to repository '{repo_name}' at remote '{remote_name}'.")
        except SystemExit:
            # If push fails due to GH push protection, instruct user to fix
            print(Fore.RED + f"Push to '{remote_name}' failed due to repository rule violations (e.g., secret scanning).")
            print(Fore.RED + "Please remove any secrets from your files and commit again, or follow GitHub's instructions.")
            sys.exit(1)

    print(Fore.GREEN + f"Project successfully uploaded to repository '{repo_name}'.")


def get_github_username(github_token):
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

    workflow_path = os.path.join(workflow_dir, 'build.yml')
    with open(workflow_path, 'w', encoding='utf-8') as f:
        f.write(workflow_content)
    print(Fore.GREEN + "GitHub Actions workflow file successfully created locally.")

    run_command(f"git add {workflow_dir}", cwd=project_path, verbose=verbose)
    commit_message = "Update GitHub Actions workflow"
    returncode, stdout, _ = run_command(f'git commit -m "{commit_message}"', cwd=project_path, verbose=verbose, check=False)
    commit_output = stdout.lower() if stdout else ''
    if returncode != 0:
        if "nothing to commit" in commit_output or "working tree clean" in commit_output:
            print(Fore.YELLOW + "Workflow file already committed or no changes. Skipping commit step.")
        else:
            print(Fore.RED + f"Error during git commit:\n{stdout}")
            sys.exit(1)
    else:
        print(Fore.GREEN + "Workflow commit created.")

    print(Fore.YELLOW + "Pushing workflow to GitHub...")
    try:
        run_command("git push", cwd=project_path, verbose=verbose)
    except SystemExit:
        print(Fore.RED + "Push failed due to repository rule violations. Please fix the issue and try again.")
        sys.exit(1)
    print(Fore.GREEN + "GitHub Actions workflow file successfully pushed to repository.")

    print(Fore.YELLOW + "Waiting for GitHub to register the new workflow...")
    time.sleep(10)  # Wait for 10 seconds


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
        print(Fore.GREEN + "GitHub Actions permissions successfully set to 'Read and write'.")
    else:
        print(Fore.RED + f"Failed to set GitHub Actions permissions: {response.status_code} - {response.text}")
        sys.exit(1)


def trigger_workflow_dispatch(repo_name, github_token, branch, verbose=False):
    print(Fore.YELLOW + "Triggering GitHub Actions workflow via API...")
    owner = get_github_username(github_token)
    url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/workflows/build.yml/dispatches"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"ref": branch}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 204:
        print(Fore.GREEN + "Workflow dispatch event triggered successfully.")
    else:
        print(Fore.RED + f"Failed to trigger workflow dispatch: {response.status_code} - {response.text}")
        sys.exit(1)


def wait_for_workflow_completion(repo, github_token, build_timeout, poll_interval, branch, verbose=False):
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

        # List all workflow names for debugging
        if verbose:
            print(Fore.CYAN + "Available Workflows:")
            for wf in workflows:
                print(f"- {wf.name}")

        # Adjusted to search for the correct workflow name
        workflow = next((wf for wf in workflows if wf.name.lower() == "build"), None)
        if not workflow:
            print(Fore.YELLOW + "Workflow 'Build' not found. Waiting...")
            time.sleep(poll_interval)
            continue

        runs = workflow.get_runs(branch=branch, event="workflow_dispatch")
        if runs.totalCount == 0:
            print(Fore.YELLOW + "No workflow runs found for 'Build'. Waiting...")
            time.sleep(poll_interval)
            continue

        workflow_run = runs[0]
        print(Fore.CYAN + f"Found Workflow Run ID: {workflow_run.id} | Status: {workflow_run.status} | Conclusion: {workflow_run.conclusion}")

        if workflow_run.status != "completed":
            print(Fore.YELLOW + f"Workflow run {workflow_run.id} is '{workflow_run.status}'. Waiting...")
            time.sleep(poll_interval)
        else:
            if workflow_run.conclusion == "success":
                print(Fore.GREEN + "GitHub Actions workflow completed successfully.")
                if verbose:
                    download_and_display_workflow_logs(repository, workflow_run.id, github_token)
                return
            else:
                print(Fore.RED + f"GitHub Actions workflow failed: {workflow_run.conclusion}")
                if verbose:
                    download_and_display_workflow_logs(repository, workflow_run.id, github_token)
                sys.exit(1)
    print(Fore.RED + "Timeout reached. Workflow did not complete in time.")
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
        print(Fore.RED + f"Failed to download workflow logs: {response.status_code} - {response.text}")


def download_artifact(repo, artifact_name, builds_dir, file_extension, verbose=False):
    print(Fore.YELLOW + f"Fetching the latest release for {file_extension.upper()}...")
    releases = repo.get_releases()
    if releases.totalCount == 0:
        print(Fore.RED + "No releases found.")
        sys.exit(1)
    latest_release = releases[0]
    assets = latest_release.get_assets()
    artifact_asset = next((asset for asset in assets if asset.name.endswith(file_extension)), None)
    if not artifact_asset:
        print(Fore.RED + f"No {file_extension.upper()} file found in the latest release.")
        sys.exit(1)
    download_url = artifact_asset.browser_download_url
    print(Fore.GREEN + f"{file_extension.upper()} download URL: {download_url}")
    os.makedirs(builds_dir, exist_ok=True)
    artifact_path = os.path.join(builds_dir, artifact_asset.name)
    print(Fore.YELLOW + f"Downloading the {file_extension.upper()} file to '{artifact_path}'...")
    try:
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(artifact_path, 'wb') as f, tqdm(
                desc=artifact_asset.name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    bar.update(size)
        print(Fore.GREEN + f"{file_extension.upper()} successfully downloaded to '{artifact_path}'.")
    except Exception as e:
        print(Fore.RED + f"Error downloading the {file_extension.upper()}: {e}")
        sys.exit(1)


def get_workflow_yaml(platforms, ipa_name, apk_name, branch):
    yaml_content = f"""
    name: Build

    on:
      workflow_dispatch:

    permissions:
      contents: write

    jobs:
    """
    for platform in platforms:
        if platform.lower() == 'ios':
            yaml_content += f"""
      build-ios:
        name: iOS Build
        runs-on: macos-latest
        steps:
          - uses: actions/checkout@v3
          - uses: subosito/flutter-action@v2
            with:
              channel: 'stable'
              architecture: x64
          - run: flutter config --no-analytics
          - run: flutter pub get
          - run: pod repo update
            working-directory: ios
          - run: flutter build ios --release --no-codesign --verbose
          - name: Verify Build Output
            run: ls -la build/ios/iphoneos
          - run: mkdir Payload
            working-directory: build/ios/iphoneos
          - run: mv Runner.app Payload
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
              body: "This is the first release"
    """
        elif platform.lower() == 'android':
            yaml_content += f"""
      build-android:
        name: Android Build
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - uses: subosito/flutter-action@v2
            with:
              channel: 'stable'
              architecture: x64
          - run: flutter pub get
          - run: flutter build apk --release --verbose
          - name: Upload APK to release
            uses: svenstaro/upload-release-action@v2
            with:
              repo_token: ${{{{ secrets.GITHUB_TOKEN }}}}
              file: build/app/outputs/flutter-apk/{apk_name}
              tag: v1.0
              overwrite: true
              body: "This is the first release"
    """
    return textwrap.dedent(yaml_content)


def check_and_install_dependencies(package_versions=None, verbose=False):
    check_and_install_git(verbose=verbose)
    check_and_install_gh(verbose=verbose)
    install_python_packages(package_versions=package_versions, verbose=verbose)


def delete_old_workflow_runs(repo, github_token, verbose=False):
    print(Fore.YELLOW + "Deleting old workflow runs...")
    g = Github(github_token)
    user = g.get_user()
    repository = g.get_repo(f"{user.login}/{repo.name}")
    workflows = repository.get_workflows()

    for workflow in workflows:
        print(Fore.CYAN + f"Processing Workflow: {workflow.name}")
        runs = workflow.get_runs()
        for run in runs:
            try:
                print(Fore.CYAN + f"Attempting to delete Workflow Run ID: {run.id} | Status: {run.status}")
                run.delete()
                print(Fore.GREEN + f"Deleted workflow run {run.id} for '{workflow.name}'.")
            except GithubException as e:
                print(Fore.RED + f"Failed to delete workflow run {run.id}: {e.data.get('message', 'Unknown error')}")
            except Exception as e:
                print(Fore.RED + f"Unexpected error deleting workflow run {run.id}: {e}")
    print(Fore.GREEN + "All old workflow runs attempted to be deleted.")


def cache_dependencies(project_path, cache_dir, verbose=False):
    print(Fore.YELLOW + "Caching dependencies...")
    cache_path = os.path.join(cache_dir, 'flutter_packages')
    if not os.path.exists(cache_path):
        os.makedirs(cache_path, exist_ok=True)
    src = os.path.join(project_path, 'pubspec.lock')
    dest = os.path.join(cache_path, 'pubspec.lock')
    if os.path.exists(src):
        shutil.copy(src, dest)
        if verbose:
            print(Fore.GREEN + f"Cached pubspec.lock to {dest}")
    print(Fore.GREEN + "Dependencies cached.")


def restore_cached_dependencies(project_path, cache_dir, verbose=False):
    print(Fore.YELLOW + "Restoring cached dependencies...")
    cache_path = os.path.join(cache_dir, 'flutter_packages', 'pubspec.lock')
    src = cache_path
    dest = os.path.join(project_path, 'pubspec.lock')
    if os.path.exists(src):
        shutil.copy(src, dest)
        if verbose:
            print(Fore.GREEN + f"Restored pubspec.lock from {src}")
    else:
        print(Fore.YELLOW + "No cached dependencies found.")


def interactive_wizard(args):
    print(Fore.CYAN + "Entering Interactive Mode...\n")
    token = args.token or os.getenv('GITHUB_TOKEN') or input("GitHub Personal Access Token: ").strip()
    if not token:
        print(Fore.RED + "GitHub Token is required.")
        sys.exit(1)
    action = input("Select action ('createrepo' or 'repo'): ").strip().lower()
    while action not in ['createrepo', 'repo']:
        action = input("Invalid action. Select 'createrepo' or 'repo': ").strip().lower()
    repo = input("Enter GitHub repository name: ").strip()
    ipa_name = input("Enter IPA file name (default 'FlutterIpaExport.ipa'): ").strip() or 'FlutterIpaExport.ipa'
    apk_name = input("Enter APK file name (default 'FlutterApkExport.apk'): ").strip() or 'FlutterApkExport.apk'
    build_dir = input("Enter build directory (default 'builds'): ").strip() or 'builds'
    project_path = input("Enter path to Flutter project (default '.'): ").strip() or '.'
    skip_dependencies = input("Skip installing dependencies? (y/n, default 'n'): ").strip().lower() == 'y'
    skip_build = input("Skip build and download steps? (y/n, default 'n'): ").strip().lower() == 'y'
    skip_upload = input("Skip uploading project to GitHub? (y/n, default 'n'): ").strip().lower() == 'y'
    build_timeout = int(input("Enter build timeout in seconds (default '1800'): ").strip() or '1800')
    poll_interval = int(input("Enter polling interval in seconds (default '30'): ").strip() or '30')
    verbose = input("Enable verbose output? (y/n, default 'n'): ").strip().lower() == 'y'
    branch = input("Enter branch name (default 'main'): ").strip() or 'main'
    platforms_input = input("Select platforms to build (comma-separated, options: iOS, Android, default 'iOS'): ").strip()
    platforms = [p.strip() for p in platforms_input.split(',')] if platforms_input else ['iOS']
    include_specific = input("Do you want to include specific files? (y/n, default 'n'): ").strip().lower() == 'y'
    include_patterns = [p.strip() for p in input("Enter file patterns to include (comma-separated, leave blank for all): ").strip().split(',')] if include_specific else None
    exclude_specific = input("Do you want to exclude specific files? (y/n, default 'n'): ").strip().lower() == 'y'
    exclude_patterns = [p.strip() for p in input("Enter file patterns to exclude (comma-separated, leave blank for none): ").strip().split(',')] if exclude_specific else None
    remotes_input = input("Enter additional GitHub usernames for multiple remotes (comma-separated, leave blank for none): ").strip()
    remotes = [r.strip() for r in remotes_input.split(',')] if remotes_input else None

    args.action = action
    args.repo = repo
    args.ipa_name = ipa_name
    args.apk_name = apk_name
    args.build_dir = build_dir
    args.project_path = project_path
    args.skip_dependencies = skip_dependencies
    args.skip_build = skip_build
    args.skip_upload = skip_upload
    args.build_timeout = build_timeout
    args.poll_interval = poll_interval
    args.verbose = verbose
    args.branch = branch
    args.platforms = platforms
    args.include = include_patterns
    args.exclude = exclude_patterns
    args.remotes = remotes
    args.token = token


def main():
    print_ascii_art()
    parser = argparse.ArgumentParser(
        description="Automates creation and management of GitHub repositories for Flutter projects."
    )
    parser.add_argument('--token', '-t', type=str, help='GitHub Personal Access Token.')
    parser.add_argument('--action', '-a', choices=['createrepo', 'repo'], help="Action: 'createrepo' or 'repo'")
    parser.add_argument('--repo', '-r', type=str, help='GitHub repository name.')
    parser.add_argument('--ipa-name', type=str, default='FlutterIpaExport.ipa', help='Name of the IPA file.')
    parser.add_argument('--apk-name', type=str, default='FlutterApkExport.apk', help='Name of the APK file.')
    parser.add_argument('--build-dir', type=str, default='builds', help='Directory to store builds.')
    parser.add_argument('--project-path', '-p', type=str, default='.', help='Path to Flutter project.')
    parser.add_argument('--skip-dependencies', action='store_true', help='Skip installing dependencies.')
    parser.add_argument('--skip-build', action='store_true', help='Skip build and download.')
    parser.add_argument('--skip-upload', action='store_true', help='Skip uploading project to GitHub.')
    parser.add_argument('--build-timeout', type=int, default=1800, help='Build timeout in seconds.')
    parser.add_argument('--poll-interval', type=int, default=30, help='Polling interval in seconds.')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output.')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode.')
    parser.add_argument('--branch', type=str, default='main', help='Branch name to use.')
    parser.add_argument('--platforms', type=str, nargs='+', choices=['iOS', 'Android'], default=['iOS'], help='Platforms to build.')
    parser.add_argument('--include', type=str, nargs='+', help='File patterns to include.')
    parser.add_argument('--exclude', type=str, nargs='+', help='File patterns to exclude.')
    parser.add_argument('--remotes', type=str, nargs='+', help='Additional GitHub usernames for multiple remotes.')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.interactive:
        interactive_wizard(args)

    BUILD_TIMEOUT = args.build_timeout
    POLL_INTERVAL = args.poll_interval
    BUILD_DIR = args.build_dir
    IPA_NAME = args.ipa_name
    APK_NAME = args.apk_name
    PROJECT_PATH = args.project_path
    BRANCH = args.branch
    PLATFORMS = args.platforms
    INCLUDE_PATTERNS = args.include
    EXCLUDE_PATTERNS = args.exclude
    REMOTES = args.remotes

    github_token = get_github_token(args)

    if not args.skip_dependencies:
        check_and_install_dependencies(verbose=args.verbose)
        cache_dependencies(PROJECT_PATH, os.path.join(PROJECT_PATH, '.cache'), verbose=args.verbose)
    else:
        print(Fore.YELLOW + "Skipping dependency checks.")

    g = Github(github_token)
    user = g.get_user()

    repo_name = args.repo
    action = args.action

    if not action:
        print(Fore.RED + "Action is required. Use '--action createrepo' or '--action repo'.")
        sys.exit(1)

    if action == "createrepo":
        repo = create_repo(repo_name, github_token, verbose=args.verbose)
        set_workflow_permissions(repo_name, github_token, verbose=args.verbose)
        # Delete old workflow runs (if any)
        delete_old_workflow_runs(repo, github_token, verbose=args.verbose)
        if not args.skip_upload:
            upload_project(
                repo_name,
                github_token,
                project_path=PROJECT_PATH,
                branch=BRANCH,
                ipa_name=IPA_NAME,
                apk_name=APK_NAME,
                include_patterns=INCLUDE_PATTERNS,
                exclude_patterns=EXCLUDE_PATTERNS,
                remotes=REMOTES,
                verbose=args.verbose
            )
        else:
            print(Fore.YELLOW + "Skipping project upload.")
    elif action == "repo":
        try:
            repo = g.get_repo(f"{user.login}/{repo_name}")
            print(Fore.GREEN + f"Repository '{repo_name}' found.")
            set_workflow_permissions(repo_name, github_token, verbose=args.verbose)
            delete_old_workflow_runs(repo, github_token, verbose=args.verbose)
        except GithubException as e:
            print(Fore.RED + f"Repository '{repo_name}' not found or inaccessible: {e.data.get('message', 'Unknown error')}")
            sys.exit(1)

        if not args.skip_upload:
            upload_project(
                repo_name,
                github_token,
                project_path=PROJECT_PATH,
                branch=BRANCH,
                ipa_name=IPA_NAME,
                apk_name=APK_NAME,
                include_patterns=INCLUDE_PATTERNS,
                exclude_patterns=EXCLUDE_PATTERNS,
                remotes=REMOTES,
                verbose=args.verbose
            )
        else:
            print(Fore.YELLOW + "Skipping project upload.")

    workflow_yaml = get_workflow_yaml(PLATFORMS, IPA_NAME, APK_NAME, BRANCH)
    add_github_actions_workflow(workflow_yaml, project_path=PROJECT_PATH, verbose=args.verbose)

    if not args.skip_build:
        trigger_workflow_dispatch(repo_name, github_token, BRANCH, verbose=args.verbose)
        wait_for_workflow_completion(repo, github_token, BUILD_TIMEOUT, POLL_INTERVAL, BRANCH, verbose=args.verbose)
        if 'iOS' in PLATFORMS:
            download_artifact(repo, IPA_NAME, BUILD_DIR, '.ipa', verbose=args.verbose)
        if 'Android' in PLATFORMS:
            download_artifact(repo, APK_NAME, BUILD_DIR, '.apk', verbose=args.verbose)
    else:
        print(Fore.YELLOW + "Skipping build and download steps.")


if __name__ == "__main__":
    main()
