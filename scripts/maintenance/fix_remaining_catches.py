#!/usr/bin/env python3
"""
找出所有只调用handleAPIError但没有showToast的catch块
"""

import re

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def find_catches_without_toast():
    html = read_file('/Users/alwan/FieldMind-Native/Resources/index.html')
    lines = html.split('\n')

    issues = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 查找catch块
        if re.match(r'\s*}\s*catch\s*\(', line):
            catch_start = i

            # 找到catch块结束
            brace_count = 0
            catch_end = catch_start
            found_open = False

            for j in range(catch_start, min(catch_start + 20, len(lines))):
                if '{' in lines[j]:
                    found_open = True
                    brace_count += lines[j].count('{')
                brace_count -= lines[j].count('}')

                if found_open and brace_count == 0:
                    catch_end = j
                    break

            # 提取catch块内容
            catch_body = '\n'.join(lines[catch_start:catch_end+1])

            # 检查是否有用户提示
            has_toast = 'showToast' in catch_body
            has_alert = 'alert(' in catch_body
            has_handle_api_error = 'handleAPIError' in catch_body

            # 如果只有handleAPIError而没有showToast，标记为需要修复
            if has_handle_api_error and not has_toast and not has_alert:
                # 查找所在函数
                func_name = '未知函数'
                for k in range(max(0, catch_start - 30), catch_start):
                    func_match = re.search(r'(?:function|const|async function)\s+(\w+)\s*\(', lines[k])
                    if func_match:
                        func_name = func_match.group(1)

                issues.append({
                    'line': catch_start + 1,
                    'function': func_name,
                    'body': catch_body.strip()[:100]
                })

            i = catch_end + 1
        else:
            i += 1

    return issues

def main():
    print("🔍 查找只有handleAPIError但缺少showToast的catch块\n")
    print("="*70)

    issues = find_catches_without_toast()

    if issues:
        print(f"发现 {len(issues)} 处需要添加showToast:\n")
        for issue in issues:
            print(f"行 {issue['line']:5d} | {issue['function']:25s}")
            print(f"         {issue['body']}")
            print()
    else:
        print("✅ 所有catch块都有用户提示")

    print("="*70)
    print("\n建议: 在handleAPIError之前添加 showToast()")

if __name__ == '__main__':
    main()
