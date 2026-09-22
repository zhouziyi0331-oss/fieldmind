"""
可视化服务 - 整合Plotly、pyecharts、NetworkX、WordCloud
提供统一的数据可视化能力
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import json
import base64
from io import BytesIO
from datetime import datetime

logger = logging.getLogger(__name__)

# 全局单例
_visualization_service = None


class VisualizationService:
    """可视化服务 - 整合多种可视化工具"""

    def __init__(self,
        enable_plotly: bool = True,
        enable_pyecharts: bool = True,
        enable_networkx: bool = True,
        enable_wordcloud: bool = True,


        use_workflow_engine: bool = True):
        """
        初始化可视化服务

        Args:
            enable_plotly: 启用Plotly
            enable_pyecharts: 启用pyecharts
            enable_networkx: 启用NetworkX+Pyvis
            enable_wordcloud: 启用WordCloud
        """
        self.enable_plotly = enable_plotly
        self.enable_pyecharts = enable_pyecharts
        self.enable_networkx = enable_networkx
        self.enable_wordcloud = enable_wordcloud

        # 延迟加载实例
        self._plotly = None
        self._pyecharts = None
        self._networkx = None
        self._wordcloud = None

        logger.info("✅ 可视化服务初始化完成")

    def _get_plotly(self):
        """延迟加载Plotly"""
        if self._plotly is None and self.enable_plotly:
            try:
                import plotly.graph_objects as go
                import plotly.express as px
                from plotly.subplots import make_subplots

                self._plotly = {
                    'go': go,
                    'px': px,
                    'make_subplots': make_subplots
                }
                logger.info("✅ Plotly加载成功")
            except ImportError as e:
                logger.warning(f"⚠️ Plotly未安装: {e}")
                self.enable_plotly = False
        return self._plotly

    def _get_pyecharts(self):
        """延迟加载pyecharts"""
        if self._pyecharts is None and self.enable_pyecharts:
            try:
                from pyecharts import options as opts
                from pyecharts.charts import (
                    Bar, Line, Pie, Scatter, WordCloud as PyechartsWordCloud,
                    Graph, Sankey, Funnel, Gauge
                )

                self._pyecharts = {
                    'opts': opts,
                    'Bar': Bar,
                    'Line': Line,
                    'Pie': Pie,
                    'Scatter': Scatter,
                    'WordCloud': PyechartsWordCloud,
                    'Graph': Graph,
                    'Sankey': Sankey,
                    'Funnel': Funnel,
                    'Gauge': Gauge
                }
                logger.info("✅ pyecharts加载成功")
            except ImportError as e:
                logger.warning(f"⚠️ pyecharts未安装: {e}")
                self.enable_pyecharts = False
        return self._pyecharts

    def _get_networkx(self):
        """延迟加载NetworkX和Pyvis"""
        if self._networkx is None and self.enable_networkx:
            try:
                import networkx as nx
                from pyvis.network import Network

                self._networkx = {
                    'nx': nx,
                    'Network': Network
                }
                logger.info("✅ NetworkX+Pyvis加载成功")
            except ImportError as e:
                logger.warning(f"⚠️ NetworkX/Pyvis未安装: {e}")
                self.enable_networkx = False
        return self._networkx

    def _get_wordcloud(self):
        """延迟加载WordCloud"""
        if self._wordcloud is None and self.enable_wordcloud:
            try:
                from wordcloud import WordCloud
                import matplotlib
                matplotlib.use('Agg')  # 非GUI后端
                import matplotlib.pyplot as plt

                self._wordcloud = {
                    'WordCloud': WordCloud,
                    'plt': plt
                }
                logger.info("✅ WordCloud加载成功")
            except ImportError as e:
                logger.warning(f"⚠️ WordCloud未安装: {e}")
                self.enable_wordcloud = False
        return self._wordcloud

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        # 尝试加载所有工具
        self._get_plotly()
        self._get_pyecharts()
        self._get_networkx()
        self._get_wordcloud()

        return {
            'available': any([
                self.enable_plotly,
                self.enable_pyecharts,
                self.enable_networkx,
                self.enable_wordcloud
            ]),
            'plotly': self.enable_plotly,
            'pyecharts': self.enable_pyecharts,
            'networkx': self.enable_networkx,
            'wordcloud': self.enable_wordcloud
        }

    # ========== Plotly 图表 ==========

    def plotly_bar_chart(
        self,
        data: Dict[str, List],
        x_key: str,
        y_key: str,
        title: str = "Bar Chart"
    ) -> Optional[str]:
        """
        创建Plotly柱状图

        Args:
            data: 数据字典 {'categories': [...], 'values': [...]}
            x_key: X轴键名
            y_key: Y轴键名
            title: 图表标题

        Returns:
            HTML字符串
        """
        plotly = self._get_plotly()
        if not plotly:
            return None

        try:
            go = plotly['go']

            fig = go.Figure(data=[
                go.Bar(
                    x=data[x_key],
                    y=data[y_key],
                    marker_color='rgb(55, 83, 109)'
                )
            ])

            fig.update_layout(
                title=title,
                xaxis_title=x_key,
                yaxis_title=y_key,
                template='plotly_white'
            )

            return fig.to_html(include_plotlyjs='cdn', full_html=False)
        except Exception as e:
            logger.error(f"❌ Plotly柱状图生成失败: {e}")
            return None

    def plotly_line_chart(
        self,
        data: Dict[str, List],
        x_key: str,
        y_keys: List[str],
        title: str = "Line Chart"
    ) -> Optional[str]:
        """
        创建Plotly折线图（支持多条线）

        Args:
            data: 数据字典
            x_key: X轴键名
            y_keys: Y轴键名列表（多条线）
            title: 图表标题

        Returns:
            HTML字符串
        """
        plotly = self._get_plotly()
        if not plotly:
            return None

        try:
            go = plotly['go']

            fig = go.Figure()

            for y_key in y_keys:
                fig.add_trace(go.Scatter(
                    x=data[x_key],
                    y=data[y_key],
                    mode='lines+markers',
                    name=y_key
                ))

            fig.update_layout(
                title=title,
                xaxis_title=x_key,
                yaxis_title='Value',
                template='plotly_white',
                hovermode='x unified'
            )

            return fig.to_html(include_plotlyjs='cdn', full_html=False)
        except Exception as e:
            logger.error(f"❌ Plotly折线图生成失败: {e}")
            return None

    def plotly_scatter_3d(
        self,
        data: Dict[str, List],
        x_key: str,
        y_key: str,
        z_key: str,
        color_key: Optional[str] = None,
        title: str = "3D Scatter Plot"
    ) -> Optional[str]:
        """
        创建Plotly 3D散点图

        Args:
            data: 数据字典
            x_key: X轴键名
            y_key: Y轴键名
            z_key: Z轴键名
            color_key: 颜色分组键名
            title: 图表标题

        Returns:
            HTML字符串
        """
        plotly = self._get_plotly()
        if not plotly:
            return None

        try:
            go = plotly['go']

            scatter_config = {
                'x': data[x_key],
                'y': data[y_key],
                'z': data[z_key],
                'mode': 'markers',
                'marker': {'size': 5}
            }

            if color_key and color_key in data:
                scatter_config['marker']['color'] = data[color_key]
                scatter_config['marker']['colorscale'] = 'Viridis'
                scatter_config['marker']['showscale'] = True

            fig = go.Figure(data=[go.Scatter3d(**scatter_config)])

            fig.update_layout(
                title=title,
                scene=dict(
                    xaxis_title=x_key,
                    yaxis_title=y_key,
                    zaxis_title=z_key
                ),
                template='plotly_white'
            )

            return fig.to_html(include_plotlyjs='cdn', full_html=False)
        except Exception as e:
            logger.error(f"❌ Plotly 3D散点图生成失败: {e}")
            return None

    # ========== pyecharts 图表 ==========

    def pyecharts_pie_chart(
        self,
        data: List[Tuple[str, float]],
        title: str = "饼图"
    ) -> Optional[str]:
        """
        创建pyecharts饼图

        Args:
            data: 数据列表 [("类别1", 值1), ("类别2", 值2), ...]
            title: 图表标题

        Returns:
            HTML字符串
        """
        pyecharts = self._get_pyecharts()
        if not pyecharts:
            return None

        try:
            Pie = pyecharts['Pie']
            opts = pyecharts['opts']

            pie = (
                Pie(init_opts=opts.InitOpts(width="800px", height="600px"))
                .add(
                    series_name=title,
                    data_pair=data,
                    radius=["40%", "70%"],  # 环形饼图
                    label_opts=opts.LabelOpts(
                        formatter="{b}: {c} ({d}%)"
                    )
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=title),
                    legend_opts=opts.LegendOpts(orient="vertical", pos_left="left")
                )
            )

            return pie.render_embed()
        except Exception as e:
            logger.error(f"❌ pyecharts饼图生成失败: {e}")
            return None

    def pyecharts_graph(
        self,
        nodes: List[Dict[str, Any]],
        links: List[Dict[str, Any]],
        title: str = "关系图"
    ) -> Optional[str]:
        """
        创建pyecharts关系图

        Args:
            nodes: 节点列表 [{'name': 'A', 'symbolSize': 10}, ...]
            links: 边列表 [{'source': 'A', 'target': 'B'}, ...]
            title: 图表标题

        Returns:
            HTML字符串
        """
        pyecharts = self._get_pyecharts()
        if not pyecharts:
            return None

        try:
            Graph = pyecharts['Graph']
            opts = pyecharts['opts']

            graph = (
                Graph(init_opts=opts.InitOpts(width="1000px", height="800px"))
                .add(
                    series_name="",
                    nodes=nodes,
                    links=links,
                    repulsion=8000,
                    layout="force",
                    is_roam=True,
                    is_focusnode=True,
                    label_opts=opts.LabelOpts(is_show=True)
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=title)
                )
            )

            return graph.render_embed()
        except Exception as e:
            logger.error(f"❌ pyecharts关系图生成失败: {e}")
            return None

    # ========== NetworkX + Pyvis ==========

    def networkx_knowledge_graph(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        title: str = "Knowledge Graph"
    ) -> Optional[str]:
        """
        创建NetworkX知识图谱（使用Pyvis渲染）

        Args:
            nodes: 节点列表 [{'id': 'A', 'label': 'Node A', 'group': 1}, ...]
            edges: 边列表 [{'source': 'A', 'target': 'B', 'label': 'relates'}, ...]
            title: 图表标题

        Returns:
            HTML字符串
        """
        networkx_tools = self._get_networkx()
        if not networkx_tools:
            return None

        try:
            nx = networkx_tools['nx']
            Network = networkx_tools['Network']

            # 创建NetworkX图
            G = nx.Graph()

            # 添加节点
            for node in nodes:
                G.add_node(
                    node['id'],
                    label=node.get('label', node['id']),
                    group=node.get('group', 1)
                )

            # 添加边
            for edge in edges:
                G.add_edge(
                    edge['source'],
                    edge['target'],
                    label=edge.get('label', '')
                )

            # 使用Pyvis渲染
            net = Network(
                height="800px",
                width="100%",
                bgcolor="#ffffff",
                font_color="black"
            )
            net.from_nx(G)

            # 设置物理布局
            net.set_options("""
            {
                "physics": {
                    "forceAtlas2Based": {
                        "gravitationalConstant": -50,
                        "centralGravity": 0.01,
                        "springLength": 200,
                        "springConstant": 0.08
                    },
                    "maxVelocity": 50,
                    "solver": "forceAtlas2Based",
                    "timestep": 0.35,
                    "stabilization": {"iterations": 150}
                }
            }
            """)

            # 生成HTML
            html = net.generate_html()

            return html
        except Exception as e:
            logger.error(f"❌ NetworkX知识图谱生成失败: {e}")
            return None

    # ========== WordCloud ==========

    def generate_wordcloud(
        self,
        text: str = None,
        word_freq: Dict[str, float] = None,
        width: int = 800,
        height: int = 600,
        background_color: str = 'white',
        colormap: str = 'viridis',
        font_path: Optional[str] = None
    ) -> Optional[str]:
        """
        生成词云图

        Args:
            text: 原始文本（二选一）
            word_freq: 词频字典（二选一）
            width: 宽度
            height: 高度
            background_color: 背景色
            colormap: 颜色映射
            font_path: 中文字体路径（支持中文必需）

        Returns:
            Base64编码的PNG图片
        """
        wc_tools = self._get_wordcloud()
        if not wc_tools:
            return None

        try:
            WordCloud = wc_tools['WordCloud']
            plt = wc_tools['plt']

            # 配置词云
            wc_config = {
                'width': width,
                'height': height,
                'background_color': background_color,
                'colormap': colormap,
                'relative_scaling': 0.5,
                'min_font_size': 10
            }

            # 如果提供中文字体路径
            if font_path:
                wc_config['font_path'] = font_path

            wc = WordCloud(**wc_config)

            # 生成词云
            if word_freq:
                wc.generate_from_frequencies(word_freq)
            elif text:
                wc.generate(text)
            else:
                logger.error("❌ 必须提供text或word_freq")
                return None

            # 渲染到图像
            fig, ax = plt.subplots(figsize=(width/100, height/100))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            plt.tight_layout(pad=0)

            # 转换为Base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            plt.close(fig)
            buffer.seek(0)

            img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            logger.error(f"❌ 词云生成失败: {e}")
            return None

    # ========== 高级功能 ==========

    def create_document_stats_viz(
        self,
        doc_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        为文档统计创建综合可视化

        Args:
            doc_stats: 文档统计数据

        Returns:
            包含多种图表的字典
        """
        result = {}

        # 1. 词频分布 - 柱状图
        if 'word_freq' in doc_stats and doc_stats['word_freq']:
            top_words = sorted(
                doc_stats['word_freq'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]

            bar_html = self.plotly_bar_chart(
                data={
                    'words': [w[0] for w in top_words],
                    'freq': [w[1] for w in top_words]
                },
                x_key='words',
                y_key='freq',
                title='Top 20 Word Frequency'
            )
            if bar_html:
                result['word_freq_bar'] = bar_html

        # 2. 词云图
        if 'word_freq' in doc_stats and doc_stats['word_freq']:
            wordcloud_img = self.generate_wordcloud(
                word_freq=doc_stats['word_freq']
            )
            if wordcloud_img:
                result['wordcloud'] = wordcloud_img

        # 3. 实体分布 - 饼图
        if 'entities' in doc_stats and doc_stats['entities']:
            entity_type_count = {}
            for entity in doc_stats['entities']:
                etype = entity.get('type', 'Unknown')
                entity_type_count[etype] = entity_type_count.get(etype, 0) + 1

            pie_data = list(entity_type_count.items())
            pie_html = self.pyecharts_pie_chart(
                data=pie_data,
                title='实体类型分布'
            )
            if pie_html:
                result['entity_pie'] = pie_html

        return result

    def create_knowledge_graph_viz(
        self,
        kg_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        为知识图谱数据创建可视化

        Args:
            kg_data: 知识图谱数据 {'nodes': [...], 'edges': [...]}

        Returns:
            HTML字符串
        """
        if 'nodes' not in kg_data or 'edges' not in kg_data:
            return None

        # 优先使用NetworkX+Pyvis（更交互）
        html = self.networkx_knowledge_graph(
            nodes=kg_data['nodes'],
            edges=kg_data['edges'],
            title='Knowledge Graph'
        )

        # 如果失败，尝试pyecharts
        if not html and self.enable_pyecharts:
            # 转换格式
            pyecharts_nodes = [
                {
                    'name': node['id'],
                    'symbolSize': node.get('size', 20),
                    'category': node.get('group', 0)
                }
                for node in kg_data['nodes']
            ]

            pyecharts_links = [
                {
                    'source': edge['source'],
                    'target': edge['target'],
                    'value': edge.get('label', '')
                }
                for edge in kg_data['edges']
            ]

            html = self.pyecharts_graph(
                nodes=pyecharts_nodes,
                links=pyecharts_links,
                title='知识图谱'
            )

        return html






        # WorkflowEngine 集成


        self.use_workflow_engine = use_workflow_engine


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)

def get_visualization_service() -> VisualizationService:
    """获取全局单例可视化服务"""
    global _visualization_service
    if _visualization_service is None:
        _visualization_service = VisualizationService()
    return _visualization_service
