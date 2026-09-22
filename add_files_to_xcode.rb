#!/usr/bin/env ruby
require 'xcodeproj'

project_path = '/Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj'
project = Xcodeproj::Project.open(project_path)

# 获取主 target
target = project.targets.first

# 核心文件列表
core_files = [
  'fieldmind/Core/UnifiedAppState.swift',
  'fieldmind/Core/DataPipeline/DataPipeline.swift',
  'fieldmind/Core/DataPipeline/CleanDataPipeline.swift',
  'fieldmind/Core/DataPipeline/RawDataPipeline.swift',
  'fieldmind/Services/BackendService.swift',
  'fieldmind/Services/KnowledgeVaultService.swift',
  'fieldmind/Services/DistillationService.swift',
  'fieldmind/Views/MainNavigationView.swift',
  'fieldmind/Views/KnowledgeVaultView.swift',
  'fieldmind/Views/DistillationView.swift'
]

# 获取或创建组
def get_or_create_group(project, path_components)
  current_group = project.main_group
  path_components.each do |component|
    found = current_group.children.find { |child| child.display_name == component && child.isa == 'PBXGroup' }
    if found
      current_group = found
    else
      current_group = current_group.new_group(component)
    end
  end
  current_group
end

added_count = 0
skipped_count = 0

core_files.each do |file_path|
  full_path = File.join('/Users/alwan/FieldMind', file_path)

  unless File.exist?(full_path)
    puts "⚠️  文件不存在: #{file_path}"
    skipped_count += 1
    next
  end

  # 检查文件是否已在项目中
  existing_file = project.files.find { |f| f.path == file_path }
  if existing_file
    puts "⏭️  已存在: #{file_path}"
    skipped_count += 1
    next
  end

  # 解析路径并获取/创建对应的组
  path_parts = file_path.split('/')
  file_name = path_parts.pop
  group_path = path_parts[1..-1] # 跳过 'fieldmind' 前缀

  group = get_or_create_group(project, group_path)

  # 添加文件引用
  file_ref = group.new_file(full_path)

  # 添加到编译阶段
  target.source_build_phase.add_file_reference(file_ref)

  puts "✅ 已添加: #{file_path}"
  added_count += 1
end

# 保存项目
project.save

puts "\n" + "="*60
puts "📊 文件添加统计"
puts "="*60
puts "✅ 成功添加: #{added_count} 个文件"
puts "⏭️  跳过: #{skipped_count} 个文件"
puts "="*60
puts "\n🎉 Xcode 项目已更新！"
puts "📝 下一步: 在 Xcode 中打开项目并编译测试"
