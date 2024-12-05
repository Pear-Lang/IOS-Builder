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
import threading

from PyQt5 import QtCore, QtGui, QtWidgets
from colorama import init, Fore, Style
from termcolor import colored
from github import Github, GithubException
from github.GithubException import UnknownObjectException

# Initialize colorama
init(autoreset=True)

class MainWindow(QtWidgets.QMainWindow):
    # Signal for thread-safe logging
    message_signal = QtCore.pyqtSignal(str)

    def __init__(self, args):
        super().__init__()

        self.args = args

        # Window title & geometry
        self.setWindowTitle("Flutter iOS Build Automation")
        self.resize(1000, 700)
        
        # Updated stylesheet for a more polished design
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel, QCheckBox, QRadioButton, QLineEdit, QSpinBox, QComboBox, QPushButton, QGroupBox, QTabWidget::pane, QTextEdit {
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12pt;
            }
            QLineEdit, QSpinBox, QComboBox, QTextEdit {
                background-color: #2c2c2c;
                border: 1px solid #444444;
                padding: 4px;
                border-radius: 4px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
            }
            QPushButton {
                background-color: #3c3f41;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4d4f;
            }
            QGroupBox {
                border: 1px solid #444444;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                background-color: #1e1e1e;
                padding: 0px 5px;
            }
            QTabBar::tab {
                background: #2c2c2c;
                border: 1px solid #444444;
                padding: 8px 12px;
                margin: 0 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3c3f41;
                border-bottom: 2px solid #1f92ff;
            }
            QTabWidget::pane {
                border: 1px solid #444444;
                border-radius: 4px;
                margin-top: -1px;
            }
            QTextEdit {
                border: 1px solid #444444;
                border-radius: 4px;
                background-color: #2c2c2c;
                padding: 8px;
            }
        """)

        # Central widget and main layout
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        # Tabs for configuration and logs
        self.tab_widget = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Configuration tab
        config_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(config_tab, "Configuration")
        config_layout = QtWidgets.QVBoxLayout(config_tab)
        config_layout.setSpacing(15)
        config_layout.setContentsMargins(10, 10, 10, 10)

        form_group = QtWidgets.QGroupBox("Repository & Build Settings")
        config_layout.addWidget(form_group)

        self.form_layout = QtWidgets.QFormLayout(form_group)
        self.form_layout.setLabelAlignment(QtCore.Qt.AlignRight)

        self.github_token_input = QtWidgets.QLineEdit()
        self.github_token_input.setEchoMode(QtWidgets.QLineEdit.Password)
        if self.args.token:
            self.github_token_input.setText(self.args.token)
        self.form_layout.addRow("GitHub Personal Access Token:", self.github_token_input)

        self.action_combo = QtWidgets.QComboBox()
        self.action_combo.addItems(["Create Repository", "Use Existing Repository"])
        if self.args.action == "repo":
            self.action_combo.setCurrentText("Use Existing Repository")
        elif self.args.action == "createrepo":
            self.action_combo.setCurrentText("Create Repository")
        self.form_layout.addRow("Action:", self.action_combo)

        self.repo_name_input = QtWidgets.QLineEdit()
        if self.args.repo:
            self.repo_name_input.setText(self.args.repo)
        self.form_layout.addRow("Repository Name:", self.repo_name_input)

        self.ipa_name_input = QtWidgets.QLineEdit("FlutterIpaExport.ipa")
        if self.args.ipa_name:
            self.ipa_name_input.setText(self.args.ipa_name)
        self.form_layout.addRow("IPA Name:", self.ipa_name_input)

        self.build_dir_input = QtWidgets.QLineEdit("builds")
        if self.args.build_dir:
            self.build_dir_input.setText(self.args.build_dir)
        self.form_layout.addRow("Build Directory:", self.build_dir_input)

        self.project_path_input = QtWidgets.QLineEdit(os.getcwd())
        if self.args.project_path:
            self.project_path_input.setText(self.args.project_path)
        self.form_layout.addRow("Project Path:", self.project_path_input)

        self.build_timeout_input = QtWidgets.QSpinBox()
        self.build_timeout_input.setRange(60, 3600 * 5)
        self.build_timeout_input.setValue(self.args.build_timeout if self.args.build_timeout else 1800)
        self.form_layout.addRow("Build Timeout (seconds):", self.build_timeout_input)

        self.poll_interval_input = QtWidgets.QSpinBox()
        self.poll_interval_input.setRange(5, 600)
        self.poll_interval_input.setValue(self.args.poll_interval if self.args.poll_interval else 30)
        self.form_layout.addRow("Poll Interval (seconds):", self.poll_interval_input)

        self.skip_dependencies_checkbox = QtWidgets.QCheckBox("Skip Dependency Checks")
        self.skip_dependencies_checkbox.setChecked(self.args.skip_dependencies)
        self.form_layout.addRow("", self.skip_dependencies_checkbox)

        self.skip_upload_checkbox = QtWidgets.QCheckBox("Skip Project Upload")
        self.skip_upload_checkbox.setChecked(self.args.skip_upload)
        self.form_layout.addRow("", self.skip_upload_checkbox)

        self.skip_build_checkbox = QtWidgets.QCheckBox("Skip Build and Download")
        self.skip_build_checkbox.setChecked(self.args.skip_build)
        self.form_layout.addRow("", self.skip_build_checkbox)

        self.verbose_checkbox = QtWidgets.QCheckBox("Verbose Output")
        self.verbose_checkbox.setChecked(self.args.verbose)
        self.form_layout.addRow("", self.verbose_checkbox)

        # Start button on config tab
        self.start_button = QtWidgets.QPushButton("Start")
        config_layout.addWidget(self.start_button, 0, QtCore.Qt.AlignRight)

        # Logs tab
        logs_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(logs_tab, "Logs")
        logs_layout = QtWidgets.QVBoxLayout(logs_tab)
        logs_layout.setContentsMargins(10, 10, 10, 10)

        self.log_output = QtWidgets.QTextEdit()
        self.log_output.setReadOnly(True)
        logs_layout.addWidget(self.log_output)

        # Connect signals
        self.start_button.clicked.connect(self.start_process)
        self.message_signal.connect(self.append_message)

        self.thread = None

    @QtCore.pyqtSlot(str)
    def append_message(self, text):
        self.log_output.append(text)
        self.log_output.ensureCursorVisible()

    def log(self, message, color=Fore.WHITE):
        # Strip ANSI codes for display, or leave them out
        ansi_stripped = message.replace(Style.RESET_ALL, '').replace(Fore.RED, '').replace(Fore.GREEN, '').replace(Fore.YELLOW, '').replace(Fore.CYAN, '').replace(Fore.MAGENTA, '').replace(Fore.BLUE, '').replace(Fore.WHITE, '').replace(Fore.LIGHTBLUE_EX, '')
        # Emit message so that UI updates on the main thread
        self.message_signal.emit(ansi_stripped)

    def start_process(self):
        # Disable the start button
        self.start_button.setEnabled(False)
        # Switch to Logs tab automatically
        self.tab_widget.setCurrentIndex(1)
        self.thread = threading.Thread(target=self.main_process)
        self.thread.start()

    def main_process(self):
        try:
            self.run_main()
        except Exception as e:
            self.log(f"Error: {str(e)}", Fore.RED)
        finally:
            self.start_button.setEnabled(True)

    def run_main(self):
        github_token = self.github_token_input.text().strip()
        if not github_token:
            self.log("GitHub Token is required.", Fore.RED)
            return

        action = "createrepo" if self.action_combo.currentText() == "Create Repository" else "repo"
        repo_name = self.repo_name_input.text().strip()
        if not repo_name:
            self.log("Repository name is required.", Fore.RED)
            return

        ipa_name = self.ipa_name_input.text().strip()
        build_dir = self.build_dir_input.text().strip()
        project_path = self.project_path_input.text().strip()
        build_timeout = self.build_timeout_input.value()
        poll_interval = self.poll_interval_input.value()
        skip_dependencies = self.skip_dependencies_checkbox.isChecked()
        skip_upload = self.skip_upload_checkbox.isChecked()
        skip_build = self.skip_build_checkbox.isChecked()
        verbose = self.verbose_checkbox.isChecked()

        if not skip_dependencies:
            self.check_and_install_dependencies(verbose=verbose)
        else:
            self.log("Skipping dependency checks.", Fore.YELLOW)

        if action == "createrepo":
            repo = self.create_repo(repo_name, github_token, verbose=verbose)
            self.set_workflow_permissions(repo_name, github_token, verbose=verbose)
            if not skip_upload:
                self.upload_project(repo_name, github_token, project_path, verbose=verbose)
            else:
                self.log("Skipping project upload.", Fore.YELLOW)
        else:
            repo = self.get_existing_repo(repo_name, github_token)
            self.set_workflow_permissions(repo_name, github_token, verbose=verbose)
            self.delete_old_workflow_runs(repo, github_token, verbose=verbose)
            if not skip_upload:
                self.upload_project(repo_name, github_token, project_path, verbose=verbose)
            else:
                self.log("Skipping project upload.", Fore.YELLOW)

        # Add GitHub Actions Workflow
        workflow_yaml = self.get_workflow_yaml(ipa_name)
        self.add_github_actions_workflow(workflow_yaml, project_path, verbose=verbose)

        if not skip_build:
            # Trigger the Build
            self.trigger_workflow_dispatch(repo_name, github_token, verbose=verbose)

            # Wait for Build Completion
            self.wait_for_workflow_completion(repo, github_token, build_timeout, poll_interval, verbose=verbose)

            # Download the IPA
            self.download_ipa(repo, build_dir, ipa_name, verbose=verbose)
        else:
            self.log("Skipping build and download steps.", Fore.YELLOW)

    def run_command(self, command, cwd=None, verbose=True, check=True):
        if verbose:
            self.log(f"Running command: {command}", Fore.LIGHTBLUE_EX)
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
                    self.log(line.strip())
            returncode = process.wait()
            if returncode != 0 and check:
                self.log(f"Command '{command}' failed with return code {returncode}.", Fore.RED)
                sys.exit(1)
            return returncode, stdout, ''
        except subprocess.CalledProcessError as e:
            if check:
                self.log(f"Error executing: {command}", Fore.RED)
                sys.exit(1)
            else:
                return e.returncode, e.output, ''

    def install_python_packages(self, verbose=False):
        required_packages = ['PyGithub', 'requests', 'colorama', 'termcolor']
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                self.log(f"Installing missing Python package: {package}", Fore.YELLOW)
                self.run_command(f"{sys.executable} -m pip install {package}", verbose=verbose)

    def install_with_chocolatey(self, package, verbose=False):
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
            self.log("Chocolatey is not installed. Please install Chocolatey to install the required packages.", Fore.RED)
            self.log("Visit https://chocolatey.org/install for installation instructions.")
            sys.exit(1)

        self.log(f"Installing {package} with Chocolatey...", Fore.YELLOW)
        self.run_command(f"choco install {package} -y", verbose=verbose)

    def install_with_apt(self, package, verbose=False):
        try:
            self.run_command("sudo apt-get update", verbose=verbose)
            self.run_command(f"sudo apt-get install -y {package}", verbose=verbose)
        except:
            self.log(f"Error installing {package} with apt. Please install {package} manually.", Fore.RED)
            sys.exit(1)

    def install_with_homebrew(self, package, verbose=False):
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
            self.log("Homebrew is not installed. Please install Homebrew to install the required packages.", Fore.RED)
            self.log("Visit https://brew.sh/ for installation instructions.")
            sys.exit(1)

        self.log(f"Installing {package} with Homebrew...", Fore.YELLOW)
        self.run_command(f"brew install {package}", verbose=verbose)

    def check_and_install_git(self, verbose=False):
        try:
            self.run_command("git --version", verbose=verbose)
            self.log("Git is installed.", Fore.GREEN)
        except:
            self.log("Git is not installed.", Fore.YELLOW)
            self.install_git(verbose=verbose)

    def install_git(self, verbose=False):
        current_os = platform.system()
        if current_os == "Windows":
            self.install_with_chocolatey("git", verbose=verbose)
        elif current_os == "Linux":
            self.install_with_apt("git", verbose=verbose)
        elif current_os == "Darwin":
            self.install_with_homebrew("git", verbose=verbose)
        else:
            self.log("Automatic installation of Git is not supported on this operating system. Please install Git manually.", Fore.RED)
            sys.exit(1)

    def check_and_install_gh(self, verbose=False):
        try:
            self.run_command("gh --version", verbose=verbose)
            self.log("GitHub CLI (gh) is installed.", Fore.GREEN)
            # Check if gh is authenticated
            _, auth_status, _ = self.run_command("gh auth status", verbose=verbose)
            if "You are not logged into any GitHub hosts" in auth_status:
                self.log("GitHub CLI is not authenticated. Please authenticate.", Fore.YELLOW)
                self.run_command("gh auth login", verbose=verbose)
                self.run_command("gh auth setup-git", verbose=verbose)
        except:
            self.log("GitHub CLI (gh) is not installed.", Fore.YELLOW)
            self.install_gh(verbose=verbose)
            self.log("Please authenticate GitHub CLI.", Fore.YELLOW)
            self.run_command("gh auth login", verbose=verbose)
            self.run_command("gh auth setup-git", verbose=verbose)

    def install_gh(self, verbose=False):
        current_os = platform.system()
        if current_os == "Windows":
            self.install_with_chocolatey("gh", verbose=verbose)
        elif current_os == "Linux":
            self.install_with_apt("gh", verbose=verbose)
        elif current_os == "Darwin":
            self.install_with_homebrew("gh", verbose=verbose)
        else:
            self.log("Automatic installation of GitHub CLI is not supported on this operating system. Please install GitHub CLI manually.", Fore.RED)
            sys.exit(1)

    def check_and_install_dependencies(self, verbose=False):
        self.check_and_install_git(verbose=verbose)
        self.check_and_install_gh(verbose=verbose)
        self.install_python_packages(verbose=verbose)

    def create_repo(self, repo_name, github_token, verbose=False):
        g = Github(github_token)
        user = g.get_user()
        try:
            repo = user.create_repo(repo_name, private=False, auto_init=False)
            self.log(f"Repository '{repo_name}' successfully created.", Fore.GREEN)
            return repo
        except GithubException as e:
            self.log(f"Error creating the repository: {e.data['message']}", Fore.RED)
            sys.exit(1)

    def get_existing_repo(self, repo_name, github_token):
        g = Github(github_token)
        user = g.get_user()
        try:
            repo = g.get_repo(f"{user.login}/{repo_name}")
            self.log(f"Repository '{repo_name}' found.", Fore.GREEN)
            return repo
        except UnknownObjectException:
            self.log(f"Repository '{repo_name}' was not found. Please ensure the name is correct.", Fore.RED)
            sys.exit(1)

    def set_workflow_permissions(self, repo_name, github_token, verbose=False):
        self.log("Setting GitHub Actions permissions to 'Read and write'...", Fore.YELLOW)
        owner = self.get_github_username(github_token)
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
            self.log("GitHub Actions permissions successfully set to 'Read and write'.", Fore.GREEN)
        else:
            self.log(f"Failed to set GitHub Actions permissions: {response.status_code} - {response.text}", Fore.RED)
            sys.exit(1)

    def upload_project(self, repo_name, github_token, project_path, verbose=False):
        if not os.path.isdir(os.path.join(project_path, ".git")):
            self.log("Initializing Git repository...", Fore.YELLOW)
            self.run_command("git init", cwd=project_path, verbose=verbose)

        github_username = self.get_github_username(github_token)
        remote_url = f"https://github.com/{github_username}/{repo_name}.git"
        self.log(f"Setting remote 'origin' to {remote_url}", Fore.YELLOW)
        self.run_command("git remote remove origin", cwd=project_path, verbose=verbose, check=False)
        self.run_command(f"git remote add origin {remote_url}", cwd=project_path, verbose=verbose)

        self.log("Adding files to Git...", Fore.YELLOW)
        self.run_command("git add .", cwd=project_path, verbose=verbose)
        commit_message = "Initial commit"
        returncode, stdout, _ = self.run_command(f'git commit -m "{commit_message}"', cwd=project_path, verbose=verbose, check=False)
        commit_output = stdout.lower() if stdout else ''
        if returncode != 0:
            if "nothing to commit" in commit_output or "working tree clean" in commit_output:
                self.log("Nothing to commit. Skipping commit step.", Fore.YELLOW)
            else:
                self.log(f"Error during git commit:\n{stdout}", Fore.RED)
                sys.exit(1)
        else:
            self.log("Commit created.", Fore.GREEN)

        self.log("Pushing files to GitHub...", Fore.YELLOW)
        self.run_command("git branch -M main", cwd=project_path, verbose=verbose)
        self.run_command("git push -u origin main -f", cwd=project_path, verbose=verbose)
        self.log(f"Project successfully uploaded to repository '{repo_name}'.", Fore.GREEN)

    def get_github_username(self, github_token):
        g = Github(github_token)
        user = g.get_user()
        return user.login

    def add_github_actions_workflow(self, workflow_content, project_path, verbose=False):
        workflow_dir = os.path.join(project_path, '.github', 'workflows')

        if os.path.exists(workflow_dir):
            for filename in os.listdir(workflow_dir):
                file_path = os.path.join(workflow_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    if verbose:
                        self.log(f"Removed old workflow file: {file_path}", Fore.YELLOW)
        else:
            os.makedirs(workflow_dir, exist_ok=True)

        workflow_path = os.path.join(workflow_dir, 'build_ios.yml')
        with open(workflow_path, 'w', encoding='utf-8') as f:
            f.write(workflow_content)
        self.log("GitHub Actions workflow file successfully created locally.", Fore.GREEN)

        self.run_command(f"git add {workflow_dir}", cwd=project_path, verbose=verbose)
        commit_message = "Update GitHub Actions workflow for iOS build"
        returncode, stdout, _ = self.run_command(f'git commit -m "{commit_message}"', cwd=project_path, verbose=verbose, check=False)
        commit_output = stdout.lower() if stdout else ''
        if returncode != 0:
            if "nothing to commit" in commit_output or "working tree clean" in commit_output:
                self.log("Workflow file already committed or no changes. Skipping commit step.", Fore.YELLOW)
            else:
                self.log(f"Error during git commit:\n{stdout}", Fore.RED)
                sys.exit(1)
        else:
            self.log("Workflow commit created.", Fore.GREEN)

        self.log("Pushing workflow to GitHub...", Fore.YELLOW)
        self.run_command("git push", cwd=project_path, verbose=verbose)
        self.log("GitHub Actions workflow file successfully pushed to repository.", Fore.GREEN)

        self.log("Waiting for GitHub to recognize the workflow...", Fore.YELLOW)
        time.sleep(20)

    def trigger_workflow_dispatch(self, repo_name, github_token, verbose=False):
        self.log("Triggering GitHub Actions workflow via API...", Fore.YELLOW)
        owner = self.get_github_username(github_token)
        url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/workflows/build_ios.yml/dispatches"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "ref": "main"
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [204]:
            self.log("Workflow dispatch event triggered successfully.", Fore.GREEN)
        else:
            self.log(f"Failed to trigger workflow dispatch: {response.status_code} - {response.text}", Fore.RED)
            sys.exit(1)

    def wait_for_workflow_completion(self, repo, github_token, build_timeout, poll_interval, verbose=False):
        g = Github(github_token)
        user = g.get_user()
        repository = g.get_repo(f"{user.login}/{repo.name}")
        self.log("Waiting for the GitHub Actions workflow to start...", Fore.YELLOW)
        start_time = time.time()
        workflow_run = None
        while time.time() - start_time < build_timeout:
            workflows = repository.get_workflows()
            if workflows.totalCount == 0:
                self.log("No workflows found in the repository yet. Waiting...", Fore.YELLOW)
                time.sleep(poll_interval)
                continue

            workflow = next((wf for wf in workflows if wf.name == "iOS Build"), None)
            if not workflow:
                self.log("Workflow 'iOS Build' not found. Waiting...", Fore.YELLOW)
                time.sleep(poll_interval)
                continue

            runs = workflow.get_runs(branch="main")
            if runs.totalCount == 0:
                self.log("No workflow runs found. Waiting for the workflow to start...", Fore.YELLOW)
                time.sleep(poll_interval)
                continue

            workflow_run = runs[0]
            if workflow_run.status != "completed":
                self.log(f"Workflow run {workflow_run.id} is in status '{workflow_run.status}'. Waiting for completion...", Fore.YELLOW)
                time.sleep(poll_interval)
            else:
                if workflow_run.conclusion == "success":
                    self.log("GitHub Actions workflow completed successfully.", Fore.GREEN)
                    return
                else:
                    self.log(f"GitHub Actions workflow failed with conclusion: {workflow_run.conclusion}", Fore.RED)
                    sys.exit(1)
        self.log("Timeout reached. The GitHub Actions workflow did not complete within the expected time.", Fore.RED)
        sys.exit(1)

    def download_ipa(self, repo, builds_dir, ipa_name, verbose=False):
        self.log("Fetching the latest release from the repository...", Fore.YELLOW)
        releases = repo.get_releases()
        if releases.totalCount == 0:
            self.log("No releases found.", Fore.RED)
            sys.exit(1)
        latest_release = releases[0]
        assets = latest_release.get_assets()
        ipa_asset = None
        for asset in assets:
            if asset.name.endswith(".ipa"):
                ipa_asset = asset
                break
        if not ipa_asset:
            self.log("No IPA file found in the latest release.", Fore.RED)
            sys.exit(1)
        download_url = ipa_asset.browser_download_url
        self.log(f"IPA download URL: {download_url}", Fore.GREEN)
        os.makedirs(builds_dir, exist_ok=True)
        ipa_path = os.path.join(builds_dir, ipa_name)
        self.log(f"Downloading the IPA file to '{ipa_path}'...", Fore.YELLOW)
        try:
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(ipa_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            self.log(f"IPA successfully downloaded and saved to '{ipa_path}'.", Fore.GREEN)
        except Exception as e:
            self.log(f"Error downloading the IPA file: {e}", Fore.RED)
            sys.exit(1)

    def get_workflow_yaml(self, ipa_name):
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

    def delete_old_workflow_runs(self, repo, github_token, verbose=False):
        self.log("Deleting old workflow runs...", Fore.YELLOW)
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
                        self.log(f"Deleted workflow run ID {run.id} for workflow '{workflow.name}'.", Fore.YELLOW)
                except Exception as e:
                    self.log(f"Failed to delete workflow run ID {run.id}: {e}", Fore.RED)
        self.log("All old workflow runs have been deleted.", Fore.GREEN)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Automates the creation and management of GitHub repositories for Flutter iOS projects."
    )

    parser.add_argument(
        '--token', '-t',
        type=str,
        help='GitHub Personal Access Token.'
    )
    parser.add_argument(
        '--action', '-a',
        choices=['createrepo', 'repo'],
        required=False,
        help="Action: 'createrepo' to create a repo, 'repo' to use an existing repo."
    )
    parser.add_argument(
        '--repo', '-r',
        type=str,
        help='The name of the GitHub repository.'
    )
    parser.add_argument(
        '--ipa-name',
        type=str,
        default='FlutterIpaExport.ipa',
        help='Name of the IPA file (default: "FlutterIpaExport.ipa").'
    )
    parser.add_argument(
        '--build-dir',
        type=str,
        default='builds',
        help='Directory to store builds (default: "builds").'
    )
    parser.add_argument(
        '--project-path', '-p',
        type=str,
        default='.',
        help='Path to Flutter project (default: current directory).'
    )
    parser.add_argument(
        '--skip-dependencies',
        action='store_true',
        help='Skip checking and installing dependencies.'
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip triggering the build and downloading the IPA.'
    )
    parser.add_argument(
        '--skip-upload',
        action='store_true',
        help='Skip uploading the project to GitHub.'
    )
    parser.add_argument(
        '--build-timeout',
        type=int,
        default=30*60,
        help='Build timeout in seconds (default: 1800).'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=30,
        help='Polling interval in seconds (default: 30).'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output.'
    )

    return parser.parse_args()

def main():
    args = parse_arguments()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(args)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
