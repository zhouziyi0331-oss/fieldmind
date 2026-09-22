/**
 * MindMap Demo Page - Demonstration of simple-mind-map integration
 */
import React from 'react'
import MindMapComponent, { MindMapNode } from '../components/MindMapComponent'

const demoData: MindMapNode = {
  data: {
    text: 'FieldMind 研究平台',
  },
  children: [
    {
      data: { text: '文档处理' },
      children: [
        { data: { text: '14种格式支持' } },
        { data: { text: 'MarkItDown转换' } },
        { data: { text: '自动提取记忆' } },
      ],
    },
    {
      data: { text: '知识图谱' },
      children: [
        { data: { text: 'Neo4j存储' } },
        { data: { text: '关系推理' } },
        { data: { text: '可视化展示' } },
      ],
    },
    {
      data: { text: 'RAG引擎' },
      children: [
        { data: { text: 'RAGFlow集成' } },
        { data: { text: '语义搜索' } },
        { data: { text: '智能问答' } },
      ],
    },
    {
      data: { text: '三级记忆' },
      children: [
        { data: { text: '短期记忆' } },
        { data: { text: '中期记忆' } },
        { data: { text: '长期记忆' } },
      ],
    },
  ],
}

export const MindMapDemo: React.FC = () => {
  const handleNodeClick = (node: any) => {
    console.log('节点点击:', node.data?.text)
  }

  const handleNodeDbClick = (node: any) => {
    console.log('节点双击:', node.data?.text)
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">思维导图演示</h1>
        <p className="text-gray-600">
          基于 simple-mind-map 的知识图谱可视化
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <MindMapComponent
          data={demoData}
          height="600px"
          theme="default"
          layout="logicalStructure"
          onNodeClick={handleNodeClick}
          onNodeDbClick={handleNodeDbClick}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">布局</h3>
          <p className="text-sm text-blue-700">logicalStructure - 逻辑结构图</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <h3 className="font-semibold text-green-900 mb-2">主题</h3>
          <p className="text-sm text-green-700">default - 默认主题</p>
        </div>
        <div className="p-4 bg-purple-50 rounded-lg">
          <h3 className="font-semibold text-purple-900 mb-2">交互</h3>
          <p className="text-sm text-purple-700">支持点击和双击事件</p>
        </div>
      </div>
    </div>
  )
}

export default MindMapDemo
