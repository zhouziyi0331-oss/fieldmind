# Code Generation & Execution 深度分析报告

**插件名称**: Code Generation & Execution Systems  
**类别**: 代码生成和安全执行  
**分析日期**: 2026-08-30

---

## 1. 插件概述

### 核心定位
代码生成与执行系统允许 LLM 生成并安全执行代码，是实现 Code Interpreter、自动化任务、数据分析等功能的基础。核心挑战是安全性和可靠性。

### 核心特点
- **代码生成**: Prompt → Code
- **语法验证**: AST分析
- **安全沙箱**: 隔离执行环境
- **资源限制**: CPU/内存/时间限制
- **依赖管理**: 安全的包安装
- **结果捕获**: stdout/stderr/返回值

### 架构设计
```
Code Generation & Execution
├── Code Generation (代码生成)
│   ├── Prompt Engineering
│   ├── Few-shot Examples
│   ├── Self-Repair
│   └── Test Generation
├── Validation (验证)
│   ├── Syntax Check
│   ├── AST Analysis
│   ├── Security Scan
│   └── Linting
├── Sandbox (沙箱)
│   ├── Docker Container
│   ├── Virtual Environment
│   ├── Resource Limits
│   └── Network Isolation
├── Execution (执行)
│   ├── Code Runner
│   ├── Timeout Control
│   ├── Output Capture
│   └── Error Handling
└── Safety (安全)
    ├── Blacklist Check
    ├── Capability Control
    ├── Audit Logging
    └── Result Sanitization
```

---

## 2. 核心概念

### 2.1 代码生成

```python
from typing import List, Dict

def generate_code(
    task_description: str,
    language: str = "python",
    examples: List[Dict] = None,
    llm = None
) -> str:
    """
    生成代码
    
    使用 Few-shot + 自我修复
    """
    # 构建提示
    prompt_parts = [
        f"请用 {language} 编写代码来完成以下任务：",
        f"\n任务: {task_description}\n"
    ]
    
    # 添加示例
    if examples:
        prompt_parts.append("\n示例：\n")
        for i, example in enumerate(examples, 1):
            prompt_parts.append(f"示例 {i}:")
            prompt_parts.append(f"任务: {example['task']}")
            prompt_parts.append(f"代码:\n```{language}\n{example['code']}\n```\n")
    
    # 添加要求
    prompt_parts.append("\n要求:")
    prompt_parts.append("1. 代码必须是完整可运行的")
    prompt_parts.append("2. 包含必要的错误处理")
    prompt_parts.append("3. 添加注释说明关键步骤")
    prompt_parts.append(f"4. 使用 ```{language} 代码块包裹\n")
    
    prompt_parts.append("代码:")
    
    prompt = "\n".join(prompt_parts)
    
    # 生成
    response = llm.complete(prompt, temperature=0.2)
    
    # 提取代码
    code = extract_code_from_markdown(response, language)
    
    return code

def extract_code_from_markdown(text: str, language: str) -> str:
    """从 Markdown 中提取代码块"""
    import re
    
    # 查找代码块
    pattern = f"```{language}\\n(.*?)\\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # 尝试不指定语言的代码块
    pattern = "```\\n(.*?)\\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # 没有代码块，返回全部
    return text.strip()
```

### 2.2 代码验证

```python
import ast

def validate_python_code(code: str) -> Dict:
    """
    验证 Python 代码
    
    检查:
    1. 语法正确性
    2. 安全性（黑名单）
    3. 复杂度
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "metrics": {}
    }
    
    # 1. 语法检查
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        result["valid"] = False
        result["errors"].append({
            "type": "syntax",
            "message": str(e),
            "line": e.lineno
        })
        return result
    
    # 2. 安全检查
    security_issues = check_security(tree)
    if security_issues:
        result["valid"] = False
        result["errors"].extend(security_issues)
    
    # 3. 复杂度分析
    metrics = analyze_complexity(tree)
    result["metrics"] = metrics
    
    if metrics.get("cyclomatic_complexity", 0) > 10:
        result["warnings"].append({
            "type": "complexity",
            "message": "代码复杂度过高"
        })
    
    return result

def check_security(tree: ast.AST) -> List[Dict]:
    """安全检查"""
    issues = []
    
    # 危险操作黑名单
    dangerous_functions = {
        'eval', 'exec', 'compile', '__import__',
        'open', 'input', 'raw_input'
    }
    
    dangerous_modules = {
        'os', 'sys', 'subprocess', 'socket',
        'urllib', 'requests'
    }
    
    class SecurityVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            # 检查函数调用
            if isinstance(node.func, ast.Name):
                if node.func.id in dangerous_functions:
                    issues.append({
                        "type": "security",
                        "message": f"禁止使用 {node.func.id}",
                        "line": node.lineno
                    })
            
            self.generic_visit(node)
        
        def visit_Import(self, node):
            # 检查导入
            for alias in node.names:
                if alias.name in dangerous_modules:
                    issues.append({
                        "type": "security",
                        "message": f"禁止导入 {alias.name}",
                        "line": node.lineno
                    })
            
            self.generic_visit(node)
    
    visitor = SecurityVisitor()
    visitor.visit(tree)
    
    return issues

def analyze_complexity(tree: ast.AST) -> Dict:
    """分析代码复杂度"""
    metrics = {
        "lines": 0,
        "functions": 0,
        "classes": 0,
        "cyclomatic_complexity": 0
    }
    
    class MetricsVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            metrics["functions"] += 1
            # 简化的圈复杂度计算
            complexity = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For)):
                    complexity += 1
            metrics["cyclomatic_complexity"] += complexity
            self.generic_visit(node)
        
        def visit_ClassDef(self, node):
            metrics["classes"] += 1
            self.generic_visit(node)
    
    visitor = MetricsVisitor()
    visitor.visit(tree)
    
    # 计算行数
    metrics["lines"] = len(ast.unparse(tree).split('\n'))
    
    return metrics
```

### 2.3 沙箱执行

```python
import subprocess
import tempfile
import os
from pathlib import Path

class CodeSandbox:
    """代码沙箱执行器"""
    
    def __init__(
        self,
        language: str = "python",
        timeout: int = 30,
        memory_limit: str = "512m",
        use_docker: bool = True
    ):
        self.language = language
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.use_docker = use_docker
    
    def execute(self, code: str, stdin: str = "") -> Dict:
        """
        执行代码
        
        返回:
        - stdout: 标准输出
        - stderr: 标准错误
        - returncode: 返回码
        - execution_time: 执行时间
        """
        if self.use_docker:
            return self._execute_docker(code, stdin)
        else:
            return self._execute_local(code, stdin)
    
    def _execute_docker(self, code: str, stdin: str) -> Dict:
        """Docker 沙箱执行"""
        import docker
        
        client = docker.from_env()
        
        # 选择镜像
        image_map = {
            "python": "python:3.9-slim",
            "javascript": "node:16-slim",
            "bash": "bash:5"
        }
        
        image = image_map.get(self.language, "python:3.9-slim")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=self._get_file_extension(),
            delete=False
        ) as f:
            f.write(code)
            code_file = f.name
        
        try:
            # 运行容器
            container = client.containers.run(
                image,
                command=self._get_run_command(code_file),
                volumes={
                    os.path.dirname(code_file): {
                        'bind': '/workspace',
                        'mode': 'ro'
                    }
                },
                working_dir='/workspace',
                mem_limit=self.memory_limit,
                network_disabled=True,  # 禁用网络
                stdin_open=True,
                stdout=True,
                stderr=True,
                detach=True
            )
            
            # 等待完成
            result = container.wait(timeout=self.timeout)
            
            # 获取输出
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
            
            # 清理
            container.remove()
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "returncode": result['StatusCode'],
                "execution_time": None  # Docker 不易获取精确时间
            }
        
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "execution_time": None
            }
        
        finally:
            os.unlink(code_file)
    
    def _execute_local(self, code: str, stdin: str) -> Dict:
        """本地执行（不推荐用于生产）"""
        import time
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=self._get_file_extension(),
            delete=False
        ) as f:
            f.write(code)
            code_file = f.name
        
        try:
            start_time = time.time()
            
            # 执行
            result = subprocess.run(
                self._get_run_command(code_file),
                input=stdin,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "execution_time": execution_time
            }
        
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"执行超时（>{self.timeout}秒）",
                "returncode": -1,
                "execution_time": self.timeout
            }
        
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "execution_time": None
            }
        
        finally:
            os.unlink(code_file)
    
    def _get_file_extension(self) -> str:
        """获取文件扩展名"""
        ext_map = {
            "python": ".py",
            "javascript": ".js",
            "bash": ".sh"
        }
        return ext_map.get(self.language, ".txt")
    
    def _get_run_command(self, filename: str) -> List[str]:
        """获取运行命令"""
        cmd_map = {
            "python": ["python", filename],
            "javascript": ["node", filename],
            "bash": ["bash", filename]
        }
        return cmd_map.get(self.language, ["python", filename])
```

### 2.4 自我修复

```python
def self_repair_code(
    code: str,
    error_message: str,
    max_attempts: int = 3,
    llm = None
) -> str:
    """
    自我修复代码
    
    根据错误信息让 LLM 修复代码
    """
    for attempt in range(max_attempts):
        # 构建修复提示
        repair_prompt = f"""
以下代码执行时出现错误：

代码:
```python
{code}
```

错误信息:
{error_message}

请修复代码。只返回修复后的完整代码，用 ```python 包裹。

修复后的代码:
"""
        
        # 生成修复
        response = llm.complete(repair_prompt, temperature=0.1)
        
        # 提取代码
        fixed_code = extract_code_from_markdown(response, "python")
        
        # 验证
        validation = validate_python_code(fixed_code)
        
        if validation["valid"]:
            # 尝试执行
            sandbox = CodeSandbox()
            result = sandbox.execute(fixed_code)
            
            if result["returncode"] == 0:
                return fixed_code
            
            # 更新错误信息
            error_message = result["stderr"]
            code = fixed_code
        else:
            # 验证失败，更新错误信息
            error_message = "\n".join([
                err["message"] for err in validation["errors"]
            ])
            code = fixed_code
    
    # 达到最大尝试次数
    raise CodeRepairError(f"无法修复代码（尝试了 {max_attempts} 次）")

class CodeRepairError(Exception):
    pass
```

### 2.5 测试生成

```python
def generate_tests(
    function_code: str,
    llm = None
) -> str:
    """
    生成测试代码
    
    为给定函数生成单元测试
    """
    prompt = f"""
为以下 Python 函数生成完整的单元测试：

```python
{function_code}
```

要求:
1. 使用 pytest 框架
2. 包含正常情况、边界情况和异常情况
3. 测试覆盖率应达到 90% 以上
4. 添加清晰的测试说明

测试代码:
"""
    
    response = llm.complete(prompt, temperature=0.2)
    
    test_code = extract_code_from_markdown(response, "python")
    
    return test_code
```

---

## 3. 核心算法

### 3.1 AST 安全分析算法

```python
def ast_security_analysis(code: str) -> Dict:
    """
    AST 深度安全分析
    
    检测:
    - 危险函数调用
    - 文件系统访问
    - 网络访问
    - 进程操作
    - 动态代码执行
    """
    tree = ast.parse(code)
    
    findings = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }
    
    class SecurityAnalyzer(ast.NodeVisitor):
        def __init__(self):
            self.scope_depth = 0
        
        def visit_Call(self, node):
            # 检查函数调用
            func_name = self._get_function_name(node.func)
            
            if func_name in ['eval', 'exec', 'compile']:
                findings["critical"].append({
                    "type": "dynamic_execution",
                    "function": func_name,
                    "line": node.lineno,
                    "message": f"检测到动态代码执行: {func_name}"
                })
            
            elif func_name == 'open':
                findings["high"].append({
                    "type": "file_access",
                    "function": "open",
                    "line": node.lineno,
                    "message": "检测到文件访问"
                })
            
            elif func_name in ['__import__', 'importlib.import_module']:
                findings["high"].append({
                    "type": "dynamic_import",
                    "function": func_name,
                    "line": node.lineno,
                    "message": "检测到动态导入"
                })
            
            self.generic_visit(node)
        
        def visit_Import(self, node):
            for alias in node.names:
                severity = self._check_module_safety(alias.name)
                
                if severity:
                    findings[severity].append({
                        "type": "import",
                        "module": alias.name,
                        "line": node.lineno,
                        "message": f"导入了 {severity} 风险模块: {alias.name}"
                    })
            
            self.generic_visit(node)
        
        def visit_Attribute(self, node):
            # 检查属性访问
            attr_chain = self._get_attribute_chain(node)
            
            dangerous_patterns = [
                '__class__',
                '__bases__',
                '__subclasses__',
                '__globals__'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in attr_chain:
                    findings["critical"].append({
                        "type": "introspection",
                        "pattern": pattern,
                        "line": node.lineno,
                        "message": f"检测到危险的内省操作: {attr_chain}"
                    })
            
            self.generic_visit(node)
        
        def _get_function_name(self, node) -> str:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return f"{self._get_function_name(node.value)}.{node.attr}"
            return ""
        
        def _get_attribute_chain(self, node) -> str:
            if isinstance(node, ast.Attribute):
                base = self._get_attribute_chain(node.value)
                return f"{base}.{node.attr}" if base else node.attr
            elif isinstance(node, ast.Name):
                return node.id
            return ""
        
        def _check_module_safety(self, module_name: str) -> str:
            """检查模块安全性，返回风险等级"""
            critical_modules = {'os', 'sys', 'subprocess'}
            high_risk_modules = {'socket', 'urllib', 'requests', 'http'}
            medium_risk_modules = {'pickle', 'shelve', 'marshal'}
            
            if module_name in critical_modules:
                return "critical"
            elif module_name in high_risk_modules:
                return "high"
            elif module_name in medium_risk_modules:
                return "medium"
            
            return None
    
    analyzer = SecurityAnalyzer()
    analyzer.visit(tree)
    
    return findings

# 时间复杂度: O(n) - n为AST节点数
```

### 3.2 资源使用跟踪算法

```python
import resource
import signal

class ResourceMonitor:
    """资源使用监控"""
    
    def __init__(
        self,
        max_memory_mb: int = 512,
        max_cpu_seconds: int = 30
    ):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_seconds = max_cpu_seconds
    
    def execute_with_limits(self, func, *args, **kwargs):
        """执行函数，带资源限制"""
        
        def set_limits():
            # 设置内存限制
            max_memory_bytes = self.max_memory_mb * 1024 * 1024
            resource.setrlimit(
                resource.RLIMIT_AS,
                (max_memory_bytes, max_memory_bytes)
            )
            
            # 设置 CPU 时间限制
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (self.max_cpu_seconds, self.max_cpu_seconds)
            )
        
        # 设置超时信号
        def timeout_handler(signum, frame):
            raise TimeoutError("执行超时")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.max_cpu_seconds + 5)  # 留一些余量
        
        try:
            # 在子进程中执行（带限制）
            from multiprocessing import Process, Queue
            
            queue = Queue()
            
            def wrapper():
                set_limits()
                try:
                    result = func(*args, **kwargs)
                    queue.put(('success', result))
                except Exception as e:
                    queue.put(('error', str(e)))
            
            process = Process(target=wrapper)
            process.start()
            process.join(timeout=self.max_cpu_seconds + 10)
            
            if process.is_alive():
                process.terminate()
                process.join()
                raise TimeoutError("执行超时")
            
            if not queue.empty():
                status, result = queue.get()
                if status == 'success':
                    return result
                else:
                    raise RuntimeError(result)
            
            raise RuntimeError("执行失败，无返回")
        
        finally:
            signal.alarm(0)  # 取消信号

# 时间复杂度: O(T) - T为执行时间
```

---

## 4. 可复用组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Code Generator | 代码生成器 | ⭐⭐⭐⭐⭐ |
| Code Validator | 代码验证器 | ⭐⭐⭐⭐⭐ |
| Code Sandbox | 代码沙箱 | ⭐⭐⭐⭐⭐ |
| Self-Repair | 自我修复 | ⭐⭐⭐⭐⭐ |
| Test Generator | 测试生成器 | ⭐⭐⭐⭐ |
| AST Security Analyzer | AST安全分析 | ⭐⭐⭐⭐⭐ |
| Resource Monitor | 资源监控 | ⭐⭐⭐⭐⭐ |
| Docker Executor | Docker执行器 | ⭐⭐⭐⭐⭐ |
| Code Extraction | 代码提取 | ⭐⭐⭐⭐⭐ |
| Complexity Analysis | 复杂度分析 | ⭐⭐⭐⭐ |

---

## 5. 核心学习

### 关键概念
1. **沙箱执行** - Docker隔离
2. **AST分析** - 安全检查
3. **自我修复** - 错误驱动修复
4. **资源限制** - CPU/内存限制
5. **测试生成** - 自动化测试

### 核心算法
1. AST安全分析
2. 资源使用跟踪
3. 自我修复迭代
4. 代码验证流程
5. Docker沙箱执行

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ 代码沙箱执行
- ⭐⭐⭐⭐⭐ AST安全分析
- ⭐⭐⭐⭐⭐ 自我修复机制
- ⭐⭐⭐⭐ 测试生成
- ⭐⭐⭐⭐⭐ 资源监控

---

**分析完成时间**: 2026-08-30  
**已完成插件数**: 33/40 (82.5%)  
**剩余**: 7个插件
