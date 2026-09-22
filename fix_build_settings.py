#!/usr/bin/env python3
"""
Add build settings to allow duplicate outputs and fix the stringsdata issue
"""

import re
import shutil

PROJECT_FILE = '/Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj/project.pbxproj'
BACKUP_FILE = PROJECT_FILE + '.backup_duplicate_outputs'

def fix_build_settings():
    print("📖 Reading project file...")
    with open(PROJECT_FILE, 'r') as f:
        content = f.read()

    # Backup
    shutil.copy2(PROJECT_FILE, BACKUP_FILE)
    print(f"✅ Backup: {BACKUP_FILE}")

    # Find all XCBuildConfiguration sections (both Debug and Release)
    config_pattern = r'(buildSettings = \{)'

    changes = []

    # Add multiple settings to fix the issue
    settings_to_add = [
        ('VALIDATE_WORKSPACE', 'NO'),
        ('ENABLE_STRICT_OBJC_MSGSEND', 'NO'),
        ('CLANG_ENABLE_MODULE_DEBUGGING', 'NO'),
    ]

    for setting_name, setting_value in settings_to_add:
        if setting_name not in content:
            # Add after "buildSettings = {"
            pattern = r'(buildSettings = \{)'
            replacement = rf'\1\n\t\t\t\t{setting_name} = {setting_value};'
            content = re.sub(pattern, replacement, content)
            changes.append(f"{setting_name} = {setting_value}")
            print(f"✅ Added {setting_name} = {setting_value}")

    with open(PROJECT_FILE, 'w') as f:
        f.write(content)

    if changes:
        print(f"\n✅ Added {len(changes)} build settings")
    else:
        print("\n⚠️  All settings already exist")

if __name__ == '__main__':
    fix_build_settings()
