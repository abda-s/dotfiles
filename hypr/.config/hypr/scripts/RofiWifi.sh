#!/usr/bin/env bash
# /* ---- 💫 https://github.com/JaKooLit 💫 ---- */  #
# Rofi WiFi Menu

# Get active wireless device
WIFI_DEV="$(nmcli -t -f DEVICE,TYPE device status | awk -F: '$2=="wifi"{print $1; exit}')"

if [ -z "$WIFI_DEV" ]; then
    notify-send -u critical -i "network-wireless" "WiFi" "No wireless device found"
    exit 1
fi

# Check if WiFi is enabled
WIFI_ENABLED="$(nmcli -t -f WIFI g)"

# Rofi prompt
ROFI_PROMPT="WiFi Network"

if [ "$WIFI_ENABLED" = "disabled" ]; then
    CHOICE="$(printf "Enable WiFi\n" | rofi -dmenu -i -p "$ROFI_PROMPT" -theme-str 'window {width: 400px;}')"
    if [ "$CHOICE" = "Enable WiFi" ]; then
        nmcli radio wifi on
        notify-send -u low -i "network-wireless" "WiFi" "WiFi enabled"
    fi
    exit 0
fi

# Disconnect option if connected
ACTIVE_CONN="$(nmcli -t -f NAME,DEVICE connection show --active | awk -F: -v dev="$WIFI_DEV" '$2==dev{print $1; exit}')"

# Build menu
MENU=""
[ -n "$ACTIVE_CONN" ] && MENU="Disconnect: $ACTIVE_CONN\n"
MENU+="Toggle WiFi (turn off)\n"
MENU+="─── Available Networks ───\n"

# Get network list: SSID|signal|security|in-use
# Format: SSID with signal bars and lock icon
MAP_FILE="/tmp/rofi_wifi_map_$$"
touch "$MAP_FILE"

while IFS=: read -r ssid signal security inuse; do
    # Skip hidden/empty SSIDs
    [ -z "$ssid" ] && continue

    # Signal icon
    if [ "$signal" -ge 80 ]; then
        sig_icon="󰤨"
    elif [ "$signal" -ge 60 ]; then
        sig_icon="󰤥"
    elif [ "$signal" -ge 40 ]; then
        sig_icon="󰤢"
    elif [ "$signal" -ge 20 ]; then
        sig_icon="󰤟"
    else
        sig_icon="󰤯"
    fi

    # Security icon
    if [ "$security" = "--" ] || [ -z "$security" ]; then
        sec_icon=""
    else
        sec_icon="󰌾"
    fi

    # In-use marker
    if [ "$inuse" = "*" ]; then
        prefix="󰄬 "
    else
        prefix="   "
    fi

    display="${prefix}${sig_icon}  ${ssid}  ${sec_icon}"
    printf '%s\t%s\n' "$display" "$ssid" >> "$MAP_FILE"
    MENU+="${display}\n"
done < <(nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE device wifi list --rescan yes | sort -t: -k2 -nr)

# Show rofi menu
CHOICE="$(printf '%b' "$MENU" | rofi -dmenu -i -p "$ROFI_PROMPT" -theme-str 'window {width: 500px;}')"

# Cleanup
rm -f "$MAP_FILE"

[ -z "$CHOICE" ] && exit 0

# Handle special options
if [ "$CHOICE" = "Toggle WiFi (turn off)" ]; then
    nmcli radio wifi off
    notify-send -u low -i "network-wireless-disconnected" "WiFi" "WiFi turned off"
    exit 0
fi

if [[ "$CHOICE" == Disconnect:* ]]; then
    nmcli connection down "$ACTIVE_CONN"
    notify-send -u low -i "network-wireless-disconnected" "WiFi" "Disconnected from $ACTIVE_CONN"
    exit 0
fi

# Extract SSID from choice (remove prefix and icons)
SSID="$(grep -F "$CHOICE" "$MAP_FILE" 2>/dev/null | cut -f2)"
[ -z "$SSID" ] && SSID="${CHOICE#*  }"
[ -z "$SSID" ] && exit 0

# Check if already connected
if [ "$ACTIVE_CONN" = "$SSID" ]; then
    notify-send -u low -i "network-wireless" "WiFi" "Already connected to $SSID"
    exit 0
fi

# Check if connection is known
KNOWN="$(nmcli -t -f NAME connection show | grep -Fx "$SSID")"

if [ -n "$KNOWN" ]; then
    # Connect to known network
    RESULT="$(nmcli connection up "$SSID" 2>&1)"
    if [ $? -eq 0 ]; then
        notify-send -u low -i "network-wireless" "WiFi" "Connected to $SSID"
    else
        notify-send -u critical -i "network-wireless-disconnected" "WiFi" "Failed to connect to $SSID\n$RESULT"
    fi
else
    # New network: ask for password
    SEC_TYPE="$(nmcli -t -f SSID,SECURITY device wifi list | awk -F: -v ssid="$SSID" '$1==ssid{print $2; exit}')"

    if [ "$SEC_TYPE" = "--" ] || [ -z "$SEC_TYPE" ]; then
        # Open network
        RESULT="$(nmcli device wifi connect "$SSID" 2>&1)"
    else
        PASSWORD="$(rofi -dmenu -password -p "Password for $SSID" -theme-str 'window {width: 400px;}')"
        [ -z "$PASSWORD" ] && exit 0
        RESULT="$(nmcli device wifi connect "$SSID" password "$PASSWORD" 2>&1)"
    fi

    if [ $? -eq 0 ]; then
        notify-send -u low -i "network-wireless" "WiFi" "Connected to $SSID"
    else
        notify-send -u critical -i "network-wireless-disconnected" "WiFi" "Failed to connect to $SSID\n$RESULT"
    fi
fi
