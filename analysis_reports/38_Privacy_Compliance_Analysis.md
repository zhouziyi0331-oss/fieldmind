# Data Privacy & Compliance 深度分析报告

**插件名称**: Data Privacy & Compliance for LLM Applications  
**类别**: 数据隐私和合规  
**分析日期**: 2026-08-30

---

## 1. 插件概述

### 核心定位
数据隐私与合规系统确保 LLM 应用符合 GDPR、CCPA 等法规要求，保护用户隐私数据，实现数据最小化、匿名化、访问控制等合规机制。

### 核心特点
- **PII检测**: 个人身份信息识别
- **数据匿名化**: 去标识化处理
- **访问控制**: RBAC/ABAC
- **数据加密**: 静态和传输加密
- **审计日志**: 完整操作记录
- **同意管理**: 用户授权管理

### 架构设计
```
Privacy & Compliance
├── PII Detection (PII检测)
│   ├── Pattern Matching
│   ├── NER Models
│   ├── Context Analysis
│   └── Custom Rules
├── Anonymization (匿名化)
│   ├── Masking
│   ├── Pseudonymization
│   ├── Generalization
│   └── Differential Privacy
├── Access Control (访问控制)
│   ├── Authentication
│   ├── Authorization
│   ├── RBAC
│   └── ABAC
├── Encryption (加密)
│   ├── At-rest Encryption
│   ├── In-transit Encryption
│   ├── Key Management
│   └── Secure Enclaves
├── Audit & Compliance (审计合规)
│   ├── Audit Logging
│   ├── Compliance Checks
│   ├── Data Lineage
│   └── Right to be Forgotten
└── Consent Management (同意管理)
    ├── Consent Collection
    ├── Consent Storage
    ├── Consent Revocation
    └── Purpose Limitation
```

---

## 2. 核心概念

### 2.1 PII检测

```python
import re
from typing import List, Dict, Tuple

class PIIDetector:
    """PII 检测器"""
    
    def __init__(self):
        # 正则模式
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            "date": r'\b\d{2}/\d{2}/\d{4}\b'
        }
    
    def detect(self, text: str) -> List[Dict]:
        """检测 PII"""
        findings = []
        
        # 正则检测
        for pii_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text)
            
            for match in matches:
                findings.append({
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 1.0
                })
        
        # NER 模型检测
        ner_findings = self._detect_with_ner(text)
        findings.extend(ner_findings)
        
        return findings
    
    def _detect_with_ner(self, text: str) -> List[Dict]:
        """使用 NER 模型检测"""
        import spacy
        
        try:
            nlp = spacy.load("en_core_web_sm")
            doc = nlp(text)
            
            findings = []
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "GPE", "DATE"]:
                    findings.append({
                        "type": ent.label_.lower(),
                        "value": ent.text,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "confidence": 0.8
                    })
            
            return findings
        
        except:
            return []
    
    def has_pii(self, text: str) -> bool:
        """检查是否包含 PII"""
        findings = self.detect(text)
        return len(findings) > 0
```

### 2.2 数据匿名化

```python
class DataAnonymizer:
    """数据匿名化器"""
    
    def __init__(self):
        self.pii_detector = PIIDetector()
    
    def anonymize(
        self,
        text: str,
        method: str = "mask"
    ) -> Tuple[str, Dict]:
        """
        匿名化文本
        
        方法:
        - mask: 掩码（***）
        - hash: 哈希（一致性假名）
        - generalize: 泛化
        - remove: 删除
        """
        # 检测 PII
        pii_findings = self.pii_detector.detect(text)
        
        # 按位置倒序排序（避免索引偏移）
        pii_findings.sort(key=lambda x: x["start"], reverse=True)
        
        # 替换映射
        replacements = {}
        
        # 应用匿名化
        anonymized = text
        
        for finding in pii_findings:
            original = finding["value"]
            start = finding["start"]
            end = finding["end"]
            
            if method == "mask":
                replacement = self._mask(original, finding["type"])
            elif method == "hash":
                replacement = self._pseudonymize(original)
            elif method == "generalize":
                replacement = self._generalize(original, finding["type"])
            elif method == "remove":
                replacement = ""
            else:
                replacement = "***"
            
            anonymized = anonymized[:start] + replacement + anonymized[end:]
            replacements[original] = replacement
        
        return anonymized, replacements
    
    def _mask(self, value: str, pii_type: str) -> str:
        """掩码"""
        if pii_type == "email":
            # 保留第一个字符和域名
            parts = value.split("@")
            if len(parts) == 2:
                return f"{parts[0][0]}***@{parts[1]}"
        
        elif pii_type == "phone":
            # 保留最后4位
            digits = re.sub(r'\D', '', value)
            if len(digits) >= 4:
                return f"***-***-{digits[-4:]}"
        
        # 默认完全掩码
        return "***"
    
    def _pseudonymize(self, value: str) -> str:
        """假名化（一致性哈希）"""
        import hashlib
        
        # 使用哈希生成假名
        hash_value = hashlib.sha256(value.encode()).hexdigest()[:8]
        return f"[REDACTED_{hash_value}]"
    
    def _generalize(self, value: str, pii_type: str) -> str:
        """泛化"""
        if pii_type == "date":
            # 泛化到年份
            year_match = re.search(r'\d{4}', value)
            if year_match:
                return year_match.group()
        
        elif pii_type == "person":
            return "[PERSON]"
        
        return "[REDACTED]"
```

### 2.3 访问控制（RBAC）

```python
from enum import Enum
from typing import Set

class Permission(Enum):
    """权限枚举"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

class Role:
    """角色"""
    def __init__(self, name: str, permissions: Set[Permission]):
        self.name = name
        self.permissions = permissions

class User:
    """用户"""
    def __init__(self, user_id: str, roles: Set[Role]):
        self.user_id = user_id
        self.roles = roles
    
    def has_permission(self, permission: Permission) -> bool:
        """检查权限"""
        for role in self.roles:
            if permission in role.permissions:
                return True
        return False

class RBACManager:
    """RBAC 管理器"""
    
    def __init__(self):
        self.users = {}
        self.roles = {}
        
        # 预定义角色
        self._init_default_roles()
    
    def _init_default_roles(self):
        """初始化默认角色"""
        self.roles["viewer"] = Role("viewer", {Permission.READ})
        self.roles["editor"] = Role("editor", {Permission.READ, Permission.WRITE})
        self.roles["admin"] = Role("admin", {
            Permission.READ,
            Permission.WRITE,
            Permission.DELETE,
            Permission.ADMIN
        })
    
    def add_user(self, user_id: str, role_names: List[str]):
        """添加用户"""
        roles = {self.roles[name] for name in role_names if name in self.roles}
        self.users[user_id] = User(user_id, roles)
    
    def check_permission(
        self,
        user_id: str,
        permission: Permission
    ) -> bool:
        """检查权限"""
        if user_id not in self.users:
            return False
        
        return self.users[user_id].has_permission(permission)
    
    def require_permission(self, permission: Permission):
        """权限装饰器"""
        def decorator(func):
            def wrapper(user_id, *args, **kwargs):
                if not self.check_permission(user_id, permission):
                    raise PermissionError(
                        f"User {user_id} lacks permission: {permission.value}"
                    )
                return func(user_id, *args, **kwargs)
            return wrapper
        return decorator

# 使用
rbac = RBACManager()
rbac.add_user("user1", ["viewer"])
rbac.add_user("admin1", ["admin"])

@rbac.require_permission(Permission.WRITE)
def edit_document(user_id: str, doc_id: str, content: str):
    # 编辑文档
    pass
```

### 2.4 审计日志

```python
import json
from datetime import datetime
from typing import Optional

class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
    
    def log(
        self,
        event_type: str,
        user_id: str,
        resource: str,
        action: str,
        result: str,
        metadata: Optional[Dict] = None
    ):
        """记录审计日志"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "result": result,  # success, failure, denied
            "metadata": metadata or {},
            "ip_address": self._get_client_ip(),
            "user_agent": self._get_user_agent()
        }
        
        # 写入日志
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def _get_client_ip(self) -> str:
        """获取客户端 IP"""
        # 实际应从请求上下文获取
        return "0.0.0.0"
    
    def _get_user_agent(self) -> str:
        """获取 User-Agent"""
        # 实际应从请求上下文获取
        return "Unknown"
    
    def query_logs(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """查询日志"""
        logs = []
        
        with open(self.log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                
                # 过滤
                if user_id and entry["user_id"] != user_id:
                    continue
                
                entry_time = datetime.fromisoformat(entry["timestamp"])
                
                if start_time and entry_time < start_time:
                    continue
                
                if end_time and entry_time > end_time:
                    continue
                
                logs.append(entry)
        
        return logs

# 使用
audit = AuditLogger("audit.log")

audit.log(
    event_type="data_access",
    user_id="user123",
    resource="customer_data",
    action="read",
    result="success",
    metadata={"record_count": 100}
)
```

### 2.5 同意管理

```python
class ConsentManager:
    """同意管理器"""
    
    def __init__(self):
        self.consents = {}  # {user_id: {purpose: consent_record}}
    
    def request_consent(
        self,
        user_id: str,
        purpose: str,
        description: str
    ) -> str:
        """请求用户同意"""
        consent_id = str(uuid.uuid4())
        
        if user_id not in self.consents:
            self.consents[user_id] = {}
        
        self.consents[user_id][purpose] = {
            "consent_id": consent_id,
            "purpose": purpose,
            "description": description,
            "granted": False,
            "timestamp": None
        }
        
        return consent_id
    
    def grant_consent(
        self,
        user_id: str,
        purpose: str
    ):
        """授予同意"""
        if user_id in self.consents and purpose in self.consents[user_id]:
            self.consents[user_id][purpose]["granted"] = True
            self.consents[user_id][purpose]["timestamp"] = datetime.utcnow()
    
    def revoke_consent(
        self,
        user_id: str,
        purpose: str
    ):
        """撤销同意"""
        if user_id in self.consents and purpose in self.consents[user_id]:
            self.consents[user_id][purpose]["granted"] = False
    
    def has_consent(
        self,
        user_id: str,
        purpose: str
    ) -> bool:
        """检查同意"""
        if user_id not in self.consents or purpose not in self.consents[user_id]:
            return False
        
        return self.consents[user_id][purpose]["granted"]
    
    def get_consents(self, user_id: str) -> Dict:
        """获取用户所有同意"""
        return self.consents.get(user_id, {})

# 使用
consent_mgr = ConsentManager()

# 请求同意
consent_mgr.request_consent(
    user_id="user123",
    purpose="data_analysis",
    description="我们需要分析您的数据以改进服务"
)

# 用户授予同意
consent_mgr.grant_consent("user123", "data_analysis")

# 检查同意
if consent_mgr.has_consent("user123", "data_analysis"):
    # 可以处理数据
    pass
```

---

## 3. 核心算法

### 3.1 差分隐私

```python
def add_laplace_noise(
    value: float,
    sensitivity: float,
    epsilon: float
) -> float:
    """
    添加拉普拉斯噪声（差分隐私）
    
    参数:
    - value: 真实值
    - sensitivity: 敏感度
    - epsilon: 隐私预算
    
    较小的 epsilon = 更强的隐私保护
    """
    import numpy as np
    
    # 拉普拉斯噪声
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    
    return value + noise

def aggregate_with_privacy(
    values: List[float],
    epsilon: float = 1.0
) -> float:
    """
    带差分隐私的聚合
    
    示例：计算平均值
    """
    # 计算真实平均值
    true_mean = sum(values) / len(values)
    
    # 敏感度（对于平均值）
    sensitivity = (max(values) - min(values)) / len(values)
    
    # 添加噪声
    private_mean = add_laplace_noise(true_mean, sensitivity, epsilon)
    
    return private_mean

# 时间复杂度: O(n)
```

### 3.2 K-匿名化

```python
def k_anonymize(
    data: List[Dict],
    quasi_identifiers: List[str],
    k: int = 5
) -> List[Dict]:
    """
    K-匿名化
    
    确保每个记录至少有 k-1 个其他记录具有相同的准标识符
    """
    from collections import defaultdict
    
    # 按准标识符分组
    groups = defaultdict(list)
    
    for record in data:
        key = tuple(record[qi] for qi in quasi_identifiers)
        groups[key].append(record)
    
    # 泛化小组
    anonymized = []
    
    for key, group in groups.items():
        if len(group) < k:
            # 需要泛化
            generalized_key = generalize_key(key, quasi_identifiers)
            
            for record in group:
                anonymized_record = record.copy()
                for i, qi in enumerate(quasi_identifiers):
                    anonymized_record[qi] = generalized_key[i]
                
                anonymized.append(anonymized_record)
        else:
            # 已经满足 k-匿名
            anonymized.extend(group)
    
    return anonymized

def generalize_key(key: tuple, attributes: List[str]) -> tuple:
    """泛化准标识符"""
    generalized = []
    
    for value in key:
        if isinstance(value, int):
            # 数值泛化到范围
            generalized.append(f"{value // 10 * 10}-{value // 10 * 10 + 9}")
        else:
            # 字符串泛化到首字母
            generalized.append(value[0] + "*")
    
    return tuple(generalized)

# 时间复杂度: O(n) - n为记录数
```

### 3.3 数据血缘追踪

```python
class DataLineage:
    """数据血缘追踪"""
    
    def __init__(self):
        self.lineage = {}  # {data_id: lineage_info}
    
    def record_transformation(
        self,
        input_ids: List[str],
        output_id: str,
        transformation: str,
        metadata: Dict = None
    ):
        """记录数据转换"""
        self.lineage[output_id] = {
            "inputs": input_ids,
            "transformation": transformation,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
    
    def get_lineage(self, data_id: str, depth: int = -1) -> Dict:
        """获取数据血缘"""
        if depth == 0 or data_id not in self.lineage:
            return {"id": data_id}
        
        lineage_info = self.lineage[data_id]
        
        result = {
            "id": data_id,
            "transformation": lineage_info["transformation"],
            "timestamp": lineage_info["timestamp"],
            "inputs": []
        }
        
        # 递归获取输入的血缘
        for input_id in lineage_info["inputs"]:
            input_lineage = self.get_lineage(
                input_id,
                depth - 1 if depth > 0 else -1
            )
            result["inputs"].append(input_lineage)
        
        return result
    
    def find_affected_data(self, source_id: str) -> List[str]:
        """查找受影响的数据"""
        affected = []
        
        for data_id, info in self.lineage.items():
            if source_id in info["inputs"]:
                affected.append(data_id)
                # 递归查找
                affected.extend(self.find_affected_data(data_id))
        
        return affected

# 时间复杂度: O(n * d) - n为节点数，d为深度
```

---

## 4. 可复用组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| PII Detector | PII检测 | ⭐⭐⭐⭐⭐ |
| Data Anonymizer | 数据匿名化 | ⭐⭐⭐⭐⭐ |
| RBAC Manager | 角色权限控制 | ⭐⭐⭐⭐⭐ |
| Audit Logger | 审计日志 | ⭐⭐⭐⭐⭐ |
| Consent Manager | 同意管理 | ⭐⭐⭐⭐⭐ |
| Differential Privacy | 差分隐私 | ⭐⭐⭐⭐ |
| K-Anonymization | K匿名化 | ⭐⭐⭐⭐ |
| Data Lineage | 数据血缘 | ⭐⭐⭐⭐⭐ |
| Encryption | 加密工具 | ⭐⭐⭐⭐⭐ |
| Access Control Decorator | 权限装饰器 | ⭐⭐⭐⭐⭐ |

---

## 5. 核心学习

### 关键概念
1. **PII检测** - 正则+NER模型
2. **数据匿名化** - 掩码/假名/泛化
3. **RBAC** - 角色权限控制
4. **审计日志** - 完整操作记录
5. **差分隐私** - 添加噪声保护

### 核心算法
1. PII检测（正则+NER）
2. 数据匿名化策略
3. K-匿名化算法
4. 差分隐私（拉普拉斯机制）
5. 数据血缘追踪

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ PII检测和保护
- ⭐⭐⭐⭐⭐ 数据匿名化
- ⭐⭐⭐⭐⭐ RBAC权限系统
- ⭐⭐⭐⭐⭐ 审计日志
- ⭐⭐⭐⭐ 同意管理

---

**分析完成时间**: 2026-08-30  
**已完成插件数**: 38/40 (95%)  
**剩余**: 2个插件
