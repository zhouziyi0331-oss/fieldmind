#!/usr/bin/env python3
"""
Remove all Pages/Native/ file references from Xcode project
Keep only fieldmind/Pages/ references
"""

import re
import shutil
from pathlib import Path

PROJECT_FILE = '/Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj/project.pbxproj'
BACKUP_FILE = PROJECT_FILE + '.backup_before_native_removal'

def remove_native_pages():
    print("📖 Reading project file...")
    with open(PROJECT_FILE, 'r') as f:
        content = f.read()

    # Backup
    shutil.copy2(PROJECT_FILE, BACKUP_FILE)
    print(f"✅ Backup created: {BACKUP_FILE}")

    # Find all file references to Pages/Native/
    native_pattern = r'([A-F0-9]{24}) /\* ([^*]*\.swift) \*/ = \{[^}]*fileRef = ([A-F0-9]{24})[^}]*path = "?([^";\n]*Pages/Native/[^";\n]*)"?[^}]*\};'

    matches = re.findall(native_pattern, content)
    print(f"\n🔍 Found {len(matches)} Native Page file references")

    # Collect all IDs to remove
    build_file_ids = set()
    file_ref_ids = set()

    for match in matches:
        build_id, filename, file_ref_id, path = match
        print(f"  - {filename} (BuildFile: {build_id}, FileRef: {file_ref_id})")
        build_file_ids.add(build_id)
        file_ref_ids.add(file_ref_id)

    if not build_file_ids:
        print("❌ No Native Pages found in project file")
        return False

    print(f"\n🗑️  Removing {len(build_file_ids)} build file entries...")

    # Remove PBXBuildFile entries
    for build_id in build_file_ids:
        # Match full PBXBuildFile definition
        pattern = rf'{build_id} /\* [^*]+ \*/ = \{{isa = PBXBuildFile;[^}}]+\}};?\n?'
        content = re.sub(pattern, '', content)

        # Match references in build phases
        pattern = rf'{build_id} /\* [^*]+ \*/,?\n?'
        content = re.sub(pattern, '', content)

    print(f"🗑️  Removing {len(file_ref_ids)} file reference entries...")

    # Remove PBXFileReference entries
    for file_ref_id in file_ref_ids:
        pattern = rf'{file_ref_id} /\* [^*]+ \*/ = \{{isa = PBXFileReference;[^}}]+\}};?\n?'
        content = re.sub(pattern, '', content)

    # Remove Pages/Native group reference if exists
    native_group_pattern = r'[A-F0-9]{24} /\* Native \*/ = \{[^}]*path = Native;[^}]*\};?\n?'
    if re.search(native_group_pattern, content):
        content = re.sub(native_group_pattern, '', content)
        print("🗑️  Removed Native group reference")

    # Clean up any trailing commas in arrays
    content = re.sub(r',(\s*)\)', r'\1)', content)

    # Write back
    with open(PROJECT_FILE, 'w') as f:
        f.write(content)

    print(f"\n✅ Successfully cleaned project file")
    print(f"   Removed {len(build_file_ids)} build file entries")
    print(f"   Removed {len(file_ref_ids)} file reference entries")
    return True

if __name__ == '__main__':
    remove_native_pages()
