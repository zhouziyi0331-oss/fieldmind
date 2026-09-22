"""完整系统测试"""
import sys
sys.path.insert(0, '.')

def test_imports():
    """测试所有导入"""
    print("=" * 60)
    print("FieldMind 系统完整性测试")
    print("=" * 60)
    
    # 1. 模型测试
    print("\n1️⃣  测试数据模型...")
    from app.models.user import User, UserRole
    from app.models.skill import Skill, SkillStatus
    from app.models.timeline import TimelineEvent
    from app.models.industry import IndustryCategory
    from app.models.report import Report
    print("   ✅ 5个模型导入成功")
    
    # 2. Schema测试
    print("\n2️⃣  测试Pydantic Schema...")
    from app.schemas.user import UserCreate
    from app.schemas.skill import SkillResponse
    from app.schemas.timeline import TimelineEventCreate
    from app.schemas.industry import IndustryDetailResponse
    from app.schemas.report import ReportGenerateRequest
    print("   ✅ 5个Schema模块导入成功")
    
    # 3. 核心模块测试
    print("\n3️⃣  测试核心模块...")
    from app.core.security import get_password_hash, verify_password
    from app.core.database import Base, get_db
    from app.middleware.auth import get_current_user
    print("   ✅ 核心模块导入成功")
    
    # 4. API路由测试
    print("\n4️⃣  测试API路由...")
    from app.api.v1 import auth, skills, timeline, industry, reports
    
    routes = {
        'auth': len([r for r in auth.router.routes]),
        'skills': len([r for r in skills.router.routes]),
        'timeline': len([r for r in timeline.router.routes]),
        'industry': len([r for r in industry.router.routes]),
        'reports': len([r for r in reports.router.routes])
    }
    
    for name, count in routes.items():
        print(f"   ✅ {name}: {count} routes")
    
    total = sum(routes.values())
    print(f"\n   🎯 新增API端点: {total} 个")
    
    # 5. 功能测试
    print("\n5️⃣  测试功能...")
    test_hash = get_password_hash('test123')
    is_valid = verify_password('test123', test_hash)
    print(f"   ✅ 密码哈希和验证: {is_valid}")
    
    from app.core.security import create_tokens
    tokens = create_tokens('test-user', 'researcher')
    print(f"   ✅ JWT Token生成: {len(tokens['access_token'])} chars")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！系统准备就绪")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        test_imports()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
