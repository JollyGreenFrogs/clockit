#!/bin/bash
# Update Common Passwords List
# This script helps maintain an updated list of common/weak passwords
# Based on security research from multiple sources

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../src/auth/data"
PASSWORD_FILE="$DATA_DIR/common_passwords.txt"

echo "🔐 Common Passwords List Updater"
echo "================================="
echo ""

# Ensure data directory exists
mkdir -p "$DATA_DIR"

# Create backup of existing file if it exists
if [ -f "$PASSWORD_FILE" ]; then
    BACKUP_FILE="${PASSWORD_FILE}.backup-$(date +%Y%m%d-%H%M%S)"
    echo "📦 Backing up existing file to: $(basename $BACKUP_FILE)"
    cp "$PASSWORD_FILE" "$BACKUP_FILE"
fi

echo ""
echo "This script can help you update the common passwords list."
echo ""
echo "Options:"
echo "  1) Keep current list ($(wc -l < $PASSWORD_FILE 2>/dev/null || echo "0") passwords)"
echo "  2) Download from SecLists (top 10,000 passwords)"
echo "  3) Add custom passwords to existing list"
echo ""
read -p "Select option (1-3): " OPTION

case $OPTION in
    1)
        echo "✅ Keeping current password list"
        ;;
    2)
        echo "📥 Downloading top passwords from SecLists..."
        
        # Try to download from SecLists GitHub
        TEMP_FILE=$(mktemp)
        
        if curl -fsSL "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-10000.txt" -o "$TEMP_FILE" 2>/dev/null; then
            echo "# Common/Weak Passwords List" > "$PASSWORD_FILE"
            echo "# Based on SecLists by Daniel Miessler" >> "$PASSWORD_FILE"
            echo "# Source: https://github.com/danielmiessler/SecLists" >> "$PASSWORD_FILE"
            echo "# Last updated: $(date +%Y-%m-%d)" >> "$PASSWORD_FILE"
            echo "" >> "$PASSWORD_FILE"
            
            # Take top 5000 passwords (balance between security and performance)
            head -n 5000 "$TEMP_FILE" >> "$PASSWORD_FILE"
            
            rm "$TEMP_FILE"
            
            echo "✅ Downloaded $(wc -l < $PASSWORD_FILE) passwords"
        else
            echo "❌ Failed to download from SecLists"
            echo "   Keeping current list"
        fi
        ;;
    3)
        echo ""
        echo "Enter passwords to add (one per line, empty line to finish):"
        while IFS= read -r line; do
            [ -z "$line" ] && break
            echo "$line" >> "$PASSWORD_FILE"
        done
        
        # Remove duplicates and sort
        sort -u "$PASSWORD_FILE" -o "$PASSWORD_FILE"
        
        echo "✅ Updated password list"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "📊 Current password list statistics:"
echo "   Total passwords: $(grep -v '^#' $PASSWORD_FILE | grep -v '^$' | wc -l)"
echo "   File size: $(du -h $PASSWORD_FILE | cut -f1)"
echo ""
echo "⚠️  Note: Restart the application for changes to take effect"
echo ""
