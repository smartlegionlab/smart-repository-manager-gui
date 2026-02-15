# Smart Repository Manager GUI <sup>v1.0.1</sup>

A powerful desktop application for managing GitHub repositories with intelligent synchronization, SSH configuration, and comprehensive visual management tools.

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/smartlegionlab/smart-repository-manager-gui)](https://github.com/smartlegionlab/smart-repository-manager-gui/)
![GitHub top language](https://img.shields.io/github/languages/top/smartlegionlab/smart-repository-manager-gui)
[![GitHub](https://img.shields.io/github/license/smartlegionlab/smart-repository-manager-gui)](https://github.com/smartlegionlab/smart-repository-manager-gui/blob/master/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/smartlegionlab/smart-repository-manager-gui?style=social)](https://github.com/smartlegionlab/smart-repository-manager-gui/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/smartlegionlab/smart-repository-manager-gui?style=social)](https://github.com/smartlegionlab/smart-repository-manager-gui/network/members)

---

## 🚀 Overview

**Smart Repository Manager GUI** provides a complete visual interface for managing your GitHub repositories.

**Key Benefits:**
- **Visual Management**: Full graphical interface for all operations
- **Smart Table**: Lazy-loading repository list with filtering and search
- **Multi-User Support**: Switching between GitHub accounts
- **Keyboard-Driven**: Complete keyboard shortcuts for power users

---

## 📋 System Initialization

Every session begins with an **8-step mandatory system checkup**:

1. **Directory Structure** - Creates and verifies workspace organization
2. **Internet Connection** - Validates network connectivity
3. **SSH Configuration** - Checks and validates SSH setup
4. **User Management** - Select or add GitHub account
5. **User Data** - Fetches GitHub profile information
6. **Repository Loading** - Retrieves complete repository list
7. **Local Copy Check** - Scans for existing local repositories
8. **Update Detection** - Identifies repositories needing updates

---

## 🔄 Synchronization Operations

### **1. Synchronize All** `(Ctrl+S)`
Complete bidirectional sync - clones missing repositories and updates existing ones.

### **2. Update Needed Only** `(Ctrl+U)`
Smart update detection - only pulls repositories with new commits.

### **3. Clone Missing Only** `(Ctrl+M)`
Selective cloning - downloads only repositories not present locally.

### **4. Sync with Repair** `(Ctrl+R)`
Advanced recovery - detects and fixes corrupted repositories, then syncs.

### **5. Re-clone All** 
Complete refresh - removes and re-clones all local repositories.

### **6. Download All As Zip**
Complete download - download all repositories as ZIP archives.

**Live Console**: Every sync operation displays real-time logs with timestamp, status, and duration for each repository.

---

## 🖥️ Main Dashboard

### Repository Table
- **Lazy Loading**: Loads 20 repositories at a time for optimal performance
- **Smart Filtering**: Filter by Local/Remote, Needs Update, Private/Public, Forks, Archived
- **Instant Search**: Real-time filtering by name, description, or language
- **Visual Indicators**: Status icons for local presence and update requirements
- **Context Menu**: Right-click actions for quick operations

### Status Panels

| Panel | Information Displayed |
|-------|---------------------|
| **🔑 Token** | Token validity, API limits (remaining/total), reset time |
| **📚 Repositories** | Total count, local copies, pending updates |
| **👤 User** | Display name, public repos, followers count |
| **🌐 Network** | Connection status, external IP, GitHub accessibility |
| **🔐 SSH** | Configuration status, keys count, GitHub authentication |

### Detail Dialogs
- **User Information** - Complete GitHub profile with avatar
- **Token Information** - Token scopes, creation date, rate limits
- **SSH Configuration** - Key management, testing, troubleshooting
- **Network Information** - DNS, server responses, connection quality
- **Storage Management** - Disk usage, cleanup tools, repository details

---

## 🔑 SSH Management

### Key Operations
- **Generate Keys**: Support for ED25519 (recommended), RSA 4096, ECDSA, DSA
- **View Public Keys**: Display and copy to clipboard
- **Test Connection**: Verify SSH connectivity to GitHub
- **Fix Permissions**: Automatic repair of SSH file permissions
- **Add to known_hosts**: Configure GitHub host key
- **Create SSH Config**: Generate proper SSH configuration

---

## ⌨️ Keyboard Shortcuts

| Category | Shortcut       | Action |
|----------|----------------|--------|
| **File** | `F5`           | Refresh |
| | `Ctrl+Q`       | Exit |
| **Sync** | `Ctrl+S`       | Synchronize All |
| | `Ctrl+U`       | Update Needed |
| | `Ctrl+M`       | Clone Missing |
| | `Ctrl+Shift+R` | Sync with Repair |
| | `Ctrl+Shift+S` | Sync Selected |
| | `Ctrl+Shift+C` | Clone Selected |
| | `Ctrl+Shift+U` | Update Selected |
| **Repos** | `Ctrl+Shift+B` | Open in Browser |
| | `Ctrl+L`       | Open Local Folder |
| | `Ctrl+R`       | Refresh List |
| | `Ctrl+D`       | Show Details |
| | `Ctrl+Delete`  | Delete Local Copy |
| **Tools** | `Ctrl+I`       | User Information |
| | `Ctrl+T`       | Token Information |
| | `Ctrl+Alt+S`   | SSH Configuration |
| | `Ctrl+Shift+N` | Network Information |
| | `Ctrl+Shift+M` | Storage Management |
| **Help** | `F1`           | Documentation |

---

## 👥 Multi-User Management

- **Add Users**: Quick token validation and GitHub profile fetch
- **Switch Users**: Instant context switching with visual feedback
- **Delete Users**: Complete removal of user data and tokens
- **Avatar Support**: Automatic avatar download and circular display
- **Persistent Storage**: Token storage per user

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- Git installed and configured
- An initialized SSH key with a GitHub account.
- GitHub Personal Access Token (with `repo` scope)
- PyQt6

### Setup SSH 

Before using the application, you need to initialize your SSH key:

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Add to GitHub account
cat ~/.ssh/id_ed25519.pub  # Copy this output
# Paste at https://github.com/settings/keys

# Verify connection
ssh -T git@github.com
```

After that, install and run the application:

```bash
# Clone repository
git clone https://github.com/smartlegionlab/smart-repository-manager-gui.git

# Go to project folder
cd smart-repository-manager-gui/

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch application
python app.py
```

---

## 📁 Directory Structure

```
~/smart_repository_manager/
├── config.json              # Multi-user configuration
├── username_1/             # User-specific directories
│   ├── repositories/       # Local Git repositories
│   ├── archives/          # ZIP backups
│   ├── downloads/          # Downloaded repositories as ZIP archives
│   ├── logs/             # Operation logs
│   ├── backups/          # Manual backups
│   ├── temp/             # Temporary files
│   └── avatar.png        # GitHub profile picture
└── username_2/            # Additional users
```

---

## 🖼️ Screenshot

![Smart Repository Manager GUI](https://github.com/smartlegionlab/smart-repository-manager-gui/blob/master/data/images/smart_repository_manager_gui.png)

---

## 🔒 Security

- **SSH Keys**: Proper file permissions enforced automatically
- **Local-Only**: All operations performed locally with GitHub API
- **No Telemetry**: No data is sent to external servers
- **No Account Linking**: Your GitHub account is not linked to any external service

---

## Related Projects

This GUI application is powered by the same core engine as:

### [Smart Repository Manager Core](https://github.com/smartlegionlab/smart-repository-manager-core) 
A Python library for managing Git repositories with intelligent synchronization, SSH configuration validation, and GitHub integration. This library serves as the foundation for both CLI and GUI implementations.

### [Smart Repository Manager CLI](https://github.com/smartlegionlab/smart-repository-manager-cli)
A comprehensive command-line tool for users who prefer terminal-based workflows. Offers identical functionality in a text-based interface.

---

## ⚠️ DISCLAIMER

**THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES OF ANY KIND, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.**

**THE AUTHORS AND COPYRIGHT HOLDERS ASSUME NO LIABILITY FOR:**

1. **DATA LOSS OR CORRUPTION**
   - Accidental deletion or modification of local repositories
   - Corruption of Git objects or repository metadata
   - Loss of uncommitted changes or stashes
   - Incomplete or failed clone/pull operations

2. **REPOSITORY DAMAGE**
   - Force push conflicts or unintended overwrites
   - Broken Git references or detached HEAD states
   - Corrupted SSH keys or invalid configurations
   - Failed merge operations or unresolved conflicts

3. **SECURITY INCIDENTS**
   - Exposure of GitHub Personal Access Tokens
   - Compromise of SSH private keys
   - Unauthorized repository access
   - Credential theft or misuse

4. **NETWORK OR SERVICE ISSUES**
   - GitHub API rate limiting or downtime
   - Network connectivity failures
   - DNS resolution problems
   - SSL/TLS certificate errors

5. **SYSTEM OR PERFORMANCE ISSUES**
   - Excessive disk space usage
   - High CPU or memory consumption
   - Application crashes or freezes
   - Operating system compatibility problems

**YOU ASSUME FULL RESPONSIBILITY FOR:**

- **Regular backups** of all repositories and configuration files
- **Secure storage** of authentication tokens and SSH keys
- **Verification** of all operations before execution
- **Testing** in non-production environments first
- **Compliance** with GitHub Terms of Service

**BY USING THIS SOFTWARE, YOU ACKNOWLEDGE THAT:**

- This is development software in active development
- Features may change without notice
- Bugs and incomplete features may exist
- No guaranteed timeline for fixes or updates
- Technical support is provided on a best-effort basis

**Use at your own risk**. Always maintain backups of your repositories and tokens. This project is in active development and may contain bugs or incomplete features.

- USER ACCEPTS FULL AND UNCONDITIONAL RESPONSIBILITY!!!

Usage of this software constitutes your FULL AND UNCONDITIONAL ACCEPTANCE of this disclaimer. If you do not accept ALL terms and conditions, DO NOT USE THE SOFTWARE.

BY PROCEEDING, YOU ACKNOWLEDGE THAT YOU HAVE READ THIS DISCLAIMER IN ITS ENTIRETY, UNDERSTAND ITS TERMS COMPLETELY, AND ACCEPT THEM WITHOUT RESERVATION OR EXCEPTION.

---

## 📌 Development Status

**⚠️ ACTIVE DEVELOPMENT** - This project is under continuous development. While we strive for stability, you may encounter:

- Interface changes between versions
- New features in active testing
- Performance optimizations in progress
- Documentation updates pending

**Recommended for**: Development environments, personal use, testing
**Not recommended for**: Critical production systems without thorough testing

---

## 🤝 Support & Contributions

### Issues
- **Bug Reports**: Please include system information, steps to reproduce, and error logs
- **Feature Requests**: Describe the use case and expected behavior
- **Questions**: Check existing issues before creating new ones

### Contributions
1. Fork the repository
2. Create a feature branch
3. Follow existing code style
4. Submit pull request with clear description

---

## 📄 License

BSD 3-Clause License - See [LICENSE](LICENSE) file for details.

Copyright © 2026, Alexander Suvorov. All rights reserved.

---

## 👨‍💻 Developer

**Alexander Suvorov**  
- GitHub: [@smartlegionlab](https://github.com/smartlegionlab)  
- Email: [smartlegionlab@gmail.com](mailto:smartlegionlab@gmail.com)

---

*Smart Repository Manager GUI - Visual control for your GitHub universe.*