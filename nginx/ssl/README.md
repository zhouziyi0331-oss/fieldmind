# SSL 证书配置

## 本地开发（自签名证书）

生成自签名证书用于本地 HTTPS 测试:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/C=CN/ST=State/L=City/O=FieldMind/CN=localhost"
```

## 生产环境（Let's Encrypt）

使用 Certbot 获取免费的 SSL 证书:

```bash
# 安装 Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# 获取证书（替换 yourdomain.com）
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 证书会自动安装到 /etc/letsencrypt/live/yourdomain.com/
# 需要在 nginx 配置中指向这些证书
```

## 证书文件

生产环境需要以下文件:
- `privkey.pem` - 私钥
- `fullchain.pem` - 完整证书链
