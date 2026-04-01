#!/usr/bin/env bash
# /* ---- 💫 https://github.com/JaKooLit 💫 ---- */  ##
# Toggle between Weather and Prayer Times in Waybar using Rofi menu

waybar_config="$HOME/.config/waybar/config"
weather_config="[TOP] Default Laptop - Weather"
prayer_config="[TOP] Default Laptop - Prayer"
SCRIPTSDIR="$HOME/.config/hypr/scripts"
rofi_config="$HOME/.config/rofi/config-waybar-layout.rasi"

# Get current config target
current_target=$(readlink -f "$waybar_config" 2>/dev/null)
current_name=$(basename "$current_target" 2>/dev/null)

# Build options with marker
MARKER="👉"
options=()

# Add marker to current option
if [[ "$current_name" == *"Prayer"* ]]; then
    options+=("$MARKER Prayer Times")
    options+=("Weather")
else
    options+=("Prayer Times")
    options+=("$MARKER Weather")
fi

# Find the marked row index
for i in "${!options[@]}"; do
    if [[ "${options[$i]}" == *"$MARKER"* ]]; then
        default_row=$i
        break
    fi
done

# Show rofi menu
choice=$(printf '%s\n' "${options[@]}" \
    | rofi -i -dmenu \
           -config "$rofi_config" \
           -mesg "Select module to display in Waybar" \
           -selected-row "$default_row")

# Exit if nothing chosen
[[ -z "$choice" ]] && exit 0

# Remove marker
choice=${choice#"$MARKER "}

# Apply selected config
case "$choice" in
    "Prayer Times")
        echo "Switching to Prayer config"
        ln -sf "$HOME/.config/waybar/configs/$prayer_config" "$waybar_config"
        "${SCRIPTSDIR}/Refresh.sh"
        ;;
    "Weather")
        echo "Switching to Weather config"
        ln -sf "$HOME/.config/waybar/configs/$weather_config" "$waybar_config"
        "${SCRIPTSDIR}/Refresh.sh"
        ;;
esac

exit 0
