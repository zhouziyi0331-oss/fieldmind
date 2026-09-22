"""
结构化输出系统测试

演示如何使用结构化输出系统
"""
import asyncio
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from app.core.structured_output import StructuredOutputClient
from app.core.structured_output.observers import LoggingObserver, MetricsObserver


# ==================== 示例模型 ====================

class Sentiment(str, Enum):
    """情感类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Contact(BaseModel):
    """联系方式"""
    phone: Optional[str] = Field(None, description="电话号码")
    email: Optional[str] = Field(None, description="邮箱地址")
    address: Optional[str] = Field(None, description="地址")


class Person(BaseModel):
    """人物信息"""
    name: str = Field(description="姓名")
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")
    occupation: Optional[str] = Field(None, description="职业")
    contact: Optional[Contact] = Field(None, description="联系方式")
    notes: List[str] = Field(default_factory=list, description="备注信息")


class Review(BaseModel):
    """评论分析"""
    text: str = Field(description="评论原文")
    sentiment: Sentiment = Field(description="情感倾向")
    score: int = Field(ge=1, le=5, description="评分1-5")
    keywords: List[str] = Field(default_factory=list, description="关键词")


# ==================== Mock LLM 服务 ====================

class MockLLMService:
    """Mock LLM 服务用于测试"""

    async def complete_async(self, messages: List[dict], **kwargs):
        """模拟 LLM 响应"""
        # 提取用户消息
        user_message = None
        for msg in messages:
            if msg["role"] == "user":
                user_message = msg["content"]
                break

        # 根据内容返回不同响应
        if "张三" in user_message or "John" in user_message:
            return """
{
    "name": "张三",
    "age": 35,
    "occupation": "软件工程师",
    "contact": {
        "phone": "13812345678",
        "email": "zhangsan@example.com",
        "address": "北京市朝阳区xxx街"
    },
    "notes": ["VIP客户", "需要特别关注"]
}
"""
        elif "产品" in user_message or "评论" in user_message:
            return """
{
    "text": "这个产品非常好用，超出预期！",
    "sentiment": "positive",
    "score": 5,
    "keywords": ["好用", "超出预期"]
}
"""
        else:
            return "{}"


# ==================== 测试函数 ====================

async def test_basic_extraction():
    """测试基础信息提取"""
    print("\n" + "="*60)
    print("测试 1: 基础信息提取")
    print("="*60)

    # 创建客户端
    llm_service = MockLLMService()
    client = StructuredOutputClient(llm_service)

    # 添加观察者
    logging_obs = LoggingObserver()
    metrics_obs = MetricsObserver()
    client.add_observer(logging_obs)
    client.add_observer(metrics_obs)

    # 提取人物信息
    messages = [
        {"role": "user", "content": """
        提取以下信息：

        张三，35岁，软件工程师。
        电话：13812345678
        邮箱：zhangsan@example.com
        住址：北京市朝阳区xxx街
        备注：VIP客户，需要特别关注
        """}
    ]

    person = await client.create_async(
        messages=messages,
        response_model=Person,
        max_retries=3
    )

    print(f"\n✅ 提取成功!")
    print(f"姓名: {person.name}")
    print(f"年龄: {person.age}")
    print(f"职业: {person.occupation}")
    if person.contact:
        print(f"电话: {person.contact.phone}")
        print(f"邮箱: {person.contact.email}")
        print(f"地址: {person.contact.address}")
    print(f"备注: {', '.join(person.notes)}")

    # 打印指标
    print(f"\n📊 指标报告:")
    report = metrics_obs.get_report()
    for key, value in report.items():
        print(f"  {key}: {value}")


async def test_sentiment_analysis():
    """测试情感分析"""
    print("\n" + "="*60)
    print("测试 2: 情感分析")
    print("="*60)

    llm_service = MockLLMService()
    client = StructuredOutputClient(llm_service)

    messages = [
        {"role": "user", "content": "分析以下评论的情感：这个产品非常好用，超出预期！"}
    ]

    review = await client.create_async(
        messages=messages,
        response_model=Review,
        max_retries=3
    )

    print(f"\n✅ 分析成功!")
    print(f"评论: {review.text}")
    print(f"情感: {review.sentiment.value}")
    print(f"评分: {review.score}/5")
    print(f"关键词: {', '.join(review.keywords)}")


async def test_type_coercion():
    """测试类型强制转换"""
    print("\n" + "="*60)
    print("测试 3: 类型强制转换")
    print("="*60)

    from app.core.structured_output.type_coercion import coerce_value

    # 测试各种转换
    test_cases = [
        ("123", int, 123),
        ("123.45", float, 123.45),
        ("true", bool, True),
        ("yes", bool, True),
        ("positive", Sentiment, Sentiment.POSITIVE),
        ([1, 2, 3], List[str], ["1", "2", "3"]),
    ]

    print("\n类型转换测试:")
    for value, target_type, expected in test_cases:
        result = coerce_value(value, target_type)
        status = "✅" if result == expected else "❌"
        print(f"{status} {value} ({type(value).__name__}) -> {result} ({type(result).__name__})")


async def test_field_matching():
    """测试字段匹配"""
    print("\n" + "="*60)
    print("测试 4: 字段匹配")
    print("="*60)

    from app.core.structured_output.field_matcher import match_fields_fuzzy

    # 测试数据（LLM 可能返回的各种字段名变体）
    llm_data = {
        "Name": "张三",  # 大写开头
        "userAge": 35,   # 驼峰命名
        "occupation": "工程师",
        "ContactInfo": {  # 嵌套对象，大写开头
            "phoneNumber": "138...",  # 不同命名
            "Email": "test@example.com"
        }
    }

    # 匹配
    matched = match_fields_fuzzy(llm_data, Person)

    print("\n字段匹配结果:")
    for key, value in matched.items():
        print(f"  {key}: {value}")


async def test_schema_generation():
    """测试 Schema 生成"""
    print("\n" + "="*60)
    print("测试 5: JSON Schema 生成")
    print("="*60)

    from app.core.structured_output.schema_generator import generate_json_schema
    import json

    schema = generate_json_schema(Person)

    print("\nPerson 模型的 JSON Schema:")
    print(json.dumps(schema, ensure_ascii=False, indent=2))


async def test_client_stats():
    """测试客户端统计"""
    print("\n" + "="*60)
    print("测试 6: 客户端统计")
    print("="*60)

    llm_service = MockLLMService()
    client = StructuredOutputClient(llm_service)

    # 执行多次调用
    for i in range(5):
        try:
            await client.create_async(
                messages=[{"role": "user", "content": f"测试 {i+1}"}],
                response_model=Person,
                max_retries=1
            )
        except:
            pass

    stats = client.get_stats()
    print("\n📊 客户端统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


# ==================== 主函数 ====================

async def main():
    """运行所有测试"""
    print("\n🚀 结构化输出系统测试开始\n")

    try:
        await test_basic_extraction()
        await test_sentiment_analysis()
        await test_type_coercion()
        await test_field_matching()
        await test_schema_generation()
        await test_client_stats()

        print("\n" + "="*60)
        print("✅ 所有测试完成!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
