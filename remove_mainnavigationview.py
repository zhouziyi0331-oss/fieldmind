#!/usr/bin/env python3
"""
Remove MainNavigationView.swift from Xcode project to bypass the stringsdata error
"""

import re
import shutil

PROJECT_FILE = '/Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj/project.pbxproj'
BACKUP_FILE = PROJECT_FILE + '.backup_remove_mainnav'

def remove_file():
    print("📖 Reading project file...")
    with open(PROJECT_FILE, 'r') as f:
        content = f.read()

    # Backup
    shutil.copy2(PROJECT_FILE, BACKUP_FILE)
    print(f"✅ Backup: {BACKUP_FILE}")

    # Find MainNavigationView references
    # 1. PBXBuildFile
    build_pattern = r'C4364157B524937E6150F9D2 /\* MainNavigationView\.swift in Sources \*/ = \{isa = PBXBuildFile; fileRef = FBA64EE4998817B6211632EB /\* MainNavigationView\.swift \*/; \};?\n?'
    content = re.sub(build_pattern, '', content)
    print("✅ Removed PBXBuildFile entry")

    # 2. PBXFileReference
    file_ref_pattern = r'FBA64EE4998817B6211632EB /\* MainNavigationView\.swift \*/ = \{isa = PBXFileReference;[^}]+\};?\n?'
    content = re.sub(file_ref_pattern, '', content)
    print("✅ Removed PBXFileReference entry")

    # 3. Remove from PBXGroup (children array)
    group_ref_pattern = r'\s*FBA64EE4998817B6211632EB /\* MainNavigationView\.swift \*/,?\n?'
    content = re.sub(group_ref_pattern, '', content)
    print("✅ Removed from PBXGroup")

    # 4. Remove from PBXSourcesBuildPhase
    sources_pattern = r'\s*C4364157B524937E6150F9D2 /\* MainNavigationView\.swift in Sources \*/,?\n?'
    content = re.sub(sources_pattern, '', content)
    print("✅ Removed from PBXSourcesBuildPhase")

    # Clean up trailing commas
    content = re.sub(r',(\s*)\)', r'\1)', content)

    with open(PROJECT_FILE, 'w') as f:
        f.write(content)

    print("\n✅ MainNavigationView.swift removed from Xcode project")

if __name__ == '__main__':
    remove_file()
