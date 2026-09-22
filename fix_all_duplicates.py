#!/usr/bin/env python3
"""
Comprehensive fix for all duplicate file references in Xcode project
"""

import re
import shutil
from collections import defaultdict

PROJECT_FILE = '/Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj/project.pbxproj'
BACKUP_FILE = PROJECT_FILE + '.backup_comprehensive'

def fix_all_duplicates():
    print("📖 Reading project file...")
    with open(PROJECT_FILE, 'r') as f:
        content = f.read()

    # Backup
    shutil.copy2(PROJECT_FILE, BACKUP_FILE)
    print(f"✅ Backup: {BACKUP_FILE}")

    # Step 1: Find all PBXBuildFile entries
    build_file_pattern = r'([A-F0-9]{24}) /\* ([^*]+) in Sources \*/ = \{isa = PBXBuildFile; fileRef = ([A-F0-9]{24})[^}]*\};'
    build_files = re.findall(build_file_pattern, content)

    print(f"\n📊 Found {len(build_files)} PBXBuildFile entries")

    # Step 2: Group by fileRef (the actual file reference)
    file_refs = defaultdict(list)
    for build_id, filename, file_ref in build_files:
        file_refs[file_ref].append((build_id, filename))

    # Step 3: Find duplicates
    duplicates = {ref: ids for ref, ids in file_refs.items() if len(ids) > 1}

    if not duplicates:
        print("✅ No duplicates found!")
        return

    print(f"\n🔍 Found {len(duplicates)} files with duplicate references:")

    removed_count = 0
    for file_ref, build_ids in duplicates.items():
        filename = build_ids[0][1]
        print(f"\n  📄 {filename}")
        print(f"     FileRef: {file_ref}")
        print(f"     {len(build_ids)} duplicate entries found")

        # Keep only the first, remove the rest
        for i, (build_id, _) in enumerate(build_ids[1:], 1):
            print(f"     Removing duplicate #{i+1}: {build_id}")

            # Remove PBXBuildFile definition
            pattern1 = rf'{build_id} /\* [^*]+ in Sources \*/ = \{{isa = PBXBuildFile; fileRef = [A-F0-9]{{24}}[^}}]*\}};?\n?'
            content = re.sub(pattern1, '', content)

            # Remove from PBXSourcesBuildPhase files array
            pattern2 = rf'\s*{build_id} /\* [^*]+ in Sources \*/,?\n?'
            content = re.sub(pattern2, '', content)

            removed_count += 1

    # Step 4: Clean up trailing commas
    content = re.sub(r',(\s*)\)', r'\1)', content)
    content = re.sub(r',(\s*);', r'\1;', content)

    # Step 5: Write back
    with open(PROJECT_FILE, 'w') as f:
        f.write(content)

    print(f"\n✅ Successfully removed {removed_count} duplicate entries")
    print(f"   Cleaned {len(duplicates)} files")

if __name__ == '__main__':
    fix_all_duplicates()
