# WAS — Your Document Time Machine 🕰️
A simple version control tool built just for personal documents and notes.
Nothing fancy, nothing complicated.
Track things • Go back in time • Check what changed with basic terminal
## Demo Videos
**You can find all the demo videos in the preview/ folder if you clone the repo.** 
### First install walkthrough (done on Debian Linux):
https://github.com/user-attachments/assets/63e26887-9df5-4025-aeb0-1cc87f8d92da
### Make sure WAS is installed correctly:
https://github.com/user-attachments/assets/4be5777e-46f1-4717-97b0-0fef6fe56a25
### Some common uses:
https://github.com/user-attachments/assets/441581e6-5f9f-4883-b65d-8dc59c89c12b
### How to remove it when you're done:
https://github.com/user-attachments/assets/c1b72e6d-ebde-4f12-aee8-26801a4f924c

**Note:** I ran cd was-cli because the folder was in my home directory. You might need to use a different path depending on where you saved it.
**Note running around:** The ./uninstall.sh removes WAS from your system but leaves the source code in the was-cli folder. Just delete that folder manually if you want to wipe it completely.

Type '''was --help''' anytime to see all available commands.

## What Actually Is WAS?
WAS stands for Document Time Machine.It's a time matchine to see the past edits. That is why I took the name **WAS** according to past tense and first 3 word of my nickname. It's a lightweight version control system made specifically for people who write a lot—students, researchers, writers, whoever tracks changes in Word docs, notes. This project is also inspired from Git (Version Control for codes ). WAS does one thing well: save snapshots of your files so you can go back later without losing anything and do not having to save multiple copies of one file.

## Features Without The Fluff
**1. Auto-Save Watch Mode** - Watches your file, auto-saves every 2 seconds when changes happen. **Why It Matters:** Don't have to remember to commit manually.

**2. Full History Log** - Timeline showing every save with timestamps. **Why It Matters:** Remember why you changed that paragraph three months ago.

**3. Instant Rollback** - Restore any old version instantly. **Why It Matters:** Big undo button for your whole workspace.

**4. Colorized Diff View** - Green for additions, red for deletions in terminal. **Why It Matters:** See changes at a glance.

**5. Custom Tagging** - Mark versions like "final-draft" or "exam-ready". **Why It Matters:** Skip remembering weird commit IDs.

**6. Writing Stats** - Shows line growth, active days, etc. **Why It Matters:** Spot your writing habits.

**7. Export Old Versions** - Pull historical versions to a new location. **Why It Matters:** Test things out without touching current file.

**8. Search History** - Search across ALL saved versions. **Why It Matters:** Where did I write about mitochondria again?

**9. Smart Storage** - Can clean up old auto-saves, keep important ones. **Why It Matters:** Save disk space when needed.

**10. Multiple Formats** - Works with .docx, .odt, .txt, .md, .py, .json, .html. **Why It Matters:** Mix and match without needing different tools.

## Getting It Installed
**Fastest Way (One Line)**
```
git clone https://github.com/MDSUWasi/was-cli.git && cd was-cli && chmod +x install.sh && ./install.sh
```
That's it. Should be working after that.
If You Want to Do It Manually
## On Linux (Ubuntu/Debian/Fedora)


**Make sure Python 3 is there:**
```
sudo apt update && sudo apt install python3 python3-pip -y  # Debian/Ubuntu
```
or use dnf instead of apt for Fedora


**Grab the code:**
```
git clone https://github.com/MDSUWasi/was-cli.git
```
```
cd was-cli
```

**Run the installer:**
```
chmod +x install.sh
```
```
./install.sh
```

**Update your PATH (sometimes it happens automatically):**
```
echo 'export PATH="HOME/.local/bin:HOME/.local/bin:PATH"' >> ~/.bashrc
```
```
source ~/.bashrc
```

**Double-check it worked:**
```
was --help
```

## On macOS


**Install Python via Homebrew if missing:**
```
brew install python3
```

**Clone and set up:**
```
git clone https://github.com/MDSUWasi/was-cli.git
```
```
cd was-cli
```
```
chmod +x install.sh
```
```
./install.sh
```

**Update shell config:**
**For Zsh (most Macs these days):**
```
echo 'export PATH="HOME/.local/bin:HOME/.local/bin:PATH"' >> ~/.zshrc
```
```
source ~/.zshrc
```
**Or bash:**
```
echo 'export PATH="HOME/.local/bin:HOME/.local/bin:PATH"' >> ~/.bash_profile
```
```
source ~/.bash_profile
```

**Verify:**
```
was --help
```

## On Windows
No native Windows support yet honestly. Two options:


**WSL2 (recommended):** Install Ubuntu via WSL, follow Linux instructions inside there

```wsl --install -d Ubuntu```  # Run as admin in PowerShell


**Git Bash + Python:** Download Python from python.org, then try pip installing it



## Checking It Works
**After install, run a couple quick tests:**
```
was --version
```
```
was --help
```
```
mkdir ~/test_was_repo && cd ~/test_was_repo
```
```
was init
```
**Should say:** "Initialized empty 'Was' repository successfully."

## First Steps Using WAS
Takes literally 5 minutes to figure out.

**Step 1:** Initialize a Repo
```
cd ~/school_notes
```
```
was init
```
**Creates a hidden .was/ folder underneath. Stores everything there.**

**Step 2:** Track Something
```
was save chemistry_notes.docx "Started alkane basics" "Homework Week 1"
```
**You'll see output like:**

✅ Saved base state of 'chemistry_notes.docx' as v1a2b3c4d!
Base snapshot created. Future saves only trigger if actual changes detected.

**Step 3:** Turn On Auto-Protection
Keep watching while you edit:
```
was watch chemistry_notes.docx
```
WAS monitors every 2 seconds, auto-commits changes. Hit Ctrl+C when done.
Messages appear like:
```
Modification detected at 2026-06-28 14:23:41. Processing change...
Auto-saved version v5f9e8g7h6 for chemistry_notes.docx!
```
**Step 4:** Check What Changed Later
Status check:
```
was status chemistry_notes.docx
```
Shows:
```
🟡 File 'chemistry_notes.docx' is Modified (Unsaved: +12 insertions, -3 deletions).
```
**View full timeline:**
```
was log chemistry_notes.docx
```
Output looks like:
```
=== TIMELINE LOG ===
Commit ID: v5f9e8g7h6 [Tags: exam-ready]
Date:      2026-06-28 14:23:41
File:      chemistry_notes.docx
What:      Added mechanism for dehydration reactions
Why:       Prof mentioned in lecture

Commit ID: v1a2b3c4d
Date:      2026-06-25 09:15:00
File:      chemistry_notes.docx
What:      Started alkane basics
Why:       Homework Week 1
```
**Step 5:** Fix Mistakes
Deleted stuff by accident? No problem.
**See recent changes:**
```
was diff chemistry_notes.docx
```
Gets you colorized diff output showing exactly what changed.
Go back to an older version:
```
was checkout chemistry_notes.docx v1a2b3c4d
```
Done. File restored. Any unsaved current edits get overwritten though, so be careful.
**Step 6:** Bookmark Important Versions
Use tags instead of memorizing commit IDs:
```
was tag chemistry_notes.docx v5f9e8g7h6 "midterm-final"
```
Then restore easily:
```
was checkout chemistry_notes.docx midterm-final
```
**Step 7:** Find Text Across All Versions
Remember writing something somewhere but forgot where?
```
was search "photosynthesis"
```
Gives results like:
```
🔍 Found 'photosynthesis' in the following historical backups:

Version: v3c2d1e0f | File: biology_report.txt | Date: 2026-06-20 11:42:00
Lines matched: 47, 52, 89
Save context: "Added chloroplast diagrams"
```

## Dependencies: 
Literally zero external packages. Python 3.6+ only, uses standard library modules:
os, json, time, shutil, subprocess, uuid, fcntl, zipfile, xml.etree, collections.Counter, difflib
This means it runs almost anywhere without fighting package managers.

**Typical Use Cases**
1. Writing Academic Papers
2. Working on thesis with co-authors:
```
cd ~/thesis_drafts/paper_v1
```
```
was init
```
```
was save paper.docx "Initial submission draft" "Sent to advisors June 15"
```
```
was watch paper.docx  # Running while editing
```
```
was diff paper.docx   # Compare against starting point before resubmitting
```
```
was tag paper.docx v28f4a1b2c "committee-approved"
```
```
was export paper.docx committee-approved ../archives/pre_review.docx
```
**Student Notes During Finals**
Studying for exams:
```
cd ~/study_materials/histology
```
```
was init
```
```
was save organ_systems.odt "Created cardiovascular overview" "Chapter 3 prep"
```
```
was watch organ_systems.odt  # Leave running through study session
```
```
was stats organ_systems.odt   # Review daily progress
```
Stats output example:
```
📊 STUDY ANALYTICS FOR organic_chemistry.odt

Total Versions Stacked:  23
High Activity Day:       Wednesday (8 saves)
Baseline Line Count:     420 lines
Current Line Count:      891 lines
Document Line Growth:    +112%
```

**Protecting Novel Manuscripts**
**Editing creative writing:**
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
Oops deleted 5 pages?
```
was rollback chapter7_final.docx
```
```
was checkout chapter7_final.docx yesterdraft
```
```
was search "metaphorical silence echoes louder than noise"
```

## Security Best Practices (Production Environments)
WAS doesn't encrypt by default. If you want encryption yourself:
**Backup and encrypt:**
```
cp -r .was .was.backup
```
```
rm -rf .was
```
```
gpg -c .was.backup && rm .was.backup
```
```
Decrypt when needed:
```
```
gpg -d .was.backup.gpg > .was.temp && mv .was.temp .was
```
Simple workaround until proper encryption gets added.

## Contributing
Happy to accept contributions

## License
MIT License. Free forever basically.
Copyright (c) 2026 Md. Shafi Un Wasi
Standard MIT terms apply—you can do pretty much whatever. See LICENSE file for full text. **But use at your own risk.**

## Credits
1. Made by me for students, writers, Researchers, really anyone who wishes their documents had better memory.
2. Git-inspired but simplified heavily. Power users can stick with Git; this is for folks who value simplicity over feature bloat.
```
"Your words deserve a time machine."
```

## Need Help?
Read this file thoroughly first 😄
**Issues or discussions:** GitHub Issues / Discussions tab on the repo
P.S. Made this thing because I hated losing work constantly. Hope it helps someone else deal less headaches.

Built with actual effort for better digital memory
Stargazers ❤️  Stars Forks Forks
