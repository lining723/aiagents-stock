# AI Agents Stock - 前后端分离版 启动指南

## 项目结构

```
aiagents-stock/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 后端入口
│   ├── api/                    # API 路由
│   ├── core/                   # 核心配置
│   ├── schemas/                # Pydantic 模型
│   └── requirements.txt        # 后端依赖
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/         # 通用组件
│   │   ├── pages/             # 页面组件
│   │   ├── services/          # API 服务
│   │   ├── stores/            # 状态管理
│   │   ├── types/             # TypeScript 类型
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── services/                   # 业务逻辑层（保留）
├── data/                       # 数据获取层（保留）
├── agents/                     # AI 智能体层（保留）
├── strategies/                 # 策略层（保留）
├── db/                         # 数据库层（保留）
├── config/                     # 配置层（保留）
├── utils/                      # 工具层（保留）
└── app.py                      # Streamlit 版本（保留，用于对比）
```

## 前置要求

- Python 3.10+
- Node.js 18+
- npm 或 yarn

## 快速启动

### 1. 启动后端

```bash
# 进入项目根目录
cd /path/to/aiagents-stock

# 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate

# 安装后端依赖
pip install -r backend/requirements.txt

# 安装项目依赖（如果还没安装）
pip install -r requirements.txt

# 启动后端服务
python -m backend.main
```

后端将运行在：http://localhost:8000

API 文档地址：http://localhost:8000/docs

### 2. 启动前端

```bash
# 打开新的终端窗口
cd /path/to/aiagents-stock/frontend

# 安装前端依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在：http://localhost:5173

## 开发说明

### 后端开发

- 添加新的 API 路由：在 `backend/api/v1/` 目录下创建新文件
- 数据模型：在 `backend/schemas/` 目录下定义 Pydantic 模型
- 配置：修改 `backend/core/config.py`

### 前端开发

- 添加新页面：在 `frontend/src/pages/` 目录下创建组件
- 添加新组件：在 `frontend/src/components/` 目录下创建组件
- API 调用：使用 `frontend/src/services/api.ts` 中的函数
- 状态管理：使用 `frontend/src/stores/` 中的 Zustand stores

### 技术栈

#### 后端
- FastAPI - Web 框架
- Uvicorn - ASGI 服务器
- Pydantic - 数据验证
- Pydantic Settings - 配置管理

#### 前端
- React 18 - UI 框架
- TypeScript - 类型安全
- Vite - 构建工具
- Ant Design - UI 组件库
- React Router - 路由
- Zustand - 状态管理
- React Query - 数据获取
- Axios - HTTP 客户端

## 保留 Streamlit 版本

原有的 Streamlit 版本（`app.py`）仍然保留，你可以继续使用：

```bash
streamlit run app.py --server.port 8503
```

## 下一步

基础架构已搭建完成！接下来可以：

1. 在 `backend/api/v1/` 中封装核心业务 API
2. 在 `frontend/src/pages/` 中开发对应页面
3. 更新 Docker 配置以支持前后端分离部署

## 故障排除

### 后端启动失败

确保已安装所有依赖：
```bash
pip install fastapi uvicorn pydantic pydantic-settings python-multipart
```

### 前端启动失败

确保 Node.js 版本 >= 18：
```bash
node --version
```

重新安装依赖：
```bash
rm -rf node_modules package-lock.json
npm install
```

### 前后端连接失败

- 确保后端正在运行（http://localhost:8000）
- 检查前端控制台的网络请求
- 验证 CORS 配置正确
