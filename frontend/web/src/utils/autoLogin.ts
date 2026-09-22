/**
 * 自动登录工具
 * 用于开发环境自动获取token
 */

export async function autoLogin() {
  // 检查是否已有token
  const existingToken = localStorage.getItem('auth_token')
  if (existingToken) {
    console.log('✅ 已有认证token')
    return
  }

  // 自动登录
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'admin',
        password: 'admin123456',
      }),
    })

    const data = await response.json()

    if (data.access_token) {
      localStorage.setItem('auth_token', data.access_token)
      console.log('✅ 自动登录成功')
    } else {
      console.error('❌ 自动登录失败:', data)
    }
  } catch (error) {
    console.error('❌ 自动登录出错:', error)
  }
}
