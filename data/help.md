# Smart Repository Manager — Help

## What is this application?

Smart Repository Manager is a desktop application for managing your GitHub
repositories. It talks to GitHub via a Personal Access Token, lists your
repositories, and helps you clone, update, repair and download them locally.

All data stays on your machine. The application does not send anything to
third-party servers — only to the GitHub API, with your token.

---

## First launch

When you start the application for the first time, it runs a short checkup:

1. **Directory structure** — creates `~/smart_repository_manager/`
2. **Internet connection** — checks connectivity and GitHub access
3. **User management** — asks you to select or add a GitHub account
4. **User data** — fetches your GitHub profile
5. **Repository loading** — downloads the list of your repositories
6. **Local copies** — checks which repositories are already cloned
7. **Update detection** — finds repositories that have new commits on GitHub

After the checkup finishes, the main window opens.

---

## Getting a GitHub token

1. Open https://github.com/settings/tokens/new
2. Give the token a name (anything, e.g. "Smart Repository Manager")
3. Select the `repo` scope
4. Click **Generate token**
5. Copy the token and paste it into the "Add new user" field in the app

The token is stored locally in `~/smart_repository_manager/config.json`.

---

## Main window

### Header

- **Title** — "Smart Repository Manager"
- **@username** (top-right) — click to open User Information

### Status panels

| Panel            | What it shows                                                     |
|------------------|-------------------------------------------------------------------|
| **Token**        | Token validity, GitHub API limit (remaining / total), reset time  |
| **Repositories** | Total repositories, how many cloned locally, how many need update |
| **User**         | Display name, public repositories count, followers                |
| **Network**      | Online / offline, external IP, GitHub API reachability            |

### Repository table

- **Columns**: #, Name, Last Update, Actual (update flag), Local (clone flag), Private
- **Lazy loading**: 20 repositories per page. Click **Load more** to see the next 20.
- **Search** — filters by name, description or language in real time
- **Filter** — All / Local Only / Remote Only / Needs Update / Private / Public / Forks / Archived
- **Double click** — opens repository details
- **Right click** — context menu with actions (clone, update, re-clone, delete, download, open in browser, show details)

### Buttons (bottom row)

- **Update (N)** — only appears when N repositories need an update. Runs "Update Needed Only" for those N.
- **Sync Actions** — dropdown menu with all sync operations
- **Folders** — storage management (disk usage, cleanup)
- **Network** — network diagnostics
- **Token** — token details and rate limits
- **Exit** — closes the application (with confirmation)

---

## Synchronization operations

### Synchronize All (`Ctrl+S`)
Clones missing repositories and updates existing ones. Use this when you
want everything in sync.

### Update Needed Only (`Ctrl+U`)
Pulls only repositories that have new commits on GitHub. Skips repositories
that are already up to date. Fastest way to keep your local copies fresh.

### Clone Missing Only (`Ctrl+M`)
Clones only repositories that you don't have locally. Does not touch
existing local copies.

### Sync with Repair (`Ctrl+Shift+R`)
Checks every local repository for corruption. Corrupted repositories are
re-cloned, working repositories are updated. Slower than normal sync, but
fixes broken clones.

### Re-clone All (`Ctrl+Alt+R`)
**Deletes** every local repository and clones it again from GitHub.
Use only when you want a completely fresh start.

### Download All Repositories (`Ctrl+Shift+D`)
Downloads each repository as a ZIP archive (not a git clone). Useful for
backups or when you don't have git. Downloads go to
`~/smart_repository_manager/<username>/downloads/`.

### Selected operations
- **Sync Selected** (`Ctrl+Shift+S`) — sync only the selected repositories
- **Clone Selected** (`Ctrl+Shift+C`) — clone only the selected ones
- **Update Selected** (`Ctrl+Shift+U`) — update only the selected ones

---

## Repository details dialog

Double click a repository (or `Ctrl+D`) to open details:

- **Name, full name, description**
- **URL, creation date, last update, default branch, license, homepage**
- **Statistics**: language, stars, forks, watchers, open issues, size
- **Status**: "Update Available" or "Up to date"
- **Local**: "Local copy exists" or "Not cloned locally"
- **Repo Actions** — dropdown menu (clone / update / re-clone / delete / download / open in browser)

---

## Multi-user management

The application supports multiple GitHub accounts:

- **Add** — paste a new token in the user selection dialog on first launch
- **Switch** — select a different account from the same dialog
- **Delete** — removes the token and cached data for that account

Each user has its own directory under `~/smart_repository_manager/<username>/`.

---

## Keyboard shortcuts

### File
| Shortcut | Action         |
|----------|----------------|
| `Ctrl+B` | Create Archive |
| `F5`     | Refresh        |
| `Ctrl+Q` | Exit           |

### Synchronization
| Shortcut       | Action              |
|----------------|---------------------|
| `Ctrl+S`       | Synchronize All     |
| `Ctrl+U`       | Update Needed Only  |
| `Ctrl+M`       | Clone Missing Only  |
| `Ctrl+Shift+R` | Sync with Repair    |
| `Ctrl+Alt+R`   | Re-clone All        |
| `Ctrl+Shift+S` | Sync Selected       |
| `Ctrl+Shift+C` | Clone Selected      |
| `Ctrl+Shift+U` | Update Selected     |
| `Ctrl+Shift+D` | Download all as ZIP |

### Repositories
| Shortcut       | Action            |
|----------------|-------------------|
| `Ctrl+Shift+B` | Open in Browser   |
| `Ctrl+L`       | Open Local Folder |
| `Ctrl+D`       | Show Details      |
| `Ctrl+R`       | Refresh List      |
| `Ctrl+Del`     | Delete Local Copy |

### Tools
| Shortcut       | Action              |
|----------------|---------------------|
| `Ctrl+I`       | User Information    |
| `Ctrl+T`       | Token Information   |
| `Ctrl+Shift+N` | Network Information |
| `Ctrl+Shift+M` | Storage Management  |

### Help
| Shortcut       | Action                  |
|----------------|-------------------------|
| `F1`           | This help               |
| `Ctrl+/`       | Keyboard shortcuts list |
| `Ctrl+Shift+A` | About                   |

---

## Where data is stored

```
~/smart_repository_manager/
├── config.json              # tokens for all users
├── <username>/
│   ├── repositories/        # local git clones
│   ├── archives/            # ZIP backups (Ctrl+B)
│   ├── downloads/           # ZIP downloads (Ctrl+Shift+D)
│   ├── logs/                # operation logs
│   ├── backups/             # manual backups
│   ├── temp/                # temporary files
│   └── avatar.png           # GitHub avatar
```

If you want to start completely fresh: delete `~/smart_repository_manager/`
and restart the application. It will recreate everything and ask for the
token again.

---

## Troubleshooting

**"Invalid token"**
The token must have `repo` scope. Regenerate it at
https://github.com/settings/tokens and paste again.

**"Failed to load repositories"**
Usually a network issue or expired token. Check the Network panel first.
If network is fine — try deleting the user and adding the token again.

**"Warning: Failed to fetch all branches ... timed out"**
This is a non-fatal warning. It happens when a large repository takes more
than 60 seconds to fetch metadata (for example, repositories with a very
long history). The application will still work — the repository just gets
flagged as "needs update". You can ignore this warning.

**Repository shows "Update Available" but there are no new commits**
Click "Update Needed Only" (`Ctrl+U`) for that repository. The flag will
clear after a successful pull.

**Application doesn't start on Linux with an xcb error**
Install the missing system library:

```
sudo apt install libxcb-cursor0
```

---

## Where to get more

- **Project repository**: https://github.com/smartlegionlab/smart-repository-manager-gui
- **Core library**: https://github.com/smartlegionlab/smart-repository-manager-core
- **CLI version**: https://github.com/smartlegionlab/smart-repository-manager-cli

