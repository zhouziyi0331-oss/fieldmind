#!/usr/bin/env python3
"""
Add ALLOW_TARGET_PLATFORM_SPECIALIZATION build setting to fix duplicate output error
"""

import re
import shutil

PROJECT_FILE = '/Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj/project.pbxproj'
BACKUP_FILE = PROJECT_FILE + '.backup_build_settings'

def add_build_setting():
    print("📖 Reading project file...")
    with open(PROJECT_FILE, 'r') as f:
        content = f.read()

    # Backup
    shutil.copy2(PROJECT_FILE, BACKUP_FILE)
    print(f"✅ Backup: {BACKUP_FILE}")

    # Find the XCBuildConfiguration section for Debug
    debug_pattern = r'(/\* Debug \*/ = \{[^}]*buildSettings = \{)'

    # Check if ALLOW_TARGET_PLATFORM_SPECIALIZATION already exists
    if 'ALLOW_TARGET_PLATFORM_SPECIALIZATION' in content:
        print("⚠️  ALLOW_TARGET_PLATFORM_SPECIALIZATION already exists")
    else:
        # Add the setting after buildSettings = {
        replacement = r'\1\n\t\t\t\tALLOW_TARGET_PLATFORM_SPECIALIZATION = YES;'
        content = re.sub(debug_pattern, replacement, content, count=1)
        print("✅ Added ALLOW_TARGET_PLATFORM_SPECIALIZATION = YES to Debug configuration")

    # Also try adding SWIFT_EMIT_LOC_STRINGS
    if 'SWIFT_EMIT_LOC_STRINGS' not in content:
        content = re.sub(debug_pattern, r'\1\n\t\t\t\tSWIFT_EMIT_LOC_STRINGS = NO;', content, count=1)
        print("✅ Added SWIFT_EMIT_LOC_STRINGS = NO to Debug configuration")

    with open(PROJECT_FILE, 'w') as f:
        f.write(content)

    print("\n✅ Build settings updated")

if __name__ == '__main__':
    add_build_setting()
