# SQLite3 模块缺失问题修复指南

## 问题描述

```
ModuleNotFoundError: No module named '_sqlite3'
```

这个错误发生在 Python 尝试导入 `sqlite3` 模块时，表明当前 Python 环境缺少 SQLite3 支持。

## 问题原因

1. **SQLite 开发库未安装**：系统缺少 `libsqlite3-dev`（Debian/Ubuntu）或 `sqlite-devel`（CentOS/RHEL）包
2. **Python 编译时未包含 SQLite3 支持**：从源代码编译 Python 时没有正确配置 SQLite3
3. **Python 版本问题**：某些 Python 3.13 版本可能存在兼容性问题

## 解决方案（按推荐顺序）

### 方案 1：使用 Docker 部署（最简单，推荐）

项目已经包含完整的 Docker 支持，Docker 环境已经预配置了 SQLite3。

```bash
# 使用部署脚本
./deploy.sh

# 或手动启动
docker-compose up -d --build
```

**优点**：
- 无需配置系统环境
- 一键部署，开箱即用
- 环境隔离，不影响系统

### 方案 2：安装 SQLite 开发库并重新创建虚拟环境

#### 步骤 1：安装 SQLite 开发库

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y libsqlite3-dev
```

**CentOS/RHEL:**
```bash
sudo yum install -y sqlite-devel
```

**Fedora:**
```bash
sudo dnf install -y sqlite-devel
```

**Arch Linux:**
```bash
sudo pacman -S sqlite
```

#### 步骤 2：重新创建虚拟环境

```bash
# 删除旧的虚拟环境
rm -rf venv

# 创建新的虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

#### 步骤 3：验证 SQLite3

```bash
python3 -c "import sqlite3; print('SQLite3 版本:', sqlite3.sqlite_version)"
```

### 方案 3：使用 pyenv 重新安装 Python

如果方案 2 不起作用，可以使用 pyenv 重新安装 Python：

```bash
# 安装 pyenv（如果未安装）
curl https://pyenv.run | bash

# 添加到 shell 配置（~/.bashrc 或 ~/.zshrc）
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# 重新加载配置
source ~/.bashrc

# 重新安装 Python（包含 SQLite3 支持）
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
pyenv uninstall -f "$PYTHON_VERSION"
PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" pyenv install "$PYTHON_VERSION"
```

### 方案 4：使用系统包管理器重新安装 Python

```bash
# Ubuntu/Debian
sudo apt-get install --reinstall python3 python3-dev

# CentOS/RHEL
sudo yum reinstall python3 python3-devel

# Fedora
sudo dnf reinstall python3 python3-devel
```

## 自动化修复脚本

项目提供了自动化修复脚本 `fix_sqlite3_error.sh`：

```bash
# 给脚本执行权限
chmod +x fix_sqlite3_error.sh

# 运行脚本
./fix_sqlite3_error.sh
```

脚本会自动检测你的 Linux 发行版并提供修复选项。

## 预防措施

1. **在新系统上安装 Python 前先安装 SQLite 开发库**
2. **使用 Docker 部署避免环境问题**
3. **使用 pyenv 管理 Python 版本**

## 验证修复

修复完成后，运行以下命令验证：

```bash
# 测试 SQLite3 导入
python3 -c "import sqlite3; print('✓ SQLite3 正常')"

# 测试应用启动
python3 -c "from db.database import Database; print('✓ 数据库模块正常')"
```

## 常见问题

### Q: 为什么 Docker 可以解决这个问题？
A: Docker 镜像已经包含了完整的 SQLite3 支持和所有必要的依赖，无需在宿主机上配置。

### Q: 我可以使用 Python 3.12 代替 3.13 吗？
A: 可以！Python 3.12 通常更稳定且兼容性更好。修改 `requirements.txt` 和 Dockerfile 中的 Python 版本即可。

### Q: 修复后仍然报错怎么办？
A: 尝试完全删除虚拟环境并重新创建，或者直接使用 Docker 部署。
