#!/usr/bin/env bash
# /* ---- 💫 https://github.com/JaKooLit 💫 ---- */  ##
# Toggle between Weather and Prayer Times in Waybar

waybar_config="$HOME/.config/waybar/config"
weather_config="[TOP] Default Laptop - Weather"
prayer_config="[TOP] Default Laptop - Prayer"
SCRIPTSDIR="$HOME/.config/hypr/scripts"

# Get current config target
current_target=$(readlink -f "$waybar_config" 2>/dev/null)
current_name=$(basename "$current_target" 2>/dev/null)

# Switch between configs
case "$current_name" in
    *Prayer*)
        echo "Switching to Weather config"
        new_config="$weather_config"
        ;;
    *)
        echo "Switching to Prayer config"
        new_config="$prayer_config"
        ;;
esac

# Apply new config
ln -sf "$HOME/.config/waybar/configs/$new_config" "$waybar_config"

# Refresh Waybar
"${SCRIPTSDIR}/Refresh.sh"

exit 0
