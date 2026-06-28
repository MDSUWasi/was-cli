# 🕰️ WAS — Your Document Time Machine CLI
A powerful version control system designed specifically for personal documents and study notes.Python
License
Platform
Download
Track • Restore • Analyze your documents with simple terminal commands

## 🎬 Quick Demo Videos
### 📁 All demos available in the try/ folder
**Installing was for first time (The demo is done on Linux Device running Debian)**

https://github.com/user-attachments/assets/63e26887-9df5-4025-aeb0-1cc87f8d92da

**Checking whether WAS was successfully installed or not**

https://github.com/user-attachments/assets/4be5777e-46f1-4717-97b0-0fef6fe56a25

**Basic uses of WAS** 

https://github.com/user-attachments/assets/441581e6-5f9f-4883-b65d-8dc59c89c12b


**Uninstalling WAS**

https://github.com/user-attachments/assets/c1b72e6d-ebde-4f12-aee8-26801a4f924c

**Note:** I have used cd was-cli because was-cli folder is inside my root directory (Or main files). But users may need to add the accurate path according to the path where was-cli was saved

**Note:** Uninstalling using "./uninstall.sh" will uninstall it from device but the source code will remain in a folder name "was-cli". To completely remove WAS, just delete the folder (was-cli) after using ./uninstall.sh

## You can easily see all commands for WAS by typing ``` was --help ``` inside the terminal

## 🤔 What is WAS?
WAS (Document Time Machine) is a lightweight, zero-dependency version control system built exclusively for personal document management. Inspired by Git but simplified for writers, students, researchers, and anyone who needs to track changes in their Word docs, notes, manuscripts, or code files.
Unlike traditional VCS tools that require learning complex concepts like branches, stashes, and remotes, WAS focuses purely on one job: automatic time-travel for your documents.
Why Build Another Version Control Tool?
graph TD

    

## ✨ Key Features at a Glance
<table>
<tr>
<th width="18%">Feature</th>
<th>Description</th>
<th>Why You'll Love It</th>
</tr>
<tr>
<td><strong>🔄 Auto-Save Watch Mode</strong></td>
<td>Background monitoring detects file modifications and saves snapshots automatically every 2 seconds</td>
<td>No need to remember manual commits — just edit!</td>
</tr>
<tr>
<td><strong>📜 Full History Log</strong></td>
<td>Timeline view of all commits with timestamps, messages, and custom tags</td>
<td>See exactly when and why you made changes months ago</td>
</tr>
<tr>
<td><strong>⏪ Instant Rollback</strong></td>
<td>Restore any document to a specific historical version with one command</td>
<td>Mistake undo button for your entire workspace</td>
</tr>
<tr>
<td><strong>🎨 Colorized Diff View</strong></td>
<td>Green/red highlighting shows additions/deletions directly in terminal</td>
<td>Visually understand what changed without external tools</td>
</tr>
<tr>
<td><strong>🏷️ Custom Tagging</strong></td>
<td>Mark important milestones ("exam-prep", "final-draft", "v3-revision")</td>
<td>Navigate timeline with meaningful names instead of cryptic IDs</td>
</tr>
<tr>
<td><strong>📊 Writing Analytics</strong></td>
<td>Track line growth, most active days, and document statistics</td>
<td>Become aware of your writing habits and productivity patterns</td>
</tr>
<tr>
<td><strong>📦 Workspace Export</strong></td>
<td>Extract historical versions to new locations without affecting current workspace</td>
<td>Create drafts from old versions without losing modern edits</td>
</tr>
<tr>
<td><strong>🔍 Full-History Search</strong></td>
<td>Search entire document history for terms/phrases across all snapshots</td>
<td>"Where did I write that paragraph about mitochondria?"</td>
</tr>
<tr>
<td><strong>💾 Storage Optimization</strong></td>
<td>Purge automatic background saves to reclaim disk space while keeping key versions</td>
<td>Balance convenience with storage efficiency</td>
</tr>
<tr>
<td><strong>📄 Multi-Format Support</strong></td>
<td>.docx, .odt, .txt, .md, .py, .json, .html, .css — plus more coming</td>
<td>Unified tool for mixed-format workflows</td>
</tr>
</table>

## 🛠️ Installation Guide

**⚡ One-Line Install (Recommended)**

Copy and paste into your terminal:
```
git clone https://github.com/MDSUWasi/was-cli.git && cd was-cli && chmod +x install.sh && ./install.sh


```

## 🖥️ Platform-Specific Instructions
**Linux (Ubuntu/Debian/Fedora/Mint)**
### 1. Ensure Python 3 is installed
```
sudo apt update && sudo apt install python3 python3-pip -y
```
```
use "apt for debian based destros and "dnf" for fedora based destros
```

### 2. Clone or download repository
```
git clone https://github.com/MDSUWasi/was-cli.git
cd was-cli
```

### 3. Run installer script
```
chmod +x install.sh
./install.sh
```

### 4. Add to PATH (if not done automatically)
```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 5. Verify installation
```
was --help
```

**MAC-OS**

### 1. Install Python via Homebrew (if not already present)
```
brew install python3
```

### 2. Clone repository
```
git clone https://github.com/MDSUWasi/was-cli.git
cd was-cli
```

### 3. Run installer
```
chmod +x install.sh
./install.sh
```
### 4. For Zsh users (default on macOS Catalina+)
```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```
### 5. For Bash users
```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```
### 6. Verify
```
was --help
```

**Windows (WSL/Git Bash)**

### Windows doesn't have native support yet. Use WSL2:

### 1. Install WSL2 (PowerShell as Administrator)
```
wsl --install -d Ubuntu
```
### 2. Follow Linux instructions above inside WSL terminal

### Alternative: Use Git Bash with Python installed
### Download Python from python.org/downloads
### Then run pip install was-cli


## ✅ Verifying Installation
After installation, confirm everything works:
### Check version
```
was --version
```
### Test help command
```
was --help
```
### Try basic initialization in test directory
```
mkdir ~/test_was_repo && cd ~/test_was_repo
```
```
was init
```

**You should see: "Initialized empty 'Was' repository successfully."**

## ❌ Uninstallation
**Want to remove WAS cleanly?**

### Option 1: Use provided uninstaller
```
cd /path/to/was-cli
chmod +x uninstall.sh
```
```
./uninstall.sh
```

## 🚀 Quick Start Guide

Learn WAS in under 5 minutes!

### Step 1: Initialize Your First Repository
```
cd ~/school_notes
```
```
was init
```

Creates a hidden .was/ directory to store all version data:
```
~/school_notes/
├── chemistry_notes.docx
├── biology_report.txt
└── .was/                 ← Hidden repository database
    ├── history.json      ← Commit history metadata
    └── versions/         ← Stored snapshots per version
        ├── v1_chemistry_notes.docx
        └── v2_biology_report.txt
```

### Step 2: Track Your First File
```
was save chemistry_notes.docx "Started alkane basics" "Homework Week 1"
```
Output:
```
✅ Saved base state of 'chemistry_notes.docx' as v1a2b3c4d!
```

This creates a baseline snapshot. Subsequent saves only commit if changes are detected.

### Step 3: Enable Auto-Protection (Foreground)
```
was watch chemistry_notes.docx
```
WAS will now monitor the file every 2 seconds and auto-save changes automatically. 
Press Ctrl+C to stop watching.

Each auto-save appears as:
Modification detected at 2026-06-28 14:23:41. Processing change...
Auto-saved version v5f9e8g7h6 for chemistry_notes.docx!


### Step 4: Review Progress Later
#### Check current status
```
was status chemistry_notes.docx
```
Output:
```
🟡 File 'chemistry_notes.docx' is Modified (Unsaved: +12 insertions, -3 deletions).
```

## See full timeline
```
was log chemistry_notes.docx
```
Output:
```
=== TIMELINE LOG ===

Commit ID: v5f9e8g7h6 [Tags: exam-ready]
Date:      2026-06-28 14:23:41
File:      chemistry_notes.docx
What:      Added mechanism for dehydration reactions
Why:       Prof mentioned in lecture

----------------------------------------
Commit ID: v1a2b3c4d
Date:      2026-06-25 09:15:00
File:      chemistry_notes.docx
What:      Started alkane basics
Why:       Homework Week 1
----------------------------------------
```

### Step 5: Recover Lost Work

Accidentally deleted content? No panic!
#### See what changed
```
was diff chemistry_notes.docx
```
Output (colorized):
```
@@ -12,5 +12,8 @@ Alkane Naming Convention
 The parent chain determines the prefix:
   methane = 1 carbon
+ethane = 2 carbons
+propane = 3 carbons
+buts = 4 carbons
 hexane = 6 carbons
 heptane = 7 carbons
 octane = 8 carbons
 ```
### Restore to earlier version
```
was checkout chemistry_notes.docx v1a2b3c4d
```
Done! Your file is back to its earlier state. Current unsaved changes are discarded.

### Step 6: Tag Important Milestones
Create friendly bookmarks for critical versions:
```
was tag chemistry_notes.docx v5f9e8g7h6 "midterm-final"
```
Later, easily restore using the tag name:
```
was checkout chemistry_notes.docx midterm-final
```
## Step 7: Discover Where You Mentioned Something
```
was search "photosynthesis"
```
Output:

```
🔍 Found 'photosynthesis' in the following historical backups:
  * Version: v3c2d1e0f | File: biology_report.txt | Date: 2026-06-20 11:42:00
    Lines matched: 47, 52, 89
    Save context: "Added chloroplast diagrams"
```

## ⚙️ How It Works Under the Hood
Understanding the architecture helps you trust your data. WAS is modular and transparent.
Architecture Overview
flowchart TB
    subgraph User["User Layer"]
        CLI[Cli.py - Terminal Interface]
    end
    
    subgraph Logic["Logic Layer"]
        Hist[History.py - Database & Commits]
        Ext[Extractor.py - Format Parsing]
        Dif[Differ.py - Delta Generation]
    end
    
    subgraph Storage["Storage Layer"]
        JSON[.was/history.json]
        SNAPS[.was/versions/*.ext]
    end
    
    CLI --> Hist
    Hist --> Ext
    Hist --> Dif
    Hist --> JSON
    Hist --> SNAPS

## Module-by-Module Breakdown
### 1. cli.py — The Commander

Handles all user input, argument parsing, and dispatches to appropriate handlers. Maintains colorful, readable terminal output.

***Key responsibilities:***

Parse command arguments (sys.argv)
Route to handler functions (handle_init, handle_save, etc.)
Format user-facing output with ANSI colors
Display help menu when no command given

### 2. history.py — The Core Brain
All database operations live here. This is where commits are recorded, histories retrieved, and snapshots managed.

**Functions include:**

**init_repository()** — Creates .was/ structure
**save_commit()** — Saves new snapshots with metadata
**checkout_file()** — Restores specific versions
**get_status()** — Detects unsaved changes
**get_statistics()** — Generates analytics
**search_history()** — Finds text across all backups
**purge_history()** — Cleans redundant auto-saves
```
Data model:
{
  "repository_info": {
    "created_at": 1719504000,
    "version": "1.4.0"
  },
  "commits": [
    {
      "id": "v1a2b3c4d",
      "timestamp": 1719504900,
      "filepath": "chemistry_notes.docx",
      "message": "Started alkane basics",
      "reason": "Homework Week 1",
      "snapshot_file": "v1a2b3c4d_chemistry_notes.docx",
      "is_baseline": true,
      "delta": []
    }
  ],
  "tracked_files": {
    "chemistry_notes.docx": {
      "current_version": "v1a2b3c4d"
    }
  },
  "tags": {
    "midterm-final": {
      "filepath": "chemistry_notes.docx",
      "version_id": "v5f9e8g7h6"
    }
  }
}
```
### 3. extractor.py — The Decoder
Universal text extraction for multiple document formats. Each extension gets dedicated parser.

**Supported formats:**

DOCX → OpenXML ZIP structure → XML paragraph nodes → concatenated text
ODT → ODF ZIP structure → XML text elements → extracted paragraphs
.txt, .md, .py, etc. → UTF-8 raw lines

Uses only standard library (zipfile, xml.etree.ElementTree).

### 4. differ.py — The Comparator
Generates unified diffs between two file states using Python's difflib. Outputs both human-readable colorized diffs and numerical summaries.

**Produces:**

Insertion count (+lines added)
Deletion count (-lines removed)
Colored terminal output (green/additions, red/deletions, cyan/context)

### 5. patcher.py — Future Ready (Currently Unused)
Contains apply_delta() for applying patches during checkout. Not wired in because WAS prioritizes safety through full snapshots over delta-only storage. Designed for future optimization where you might switch to delta-based storage.
### 6. Security Helpers (Embedded throughout)

Path validation — Prevents escaping workspace via symlinks or ../ attacks
Atomic writes — Temp file + shutil.move prevents corruption on crash
File locking — fcntl.flock() handles concurrent access gracefully
String sanitization — Trims length, removes control characters before database storage


Snapshot Strategy Explained
sequenceDiagram
    participant U as User
    participant W as WAS Watch Mode
    participant S as Snapshot Store
    participant DB as Database JSON
    
    U->>W: Edit document continuously
    alt File modified every 2 sec
        W->>S: Copy complete file snapshot
        S->>DB: Record commit entry with ID
        DB-->>U: Notification: "Auto-saved!"
    else No change detected
        W-->>W: Skip saving (no-op)
    end
## Why full snapshots?

Simpler and less error-prone than deltas
Guaranteed recoverability even if patch algorithm has bugs
Easy to audit/debug (open .was/versions/vXXX_filename.ext)
Modern SSDs + compression make storage cost negligible


**📦 Dependencies (None!)
That's right — WAS requires only Python's standard library**.
## Internal requirements verified at runtime:
python_requires = ">=3.6"

## Standard libraries used internally:
```
import os           # Path manipulation, file existence checks
import json         # Database serialization
import time         # Timestamp generation
import shutil       # Atomic file moves, copies
import subprocess   # System notifications via notify-send
import uuid         # Unique version identifiers
import fcntl        # File locking for concurrency
import zipfile      # DOCX/ODT ZIP unpacking
import xml.etree    # Document XML parsing
from collections import Counter  # Statistics aggregation
from difflib import unified_diff  # Change detection
```

### External dependencies: ZERO
### This ensures maximum compatibility ### across distros and minimal probematic surface

**📂 Directory Structure After Install**
```
project_folder/
│
├── install.sh              # Main installer script (auto-fixes PATH)
├── uninstall.sh            # Safe removal script
├── pyproject.toml          # Modern build backend specification
├── setup.py                # Legacy setuptools compatibility
├── LICENSE                 # MIT License text
├── README.md               # This file!
│
└── was/                    # Main package directory
    ├── __init__.py         # Package metadata (__version__)
    ├── __main__.py         # Entry point: python -m was
    ├── cli.py              # User interface & command routing
    ├── history.py          # Repository logic, database ops
    ├── extractor.py        # Multi-format document parsers
    ├── differ.py           # Delta generation & visualization
    ├── patcher.py          # Future delta application module
    └── try/                # 🎬 Demo videos folder (see below)
        ├── install_demo.mp4
        ├── usage_walkthrough.mp4
        └── uninstall_demo.mp4
```

## 💼 Real-World Workflows

**Scenario 1:** Academic Paper Drafting
You're writing a thesis with multiple co-authors.
```
cd ~/thesis_drafts/paper_v1
```
```
was init
```

## Initial version sent to committee
```
was save paper.docx "Initial submission draft" "Sent to advisors June 15"
```

## Enable protection during revisions
```
was watch paper.docx
```
## While editing in LaTeX, WAS captures every change automatically

## Before resubmission, compare against initial
``
was diff paper.docx
``
## Tag final approved version
```
was tag paper.docx v28f4a1b2c "committee-approved"
```
## Export pre-review version for lab archives
```
was export paper.docx committee-approved ../archives/pre_review.docx
```
** Scenario 2:** Student Study Notes
Taking notes for finals week.
``
cd ~/study_materials/histology
```
```
was init
```

## Note-taking begins
```
was save organ_systems.odt "Created cardiovascular overview" "Chapter 3 prep"
``

## Daily studying triggers autosaves

```
was watch organ_systems.odt
```
Leave running all study session

## Night review: what got updated today?
```
was stats organ_systems.odt
```
Output:
```
📊 STUDY ANALYTICS FOR organic_chemistry.odt
  * Total Versions Stacked:  23
  * High Activity Day:       Wednesday (8 saves)
  * Baseline Line Count:     420 lines
  * Current Line Count:      891 lines
  * Document Line Growth:    +112%
```

**Scenario 3:** Creative Writing Backups
Protecting manuscript progress during editing sessions.
```
cd ~/novel_manuscripts/chapter7
```
```
was init
```
```
was save chapter7_final.docx "Opened for heavy revision" "Editing marathon"
```
```
was watch chapter7_final.docx
```

## Oops, accidentally deleted 5 pages! Undo immediately:
```
was rollback chapter7_final.docx
```
## Or recover yesterday's version
```
was checkout chapter7_final.docx yesterdraft
```
## Find that brilliant metaphor you wrote weeks ago
```
was search "metaphorical silence echoes louder than noise"
```

**Scenario 4:** Software Documentation Updates
Maintaining technical docs alongside code.
```
cd ~/repo/docs/api_reference
```
```
was init
```
## Each significant documentation update gets tagged
```
was save auth_api.md "Updated OAuth flow examples" "PR #247 merged"
was tag auth_api.md v3d2e1f0 "api-v2-release"
```
## Compare documentation evolution over month
```
was log auth_api.md
```
## 🔐 Best Practices for Maximum Security
For production environments, consider adding encryption yourself:
### Encrypt the repository after init
```
cp -r .was .was.backup
```
```
rm -rf .was
```
```
gpg -c .was.backup && rm .was.backup
```
### Decrypt when needed
```
gpg -d .was.backup.gpg > .was.temp && mv .was.temp .was
```

**Interested in contributing? Fork and PR anytime!**

## 🤝 Contributing

WAS thrives on community collaboration!

#### Clone repository
```
git clone https://github.com/MDSUWasi/WAS.git
```
```
cd WAS-Doc-TimeMachine
```

### Create development virtualenv
```
python3 -m venv dev_env
```
```
source dev_env/bin/activate
```
### Install in editable mode
```
pip install -e .
```

### Make changes
```
vim was/cli.py
```
### Test locally
```
was --help
```
```
was init
```
## ... run experiments ...

### Submit pull request!

git add .

git commit -m "feat: improved X 

behavior for Y scenario"

git push origin main
### Create PR on GitHub UI
Coding Standards

## 📄 License
MIT License — Free forever.
Copyright (c) 2026 WAS Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Full license text: LICENSE

## 👥 Credits
Built by ME ❤️ for students, writers, researchers, and everyone else who deserves reliable document history.
Inspired by Git but stripped down for personal workflows where simplicity beats power features.

"Your words deserve a time machine."


📞 Get Help

Documentation: Read this README thoroughly
Issues: GitHub Issues
Discussions: GitHub Discussions


<div align="center">
🌈 Made with passion for better digital memory management
Stargazers ❤️  Stars
Forks Forks
</div>
