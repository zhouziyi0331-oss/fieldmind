import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Search, Clock } from 'lucide-react';

const Topbar = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [searchQuery, setSearchQuery] = useState('');
  const location = useLocation();

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getPageTitle = () => {
    const pathMap: Record<string, string> = {
      '/overview': '概览',
      '/materials': '材料导入',
      '/keywords': '关键词解锁',
      '/business': '在地业态分析',
      '/visualization': '可视化看板',
      '/thinking': '思维模型',
      '/skills': 'Skill生态',
    };
    return pathMap[location.pathname] || 'FieldMind';
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement search functionality
    console.log('Search:', searchQuery);
  };

  return (
    <div className="topbar">
      <div className="topbar-left">
        <h1 className="page-title">{getPageTitle()}</h1>
        <div className="breadcrumb">
          <span>FieldMind</span>
          <span className="breadcrumb-separator">/</span>
          <span>{getPageTitle()}</span>
        </div>
      </div>

      <div className="topbar-right">
        <form className="search-box" onSubmit={handleSearch}>
          <Search className="search-icon" size={18} />
          <input
            type="text"
            className="search-input"
            placeholder="搜索项目、对话、文件..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </form>

        <div className="live-clock">
          <Clock className="clock-icon" size={16} />
          <span>{formatTime(currentTime)}</span>
        </div>
      </div>
    </div>
  );
};

export default Topbar;
