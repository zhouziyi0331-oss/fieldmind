#!/usr/bin/env python3
"""
Fix duplicate file references in Xcode project by directly editing pbxproj
"""

import re
from collections import defaultdict

PROJECT_FILE = '/Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj/project.pbxproj'

def fix_duplicates():
    print("Reading project file...")
    with open(PROJECT_FILE, 'r') as f:
        content = f.read()

    # Find all PBXBuildFile sections
    # Pattern: UUID /* filename */ = {isa = PBXBuildFile; fileRef = ...
    build_file_pattern = r'([A-F0-9]{24}) /\* ([^*]+) \*/ = \{isa = PBXBuildFile; fileRef = ([A-F0-9]{24})'

    build_files = re.findall(build_file_pattern, content)

    # Track files by their fileRef (the actual file reference ID)
    file_refs = defaultdict(list)
    for build_id, filename, file_ref in build_files:
        file_refs[file_ref].append((build_id, filename))

    # Find duplicates
    duplicates = {ref: ids for ref, ids in file_refs.items() if len(ids) > 1}

    if not duplicates:
        print("No duplicates found!")
        return

    print(f"\nFound {len(duplicates)} files with duplicate build references:")

    # For each duplicate, keep only the first occurrence, remove others
    removed_count = 0
    for file_ref, build_ids in duplicates.items():
        filename = build_ids[0][1]
        print(f"  {filename}: {len(build_ids)} references")

        # Keep first, remove rest
        for build_id, _ in build_ids[1:]:
            # Remove the build file definition
            pattern1 = rf'{build_id} /\* [^*]+ \*/ = \{{isa = PBXBuildFile;[^}}]+\}};?\n?'
            content = re.sub(pattern1, '', content)

            # Remove references to this build file ID in PBXSourcesBuildPhase
            pattern2 = rf'{build_id} /\* [^*]+ \*/,?\n?'
            content = re.sub(pattern2, '', content)

            removed_count += 1

    print(f"\n✅ Removed {removed_count} duplicate build file references")

    # Backup original
    print("\nBacking up original project.pbxproj...")
    with open(PROJECT_FILE + '.backup', 'w') as f:
        f.write(open(PROJECT_FILE).read())

    # Write fixed content
    print("Writing fixed project file...")
    with open(PROJECT_FILE, 'w') as f:
        f.write(content)

    print("✅ Done! Backup saved as project.pbxproj.backup")

if __name__ == '__main__':
    fix_duplicates()
