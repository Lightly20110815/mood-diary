# 每日心情记录工具 - Vercel 部署指南

## 架构
- Flask (Python Serverless Function) → Vercel
- 数据库 → Vercel Postgres
- 静态文件 → Vercel CDN

## 1. 推送代码到 GitHub

```bash
cd mood-diary
git init
git add .
git commit -m "init: mood diary app"
git remote add origin https://github.com/你的用户名/mood-diary.git
git push -u origin main
```

## 2. 在 Vercel 创建项目

1. 打开 https://vercel.com → New Project → 导入 GitHub 仓库
2. Framework Preset 选 **Other**
3. 不需要改 Build/Output 设置，`vercel.json` 已配置好

## 3. 创建 Vercel Postgres 数据库

1. Vercel 控制台 → Storage → Create Database → Postgres
2. 创建后进入数据库设置页，环境变量会自动注入到项目中

## 4. 配置环境变量

Vercel → Project → Settings → Environment Variables，添加：

| Key | Value |
|---|---|
| `SECRET_KEY` | 随机字符串（可用 `openssl rand -hex 32` 生成）|
| `ADMIN_PASSWORD` | 你的管理员密码 |

> `POSTGRES_URL` 等数据库连接变量由 Vercel Postgres 自动注入，无需手动添加。

## 5. 部署

Vercel 会自动部署。或在本地：

```bash
npm i -g vercel
vercel
```

## 6. 初始化数据库表

首次部署后需要创建表。两种方式：

### 方式 A：本地连远程库建表

```bash
# 安装依赖
source venv/bin/activate
pip install -r requirements.txt

# 用 Vercel Postgres 的连接串本地运行
# 从 Vercel 控制台复制 POSTGRES_URL
export POSTGRES_URL="postgresql://user:pass@host/db"
python -c "from app import app, db; 
ctx = app.app_context(); ctx.push(); db.create_all(); print('tables created')"
```

### 方式 B：临时加一个初始化路由

在 `app.py` 临时加 `@app.route('/init')` 调用 `db.create_all()`，部署后访问一次 `/init` 再删掉。

## 7. 访问

- 公开页面：`https://你的项目.vercel.app`
- 管理员登录：`https://你的项目.vercel.app/login`
- 密码：你在环境变量中设置的 `ADMIN_PASSWORD`

## 绑定自定义域名

Vercel → Project → Settings → Domains → 添加域名 → 按提示在域名 DNS 添加 CNAME 记录。HTTPS 自动签发。

## 备份

Vercel Postgres 控制台可直接导出，或用 `pg_dump`：

```bash
pg_dump "postgresql://连接串" > backup.sql
```
