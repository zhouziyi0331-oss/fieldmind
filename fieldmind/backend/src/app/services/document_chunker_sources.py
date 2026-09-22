"""
DocumentChunker 的 sources 处理扩展

这个文件包含处理结构化数据源（sources）的方法
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def chunk_with_sources(
    text: str,
    metadata: Dict[str, Any],
    sources: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    使用 sources 进行结构化切块 ⭐⭐⭐ 核心方法

    适用于：
    - 表格数据（按行或按工作表切块）
    - 音频数据（按 segment 切块）
    - 其他结构化数据

    Args:
        text: 文档文本（用于生成 chunk ID）
        metadata: 元数据
        sources: 结构化数据源

    Returns:
        结构化的 chunks
    """
    logger.info(f"📊 开始结构化切块，sources 数量: {len(sources)}")

    chunks = []

    # 判断数据类型（表格 vs 音频）
    if sources and sources[0].get('source', {}).get('sheet'):
        # 表格数据：按工作表分组
        logger.info("   类型：表格数据")
        chunks = chunk_table_sources(sources, metadata)
    elif sources and sources[0].get('source', {}).get('start'):
        # 音频数据：按 segment 切块
        logger.info("   类型：音频数据")
        chunks = chunk_audio_sources(sources, metadata)
    else:
        # 未知类型：使用通用切块
        logger.info("   类型：通用")
        chunks = chunk_generic_sources(sources, metadata)

    # 添加 chunk 间的链接
    chunks = add_chunk_links(chunks)

    logger.info(f"✅ 结构化切块完成，生成 {len(chunks)} 个 chunks")

    return chunks


def chunk_table_sources(
    sources: List[Dict[str, Any]],
    metadata: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    表格数据切块 ⭐⭐⭐

    策略：按工作表分组，每个工作表一个或多个 chunk
    """
    chunks = []
    chunks_by_sheet = {}

    # 按工作表分组
    for source in sources:
        sentence = source.get('sentence', '')
        source_meta = source.get('source', {})
        sheet_name = source_meta.get('sheet', 'Sheet1')

        if sheet_name not in chunks_by_sheet:
            chunks_by_sheet[sheet_name] = {
                'texts': [],
                'rows': [],
                'row_range': [9999, 0]  # [min, max]
            }

        chunks_by_sheet[sheet_name]['texts'].append(sentence)

        # 收集行数据
        row_data = source_meta.get('row_data')
        if row_data:
            chunks_by_sheet[sheet_name]['rows'].append(row_data)

            # 更新行范围
            row_num = row_data.get('row', 0)
            if row_num > 0:
                chunks_by_sheet[sheet_name]['row_range'][0] = min(
                    chunks_by_sheet[sheet_name]['row_range'][0], row_num
                )
                chunks_by_sheet[sheet_name]['row_range'][1] = max(
                    chunks_by_sheet[sheet_name]['row_range'][1], row_num
                )

    # 为每个工作表创建 chunk
    chunk_index = 0
    for sheet_name, sheet_data in chunks_by_sheet.items():
        chunk_text = '\n'.join(sheet_data['texts'])

        # 构建结构化数据
        structured_data = {
            'sheet_name': sheet_name,
            'row_count': len(sheet_data['rows']),
            'rows': sheet_data['rows'],  # ⭐⭐⭐ 完整的行数据
            'data_types': infer_column_types(sheet_data['rows'])
        }

        # 行范围
        row_range = sheet_data['row_range']
        if row_range[0] <= row_range[1]:
            row_range_str = f"{row_range[0]}-{row_range[1]}"
        else:
            row_range_str = "unknown"

        chunk = {
            'chunk_id': f"chunk_{chunk_index:03d}",
            'text': chunk_text,
            'metadata': {
                **metadata,
                'chunk_type': 'table_sheet',
                'is_table': True,
                'sheet_name': sheet_name,
                'row_range': row_range_str,
                'structured_data': structured_data,  # ⭐⭐⭐ 保存结构化数据
                'start_pos': 0,
                'end_pos': len(chunk_text)
            }
        }

        chunks.append(chunk)
        chunk_index += 1

    return chunks


def infer_column_types(rows: List[Dict[str, Any]]) -> Dict[int, str]:
    """推断列的数据类型"""
    if not rows:
        return {}

    column_types = {}

    # 采样前10行
    sample_rows = rows[:10]

    for row in sample_rows:
        cells = row.get('cells', [])

        for col_idx, cell in enumerate(cells):
            cell_type = cell.get('type', 'string')

            if col_idx not in column_types:
                column_types[col_idx] = {}

            if cell_type not in column_types[col_idx]:
                column_types[col_idx][cell_type] = 0

            column_types[col_idx][cell_type] += 1

    # 选择出现最多的类型
    result = {}
    for col_idx, type_counts in column_types.items():
        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]
        result[col_idx] = dominant_type

    return result


def chunk_audio_sources(
    sources: List[Dict[str, Any]],
    metadata: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    音频数据切块

    策略：每个 segment 一个 chunk
    """
    chunks = []

    for i, source in enumerate(sources):
        sentence = source.get('sentence', '')
        source_meta = source.get('source', {})

        chunk = {
            'chunk_id': f"chunk_{i:03d}",
            'text': sentence,
            'metadata': {
                **metadata,
                'chunk_type': 'audio_segment',
                'start_sec': source_meta.get('start'),
                'end_sec': source_meta.get('end'),
                'speaker': source_meta.get('speaker'),
                'start_pos': 0,
                'end_pos': len(sentence)
            }
        }

        chunks.append(chunk)

    return chunks


def chunk_generic_sources(
    sources: List[Dict[str, Any]],
    metadata: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    通用数据切块

    策略：每个 source 一个 chunk
    """
    chunks = []

    for i, source in enumerate(sources):
        sentence = source.get('sentence', '')

        chunk = {
            'chunk_id': f"chunk_{i:03d}",
            'text': sentence,
            'metadata': {
                **metadata,
                'chunk_type': 'generic',
                'start_pos': 0,
                'end_pos': len(sentence),
                'source': source.get('source', {})
            }
        }

        chunks.append(chunk)

    return chunks


def add_chunk_links(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """添加 chunk 之间的链接关系"""
    for i, chunk in enumerate(chunks):
        if i > 0:
            chunk['prev_chunk_id'] = chunks[i - 1]['chunk_id']
        if i < len(chunks) - 1:
            chunk['next_chunk_id'] = chunks[i + 1]['chunk_id']

    return chunks
