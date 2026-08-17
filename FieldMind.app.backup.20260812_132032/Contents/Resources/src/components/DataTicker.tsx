import { useEffect, useState } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { Files, MessageSquare, Database, Activity } from 'lucide-react';

const DataTicker = () => {
  const { currentStats } = useProjectStore();
  const [tickerData, setTickerData] = useState<Array<{
    icon: any;
    label: string;
    value: string;
  }>>([]);

  useEffect(() => {
    if (!currentStats) return;

    const data = [
      {
        icon: Files,
        label: '文件总数',
        value: currentStats.files.total.toString(),
      },
      {
        icon: MessageSquare,
        label: '对话数量',
        value: currentStats.conversations.total.toString(),
      },
      {
        icon: Database,
        label: '知识图谱节点',
        value: currentStats.knowledge.graph_nodes.toString(),
      },
      {
        icon: Database,
        label: '向量文档',
        value: currentStats.knowledge.vector_documents.toString(),
      },
      {
        icon: Activity,
        label: '就绪文件',
        value: `${currentStats.files.ready_percentage}%`,
      },
      {
        icon: MessageSquare,
        label: '消息总数',
        value: currentStats.messages.total.toString(),
      },
    ];

    setTickerData([...data, ...data]); // 复制一份用于无缝滚动
  }, [currentStats]);

  if (!tickerData.length) return null;

  return (
    <div className="data-ticker">
      <div className="ticker-content">
        {tickerData.map((item, index) => {
          const Icon = item.icon;
          return (
            <div key={index} className="ticker-item">
              <Icon className="ticker-icon" size={16} />
              <span className="ticker-label">{item.label}:</span>
              <span className="ticker-value">{item.value}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DataTicker;
