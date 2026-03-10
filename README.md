# Ubuntu Hyprland Dotfiles 🐧✨

This repository contains my personal configuration files (dotfiles) for my Ubuntu system running the **JaKooLit Hyprland** rice. It uses GNU Stow to manage and deploy the configurations seamlessly.

## 🌟 Features

* **Window Manager:** [Hyprland](https://hyprland.org/) (Configured via [JaKooLit's Ubuntu Rice](https://github.com/JaKooLit/Ubuntu-Hyprland))
* **Panel/Bar:** [Waybar](https://github.com/Alexays/Waybar)
* **Application Launcher:** [Rofi](https://github.com/lbonn/rofi-wayland)
* **Terminal Emulator:** [Kitty](https://sw.kovidgoyal.net/kitty/)
* **Shell & Prompt:** Bash with [Starship](https://starship.rs/)
* **Color Scheme Generator:** [Wallust](https://codeberg.org/explosion-mental/wallust)
* **Notification Daemon:** [SwayNC](https://github.com/ErikReider/SwayNotificationCenter)
* **Widgets/UI:** [AGS (Aylur's GTK Shell)](https://github.com/Aylur/ags)

## 📁 Repository Structure

This repository is structured for use with [GNU Stow](https://www.gnu.org/software/stow/). Each directory at the root level acts as a "package" that mirrors the target structure in the home directory (`~/`).

* `hypr/` - Core Hyprland configurations (`~/.config/hypr`)
* `waybar/` - Top/Bottom bar configurations (`~/.config/waybar`)
* `kitty/` - Terminal emulator settings (`~/.config/kitty`)
* `rofi/` - Application launcher themes and settings (`~/.config/rofi`)
* `bash/` - Shell configuration (`~/.bashrc`, `~/.profile`)
* *...and more.*

*(Note: Personal files like terminal alternatives, system monitors, and audio visualizers are kept locally and not tracked in this core UI repository).*

## 🚀 Installation

To replicate this exact setup on a new machine, follow these steps:

### Prerequisites

You must have the [JaKooLit Ubuntu-Hyprland](https://github.com/JaKooLit/Ubuntu-Hyprland) base installed first. 

### Deployment

1. **Clone the repository:**
   ```bash
   git clone <your-github-repo-url> ~/dotfiles
   cd ~/dotfiles
   ```

2. **Run the installation script:**
   The included script will automatically install GNU Stow (if missing), set up your local Git credentials securely, and create all the necessary symlinks.

   ```bash
   chmod +x install.sh
   ./install.sh
   ```

## 🔒 Security Note (Git Credentials)

Your Git email is **not** stored in this public repository. The `install.sh` script will prompt you to create a local file called `~/.gitconfig.local` to store your name and email. The tracked `.gitconfig` file simply includes this local file, keeping your personal information safe.

## 🔄 Updating the Rice

Because these files are symlinked via Stow, any updates applied by the JaKooLit update script will automatically modify the files inside this repository. 

After running the JaKooLit update script, you can review the changes using:
```bash
cd ~/dotfiles
git status
git diff
```
If you are happy with the updates, simply commit and push them to your repository!
