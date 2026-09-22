/**
 * 项目验证 Hook
 * 自动验证项目是否存在，不存在则跳转
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export const useProjectValidation = (projectId: number | null) => {
  const navigate = useNavigate();

  useEffect(() => {
    if (!projectId) {
      return;
    }

    // 验证项目是否存在
    const validateProject = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/projects/${projectId}/`
        );

        if (!response.ok) {
          if (response.status === 404) {
            console.warn(`⚠️ 项目 ${projectId} 不存在，跳转到项目列表`);
            // 清理本地缓存
            localStorage.removeItem('lastProjectId');
            // 跳转到项目列表
            navigate('/projects', { replace: true });
          }
        }
      } catch (error) {
        console.error('验证项目失败:', error);
        // 网络错误时也跳转到安全页面
        navigate('/projects', { replace: true });
      }
    };

    validateProject();
  }, [projectId, navigate]);
};
