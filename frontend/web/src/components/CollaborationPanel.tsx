/**
 * CollaborationPanel - 协作与权限管理面板
 *
 * 功能：
 * 1. 成员列表显示（角色、加入时间）
 * 2. 添加/移除成员
 * 3. 角色分配与修改（OWNER, ADMIN, EDITOR, VIEWER）
 * 4. 生成邀请链接
 * 5. 活动日志查看
 * 6. 权限检查
 */

import React, { useEffect, useState } from 'react';
import axios from 'axios';

enum ProjectRole {
  OWNER = 'OWNER',
  ADMIN = 'ADMIN',
  EDITOR = 'EDITOR',
  VIEWER = 'VIEWER'
}

interface Member {
  user_id: number;
  username: string;
  email: string;
  role: ProjectRole;
  joined_at: string;
}

interface InviteLink {
  invite_code: string;
  invite_url: string;
  role: ProjectRole;
  expires_at: string;
}

interface ActivityLog {
  id: number;
  user_id: number;
  username: string;
  action: string;
  target_type: string;
  target_id?: number;
  details?: any;
  created_at: string;
}

interface CollaborationPanelProps {
  projectId: number;
  currentUserId: number;
  currentUserRole: ProjectRole;
}

const CollaborationPanel: React.FC<CollaborationPanelProps> = ({
  projectId,
  currentUserId,
  currentUserRole
}) => {
  const [members, setMembers] = useState<Member[]>([]);
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'members' | 'activity'>('members');
  const [inviteLink, setInviteLink] = useState<InviteLink | null>(null);
  const [inviteRole, setInviteRole] = useState<ProjectRole>(ProjectRole.VIEWER);
  const [showInviteModal, setShowInviteModal] = useState(false);

  // 角色权限映射
  const rolePermissions: Record<ProjectRole, string[]> = {
    [ProjectRole.OWNER]: ['删除项目', '管理成员', '上传文档', '编辑分析', '查看内容'],
    [ProjectRole.ADMIN]: ['管理成员', '上传文档', '编辑分析', '查看内容'],
    [ProjectRole.EDITOR]: ['上传文档', '编辑分析', '查看内容'],
    [ProjectRole.VIEWER]: ['查看内容']
  };

  // 角色颜色
  const roleColors: Record<ProjectRole, string> = {
    [ProjectRole.OWNER]: '#e74c3c',
    [ProjectRole.ADMIN]: '#3498db',
    [ProjectRole.EDITOR]: '#27ae60',
    [ProjectRole.VIEWER]: '#95a5a6'
  };

  // 角色中文名
  const roleNames: Record<ProjectRole, string> = {
    [ProjectRole.OWNER]: '所有者',
    [ProjectRole.ADMIN]: '管理员',
    [ProjectRole.EDITOR]: '编辑者',
    [ProjectRole.VIEWER]: '查看者'
  };

  // 加载成员列表
  const loadMembers = async () => {
    try {
      const response = await axios.get(`/api/v1/collaboration/projects/${projectId}/members`);
      setMembers(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载成员列表失败');
    }
  };

  // 加载活动日志
  const loadActivityLogs = async () => {
    try {
      const response = await axios.get(`/api/v1/collaboration/projects/${projectId}/activity`, {
        params: { limit: 50 }
      });
      setActivityLogs(response.data);
    } catch (err: any) {
      console.error('加载活动日志失败:', err);
    }
  };

  // 初始加载
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await loadMembers();
      await loadActivityLogs();
      setLoading(false);
    };
    load();
  }, [projectId]);

  // 生成邀请链接
  const generateInvite = async () => {
    try {
      const response = await axios.post(`/api/v1/collaboration/projects/${projectId}/invite`, {
        role: inviteRole,
        expires_in_hours: 24
      });
      setInviteLink(response.data);
      setShowInviteModal(true);
    } catch (err: any) {
      alert(err.response?.data?.detail || '生成邀请链接失败');
    }
  };

  // 修改成员角色
  const changeMemberRole = async (userId: number, newRole: ProjectRole) => {
    if (!confirm(`确定要将该成员角色修改为 ${roleNames[newRole]} 吗？`)) {
      return;
    }

    try {
      await axios.put(`/api/v1/collaboration/projects/${projectId}/members/${userId}/role`, {
        new_role: newRole
      });
      await loadMembers();
      await loadActivityLogs();
    } catch (err: any) {
      alert(err.response?.data?.detail || '修改角色失败');
    }
  };

  // 移除成员
  const removeMember = async (userId: number) => {
    if (!confirm('确定要移除该成员吗？')) {
      return;
    }

    try {
      await axios.delete(`/api/v1/collaboration/projects/${projectId}/members/${userId}`);
      await loadMembers();
      await loadActivityLogs();
    } catch (err: any) {
      alert(err.response?.data?.detail || '移除成员失败');
    }
  };

  // 复制邀请链接
  const copyInviteLink = () => {
    if (inviteLink) {
      navigator.clipboard.writeText(inviteLink.invite_url);
      alert('邀请链接已复制到剪贴板');
    }
  };

  // 检查当前用户权限
  const canManageMembers = currentUserRole === ProjectRole.OWNER || currentUserRole === ProjectRole.ADMIN;

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <div>加载中...</div>
      </div>
    );
  }

  return (
    <div className="collaboration-panel" style={{ padding: '20px' }}>
      {/* 标题栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>👥 协作与权限</h2>
        {canManageMembers && (
          <button
            onClick={generateInvite}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3498db',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            ➕ 邀请成员
          </button>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#fadbd8',
          color: '#c0392b',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          ❌ {error}
        </div>
      )}

      {/* 标签页 */}
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #ecf0f1' }}>
        <button
          onClick={() => setActiveTab('members')}
          style={{
            padding: '10px 20px',
            backgroundColor: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'members' ? '3px solid #3498db' : 'none',
            cursor: 'pointer',
            fontWeight: activeTab === 'members' ? 'bold' : 'normal',
            color: activeTab === 'members' ? '#3498db' : '#7f8c8d'
          }}
        >
          成员管理
        </button>
        <button
          onClick={() => setActiveTab('activity')}
          style={{
            padding: '10px 20px',
            backgroundColor: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'activity' ? '3px solid #3498db' : 'none',
            cursor: 'pointer',
            fontWeight: activeTab === 'activity' ? 'bold' : 'normal',
            color: activeTab === 'activity' ? '#3498db' : '#7f8c8d',
            marginLeft: '10px'
          }}
        >
          活动日志
        </button>
      </div>

      {/* 成员管理标签页 */}
      {activeTab === 'members' && (
        <div>
          {/* 成员统计 */}
          <div style={{
            backgroundColor: '#e8f8f5',
            padding: '15px',
            borderRadius: '4px',
            marginBottom: '20px'
          }}>
            <strong>项目共有 {members.length} 位成员</strong>
          </div>

          {/* 成员列表 */}
          <div style={{
            backgroundColor: '#fff',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            overflow: 'hidden'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #ecf0f1' }}>
                  <th style={{ padding: '15px', textAlign: 'left' }}>成员</th>
                  <th style={{ padding: '15px', textAlign: 'left' }}>角色</th>
                  <th style={{ padding: '15px', textAlign: 'left' }}>权限</th>
                  <th style={{ padding: '15px', textAlign: 'left' }}>加入时间</th>
                  {canManageMembers && (
                    <th style={{ padding: '15px', textAlign: 'center' }}>操作</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {members.map((member) => (
                  <tr key={member.user_id} style={{ borderBottom: '1px solid #ecf0f1' }}>
                    <td style={{ padding: '15px' }}>
                      <div>
                        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                          {member.username}
                          {member.user_id === currentUserId && (
                            <span style={{
                              marginLeft: '8px',
                              padding: '2px 6px',
                              backgroundColor: '#3498db',
                              color: '#fff',
                              borderRadius: '4px',
                              fontSize: '10px'
                            }}>
                              我
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '12px', color: '#95a5a6' }}>
                          {member.email}
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '15px' }}>
                      <span style={{
                        padding: '6px 12px',
                        backgroundColor: roleColors[member.role],
                        color: '#fff',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 'bold'
                      }}>
                        {roleNames[member.role]}
                      </span>
                    </td>
                    <td style={{ padding: '15px' }}>
                      <div style={{ fontSize: '12px', color: '#7f8c8d' }}>
                        {rolePermissions[member.role].join('、')}
                      </div>
                    </td>
                    <td style={{ padding: '15px', fontSize: '12px', color: '#7f8c8d' }}>
                      {new Date(member.joined_at).toLocaleDateString('zh-CN')}
                    </td>
                    {canManageMembers && (
                      <td style={{ padding: '15px', textAlign: 'center' }}>
                        {member.user_id !== currentUserId && member.role !== ProjectRole.OWNER && (
                          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                            <select
                              value={member.role}
                              onChange={(e) => changeMemberRole(member.user_id, e.target.value as ProjectRole)}
                              style={{
                                padding: '4px 8px',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                fontSize: '12px'
                              }}
                            >
                              {Object.values(ProjectRole)
                                .filter(role => role !== ProjectRole.OWNER)
                                .map(role => (
                                  <option key={role} value={role}>
                                    {roleNames[role]}
                                  </option>
                                ))}
                            </select>
                            <button
                              onClick={() => removeMember(member.user_id)}
                              style={{
                                padding: '4px 8px',
                                backgroundColor: '#e74c3c',
                                color: '#fff',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '12px'
                              }}
                            >
                              移除
                            </button>
                          </div>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 角色说明 */}
          <div style={{
            marginTop: '20px',
            padding: '20px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px'
          }}>
            <h4 style={{ marginBottom: '15px' }}>角色权限说明</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px' }}>
              {Object.entries(rolePermissions).map(([role, permissions]) => (
                <div key={role}>
                  <div style={{
                    padding: '6px 12px',
                    backgroundColor: roleColors[role as ProjectRole],
                    color: '#fff',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    marginBottom: '8px',
                    display: 'inline-block'
                  }}>
                    {roleNames[role as ProjectRole]}
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#7f8c8d' }}>
                    {permissions.map((perm, idx) => (
                      <li key={idx}>{perm}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 活动日志标签页 */}
      {activeTab === 'activity' && (
        <div>
          {activityLogs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '50px', color: '#95a5a6' }}>
              暂无活动记录
            </div>
          ) : (
            <div style={{
              backgroundColor: '#fff',
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              {activityLogs.map((log) => (
                <div
                  key={log.id}
                  style={{
                    padding: '15px 20px',
                    borderBottom: '1px solid #ecf0f1',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '15px'
                  }}
                >
                  <div style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#3498db',
                    marginTop: '6px',
                    flexShrink: 0
                  }}></div>
                  <div style={{ flex: 1 }}>
                    <div style={{ marginBottom: '5px' }}>
                      <span style={{ fontWeight: 'bold', color: '#2c3e50' }}>
                        {log.username}
                      </span>
                      <span style={{ marginLeft: '8px', color: '#7f8c8d' }}>
                        {log.action}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#95a5a6' }}>
                      {new Date(log.created_at).toLocaleString('zh-CN')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 邀请链接模态框 */}
      {showInviteModal && inviteLink && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
          onClick={() => setShowInviteModal(false)}
        >
          <div
            style={{
              backgroundColor: '#fff',
              padding: '30px',
              borderRadius: '8px',
              maxWidth: '500px',
              width: '100%',
              boxShadow: '0 4px 16px rgba(0,0,0,0.2)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginBottom: '20px' }}>邀请链接已生成</h3>

            <div style={{ marginBottom: '15px' }}>
              <div style={{ fontSize: '12px', color: '#7f8c8d', marginBottom: '5px' }}>
                角色：
                <span style={{
                  marginLeft: '5px',
                  padding: '4px 8px',
                  backgroundColor: roleColors[inviteLink.role],
                  color: '#fff',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}>
                  {roleNames[inviteLink.role]}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#7f8c8d' }}>
                有效期至：{new Date(inviteLink.expires_at).toLocaleString('zh-CN')}
              </div>
            </div>

            <div style={{
              padding: '15px',
              backgroundColor: '#f8f9fa',
              borderRadius: '4px',
              wordBreak: 'break-all',
              marginBottom: '15px',
              fontSize: '14px'
            }}>
              {inviteLink.invite_url}
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={copyInviteLink}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#27ae60',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                📋 复制链接
              </button>
              <button
                onClick={() => setShowInviteModal(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#95a5a6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CollaborationPanel;
