#!/usr/bin/env bash
# Rofi Theme Validator
# Validates Rofi theme syntax before applying it

# Usage: validate-theme.sh <theme-path> [--test]

THEME_PATH="$1"
TEST_MODE=false

# Check for test flag
if [ "$2" == "--test" ]; then
    TEST_MODE=true
fi

# Validate arguments
if [ -z "$THEME_PATH" ]; then
    echo "❌ Error: No theme path provided"
    echo "Usage: $0 <theme-path> [--test]"
    echo "  <theme-path>: Path to .rasi theme file"
    echo "  [--test]: Launch Rofi briefly to test theme"
    exit 1
fi

# Check if theme file exists
if [ ! -f "$THEME_PATH" ]; then
    echo "❌ Error: Theme file not found: $THEME_PATH"
    exit 1
fi

# Parse theme and capture errors
LOG_FILE="/tmp/rofi-validation-$(date +%s).log"
rofi -no-config -theme "$THEME_PATH" -dump-theme 2>&1 > "$LOG_FILE"

# Check for errors
if grep -q "Failed to parse theme" "$LOG_FILE"; then
    echo "❌ THEME VALIDATION FAILED"
    echo "Theme: $(basename "$THEME_PATH")"
    echo "Path: $THEME_PATH"
    echo ""
    
    # Extract and display error details
    echo "📋 Error Details:"
    grep "Parser error" "$LOG_FILE" | sed 's/^/  /'
    grep "Location:" "$LOG_FILE" | sed 's/^/  /'
    
    # Show problematic lines
    grep "Location:" "$LOG_FILE" | grep -o "line [0-9]*" | sort -u | while read line_info; do
        line_num=$(echo "$line_info" | grep -o "[0-9]*")
        echo ""
        echo "Line $line_num:"
        sed -n "${line_num}p" "$THEME_PATH" | sed 's/^/    /'
    done
    
    echo ""
    echo "💡 Fix the syntax errors and try again"
    exit 1
else
    echo "✅ THEME VALIDATION PASSED"
    echo "Theme: $(basename "$THEME_PATH")"
    echo "Path: $THEME_PATH"
    echo ""
    
    if [ "$TEST_MODE" == true ]; then
        echo "🧪 Testing theme visually..."
        rofi -theme "$THEME_PATH" -show drun &
        ROFI_PID=$!
        sleep 2
        kill $ROFI_PID 2>/dev/null
        echo "✅ Visual test complete"
    fi
    
    exit 0
fi
