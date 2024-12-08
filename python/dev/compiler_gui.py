import sys
import subprocess
import time
import platform
import shutil
import os
import textwrap
import requests
import zipfile
import io
import json
import hashlib

from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox, 
    QCheckBox, QComboBox, QHBoxLayout, QInputDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor  # Importiert QTextCursor für die Log-Funktion

from colorama import init, Fore, Style
from github import Github, GithubException

init(autoreset=True)

# ================================
# Helper Functions (Modified for GUI)
# ================================

def run_command(command, cwd=None, verbose=True, check=True, use_tqdm=False, progress_callback=None):
    if verbose and progress_callback:
        progress_callback(f"➤ Running command: {command}")
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
        if use_tqdm and progress_callback:
            for line in iter(process.stdout.readline, ''):
                if line:
                    stdout += line
                    progress_callback(line.strip())
        else:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                stdout += line
                if verbose and progress_callback:
                    progress_callback(line.strip())
        returncode = process.wait()
        if returncode != 0 and check:
            if progress_callback:
                progress_callback(f"Command '{command}' failed with return code {returncode}.")
            raise subprocess.CalledProcessError(returncode, command)
        return returncode, stdout, ''
    except subprocess.CalledProcessError as e:
        if check:
            if progress_callback:
                progress_callback(f"Error executing: {command}")
            raise e
        else:
            return e.returncode, e.output, ''

def open_new_window_and_run(command, progress_callback=None):
    current_os = platform.system()
    if current_os == "Windows":
        subprocess.Popen(f'start cmd /c "{command}"', shell=True)
    elif current_os == "Darwin":  # macOS
        subprocess.Popen(f'osascript -e \'tell application "Terminal" to do script "{command}"\'', shell=True)
    else:
        subprocess.Popen(f'{command}', shell=True)

def install_python_packages(package_versions=None, verbose=False, progress_callback=None):
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
            if progress_callback:
                progress_callback(f"Installing missing Python package: {package}")
            if sys.argv[0].endswith('.exe'):
                if progress_callback:
                    progress_callback(f"Running as .exe. Opening new Python window to install {package}...")
                python_path = shutil.which("python") or "python"
                open_new_window_and_run(f'{python_path} -m pip install {spec}', progress_callback)
                if progress_callback:
                    progress_callback("Relaunching the script with the same arguments...")
                subprocess.Popen([sys.executable] + sys.argv)
                raise SystemExit
            else:
                run_command(f"{sys.executable} -m pip install {spec}", verbose=verbose, progress_callback=progress_callback)

def install_with_chocolatey(package, verbose=False, progress_callback=None):
    try:
        run_command("choco -v", verbose=verbose, check=True, progress_callback=progress_callback)
    except subprocess.CalledProcessError:
        if progress_callback:
            progress_callback("Chocolatey is not installed. Please install Chocolatey.")
        raise Exception("Chocolatey is not installed.")

    if progress_callback:
        progress_callback(f"Installing {package} with Chocolatey...")
    run_command(f"choco install {package} -y", verbose=verbose, progress_callback=progress_callback)

def install_with_apt(package, verbose=False, progress_callback=None):
    try:
        run_command("sudo apt-get update", verbose=verbose, progress_callback=progress_callback)
        run_command(f"sudo apt-get install -y {package}", verbose=verbose, progress_callback=progress_callback)
    except Exception:
        if progress_callback:
            progress_callback(f"Error installing {package} with apt. Please install manually.")
        raise Exception(f"Error installing {package} with apt.")

def install_with_homebrew(package, verbose=False, progress_callback=None):
    try:
        run_command("brew --version", verbose=verbose, check=True, progress_callback=progress_callback)
    except subprocess.CalledProcessError:
        if progress_callback:
            progress_callback("Homebrew is not installed. Please install Homebrew.")
        raise Exception("Homebrew is not installed.")

    if progress_callback:
        progress_callback(f"Installing {package} with Homebrew...")
    run_command(f"brew install {package}", verbose=verbose, progress_callback=progress_callback)

def install_git(verbose=False, progress_callback=None):
    current_os = platform.system()
    if current_os == "Windows":
        install_with_chocolatey("git", verbose=verbose, progress_callback=progress_callback)
    elif current_os == "Linux":
        install_with_apt("git", verbose=verbose, progress_callback=progress_callback)
    elif current_os == "Darwin":
        install_with_homebrew("git", verbose=verbose, progress_callback=progress_callback)
    else:
        if progress_callback:
            progress_callback("Git installation not supported automatically. Install manually.")
        raise Exception("Git installation not supported automatically.")

def check_and_install_git(verbose=False, progress_callback=None):
    try:
        returncode, stdout, _ = run_command("git --version", verbose=verbose, check=False, progress_callback=progress_callback)
        if returncode == 0:
            if progress_callback:
                progress_callback("Git is installed.")
            return
    except:
        pass
    if progress_callback:
        progress_callback("Git is not installed. Installing now...")
    install_git(verbose=verbose, progress_callback=progress_callback)
    run_command("git --version", verbose=verbose, progress_callback=progress_callback)

def install_gh(verbose=False, progress_callback=None):
    current_os = platform.system()
    if current_os == "Windows":
        install_with_chocolatey("gh", verbose=verbose, progress_callback=progress_callback)
    elif current_os == "Linux":
        install_with_apt("gh", verbose=verbose, progress_callback=progress_callback)
    elif current_os == "Darwin":
        install_with_homebrew("gh", verbose=verbose, progress_callback=progress_callback)
    else:
        if progress_callback:
            progress_callback("Installing GitHub CLI not supported automatically. Install manually.")
        raise Exception("Installing GitHub CLI not supported automatically.")

    if progress_callback:
        progress_callback("GitHub CLI (gh) installed. Opening new window for `gh auth login`...")
    if platform.system() == "Windows":
        open_new_window_and_run('gh auth login', progress_callback)
        open_new_window_and_run('gh auth setup-git', progress_callback)
    else:
        run_command("gh auth login", verbose=verbose, progress_callback=progress_callback)
        run_command("gh auth setup-git", verbose=verbose, progress_callback=progress_callback)

def check_and_install_gh(verbose=False, progress_callback=None):
    try:
        returncode, stdout, _ = run_command("gh --version", verbose=verbose, check=False, progress_callback=progress_callback)
        if returncode == 0:
            if progress_callback:
                progress_callback("GitHub CLI (gh) is installed.")
            return
        else:
            raise Exception
    except:
        if progress_callback:
            progress_callback("GitHub CLI (gh) not installed.")
        install_gh(verbose=verbose, progress_callback=progress_callback)

def get_github_token(progress_callback=None):
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        if progress_callback:
            progress_callback("Please enter your GitHub Personal Access Token.")
        token, ok = QInputDialog.getText(None, "GitHub Token", "Enter GitHub Personal Access Token:", QLineEdit.Password)
        if ok:
            token = token.strip()
    if not token:
        if progress_callback:
            progress_callback("GitHub Token is required.")
        raise Exception("GitHub Token is required.")
    return token

def create_repo(repo_name, github_token, verbose=False, progress_callback=None):
    try:
        g = Github(github_token)
        user = g.get_user()

        # Check if repo exists first
        try:
            existing_repo = g.get_repo(f"{user.login}/{repo_name}")
            if progress_callback:
                progress_callback(f"Repository '{repo_name}' already exists.")
            return existing_repo
        except GithubException as e:
            if e.status != 404:
                if progress_callback:
                    progress_callback(f"Error checking repository existence: {e.data['message']}")
                raise Exception(e.data['message'])
            # Repo does not exist, proceed to create it

        repo = user.create_repo(repo_name, private=False, auto_init=False)
        if progress_callback:
            progress_callback(f"Repository '{repo_name}' successfully created.")
        return repo
    except GithubException as e:
        if progress_callback:
            progress_callback(f"Error creating the repository: {e.data.get('message', 'Unknown error')}")
        raise Exception(e.data.get('message', 'Unknown error'))

def get_github_username(github_token, progress_callback=None):
    try:
        g = Github(github_token)
        user = g.get_user()
        return user.login
    except GithubException as e:
        if progress_callback:
            progress_callback(f"Error fetching GitHub username: {e.data.get('message', 'Unknown error')}")
        raise Exception(e.data.get('message', 'Unknown error'))

def upload_project(repo_name, github_token, project_path, branch, ipa_name, apk_name,
                  include_patterns=None, exclude_patterns=None, remotes=None, verbose=False, progress_callback=None):
    try:
        if not os.path.isdir(os.path.join(project_path, ".git")):
            if progress_callback:
                progress_callback("Initializing Git repository...")
            run_command("git init", cwd=project_path, verbose=verbose, progress_callback=progress_callback)

        github_username = get_github_username(github_token, progress_callback=progress_callback)
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
            if progress_callback:
                progress_callback(f"Adding remote '{remote_name}' to {remote_url}")
            run_command(f"git remote add {remote_name} {remote_url}", cwd=project_path, verbose=verbose, check=False, progress_callback=progress_callback)

        if progress_callback:
            progress_callback("Adding files to Git...")
        add_command = "git add ."
        if include_patterns:
            include_str = ' '.join(include_patterns)
            add_command = f"git add {include_str}"
        if exclude_patterns:
            if progress_callback:
                progress_callback("Excluding specified patterns from git add.")
            for pattern in exclude_patterns:
                run_command(f"git rm -r --cached {pattern}", cwd=project_path, verbose=verbose, check=False, progress_callback=progress_callback)
        run_command(add_command, cwd=project_path, verbose=verbose, progress_callback=progress_callback)

        commit_message = "Initial commit"
        returncode, stdout, _ = run_command(f'git commit -m "{commit_message}"', cwd=project_path, verbose=verbose, check=False, progress_callback=progress_callback)
        commit_output = stdout.lower() if stdout else ''
        if returncode != 0:
            if "nothing to commit" in commit_output or "working tree clean" in commit_output:
                if progress_callback:
                    progress_callback("Nothing to commit. Skipping commit step.")
            else:
                if progress_callback:
                    progress_callback(f"Error during git commit:\n{stdout}")
                raise Exception("Error during git commit.")
        else:
            if progress_callback:
                progress_callback("Commit created.")

        # Push to all remotes
        for remote_url in remote_urls:
            remote_hash = hashlib.md5(remote_url.encode()).hexdigest()[:6]
            remote_name = f"origin_{remote_hash}"
            try:
                run_command(f"git branch -M {branch}", cwd=project_path, verbose=verbose, progress_callback=progress_callback)
                run_command(f"git push -u {remote_name} {branch} -f", cwd=project_path, verbose=verbose, progress_callback=progress_callback)
                if progress_callback:
                    progress_callback(f"Project successfully uploaded to repository '{repo_name}' at remote '{remote_name}'.")
            except subprocess.CalledProcessError:
                if progress_callback:
                    progress_callback(f"Push to '{remote_name}' failed due to repository rule violations (e.g., secret scanning).")
                raise Exception(f"Push to '{remote_name}' failed due to repository rule violations.")

        if progress_callback:
            progress_callback(f"Project successfully uploaded to repository '{repo_name}'.")
    except Exception as e:
        if progress_callback:
            progress_callback(str(e))
        raise e

def add_github_actions_workflow(workflow_content, project_path, verbose=False, progress_callback=None):
    try:
        workflow_dir = os.path.join(project_path, '.github', 'workflows')

        if os.path.exists(workflow_dir):
            for filename in os.listdir(workflow_dir):
                file_path = os.path.join(workflow_dir, filename)
                if os.path.isfile(file_path):
                    if progress_callback:
                        progress_callback(f"Removing old workflow file: {file_path}")
                    os.remove(file_path)
                    if verbose and progress_callback:
                        progress_callback(f"Removed old workflow file: {file_path}")
        else:
            os.makedirs(workflow_dir, exist_ok=True)

        workflow_path = os.path.join(workflow_dir, 'build.yml')
        with open(workflow_path, 'w', encoding='utf-8') as f:
            f.write(workflow_content)
        if progress_callback:
            progress_callback("GitHub Actions workflow file successfully created locally.")

        run_command(f"git add {workflow_dir}", cwd=project_path, verbose=verbose, progress_callback=progress_callback)
        commit_message = "Update GitHub Actions workflow"
        returncode, stdout, _ = run_command(f'git commit -m "{commit_message}"', cwd=project_path, verbose=verbose, check=False, progress_callback=progress_callback)
        commit_output = stdout.lower() if stdout else ''
        if returncode != 0:
            if "nothing to commit" in commit_output or "working tree clean" in commit_output:
                if progress_callback:
                    progress_callback("Workflow file already committed or no changes. Skipping commit step.")
            else:
                if progress_callback:
                    progress_callback(f"Error during git commit:\n{stdout}")
                raise Exception("Error during git commit.")
        else:
            if progress_callback:
                progress_callback("Workflow commit created.")

        if progress_callback:
            progress_callback("Pushing workflow to GitHub...")
        try:
            run_command("git push", cwd=project_path, verbose=verbose, progress_callback=progress_callback)
            if progress_callback:
                progress_callback("GitHub Actions workflow file successfully pushed to repository.")
        except subprocess.CalledProcessError:
            if progress_callback:
                progress_callback("Push failed due to repository rule violations. Please fix the issue and try again.")
            raise Exception("Push failed due to repository rule violations.")

        if progress_callback:
            progress_callback("Waiting for GitHub to register the new workflow...")
        time.sleep(10)  # Wait for 10 seconds
    except Exception as e:
        if progress_callback:
            progress_callback(str(e))
        raise e

def set_workflow_permissions(repo_name, github_token, verbose=False, progress_callback=None):
    try:
        if progress_callback:
            progress_callback("Setting GitHub Actions permissions to 'Read and write'...")
        owner = get_github_username(github_token, progress_callback=progress_callback)
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
            if progress_callback:
                progress_callback("GitHub Actions permissions successfully set to 'Read and write'.")
        else:
            if progress_callback:
                progress_callback(f"Failed to set GitHub Actions permissions: {response.status_code} - {response.text}")
            raise Exception(f"Failed to set GitHub Actions permissions: {response.status_code} - {response.text}")
    except Exception as e:
        if progress_callback:
            progress_callback(str(e))
        raise e

def trigger_workflow_dispatch(repo_name, github_token, branch, verbose=False, progress_callback=None):
    try:
        if progress_callback:
            progress_callback("Triggering GitHub Actions workflow via API...")
        owner = get_github_username(github_token, progress_callback=progress_callback)
        url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/workflows/build.yml/dispatches"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"ref": branch}
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 204:
            if progress_callback:
                progress_callback("Workflow dispatch event triggered successfully.")
        else:
            if progress_callback:
                progress_callback(f"Failed to trigger workflow dispatch: {response.status_code} - {response.text}")
            raise Exception(f"Failed to trigger workflow dispatch: {response.status_code} - {response.text}")
    except Exception as e:
        if progress_callback:
            progress_callback(str(e))
        raise e

def wait_for_workflow_completion(repo, github_token, build_timeout, poll_interval, branch, verbose=False, progress_callback=None):
    try:
        g = Github(github_token)
        user = g.get_user()
        repository = g.get_repo(f"{user.login}/{repo.name}")
        if progress_callback:
            progress_callback("Waiting for the GitHub Actions workflow to start...")
        start_time = time.time()
        workflow_run = None
        while time.time() - start_time < build_timeout:
            workflows = repository.get_workflows()
            if workflows.totalCount == 0:
                if progress_callback:
                    progress_callback("No workflows found. Waiting...")
                time.sleep(poll_interval)
                continue

            # List all workflow names for debugging
            if verbose and progress_callback:
                progress_callback("Available Workflows:")
                for wf in workflows:
                    progress_callback(f"- {wf.name}")

            # Search for the 'Build' workflow
            workflow = next((wf for wf in workflows if wf.name.lower() == "build"), None)
            if not workflow:
                if progress_callback:
                    progress_callback("Workflow 'Build' not found. Waiting...")
                time.sleep(poll_interval)
                continue

            runs = workflow.get_runs(branch=branch, event="workflow_dispatch")
            if runs.totalCount == 0:
                if progress_callback:
                    progress_callback("No workflow runs found for 'Build'. Waiting...")
                time.sleep(poll_interval)
                continue

            workflow_run = runs[0]
            if progress_callback:
                progress_callback(f"Found Workflow Run ID: {workflow_run.id} | Status: {workflow_run.status} | Conclusion: {workflow_run.conclusion}")

            if workflow_run.status != "completed":
                if progress_callback:
                    progress_callback(f"Workflow run {workflow_run.id} is '{workflow_run.status}'. Waiting...")
                time.sleep(poll_interval)
            else:
                if workflow_run.conclusion == "success":
                    if progress_callback:
                        progress_callback("GitHub Actions workflow completed successfully.")
                    if verbose:
                        download_and_display_workflow_logs(repository, workflow_run.id, github_token, progress_callback=progress_callback)
                    return
                else:
                    if progress_callback:
                        progress_callback(f"GitHub Actions workflow failed: {workflow_run.conclusion}")
                    if verbose:
                        download_and_display_workflow_logs(repository, workflow_run.id, github_token, progress_callback=progress_callback)
                    raise Exception(f"GitHub Actions workflow failed: {workflow_run.conclusion}")
        if progress_callback:
            progress_callback("Timeout reached. Workflow did not complete in time.")
        raise Exception("Timeout reached. Workflow did not complete in time.")
    except Exception as e:
        if progress_callback:
            progress_callback(str(e))
        raise e

def download_and_display_workflow_logs(repository, run_id, github_token, progress_callback=None):
    try:
        if progress_callback:
            progress_callback("Downloading workflow logs...")
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
                        if progress_callback:
                            progress_callback(f"\n--- Log file: {zipinfo.filename} ---")
                        log_content = thefile.read().decode('utf-8', errors='ignore')
                        progress_callback(log_content)
        else:
            if progress_callback:
                progress_callback(f"Failed to download workflow logs: {response.status_code} - {response.text}")
            raise Exception(f"Failed to download workflow logs: {response.status_code} - {response.text}")
    except Exception as e:
        if progress_callback:
            progress_callback(str(e))
        raise e

def download_artifact(repo, artifact_name, builds_dir, file_extension, verbose=False, progress_callback=None):
    try:
        if progress_callback:
            progress_callback(f"Fetching the latest release for {file_extension.upper()}...")
        releases = repo.get_releases()
        if releases.totalCount == 0:
            if progress_callback:
                progress_callback("No releases found.")
            raise Exception("No releases found.")
        latest_release = releases[0]
        assets = latest_release.get_assets()
        artifact_asset = next((asset for asset in assets if asset.name.endswith(file_extension)), None)
        if not artifact_asset:
            if progress_callback:
                progress_callback(f"No {file_extension.upper()} file found in the latest release.")
            raise Exception(f"No {file_extension.upper()} file found in the latest release.")
        download_url = artifact_asset.browser_download_url
        if progress_callback:
            progress_callback(f"{file_extension.upper()} download URL: {download_url}")
        os.makedirs(builds_dir, exist_ok=True)
        artifact_path = os.path.join(builds_dir, artifact_asset.name)
        if progress_callback:
            progress_callback(f"Downloading the {file_extension.upper()} file to '{artifact_path}'...")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(artifact_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(f"Downloaded {downloaded} of {total_size} bytes")
        if progress_callback:
            progress_callback(f"{file_extension.upper()} successfully downloaded to '{artifact_path}'.")
    except Exception as e:
        if progress_callback:
            progress_callback(str(e))
        raise e

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

def check_and_install_dependencies(package_versions=None, verbose=False, progress_callback=None):
    check_and_install_git(verbose=verbose, progress_callback=progress_callback)
    check_and_install_gh(verbose=verbose, progress_callback=progress_callback)
    install_python_packages(package_versions=package_versions, verbose=verbose, progress_callback=progress_callback)

def delete_old_workflow_runs(repo, github_token, verbose=False, progress_callback=None):
    try:
        if progress_callback:
            progress_callback("Deleting old workflow runs...")
        g = Github(github_token)
        user = g.get_user()
        repository = g.get_repo(f"{user.login}/{repo.name}")
        workflows = repository.get_workflows()

        for workflow in workflows:
            if progress_callback:
                progress_callback(f"Processing Workflow: {workflow.name}")
            runs = workflow.get_runs()
            for run in runs:
                try:
                    if progress_callback:
                        progress_callback(f"Attempting to delete Workflow Run ID: {run.id} | Status: {run.status}")
                    run.delete()
                    if progress_callback:
                        progress_callback(f"Deleted workflow run {run.id} for '{workflow.name}'.")
                except GithubException as e:
                    if progress_callback:
                        progress_callback(f"Failed to delete workflow run {run.id}: {e.data.get('message', 'Unknown error')}")
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"Unexpected error deleting workflow run {run.id}: {e}")
        if progress_callback:
            progress_callback("All old workflow runs attempted to be deleted.")
    except Exception as e:
        if progress_callback:
            progress_callback(str(e))
        raise e

def cache_dependencies(project_path, cache_dir, verbose=False, progress_callback=None):
    try:
        if progress_callback:
            progress_callback("Caching dependencies...")
        cache_path = os.path.join(cache_dir, 'flutter_packages')
        if not os.path.exists(cache_path):
            os.makedirs(cache_path, exist_ok=True)
        src = os.path.join(project_path, 'pubspec.lock')
        dest = os.path.join(cache_path, 'pubspec.lock')
        if os.path.exists(src):
            shutil.copy(src, dest)
            if verbose and progress_callback:
                progress_callback(f"Cached pubspec.lock to {dest}")
        if progress_callback:
            progress_callback("Dependencies cached.")
    except Exception as e:
        if progress_callback:
            progress_callback(str(e))
        raise e

def restore_cached_dependencies(project_path, cache_dir, verbose=False, progress_callback=None):
    try:
        if progress_callback:
            progress_callback("Restoring cached dependencies...")
        cache_path = os.path.join(cache_dir, 'flutter_packages', 'pubspec.lock')
        src = cache_path
        dest = os.path.join(project_path, 'pubspec.lock')
        if os.path.exists(src):
            shutil.copy(src, dest)
            if verbose and progress_callback:
                progress_callback(f"Restored pubspec.lock from {src}")
        else:
            if progress_callback:
                progress_callback("No cached dependencies found.")
    except Exception as e:
        if progress_callback:
            progress_callback(str(e))
        raise e

# ================================
# Worker Thread for Background Tasks
# ================================

class Worker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super(Worker, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.func(*self.args, **self.kwargs, progress_callback=self.progress.emit)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

# ================================
# Main Application Window
# ================================

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Flutter GitHub Manager'
        self.setGeometry(100, 100, 900, 700)
        self.workers = []  # To keep references to worker threads
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)

        # Main layout
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Tabs
        self.repoTab = QWidget()
        self.buildTab = QWidget()
        self.statusTab = QWidget()

        self.tabs.addTab(self.repoTab, "Repository Setup")
        self.tabs.addTab(self.buildTab, "Build Configuration")
        self.tabs.addTab(self.statusTab, "Logs & Status")

        # Repository Setup Tab
        self.repo_layout = QFormLayout()

        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.repo_layout.addRow(QLabel("GitHub Token:"), self.token_input)

        self.action_combo = QComboBox()
        self.action_combo.addItems(['createrepo', 'repo'])
        self.repo_layout.addRow(QLabel("Action:"), self.action_combo)

        self.repo_name_input = QLineEdit()
        self.repo_layout.addRow(QLabel("Repository Name:"), self.repo_name_input)

        # Entfernen des "Execute" Buttons
        # Stattdessen integrieren wir die Aktion in den Build-Prozess

        self.repoTab.setLayout(self.repo_layout)

        # Build Configuration Tab
        self.build_layout = QFormLayout()

        # Project Path with Browse Button
        self.project_path_input = QLineEdit()
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_project)
        project_layout = QHBoxLayout()
        project_layout.addWidget(self.project_path_input)
        project_layout.addWidget(self.browse_btn)
        self.build_layout.addRow(QLabel("Project Path:"), project_layout)

        self.ipa_name_input = QLineEdit("FlutterIpaExport.ipa")
        self.build_layout.addRow(QLabel("IPA File Name:"), self.ipa_name_input)

        self.apk_name_input = QLineEdit("FlutterApkExport.apk")
        self.build_layout.addRow(QLabel("APK File Name:"), self.apk_name_input)

        self.build_dir_input = QLineEdit("builds")
        self.build_layout.addRow(QLabel("Build Directory:"), self.build_dir_input)

        self.branch_input = QLineEdit("main")
        self.build_layout.addRow(QLabel("Branch Name:"), self.branch_input)

        self.platforms_combo = QComboBox()
        self.platforms_combo.addItems(['iOS', 'Android', 'iOS, Android'])
        self.build_layout.addRow(QLabel("Platforms to Build:"), self.platforms_combo)

        self.include_checkbox = QCheckBox("Include Specific Files")
        self.include_patterns_input = QLineEdit()
        self.include_patterns_input.setPlaceholderText("e.g., src/, assets/")
        self.include_patterns_input.setEnabled(False)
        self.include_checkbox.stateChanged.connect(self.toggle_include_patterns)
        self.build_layout.addRow(self.include_checkbox, self.include_patterns_input)

        self.exclude_checkbox = QCheckBox("Exclude Specific Files")
        self.exclude_patterns_input = QLineEdit()
        self.exclude_patterns_input.setPlaceholderText("e.g., *.log, secrets/")
        self.exclude_patterns_input.setEnabled(False)
        self.exclude_checkbox.stateChanged.connect(self.toggle_exclude_patterns)
        self.build_layout.addRow(self.exclude_checkbox, self.exclude_patterns_input)

        self.remotes_input = QLineEdit()
        self.remotes_input.setPlaceholderText("Comma-separated GitHub usernames")
        self.build_layout.addRow(QLabel("Additional GitHub Remotes:"), self.remotes_input)

        self.verbose_checkbox = QCheckBox("Enable Verbose Output")
        self.build_layout.addRow(self.verbose_checkbox)

        self.start_build_btn = QPushButton("Start Build")
        self.start_build_btn.clicked.connect(self.start_build)
        self.build_layout.addRow(self.start_build_btn)

        self.buildTab.setLayout(self.build_layout)

        # Logs & Status Tab
        self.status_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.status_layout.addWidget(self.log_text)
        self.statusTab.setLayout(self.status_layout)

        # Add tabs to main layout
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # Toggle include patterns input
    def toggle_include_patterns(self, state):
        self.include_patterns_input.setEnabled(state == Qt.Checked)

    # Toggle exclude patterns input
    def toggle_exclude_patterns(self, state):
        self.exclude_patterns_input.setEnabled(state == Qt.Checked)

    # Browse for project directory
    def browse_project(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if directory:
            self.project_path_input.setText(directory)

    # Log messages to the log_text widget
    def log(self, message):
        self.log_text.append(message)
        self.log_text.moveCursor(QTextCursor.End)  # Korrigierte Zeile

    # Start build process
    def start_build(self):
        # Gather all build configurations
        token = self.token_input.text().strip()
        repo_name = self.repo_name_input.text().strip()
        project_path = self.project_path_input.text().strip()
        ipa_name = self.ipa_name_input.text().strip()
        apk_name = self.apk_name_input.text().strip()
        build_dir = self.build_dir_input.text().strip()
        branch = self.branch_input.text().strip()
        platforms = self.platforms_combo.currentText()
        verbose = self.verbose_checkbox.isChecked()
        action = self.action_combo.currentText()  # Get the selected action

        include_patterns = None
        if self.include_checkbox.isChecked():
            include_text = self.include_patterns_input.text().strip()
            if include_text:
                include_patterns = [p.strip() for p in include_text.split(',')]

        exclude_patterns = None
        if self.exclude_checkbox.isChecked():
            exclude_text = self.exclude_patterns_input.text().strip()
            if exclude_text:
                exclude_patterns = [p.strip() for p in exclude_text.split(',')]

        remotes = None
        remotes_text = self.remotes_input.text().strip()
        if remotes_text:
            remotes = [r.strip() for r in remotes_text.split(',')]

        if not all([token, repo_name, project_path]):
            QMessageBox.warning(self, "Input Error", "Please provide GitHub Token, Repository Name, and Project Path.")
            return

        # Check if a build is already running
        if any(worker.isRunning() for worker in self.workers):
            QMessageBox.warning(self, "Build in Progress", "Ein Build-Prozess läuft bereits.")
            return

        self.log("Starting build process...")

        # Clear old logs
        self.log_text.clear()

        # Start Worker Thread
        worker = Worker(
            self.build_process, 
            token, repo_name, project_path, ipa_name, apk_name, 
            build_dir, branch, platforms, verbose,
            include_patterns, exclude_patterns, remotes, action
        )
        self.workers.append(worker)  # Keep a reference to prevent garbage collection
        worker.progress.connect(self.log)
        worker.finished.connect(lambda: self.log("Build process completed successfully."))
        worker.error.connect(lambda e: self.log(f"Error: {e}"))
        worker.finished.connect(lambda: self.workers.remove(worker))
        worker.error.connect(lambda e: self.workers.remove(worker))
        worker.start()
        
        # Switch to "Logs & Status" Tab
        self.tabs.setCurrentWidget(self.statusTab)

    # Build process logic
    def build_process(self, token, repo_name, project_path, ipa_name, apk_name, 
                     build_dir, branch, platforms, verbose,
                     include_patterns, exclude_patterns, remotes, action, progress_callback):
        try:
            # Check and install dependencies
            progress_callback("Checking and installing dependencies...")
            check_and_install_dependencies(verbose=verbose, progress_callback=progress_callback)

            # Cache dependencies
            progress_callback("Caching dependencies...")
            cache_dependencies(project_path, os.path.join(project_path, '.cache'), verbose=verbose, progress_callback=progress_callback)

            # Initialize GitHub
            g = Github(token)
            user = g.get_user()

            if action == "createrepo":
                # Create new repository
                progress_callback(f"Creating new repository '{repo_name}'...")
                repo = create_repo(repo_name, token, verbose=True, progress_callback=progress_callback)
            elif action == "repo":
                # Access existing repository
                progress_callback(f"Accessing existing repository '{repo_name}'...")
                try:
                    repo = g.get_repo(f"{user.login}/{repo_name}")
                    progress_callback(f"Repository '{repo_name}' accessed successfully.")
                except GithubException as e:
                    if e.status == 404:
                        progress_callback(f"Repository '{repo_name}' not found. Please create it first.")
                    else:
                        progress_callback(f"GitHub Exception: {e.data.get('message', 'Unknown error')}")
                    raise e
            else:
                progress_callback(f"Unknown action: {action}")
                raise Exception(f"Unknown action: {action}")

            # Set workflow permissions
            set_workflow_permissions(repo_name, token, verbose=verbose, progress_callback=progress_callback)

            # Delete old workflow runs
            delete_old_workflow_runs(repo, token, verbose=verbose, progress_callback=progress_callback)

            # Upload Project
            progress_callback("Uploading project to GitHub...")
            upload_project(
                repo_name,
                token,
                project_path=project_path,
                branch=branch,
                ipa_name=ipa_name,
                apk_name=apk_name,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                remotes=remotes,
                verbose=verbose,
                progress_callback=progress_callback
            )

            # Add GitHub Actions Workflow
            progress_callback("Adding GitHub Actions workflow...")
            platform_list = [p.strip() for p in platforms.split(',')]
            workflow_yaml = get_workflow_yaml(platform_list, ipa_name, apk_name, branch)
            add_github_actions_workflow(workflow_yaml, project_path=project_path, verbose=verbose, progress_callback=progress_callback)

            # Trigger Workflow
            progress_callback("Triggering GitHub Actions workflow...")
            trigger_workflow_dispatch(repo_name, token, branch, verbose=verbose, progress_callback=progress_callback)

            # Wait for Workflow Completion
            progress_callback("Waiting for workflow to complete...")
            wait_for_workflow_completion(repo, token, 1800, 30, branch, verbose=verbose, progress_callback=progress_callback)

            # Download Artifacts
            platform_list = [p.strip() for p in platforms.split(',')]
            if 'iOS' in platform_list:
                progress_callback("Downloading IPA artifact...")
                download_artifact(repo, ipa_name, build_dir, '.ipa', verbose=verbose, progress_callback=progress_callback)
            if 'Android' in platform_list:
                progress_callback("Downloading APK artifact...")
                download_artifact(repo, apk_name, build_dir, '.apk', verbose=verbose, progress_callback=progress_callback)

        except Exception as e:
            progress_callback(str(e))
            raise e

    # ================================
    # Handle Application Closure
    # ================================

    def closeEvent(self, event):
        # Ensure all worker threads are properly terminated before closing
        for worker in self.workers:
            if worker.isRunning():
                worker.terminate()
                worker.wait()
        event.accept()

# ================================
# Entry Point
# ================================

def main():
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
