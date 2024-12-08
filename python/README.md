# Flutter GitHub Manager

**Flutter GitHub Manager** is a powerful tool for automating the management of Flutter projects with seamless integration into GitHub. This application allows you to efficiently host your Flutter projects on GitHub, set up GitHub Actions workflows for automated builds, and easily download the generated artifacts. The tool offers both a user-friendly graphical interface (GUI) and a flexible command-line interface (CLI) to cater to your individual needs.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [GUI Version](#gui-version)
  - [CLI Version](#cli-version)
- [Flags and Options](#flags-and-options)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Repository Management**: Create and manage GitHub repositories directly from the application.
- **Automated Builds**: Set up GitHub Actions workflows to perform automated builds for iOS and Android.
- **Artifact Download**: Easily download generated IPA and APK files.
- **User-Friendly GUI**: Intuitive graphical interface for easy operation.
- **Powerful CLI**: Flexible command-line interface with extensive options for advanced users.
- **Automatic Dependency Installation**: The tool checks and installs missing dependencies automatically.
- **Logging and Status Displays**: Real-time logs and status displays to monitor the build process.

## Installation

### Prerequisites

- **Python 3.6+**: Ensure that Python is installed on your system.
- **Git**: Git must be installed on your system.
- **GitHub CLI (`gh`)**: GitHub CLI is required for advanced features.

### Steps

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/flutter-github-manager.git
   cd flutter-github-manager
   ```

2. **Install Dependencies:**

   Install the required Python packages using `pip`:

   ```bash
   pip install -r requirements.txt
   ```

   Alternatively, you can allow the dependencies to be installed automatically during the first run.

3. **Install GitHub CLI:**

   Follow the official instructions to install the [GitHub CLI](https://cli.github.com/).

## Usage

### GUI Version

The GUI version provides a user-friendly interface for managing your Flutter projects with GitHub integration.

1. **Start the Application:**

   ```bash
   python compiler_gui.py
   ```

2. **Repository Setup:**

   - **GitHub Token**: Enter your GitHub Personal Access Token.
   - **Action**: Choose between `createrepo` (Create a new repository) or `repo` (Use an existing repository).
   - **Repository Name**: Enter the name of the GitHub repository.

3. **Build Configuration:**

   - **Project Path**: Select the directory of your Flutter project.
   - **IPA File Name**: Enter the name of the IPA file to be created.
   - **APK File Name**: Enter the name of the APK file to be created.
   - **Build Directory**: Choose the directory where builds should be stored.
   - **Branch Name**: Enter the branch name (default is `main`).
   - **Platforms to Build**: Select the platforms (`iOS`, `Android`, or both).
   - **Include/Exclude Specific Files**: Optionally include or exclude specific files.
   - **Additional GitHub Remotes**: Enter additional GitHub usernames for multiple remotes.
   - **Enable Verbose Output**: Enable this option for detailed logs.

4. **Start the Build:**

   Click on **Start Build** to initiate the build process. Switch to the **Logs & Status** tab to monitor the progress and logs in real-time.

### CLI Version

The CLI version offers a flexible way to manage your Flutter projects via the command line with numerous configuration options.

#### Basic Usage

```bash
python compiler.py --action <ACTION> --repo <REPO_NAME> [OPTIONS]
```

#### Example

Creating a new repository and starting a build:

```bash
python compiler.py --action createrepo --repo MyFlutterApp --token YOUR_GITHUB_TOKEN
```

## Flags and Options

Below are all the available flags and options for the CLI version of the tool:

| Flag/Option                  | Short Form | Description                                                                                                 | Default Value          |
|------------------------------|------------|-------------------------------------------------------------------------------------------------------------|------------------------|
| `--token`                    | `-t`       | GitHub Personal Access Token. Alternatively, the token can be provided via the `GITHUB_TOKEN` environment variable. | -                      |
| `--action`                   | `-a`       | Action to perform: `createrepo` (Create a new repository) or `repo` (Use an existing repository).             | -                      |
| `--repo`                     | `-r`       | Name of the GitHub repository.                                                                              | -                      |
| `--ipa-name`                 |            | Name of the IPA file to be created.                                                                          | `FlutterIpaExport.ipa` |
| `--apk-name`                 |            | Name of the APK file to be created.                                                                          | `FlutterApkExport.apk` |
| `--build-dir`                |            | Directory where builds should be stored.                                                                      | `builds`               |
| `--project-path`             | `-p`       | Path to the Flutter project.                                                                                   | `.`                    |
| `--skip-dependencies`        |            | Skips the installation of dependencies.                                                                        | `False`                |
| `--skip-build`               |            | Skips the build and download steps.                                                                             | `False`                |
| `--skip-upload`              |            | Skips uploading the project to GitHub.                                                                          | `False`                |
| `--build-timeout`            |            | Build timeout in seconds.                                                                                       | `1800`                 |
| `--poll-interval`            |            | Polling interval in seconds for workflow status.                                                                 | `30`                   |
| `--verbose`                  | `-v`       | Enables verbose output for detailed logs.                                                                        | `False`                |
| `--interactive`              | `-i`       | Runs the tool in interactive mode, guiding you step by step through the process.                                 | `False`                |
| `--branch`                   |            | Name of the Git branch to use.                                                                                   | `main`                 |
| `--platforms`                |            | Platforms to build for: `iOS`, `Android`. Multiple platforms can be specified separated by spaces.               | `['iOS']`              |
| `--include`                  |            | File patterns to include (e.g., `src/, assets/`). Multiple patterns separated by spaces.                         | -                      |
| `--exclude`                  |            | File patterns to exclude (e.g., `*.log, secrets/`). Multiple patterns separated by spaces.                       | -                      |
| `--remotes`                  |            | Additional GitHub usernames for multiple remotes. Multiple usernames separated by spaces.                         | -                      |

### Interactive Mode

Start the tool in interactive mode to be guided step by step through the process:

```bash
python compiler.py --interactive
```

## Contributing

Contributions to **Flutter GitHub Manager** are welcome! Follow these steps to contribute:

1. **Fork** the repository.
2. Create a **new branch** for your changes.
3. **Commit** your changes with meaningful messages.
4. **Push** your branch to your fork.
5. **Open** a Pull Request.

Please ensure that your changes are well-documented and tested.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For questions, suggestions, or support, please contact:

- **Name**: Your Name
- **Email**: your.email@example.com
- **GitHub**: [@yourusername](https://github.com/yourusername)

---