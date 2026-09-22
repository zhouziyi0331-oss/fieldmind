#!/usr/bin/env python3
"""
Week 6-7 Day 4: 知识复用率跟踪系统

功能：
1. 设计复用率指标体系
2. 实现使用跟踪机制
3. 生成复用率报告
4. 创建复用趋势分析
5. 建立复用效率评估
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, Counter
import random


class KnowledgeReuseTracker:
    """知识复用率跟踪器"""

    def __init__(self, db_path: str, assets_dir: str, output_dir: str):
        self.db_path = db_path
        self.assets_dir = assets_dir
        self.output_dir = output_dir

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/metrics", exist_ok=True)
        os.makedirs(f"{output_dir}/reports", exist_ok=True)

        # 初始化跟踪数据库
        self.tracking_db = f"{output_dir}/reuse_tracking.db"
        self._init_tracking_db()

    def _init_tracking_db(self):
        """初始化跟踪数据库"""
        print("🗄️  初始化跟踪数据库...")

        conn = sqlite3.connect(self.tracking_db)
        cursor = conn.cursor()

        # 创建使用记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                context TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建复用统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reuse_stats (
                asset_id TEXT PRIMARY KEY,
                asset_type TEXT NOT NULL,
                total_views INTEGER DEFAULT 0,
                total_uses INTEGER DEFAULT 0,
                total_shares INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0.0,
                last_used DATETIME,
                first_used DATETIME,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建评分表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                user_id TEXT,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

        print("   ✓ 跟踪数据库初始化完成")

    def simulate_usage_data(self, patterns: List[Dict], skills: List[Dict], days: int = 90):
        """模拟使用数据（用于演示）"""
        print(f"\n📈 模拟 {days} 天的使用数据...")

        conn = sqlite3.connect(self.tracking_db)
        cursor = conn.cursor()

        total_events = 0
        start_date = datetime.now() - timedelta(days=days)

        # 模拟用户ID
        users = [f"user_{i:03d}" for i in range(1, 51)]  # 50个用户

        # 模拟知识模式的使用
        for pattern in patterns:
            chunk_id = pattern['chunk_id']
            quality = pattern['confidence']

            # 高质量内容使用频率更高
            base_usage = int(quality * 100)
            num_events = random.randint(base_usage // 2, base_usage * 2)

            for _ in range(num_events):
                # 随机日期
                days_offset = random.randint(0, days)
                timestamp = start_date + timedelta(days=days_offset)

                # 随机用户
                user = random.choice(users)

                # 随机动作
                action = random.choice(['view', 'view', 'view', 'use', 'use', 'share'])

                cursor.execute("""
                    INSERT INTO usage_log (asset_id, asset_type, user_id, action, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (chunk_id, 'pattern', user, action, timestamp))

                total_events += 1

        # 模拟 Skills 的使用
        for skill in skills:
            skill_name = skill['skill_name']
            quality = skill['quality_avg']

            base_usage = int(quality * 150)  # Skills 使用频率更高
            num_events = random.randint(base_usage, base_usage * 3)

            for _ in range(num_events):
                days_offset = random.randint(0, days)
                timestamp = start_date + timedelta(days=days_offset)
                user = random.choice(users)
                action = random.choice(['view', 'view', 'use', 'use', 'use', 'share'])

                cursor.execute("""
                    INSERT INTO usage_log (asset_id, asset_type, user_id, action, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (skill_name, 'skill', user, action, timestamp))

                total_events += 1

        conn.commit()

        print(f"   ✓ 模拟了 {total_events} 个使用事件")

        # 模拟评分
        print("   模拟用户评分...")
        ratings_count = 0

        # 为部分资产添加评分
        all_assets = [(p['chunk_id'], 'pattern', p['confidence']) for p in patterns[:100]]
        all_assets.extend([(s['skill_name'], 'skill', s['quality_avg']) for s in skills])

        for asset_id, asset_type, quality in all_assets:
            # 高质量内容更可能被评分
            if random.random() < quality:
                num_ratings = random.randint(1, 10)

                for _ in range(num_ratings):
                    user = random.choice(users)
                    # 评分围绕质量分波动
                    rating = max(1, min(5, int(quality * 5) + random.randint(-1, 1)))

                    cursor.execute("""
                        INSERT INTO ratings (asset_id, user_id, rating)
                        VALUES (?, ?, ?)
                    """, (asset_id, user, rating))

                    ratings_count += 1

        conn.commit()
        conn.close()

        print(f"   ✓ 模拟了 {ratings_count} 个评分")

    def calculate_reuse_stats(self):
        """计算复用统计"""
        print("\n📊 计算复用统计...")

        conn = sqlite3.connect(self.tracking_db)
        cursor = conn.cursor()

        # 汇总每个资产的使用统计
        cursor.execute("""
            SELECT
                asset_id,
                asset_type,
                SUM(CASE WHEN action = 'view' THEN 1 ELSE 0 END) as views,
                SUM(CASE WHEN action = 'use' THEN 1 ELSE 0 END) as uses,
                SUM(CASE WHEN action = 'share' THEN 1 ELSE 0 END) as shares,
                MIN(timestamp) as first_used,
                MAX(timestamp) as last_used
            FROM usage_log
            GROUP BY asset_id, asset_type
        """)

        stats_count = 0
        for row in cursor.fetchall():
            asset_id, asset_type, views, uses, shares, first_used, last_used = row

            # 获取平均评分
            cursor.execute("""
                SELECT AVG(rating) FROM ratings WHERE asset_id = ?
            """, (asset_id,))
            avg_rating_row = cursor.fetchone()
            avg_rating = avg_rating_row[0] if avg_rating_row[0] else 0.0

            # 插入或更新统计
            cursor.execute("""
                INSERT OR REPLACE INTO reuse_stats
                (asset_id, asset_type, total_views, total_uses, total_shares,
                 avg_rating, first_used, last_used, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (asset_id, asset_type, views, uses, shares, avg_rating, first_used, last_used))

            stats_count += 1

        conn.commit()
        conn.close()

        print(f"   ✓ 计算了 {stats_count} 个资产的统计数据")

    def generate_metrics(self) -> Dict:
        """生成复用率指标"""
        print("\n📏 生成复用率指标...")

        conn = sqlite3.connect(self.tracking_db)
        cursor = conn.cursor()

        # 1. 总体指标
        cursor.execute("SELECT COUNT(*) FROM reuse_stats WHERE asset_type = 'pattern'")
        total_patterns_with_usage = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reuse_stats WHERE asset_type = 'skill'")
        total_skills_with_usage = cursor.fetchone()[0]

        # 加载总资产数
        with open(f"{self.assets_dir}/knowledge_patterns_20260913_151640.json") as f:
            total_patterns = len(json.load(f)['patterns'])

        with open(f"{self.assets_dir}/skills_catalog.json") as f:
            total_skills = len(json.load(f)['skills'])

        # 2. 使用率
        cursor.execute("""
            SELECT
                SUM(total_views) as total_views,
                SUM(total_uses) as total_uses,
                SUM(total_shares) as total_shares
            FROM reuse_stats
        """)
        total_views, total_uses, total_shares = cursor.fetchone()

        # 3. 平均指标
        cursor.execute("""
            SELECT
                AVG(total_views) as avg_views,
                AVG(total_uses) as avg_uses,
                AVG(total_shares) as avg_shares,
                AVG(avg_rating) as avg_rating
            FROM reuse_stats
        """)
        avg_views, avg_uses, avg_shares, avg_rating = cursor.fetchone()

        # 4. Top 资产
        cursor.execute("""
            SELECT asset_id, asset_type, total_uses, avg_rating
            FROM reuse_stats
            ORDER BY total_uses DESC
            LIMIT 20
        """)
        top_assets = [
            {
                'asset_id': row[0],
                'asset_type': row[1],
                'total_uses': row[2],
                'avg_rating': row[3],
            }
            for row in cursor.fetchall()
        ]

        # 5. 活跃用户数
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM usage_log")
        active_users = cursor.fetchone()[0]

        # 6. 复用率计算
        pattern_reuse_rate = (total_patterns_with_usage / total_patterns * 100) if total_patterns > 0 else 0
        skill_reuse_rate = (total_skills_with_usage / total_skills * 100) if total_skills > 0 else 0

        # 7. 使用转化率
        conversion_rate = (total_uses / total_views * 100) if total_views > 0 else 0

        conn.close()

        metrics = {
            'overview': {
                'total_patterns': total_patterns,
                'total_skills': total_skills,
                'patterns_with_usage': total_patterns_with_usage,
                'skills_with_usage': total_skills_with_usage,
                'pattern_reuse_rate': round(pattern_reuse_rate, 2),
                'skill_reuse_rate': round(skill_reuse_rate, 2),
                'overall_reuse_rate': round((total_patterns_with_usage + total_skills_with_usage) / (total_patterns + total_skills) * 100, 2),
            },
            'usage': {
                'total_views': total_views,
                'total_uses': total_uses,
                'total_shares': total_shares,
                'avg_views_per_asset': round(avg_views, 2),
                'avg_uses_per_asset': round(avg_uses, 2),
                'avg_shares_per_asset': round(avg_shares, 2),
                'view_to_use_conversion': round(conversion_rate, 2),
            },
            'quality': {
                'avg_rating': round(avg_rating, 2),
            },
            'engagement': {
                'active_users': active_users,
            },
            'top_assets': top_assets,
        }

        print(f"   ✓ 生成了 {len(metrics)} 类指标")

        # 保存指标
        metrics_file = f"{self.output_dir}/metrics/reuse_metrics.json"
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 保存到: {metrics_file}")

        return metrics

    def generate_trend_analysis(self, days: int = 90) -> Dict:
        """生成复用趋势分析"""
        print("\n📈 生成复用趋势分析...")

        conn = sqlite3.connect(self.tracking_db)
        cursor = conn.cursor()

        # 按天统计
        cursor.execute("""
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as events,
                SUM(CASE WHEN action = 'view' THEN 1 ELSE 0 END) as views,
                SUM(CASE WHEN action = 'use' THEN 1 ELSE 0 END) as uses,
                SUM(CASE WHEN action = 'share' THEN 1 ELSE 0 END) as shares
            FROM usage_log
            WHERE timestamp >= date('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (days,))

        daily_stats = []
        for row in cursor.fetchall():
            daily_stats.append({
                'date': row[0],
                'events': row[1],
                'views': row[2],
                'uses': row[3],
                'shares': row[4],
            })

        # 按周统计
        cursor.execute("""
            SELECT
                strftime('%Y-W%W', timestamp) as week,
                COUNT(*) as events,
                SUM(CASE WHEN action = 'use' THEN 1 ELSE 0 END) as uses
            FROM usage_log
            WHERE timestamp >= date('now', '-' || ? || ' days')
            GROUP BY week
            ORDER BY week
        """, (days,))

        weekly_stats = []
        for row in cursor.fetchall():
            weekly_stats.append({
                'week': row[0],
                'events': row[1],
                'uses': row[2],
            })

        # 按月统计
        cursor.execute("""
            SELECT
                strftime('%Y-%m', timestamp) as month,
                COUNT(*) as events,
                SUM(CASE WHEN action = 'use' THEN 1 ELSE 0 END) as uses
            FROM usage_log
            WHERE timestamp >= date('now', '-' || ? || ' days')
            GROUP BY month
            ORDER BY month
        """, (days,))

        monthly_stats = []
        for row in cursor.fetchall():
            monthly_stats.append({
                'month': row[0],
                'events': row[1],
                'uses': row[2],
            })

        conn.close()

        trends = {
            'period': f'Last {days} days',
            'daily': daily_stats,
            'weekly': weekly_stats,
            'monthly': monthly_stats,
            'summary': {
                'total_days': len(daily_stats),
                'avg_events_per_day': sum(d['events'] for d in daily_stats) / len(daily_stats) if daily_stats else 0,
                'avg_uses_per_day': sum(d['uses'] for d in daily_stats) / len(daily_stats) if daily_stats else 0,
            }
        }

        # 保存趋势数据
        trends_file = f"{self.output_dir}/metrics/reuse_trends.json"
        with open(trends_file, 'w', encoding='utf-8') as f:
            json.dump(trends, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 分析了 {len(daily_stats)} 天的数据")
        print(f"   ✓ 保存到: {trends_file}")

        return trends

    def generate_efficiency_report(self, metrics: Dict, trends: Dict) -> Dict:
        """生成复用效率报告"""
        print("\n⚡ 生成复用效率报告...")

        # 计算效率指标
        efficiency = {
            'reuse_effectiveness': {
                'overall_reuse_rate': metrics['overview']['overall_reuse_rate'],
                'pattern_reuse_rate': metrics['overview']['pattern_reuse_rate'],
                'skill_reuse_rate': metrics['overview']['skill_reuse_rate'],
                'grade': self._grade_reuse_rate(metrics['overview']['overall_reuse_rate']),
            },
            'usage_intensity': {
                'avg_uses_per_asset': metrics['usage']['avg_uses_per_asset'],
                'view_to_use_conversion': metrics['usage']['view_to_use_conversion'],
                'share_rate': (metrics['usage']['total_shares'] / metrics['usage']['total_uses'] * 100) if metrics['usage']['total_uses'] > 0 else 0,
                'grade': self._grade_usage_intensity(metrics['usage']['avg_uses_per_asset']),
            },
            'content_quality': {
                'avg_rating': metrics['quality']['avg_rating'],
                'grade': self._grade_quality(metrics['quality']['avg_rating']),
            },
            'user_engagement': {
                'active_users': metrics['engagement']['active_users'],
                'avg_events_per_day': trends['summary']['avg_events_per_day'],
                'grade': self._grade_engagement(metrics['engagement']['active_users']),
            },
            'overall_score': 0,  # 将在下面计算
        }

        # 计算总分（0-100）
        grades = {
            'A': 90, 'B': 75, 'C': 60, 'D': 40, 'F': 20
        }

        scores = [
            grades.get(efficiency['reuse_effectiveness']['grade'], 50),
            grades.get(efficiency['usage_intensity']['grade'], 50),
            grades.get(efficiency['content_quality']['grade'], 50),
            grades.get(efficiency['user_engagement']['grade'], 50),
        ]

        efficiency['overall_score'] = sum(scores) / len(scores)
        efficiency['overall_grade'] = self._score_to_grade(efficiency['overall_score'])

        # 生成改进建议
        efficiency['recommendations'] = self._generate_recommendations(efficiency)

        # 保存报告
        report_file = f"{self.output_dir}/reports/efficiency_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(efficiency, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 总分: {efficiency['overall_score']:.1f} ({efficiency['overall_grade']})")
        print(f"   ✓ 保存到: {report_file}")

        return efficiency

    def _grade_reuse_rate(self, rate: float) -> str:
        """复用率评级"""
        if rate >= 80:
            return 'A'
        elif rate >= 60:
            return 'B'
        elif rate >= 40:
            return 'C'
        elif rate >= 20:
            return 'D'
        else:
            return 'F'

    def _grade_usage_intensity(self, avg_uses: float) -> str:
        """使用强度评级"""
        if avg_uses >= 50:
            return 'A'
        elif avg_uses >= 30:
            return 'B'
        elif avg_uses >= 15:
            return 'C'
        elif avg_uses >= 5:
            return 'D'
        else:
            return 'F'

    def _grade_quality(self, avg_rating: float) -> str:
        """质量评级"""
        if avg_rating >= 4.5:
            return 'A'
        elif avg_rating >= 4.0:
            return 'B'
        elif avg_rating >= 3.5:
            return 'C'
        elif avg_rating >= 3.0:
            return 'D'
        else:
            return 'F'

    def _grade_engagement(self, active_users: int) -> str:
        """用户参与度评级"""
        if active_users >= 40:
            return 'A'
        elif active_users >= 30:
            return 'B'
        elif active_users >= 20:
            return 'C'
        elif active_users >= 10:
            return 'D'
        else:
            return 'F'

    def _score_to_grade(self, score: float) -> str:
        """分数转评级"""
        if score >= 90:
            return 'A'
        elif score >= 75:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 40:
            return 'D'
        else:
            return 'F'

    def _generate_recommendations(self, efficiency: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于复用率
        if efficiency['reuse_effectiveness']['grade'] in ['D', 'F']:
            recommendations.append("复用率偏低，建议加强知识推广和培训")

        # 基于使用强度
        if efficiency['usage_intensity']['grade'] in ['D', 'F']:
            recommendations.append("使用强度不足，建议优化内容质量和易用性")

        # 基于内容质量
        if efficiency['content_quality']['grade'] in ['C', 'D', 'F']:
            recommendations.append("内容质量需要提升，建议审查低评分内容")

        # 基于用户参与度
        if efficiency['user_engagement']['grade'] in ['D', 'F']:
            recommendations.append("用户参与度低，建议增加激励机制")

        # 基于转化率
        if efficiency['usage_intensity']['view_to_use_conversion'] < 20:
            recommendations.append("浏览到使用转化率低，建议优化内容展示和引导")

        if not recommendations:
            recommendations.append("整体表现良好，继续保持")

        return recommendations

    def generate_dashboard_data(self, metrics: Dict, trends: Dict, efficiency: Dict) -> Dict:
        """生成仪表板数据"""
        print("\n📊 生成复用仪表板数据...")

        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'kpis': {
                'overall_reuse_rate': metrics['overview']['overall_reuse_rate'],
                'total_uses': metrics['usage']['total_uses'],
                'active_users': metrics['engagement']['active_users'],
                'avg_rating': metrics['quality']['avg_rating'],
                'overall_score': efficiency['overall_score'],
                'overall_grade': efficiency['overall_grade'],
            },
            'charts': {
                'daily_usage': [
                    {'date': d['date'], 'uses': d['uses']}
                    for d in trends['daily'][-30:]  # 最近30天
                ],
                'top_assets': metrics['top_assets'][:10],
                'reuse_by_type': {
                    'patterns': metrics['overview']['patterns_with_usage'],
                    'skills': metrics['overview']['skills_with_usage'],
                },
            },
            'grades': {
                'reuse_effectiveness': efficiency['reuse_effectiveness']['grade'],
                'usage_intensity': efficiency['usage_intensity']['grade'],
                'content_quality': efficiency['content_quality']['grade'],
                'user_engagement': efficiency['user_engagement']['grade'],
            },
            'recommendations': efficiency['recommendations'],
        }

        # 保存
        dashboard_file = f"{self.output_dir}/metrics/reuse_dashboard.json"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 保存到: {dashboard_file}")

        return dashboard

    def generate_summary_report(self, metrics: Dict, trends: Dict, efficiency: Dict):
        """生成文本摘要报告"""
        print("\n📄 生成摘要报告...")

        report = f"""# 知识复用率跟踪报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、总体指标

### 资产概况
- 总知识模式: {metrics['overview']['total_patterns']}
- 总 Skills: {metrics['overview']['total_skills']}
- 有使用记录的模式: {metrics['overview']['patterns_with_usage']}
- 有使用记录的 Skills: {metrics['overview']['skills_with_usage']}

### 复用率
- **整体复用率**: {metrics['overview']['overall_reuse_rate']}%
- 模式复用率: {metrics['overview']['pattern_reuse_rate']}%
- Skills 复用率: {metrics['overview']['skill_reuse_rate']}%

### 使用统计
- 总浏览次数: {metrics['usage']['total_views']:,}
- 总使用次数: {metrics['usage']['total_uses']:,}
- 总分享次数: {metrics['usage']['total_shares']:,}
- 浏览到使用转化率: {metrics['usage']['view_to_use_conversion']}%

### 用户参与
- 活跃用户数: {metrics['engagement']['active_users']}

---

## 二、效率评估

### 总体评分
**{efficiency['overall_score']:.1f} 分 ({efficiency['overall_grade']}级)**

### 各维度评级
- 复用有效性: {efficiency['reuse_effectiveness']['grade']}
- 使用强度: {efficiency['usage_intensity']['grade']}
- 内容质量: {efficiency['content_quality']['grade']}
- 用户参与度: {efficiency['user_engagement']['grade']}

---

## 三、趋势分析

### 使用趋势
- 分析周期: {trends['period']}
- 平均每日事件数: {trends['summary']['avg_events_per_day']:.1f}
- 平均每日使用数: {trends['summary']['avg_uses_per_day']:.1f}

---

## 四、Top 资产

### 使用次数 Top 10
"""

        for i, asset in enumerate(metrics['top_assets'][:10], 1):
            report += f"{i}. [{asset['asset_type']}] {asset['asset_id']}: {asset['total_uses']} 次使用\n"

        report += f"""
---

## 五、改进建议

"""

        for i, rec in enumerate(efficiency['recommendations'], 1):
            report += f"{i}. {rec}\n"

        report += """
---

## 六、下一步行动

### 短期（1-2周）
- 审查低复用率的资产，评估是否需要改进或删除
- 对高使用率资产进行深度分析，总结成功经验
- 加强用户培训，提高知识复用意识

### 中期（1个月）
- 优化搜索和推荐算法，提高内容发现效率
- 建立激励机制，鼓励用户分享使用经验
- 定期发布复用率报告，展示最佳实践

### 长期（3个月+）
- 建立知识资产生命周期管理流程
- 持续收集用户反馈，迭代优化内容质量
- 扩大知识库规模，覆盖更多领域和场景

---

**FieldMind Knowledge Reuse System**
Version 1.0
"""

        # 保存报告
        report_file = f"{self.output_dir}/reports/reuse_summary_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"   ✓ 保存到: {report_file}")

        return report_file

    def run(self):
        """执行完整流程"""
        print("=" * 70)
        print("Week 6-7 Day 4: 知识复用率跟踪")
        print("=" * 70)

        # 1. 加载资产数据
        with open(f"{self.assets_dir}/knowledge_patterns_20260913_151640.json") as f:
            patterns = json.load(f)['patterns']

        with open(f"{self.assets_dir}/skills_catalog.json") as f:
            skills = json.load(f)['skills']

        print(f"📚 加载了 {len(patterns)} 个知识模式, {len(skills)} 个 Skills")

        # 2. 模拟使用数据
        self.simulate_usage_data(patterns, skills, days=90)

        # 3. 计算复用统计
        self.calculate_reuse_stats()

        # 4. 生成指标
        metrics = self.generate_metrics()

        # 5. 生成趋势分析
        trends = self.generate_trend_analysis(days=90)

        # 6. 生成效率报告
        efficiency = self.generate_efficiency_report(metrics, trends)

        # 7. 生成仪表板数据
        dashboard = self.generate_dashboard_data(metrics, trends, efficiency)

        # 8. 生成摘要报告
        summary_report = self.generate_summary_report(metrics, trends, efficiency)

        # 9. 总结
        print("\n" + "=" * 70)
        print("知识复用率跟踪完成")
        print("=" * 70)

        print(f"\n📊 关键指标:")
        print(f"  整体复用率: {metrics['overview']['overall_reuse_rate']}%")
        print(f"  总使用次数: {metrics['usage']['total_uses']:,}")
        print(f"  活跃用户数: {metrics['engagement']['active_users']}")
        print(f"  平均评分: {metrics['quality']['avg_rating']:.2f}/5.0")

        print(f"\n⚡ 效率评估:")
        print(f"  总分: {efficiency['overall_score']:.1f} ({efficiency['overall_grade']})")
        print(f"  复用有效性: {efficiency['reuse_effectiveness']['grade']}")
        print(f"  使用强度: {efficiency['usage_intensity']['grade']}")
        print(f"  内容质量: {efficiency['content_quality']['grade']}")
        print(f"  用户参与度: {efficiency['user_engagement']['grade']}")

        print(f"\n📁 输出文件:")
        print(f"  - 跟踪数据库: {self.tracking_db}")
        print(f"  - 复用指标: {self.output_dir}/metrics/reuse_metrics.json")
        print(f"  - 趋势分析: {self.output_dir}/metrics/reuse_trends.json")
        print(f"  - 效率报告: {self.output_dir}/reports/efficiency_report.json")
        print(f"  - 仪表板数据: {self.output_dir}/metrics/reuse_dashboard.json")
        print(f"  - 摘要报告: {summary_report}")

        return {
            'metrics': metrics,
            'trends': trends,
            'efficiency': efficiency,
            'dashboard': dashboard,
        }


def main():
    db_path = "/Users/alwan/Downloads/FieldMind/fieldmind/backend/src/data/fieldmind.db"
    assets_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets"
    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets"

    tracker = KnowledgeReuseTracker(db_path, assets_dir, output_dir)
    result = tracker.run()

    print("\n✅ 知识复用率跟踪完成！")


if __name__ == "__main__":
    main()
