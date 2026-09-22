#!/usr/bin/env python3
"""
Remove duplicate file references from Xcode project
"""

from pbxproj import XcodeProject
import sys

PROJECT_PATH = '/Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj'

def remove_duplicate_files(project):
    """Remove duplicate file references from the project"""

    # Track files we've seen
    seen_files = set()
    duplicates_removed = 0

    # Get all build files
    for target in project.objects.get_targets():
        # Get source build phase
        build_phases = project.get_build_phases_by_name(target.get_id(), 'PBXSourcesBuildPhase')

        if not build_phases:
            continue

        source_phase = build_phases[0]

        if not hasattr(source_phase, 'files') or not source_phase.files:
            continue

        files_to_remove = []
        for build_file_id in source_phase.files:
            build_file = project.objects[build_file_id]
            if not build_file or not hasattr(build_file, 'fileRef'):
                continue

            file_ref = project.objects[build_file.fileRef]
            if not file_ref or not hasattr(file_ref, 'path'):
                continue

            file_path = file_ref.path

            # Track by file path
            if file_path in seen_files:
                files_to_remove.append(build_file_id)
                print(f"Found duplicate: {file_path}")
            else:
                seen_files.add(file_path)

        # Remove duplicates from the files list
        for build_file_id in files_to_remove:
            source_phase.files.remove(build_file_id)
            duplicates_removed += 1

    return duplicates_removed

def main():
    print("Loading Xcode project...")
    project = XcodeProject.load(PROJECT_PATH + '/project.pbxproj')

    print("\nRemoving duplicate file references...")
    count = remove_duplicate_files(project)

    print(f"\n✅ Removed {count} duplicate file references")

    if count > 0:
        print("\nSaving project...")
        project.save()
        print("✅ Project saved successfully")
    else:
        print("\nNo duplicates found - no changes made")

if __name__ == '__main__':
    main()
