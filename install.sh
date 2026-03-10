#!/bin/bash

# Exit on error
set -e

echo "Starting dotfiles installation..."

# 1. Install Stow if not installed
if ! command -v stow &> /dev/null; then
    echo "GNU Stow is not installed. Installing it now..."
    sudo apt update && sudo apt install -y stow
else
    echo "GNU Stow is already installed."
fi

# 2. Setup .gitconfig.local for privacy
if [ ! -f "$HOME/.gitconfig.local" ]; then
    echo ""
    echo "Let's set up your Git credentials (this won't be pushed to the public repo):"
    read -p "Enter your Git Name: " git_name
    read -p "Enter your Git Email: " git_email
    
    cat << EOF > "$HOME/.gitconfig.local"
[user]
	name = $git_name
	email = $git_email
EOF
    echo ".gitconfig.local created successfully!"
else
    echo ".gitconfig.local already exists. Skipping Git credential setup."
fi

# 3. Stow the directories
echo ""
echo "Stowing configurations..."

# Get the directory where the script is located
DOTFILES_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Define the packages to stow
PACKAGES=(
    "ags"
    "bash"
    "btop"
    "cava"
    "fastfetch"
    "ghostty"
    "git"
    "hypr"
    "kitty"
    "kvantum"
    "qt"
    "rofi"
    "starship"
    "swaync"
    "tmux"
    "wallust"
    "waybar"
    "wezterm"
    "wlogout"
)

# Navigate to the dotfiles directory
cd "$DOTFILES_DIR"

# Run stow for each package, skipping ones that don't exist in the repo
for package in "${PACKAGES[@]}"; do
    if [ -d "$package" ]; then
        echo "Stowing $package..."
        stow -R "$package"
    fi
done

echo ""
echo "✅ Dotfiles installed successfully!"
