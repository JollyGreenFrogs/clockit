#!/bin/bash

# Script to remove all console logging from React frontend
# This removes console.log, console.error, console.warn, console.info, console.debug statements

echo "🧹 Removing all console logging from React frontend..."

# Find all JS/JSX files in src directory and remove console logging
find react-frontend/src -name "*.js" -o -name "*.jsx" | while read file; do
    if grep -q "console\." "$file"; then
        echo "Cleaning console logging from: $file"
        
        # Create a backup
        cp "$file" "$file.backup"
        
        # Remove console logging lines (but preserve structure)
        sed -i '/console\.\(log\|error\|warn\|info\|debug\)/d' "$file"
        
        # Clean up any empty try-catch blocks or orphaned lines
        # This is a simple cleanup - may need manual review
        echo "✅ Cleaned: $file"
    fi
done

echo "🎉 Console logging cleanup complete!"
echo "ℹ️  Backup files created with .backup extension"
echo "⚠️  Please review the changes and test the application"