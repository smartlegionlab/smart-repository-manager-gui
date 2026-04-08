# Smart Repository Manager GUI <sup>v1.2.3</sup>

---

A powerful desktop application for managing GitHub repositories with intelligent synchronization, and comprehensive visual management tools.

---

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/smartlegionlab/smart-repository-manager-gui)](https://github.com/smartlegionlab/smart-repository-manager-gui/)
![GitHub top language](https://img.shields.io/github/languages/top/smartlegionlab/smart-repository-manager-gui)
[![GitHub](https://img.shields.io/github/license/smartlegionlab/smart-repository-manager-gui)](https://github.com/smartlegionlab/smart-repository-manager-gui/blob/master/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/smartlegionlab/smart-repository-manager-gui?style=social)](https://github.com/smartlegionlab/smart-repository-manager-gui/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/smartlegionlab/smart-repository-manager-gui?style=social)](https://github.com/smartlegionlab/smart-repository-manager-gui/network/members)

---

## ⚠️ Disclaimer

**By using this software, you agree to the full disclaimer terms.**

**Summary:** Software provided "AS IS" without warranty. You assume all risks.

**Full legal disclaimer:** See [DISCLAIMER.md](https://github.com/smartlegionlab/smart-repository-manager-gui/blob/master/DISCLAIMER.md)

---

## Overview

**Smart Repository Manager GUI** provides a complete visual interface for managing your GitHub repositories.

**Key Benefits:**
- **Visual Management**: Full graphical interface for all operations
- **Smart Table**: Lazy-loading repository list with filtering and search
- **Multi-User Support**: Switching between GitHub accounts
- **Keyboard-Driven**: Complete keyboard shortcuts for power users

---

## System Initialization

Every session begins with an **8-step mandatory system checkup**:

1. **Directory Structure** - Creates and verifies workspace organization
2. **Internet Connection** - Validates network connectivity
3. **User Management** - Select or add GitHub account
4. **User Data** - Fetches GitHub profile information
5. **Repository Loading** - Retrieves complete repository list
6. **Local Copy Check** - Scans for existing local repositories
7. **Update Detection** - Identifies repositories needing updates

---

## Synchronization Operations

### **1. Synchronize All** `(Ctrl+S)`
Complete bidirectional sync - clones missing repositories and updates existing ones.

### **2. Update Needed Only** `(Ctrl+U)`
Smart update detection - only pulls repositories with new commits.

### **3. Clone Missing Only** `(Ctrl+M)`
Selective cloning - cloning only repositories not present locally.

### **4. Sync with Repair** `(Ctrl+R)`
Advanced recovery - detects and fixes corrupted repositories, then syncs.

### **5. Re-clone All** 
Complete refresh - removes and re-clones all local repositories.

### **6. Download All As Zip**
Complete parallel download - download all repositories as ZIP archives.

**Live Console**: Every sync operation displays real-time logs with timestamp, status, and duration for each repository.

---

## Main Dashboard

### Repository Table
- **Lazy Loading**: Loads 20 repositories at a time for optimal performance
- **Smart Filtering**: Filter by Local/Remote, Needs Update, Private/Public, Forks, Archived
- **Instant Search**: Real-time filtering by name, description, or language
- **Visual Indicators**: Status icons for local presence and update requirements
- **Context Menu**: Right-click actions for quick operations

### Status Panels

| Panel | Information Displayed |
|-------|---------------------|
| **Token** | Token validity, API limits (remaining/total), reset time |
| **Repositories** | Total count, local copies, pending updates |
| **User** | Display name, public repos, followers count |
| **Network** | Connection status, external IP, GitHub accessibility |

### Detail Dialogs
- **User Information** - Complete GitHub profile with avatar
- **Token Information** - Token scopes, creation date, rate limits
- **Network Information** - DNS, server responses, connection quality
- **Storage Management** - Disk usage, cleanup tools, repository details

---

## Keyboard Shortcuts

### File
| Shortcut | Action |
|----------|--------|
| `Ctrl+B` | Create Archive |
| `F5` | Refresh |
| `Ctrl+Q` | Exit |

### Synchronization
| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Synchronize All |
| `Ctrl+U` | Update Needed Only |
| `Ctrl+M` | Clone Missing Only |
| `Ctrl+Shift+R` | Sync with Repair |
| `Ctrl+Alt+R` | Re-clone All Repositories |
| `Ctrl+Shift+S` | Sync Selected |
| `Ctrl+Shift+C` | Clone Selected |
| `Ctrl+Shift+U` | Update Selected |
| `Ctrl+Shift+D` | Download all repositories |

### Repositories
| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+B` | Open in Browser |
| `Ctrl+L` | Open Local Folder |
| `Ctrl+D` | Show Details |
| `Ctrl+R` | Refresh List |
| `Ctrl+Del` | Delete Local Copy |

### Tools
| Shortcut | Action |
|----------|--------|
| `Ctrl+I` | User Information |
| `Ctrl+T` | Token Information |
| `Ctrl+Shift+N` | Network Information |
| `Ctrl+Shift+M` | Storage Management |

### Help
| Shortcut | Action |
|----------|--------|
| `F1` | Documentation |
| `Ctrl+/` | Keyboard shortcuts |
| `Ctrl+Shift+A` | About |

---

## Multi-User Management

- **Add Users**: Quick token validation and GitHub profile fetch
- **Switch Users**: Instant context switching with visual feedback
- **Delete Users**: Complete removal of user data and tokens
- **Avatar Support**: Automatic avatar download and circular display
- **Persistent Storage**: Token storage per user

---

## Installation

### Prerequisites
- Python 3.8+
- Git installed and configured
- GitHub Personal Access Token (with `repo` scope)
- PyQt6

### Generate GitHub Token
1. Visit [GitHub Tokens](https://github.com/settings/tokens/new)
2. Select permissions:
   - `repo` (full repository access)
3. Generate and copy token

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

## Directory Structure

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

## Screenshot

![Smart Repository Manager GUI](https://github.com/smartlegionlab/smart-repository-manager-gui/blob/master/data/images/smart_repository_manager_gui.png)

---

## Security

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

## Development Status

**ACTIVE DEVELOPMENT** - This project is under continuous development. While we strive for stability, you may encounter:

- Interface changes between versions
- New features in active testing
- Performance optimizations in progress
- Documentation updates pending

**Recommended for**: Development environments, personal use, testing
**Not recommended for**: Critical production systems without thorough testing

---

## Support & Contributions

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

## License

BSD 3-Clause License - See [LICENSE](LICENSE) file for details.

Copyright © 2026, Alexander Suvorov. All rights reserved.

---

## Developer

**Alexander Suvorov**  
- GitHub: [@smartlegionlab](https://github.com/smartlegionlab)  
- Email: [smartlegionlab@gmail.com](mailto:smartlegionlab@gmail.com)

---

*Smart Repository Manager GUI - Visual control for your GitHub universe.*
