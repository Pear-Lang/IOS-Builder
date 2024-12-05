# Flutter iOS GitHub Automation Tool

![ASCII Art](https://raw.githubusercontent.com/pear-lang/IOS-Builder/main/assets/img/ascii_art.png)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Command-Line Arguments](#command-line-arguments)
  - [Examples](#examples)
- [How It Works](#how-it-works)
  - [Main Components](#main-components)
  - [Workflow Steps](#workflow-steps)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

The **Flutter iOS GitHub Automation Tool** is a Python-based command-line interface (CLI) that streamlines the process of creating and managing GitHub repositories for Flutter iOS projects. It automates tasks such as repository creation, dependency installation, GitHub Actions workflow setup, build triggering, and IPA (iOS App) downloading, ensuring a seamless integration between your Flutter project and GitHub.

## Features

- **Automated Repository Management**: Create new GitHub repositories or use existing ones with ease.
- **Dependency Handling**: Automatically checks and installs required Python packages and system dependencies.
- **GitHub Actions Integration**: Sets up GitHub Actions workflows for automated iOS builds.
- **Build Automation**: Triggers builds, monitors their status, and downloads the resulting IPA files.
- **Cross-Platform Support**: Works on Windows, macOS, and Linux systems.
- **Verbose Logging**: Provides detailed logs for easier debugging and monitoring.

## Prerequisites

Before using this tool, ensure you have the following installed on your system:

1. **Python 3.6 or higher**: [Download Python](https://www.python.org/downloads/)
2. **Git**: The tool can install Git automatically if it's not already installed.
3. **GitHub CLI (gh)**: The tool can install GitHub CLI automatically if it's not already installed.
4. **Flutter SDK**: [Install Flutter](https://flutter.dev/docs/get-started/install)
5. **CocoaPods**: Required for iOS builds.
   - Install via Ruby:
     ```bash
     sudo gem install cocoapods
     ```
6. **Build Tools**:
   - **Windows**: [Chocolatey](https://chocolatey.org/install) for package management.
   - **macOS**: [Homebrew](https://brew.sh/) for package management.
   - **Linux**: `apt` package manager.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/pear-lang/flutter-ios-github-automation.git
   cd flutter-ios-github-automation
   ```

2. **Install Python Dependencies**:
   The tool will automatically install required Python packages if they're missing. However, you can manually install them using:
   ```bash
   pip install -r requirements.txt
   ```

3. **Make the Script Executable** (Optional):
   If you're on a Unix-like system, you can make the script executable:
   ```bash
   chmod +x automate_github.py
   ```

## Configuration

Before running the tool, ensure you have a **GitHub Personal Access Token** with the necessary permissions. You can create one by following [GitHub's documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).

### Setting Up the GitHub Token

You can provide the GitHub token in two ways:

1. **Environment Variable**:
   ```bash
   export GITHUB_TOKEN=your_personal_access_token
   ```

2. **Command-Line Argument**:
   Pass the token using the `--token` or `-t` flag when running the script.

## Usage

The tool provides various command-line arguments to customize its behavior. Below is a comprehensive guide on how to use them.

### Command-Line Arguments

| Argument                | Short | Type    | Required | Description                                                                                   |
|-------------------------|-------|---------|----------|-----------------------------------------------------------------------------------------------|
| `--token`               | `-t`  | String  | No       | Your GitHub Personal Access Token. If not provided, the tool will attempt to read from the `GITHUB_TOKEN` environment variable. |
| `--action`              | `-a`  | String  | Yes      | Action to perform: `createrepo` to create a new repository, `repo` to use an existing repository. |
| `--repo`                | `-r`  | String  | Yes      | The name of the GitHub repository.                                                             |
| `--ipa-name`            |       | String  | No       | Name of the IPA file to be generated (default: `FlutterIpaExport.ipa`).                      |
| `--build-dir`           |       | String  | No       | Directory to store builds (default: `builds`).                                                |
| `--project-path`        | `-p`  | String  | No       | Path to your Flutter project (default is the current directory).                              |
| `--skip-dependencies`   |       | Flag    | No       | Skip checking and installing dependencies.                                                    |
| `--skip-build`          |       | Flag    | No       | Skip triggering the build and downloading the IPA.                                           |
| `--skip-upload`         |       | Flag    | No       | Skip uploading the project to GitHub.                                                          |
| `--build-timeout`       |       | Integer | No       | Build timeout in seconds (default: `1800`).                                                   |
| `--poll-interval`       |       | Integer | No       | Polling interval in seconds (default: `30`).                                                  |
| `--verbose`             | `-v`  | Flag    | No       | Enable verbose output for detailed logs.                                                      |

### Examples

1. **Create a New Repository and Upload Project**:
   ```bash
   python automate_github.py --action createrepo --repo MyFlutterApp --token your_token_here
   ```

2. **Use an Existing Repository and Skip Dependencies**:
   ```bash
   python automate_github.py -a repo -r ExistingRepo --skip-dependencies
   ```

3. **Specify a Custom IPA Name and Build Directory**:
   ```bash
   python automate_github.py -a createrepo -r MyAppRepo --ipa-name MyApp.ipa --build-dir my_builds
   ```

4. **Enable Verbose Logging**:
   ```bash
   python automate_github.py -a createrepo -r MyAppRepo -v
   ```

## How It Works

The tool is designed to automate the workflow of setting up and managing GitHub repositories for Flutter iOS projects. Below is a detailed explanation of its components and workflow.

### Main Components

1. **Dependency Management**:
   - **Python Packages**: Ensures that required Python packages (`PyGithub`, `requests`, `colorama`, `termcolor`) are installed.
   - **System Dependencies**: Checks for Git and GitHub CLI (`gh`). If missing, it installs them using appropriate package managers (`Chocolatey` for Windows, `apt` for Linux, `Homebrew` for macOS).

2. **GitHub Repository Management**:
   - **Create Repository**: Uses the GitHub API to create a new repository if `createrepo` action is specified.
   - **Use Existing Repository**: Validates the existence of the repository if `repo` action is specified.

3. **GitHub Actions Workflow Setup**:
   - **Workflow File Creation**: Generates a `build_ios.yml` workflow file tailored for Flutter iOS builds.
   - **Upload Workflow**: Adds and commits the workflow file to the repository, then pushes it to GitHub.

4. **Build Automation**:
   - **Trigger Build**: Dispatches the GitHub Actions workflow to start the iOS build.
   - **Monitor Build**: Polls the status of the workflow run until completion or timeout.
   - **Download IPA**: Fetches the generated IPA file from the latest release.

5. **Logging and Feedback**:
   - Utilizes `colorama` and `termcolor` for colored and formatted console logs, providing clear feedback on the process status.

### Workflow Steps

1. **Initialization**:
   - Prints ASCII art for a visually appealing start.
   - Parses command-line arguments to determine the action and configurations.

2. **Authentication**:
   - Retrieves the GitHub token either from the command-line argument or environment variable.
   - Validates the token by checking GitHub CLI authentication.

3. **Dependency Checks**:
   - Installs missing Python packages.
   - Ensures Git and GitHub CLI are installed, installing them if necessary.

4. **Repository Handling**:
   - **Create Repository**: If `createrepo` is chosen, it creates a new GitHub repository and sets necessary permissions.
   - **Use Existing Repository**: If `repo` is chosen, it verifies the repository's existence and cleans up old workflow runs.

5. **Project Upload**:
   - Initializes a Git repository in the specified project path if not already initialized.
   - Sets the remote origin to the GitHub repository.
   - Adds all project files, commits, and pushes them to GitHub.

6. **GitHub Actions Workflow**:
   - Generates the `build_ios.yml` workflow file with predefined steps for building the Flutter iOS app.
   - Uploads the workflow file to the repository and commits the changes.

7. **Build Process**:
   - Triggers the GitHub Actions workflow to start the iOS build.
   - Monitors the build status, waiting for completion or timeout.
   - Upon successful build, downloads the generated IPA file to the specified build directory.

8. **Completion**:
   - Provides success messages and the location of the downloaded IPA file.
   - Handles any errors by providing descriptive messages and exiting gracefully.

## Troubleshooting

Here are some common issues you might encounter and how to resolve them:

1. **Git Not Installed**:
   - **Symptom**: Error message indicating Git is not installed.
   - **Solution**: Ensure Git is installed on your system. The tool attempts to install it automatically, but you can install it manually:
     - **Windows**: Install via [Chocolatey](https://chocolatey.org/install) using `choco install git -y`.
     - **macOS**: Install via [Homebrew](https://brew.sh/) using `brew install git`.
     - **Linux**: Install via `apt` using `sudo apt-get install git -y`.

2. **GitHub CLI (`gh`) Not Installed**:
   - **Symptom**: Error message indicating GitHub CLI is not installed.
   - **Solution**: Install GitHub CLI manually:
     - **Windows**: Install via [Chocolatey](https://chocolatey.org/install) using `choco install gh -y`.
     - **macOS**: Install via [Homebrew](https://brew.sh/) using `brew install gh`.
     - **Linux**: Install via `apt` using `sudo apt-get install gh -y`.

3. **Invalid GitHub Token**:
   - **Symptom**: Authentication failures or permission errors.
   - **Solution**: Ensure your GitHub Personal Access Token is valid and has the necessary permissions (e.g., `repo`, `workflow`).

4. **Missing Python Packages**:
   - **Symptom**: Import errors for missing packages like `PyGithub`.
   - **Solution**: Run the tool with the `--skip-dependencies` flag set to `False` or manually install the required packages:
     ```bash
     pip install PyGithub requests colorama termcolor
     ```

5. **Workflow Fails to Trigger**:
   - **Symptom**: Builds do not start after triggering.
   - **Solution**: Check the GitHub Actions tab in your repository for detailed logs. Ensure the workflow file (`build_ios.yml`) is correctly configured.

6. **IPA File Not Found**:
   - **Symptom**: The tool reports that no IPA file was found in the latest release.
   - **Solution**: Ensure that the GitHub Actions workflow runs successfully and generates the IPA file. Check the build logs for any build failures.

## Contributing

Contributions are welcome! If you'd like to enhance this tool or fix issues, please follow these steps:

1. **Fork the Repository**: Click the "Fork" button at the top-right corner of this page.

2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/pear-lang/flutter-ios-github-automation.git
   cd flutter-ios-github-automation
   ```

3. **Create a New Branch**:
   ```bash
   git checkout -b feature/YourFeatureName
   ```

4. **Make Your Changes**: Implement your feature or fix.

5. **Commit Your Changes**:
   ```bash
   git commit -m "Add feature XYZ"
   ```

6. **Push to Your Fork**:
   ```bash
   git push origin feature/YourFeatureName
   ```

7. **Open a Pull Request**: Navigate to the original repository and open a pull request detailing your changes.

Please ensure your code adheres to the project's coding standards and include relevant tests where applicable.

## License

This project is licensed under the [MIT License](LICENSE).

## Conclusion

suluaP123 and Maibaum68 are autistic

---