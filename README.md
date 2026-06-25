# WAS - Your Document Time Machine CLI ⏰

**A powerful version control system designed specifically for personal documents and study notes.**

WAS tracks changes to your documents automatically, allowing you to view history, restore previous versions, and analyze your writing patterns—all with simple CLI commands.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Auto-Save Watch Mode** | Background monitoring detects file modifications and saves snapshots automatically |
| **Full History Log** | View timeline of all commits with timestamps, messages, and tags |
| **Version Checkout** | Restore any document to a specific historical version instantly |
| **Colored Diff View** | Visualize changes with green/red highlighting in terminal |
| **Custom Tagging** | Mark important milestones (e.g., "exam-prep", "final-draft") |
| **Writing Analytics** | Track line growth, most active days, and document statistics |
| **Full Workspace Export** | Extract historical versions without affecting current workspace |
| **Text Search** | Search entire document history for specific terms/phrases |
| **Storage Optimization** | Purge intermediate auto-saves to reclaim disk space |
| **Multi-Format Support** | Works with `.docx`, `.odt`, `.txt`, `.md`, `.py`, `.json`, `.html`, `.css` |

---

## 📁 Supported File Formats

| Format | Extension | Extraction Method |
|--------|-----------|-------------------|
| Word Documents | `.docx` | OpenXML ZIP parsing |
| LibreOffice | `.odt` | ODF XML parsing |
| Plain Text | `.txt` | Direct UTF-8 reading |
| Markdown | `.md` | Direct text extraction |
| Python Code | `.py` | Direct text extraction |
| JSON | `.json` | Direct text extraction |
| HTML | `.html` | Direct text extraction |
| CSS | `.css` | Direct text extraction |

---

## 📦 Installation

### Step 1: Clone or Download Project Files

Make sure these files are in the same directory:
project_folder/
├── main.py
├── extractor.py
├── differ.py
├── patcher.py
└── history.py

### Step 2: 

Make Executable: chmod +x main.pyStep 
### Step 3: 
Create Shell Alias (Optional but Recommended): Add to your ~/.bashrc or ~/.zshrc:

# Add WAS CLI to PATH
alias was="python3 /path/to/your/project/main.py" Then reload your shell configuration:source ~/.bashrc    
# For Bash
# OR
source ~/.zshrc     
# For ZshNow you can use was from anywhere in the terminal!

## 🚀 Quick Start Guide1. 
### Initialize a Repositorycd ~/school_notes
1. *was init* This creates a hidden .was/ directory to store all version data.
2. Start Tracking a Filewas save chemistry_notes.docx "Created initial alkanes section" "Base homework prep"First save creates a baseline. Subsequent saves only commit if changes are detected.
3. Enable Auto-Watch Modewas watch chemistry_notes.docxWas will now monitor the file every 2 seconds and auto-save changes. Press Ctrl+C to stop watching.

📖 Command ReferenceCore Commandswas init
Initialize a new WAS repository in the current directory.
was save <file> "<message>" ["<reason>"]
Manually commit changes to the timeline.
was save biology.txt "Added plant cells" "Prep for Quiz 1"
was log [<file>]
View history log of all commits. Optional file filter.
was log                          # All files
was log organic_chemistry.docx   # Specific file only
was checkout <file> <version/tag>
Restore a document to a previous state.
was checkout biology.txt v1                 # By version ID
was checkout organic_chemistry.docx exam-prep  # By tag name
was watch <file>
Launch background engine to auto-save updates.
was watch physics.odt

Extended Power Commands
was status <file>
Check if the file has unsaved changes compared to last commit.
Output example:
File 'organic_chemistry.docx' is Modified (Unsaved: +4 insertions, -1 deletions).

was diff <file>
View colorized differences between workspace and last saved version.

Green lines: New additions
Red lines: Deletions
Cyan lines: Changed location markers

was tag <file> <version> <tag_name>
Assign a friendly nickname to an existing version number.
was tag organic_chemistry.docx v4 midterm-revision
Subsequent checkout:
was checkout organic_chemistry.docx midterm-revision
was stats <file>
View study habits and document analytics.
Output includes:
* Total Versions Stacked
* High Activity Day
* Baseline Line Count
* Current Line Count
* Document Line Growth Percentage

was rollback <file>
Discard all active unsaved edits to match the latest commit state.
was search "<term>"
Search entire historical backups for a word or phrase. Returns all matches with line numbers and commit context.
was search "mitochondria"
was export <file> <version/tag> <destination>
Extract a specific version to a new location without altering active workspace.
was export organic_chemistry.docx v2 chemistry_draft_copy.docx
was purge <file>
Clean up automatic background saves to free disk space. Keeps baselines and manually tagged versions.
was purge organic_chemistry.docx

📂 Directory Structure
After initialization (was init):
your_project_folder/
│
├── main.py              # CLI interface
├── extractor.py         # Multi-format document extraction
├── differ.py            # Diff generation & colored output
├── patcher.py           # Patch application logic
├── history.py           # Core repository logic
│
└── .was/                # Hidden repository database (auto-generated)
    ├── history.json     # Commit history & metadata
    └── versions/        # Stored snapshots per version
        ├── v1_filename.ext
        ├── v2_filename.ext
        └── ...


🔧 Example Workflows
Workflow 1: Study Note Management
# 1. Setup
cd ~/school_notes
was init

# 2. Start first note
was save chemistry.docx "Started alkane basics" "Homework Week 1"

# 3. Enable auto-protection
was watch chemistry.docx
# Now edit in your preferred editor; Was auto-saves every change

# 4. Review progress later
was status chemistry.docx
was log chemistry.docx

# 5. Mark milestone before exam
was tag chemistry.docx v5 "exam-ready"
Workflow 2: Recover Lost Work
# Accidentally deleted content?
was diff notes.docx                    # See what changed
was checkout notes.docx v3             # Restore to earlier version
Workflow 3: Find Old References
# Need to find where you wrote something months ago?
was search "photosynthesis"            # Returns all matching versions

🔒 Security & Privacy

✅ Local-only operation — No network calls, everything stays on your machine
✅ Path traversal protection — Prevents access outside workspace directory
✅ Database locking — Prevents corruption during concurrent operations
✅ Atomic writes — Uses temp file + move to prevent partial saves
⚠️ No encryption — Snapshots stored as plain text (add GPG wrapper if needed)


🛠️ Troubleshooting
ProblemSolutionNo 'Was' repository foundRun was init firstFile is untracked by WasRun was save <file> to start trackingDatabase corrupted errorRestore from backup or reinitializeNotification errorsInstall notify-send or ignore (graceful fallback)Alias not workingRun source ~/.bashrc after adding to config

📋 Requirements

Python 3.6+
Standard library only (no external dependencies)
Linux/macOS (Windows requires WSL or Git Bash for some features)
notify-send optional (for desktop notifications)


🎯 Future Enhancements

 Encrypted snapshot storage
 Database checksum verification
 --dry-run flag for purge command
 Tag listing command (was tag --list)
 Comparison between two historical versions
 Automatic cloud backup integration (optional)


📄 License
Free to use, modify, and distribute. Built with ❤️ for students and writers who need reliable document versioning.

👤 Credits
Built from collaborative brainstorming sessions. Inspired by Git but simplified for personal document management workflows.

"Your words deserve a time machine."

---