"""
统一 ID 生成器

使用示例:
    from id_generator import UnifiedIDGenerator, EntityType

    # 生成项目 ID
    project_id = UnifiedIDGenerator.generate(EntityType.PROJECT)
    # 输出: proj_a1b2c3d4e5f6

    # 验证 ID
    is_valid = UnifiedIDGenerator.validate(project_id)
    # 输出: True

    # 提取类型
    entity_type = UnifiedIDGenerator.extract_type(project_id)
    # 输出: EntityType.PROJECT
"""

    """统一 ID 生成器"""

    @staticmethod
    def generate(entity_type: EntityType, metadata: Optional[Dict] = None) -> str:
        """
        生成全局唯一 ID

        格式: {prefix}_{uuid_short}
        示例: proj_a1b2c3d4, doc_e5f6g7h8

        Args:
            entity_type: 实体类型
            metadata: 可选元数据（用于生成可读性更好的 ID）

        Returns:
            全局唯一 ID
        """
        # 生成 UUID
        unique_id = str(uuid.uuid4()).replace('-', '')[:12]

        # 拼接前缀
        prefix = entity_type.value
        return f"{prefix}_{unique_id}"

    @staticmethod
    def generate_from_content(entity_type: EntityType, content: str) -> str:
        """
        从内容生成确定性 ID（幂等）

        用于：相同内容应该生成相同 ID 的场景
        """
        # 使用内容的 hash 生成确定性 ID
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
        prefix = entity_type.value
        return f"{prefix}_{content_hash}"

    @staticmethod
    def validate(entity_id: str) -> bool:
        """验证 ID 格式"""
        if not entity_id or '_' not in entity_id:
            return False

        prefix, unique_part = entity_id.split('_', 1)

        # 检查前缀是否合法
        valid_prefixes = [e.value for e in EntityType]
        if prefix not in valid_prefixes:
            return False

        # 检查 ID 部分长度
        if len(unique_part) != 12:
            return False

        return True

    @staticmethod
    def extract_type(entity_id: str) -> Optional[EntityType]:
        """从 ID 提取实体类型"""
        if not UnifiedIDGenerator.validate(entity_id):
            return None

        prefix = entity_id.split('_')[0]
        for entity_type in EntityType:
            if entity_type.value == prefix:
                return entity_type

        return None


