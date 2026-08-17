import { NavLink } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import {
  LayoutDashboard,
  Upload,
  Key,
  Store,
  BarChart3,
  Brain,
  Zap,
  Plus
} from 'lucide-react';

const Sidebar = () => {
  const { projects, currentProject, selectProject, createProject } = useProjectStore();

  const handleNewProject = () => {
    const name = prompt('请输入项目名称：');
    if (name) {
      createProject(name);
    }
  };

  const navItems = [
    { path: '/overview', icon: LayoutDashboard, label: '概览' },
    { path: '/materials', icon: Upload, label: '材料导入' },
    { path: '/keywords', icon: Key, label: '关键词解锁' },
    { path: '/business', icon: Store, label: '在地业态分析' },
    { path: '/visualization', icon: BarChart3, label: '可视化看板' },
    { path: '/thinking', icon: Brain, label: '思维模型' },
    { path: '/skills', icon: Zap, label: 'Skill生态' },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <div className="logo-icon">
            <Brain size={20} />
          </div>
          <span>FieldMind</span>
        </div>
        <div className="project-selector">
          <select
            className="project-select"
            value={currentProject?.id || ''}
            onChange={(e) => selectProject(e.target.value)}
          >
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
          <button className="new-project-btn" onClick={handleNewProject}>
            <Plus size={14} style={{ display: 'inline', marginRight: '4px' }} />
            新建项目
          </button>
        </div>
      </div>

      <nav className="nav-menu">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon className="nav-icon" size={20} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
};

export default Sidebar;
