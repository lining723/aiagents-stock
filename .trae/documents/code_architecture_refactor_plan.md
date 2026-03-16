# 代码架构重构计划

## 当前问题
当前项目所有文件都位于根目录，存在以下问题：
- 文件数量过多（70+个Python文件），难以管理
- 不同功能模块混杂在一起
- 缺乏清晰的目录结构
- 导入路径不清晰

## 重构目标
建立清晰的分层架构，提高代码可维护性和可读性。

---

## [ ] 任务 1: 创建新的目录结构
- **Priority**: P0
- **Depends On**: None
- **Description**: 创建以下目录结构
  - `ui/` - 所有UI组件
  - `data/` - 数据获取模块
  - `agents/` - AI智能体
  - `db/` - 数据库模块
  - `services/` - 服务层（监控、通知等）
  - `utils/` - 工具类（PDF生成等）
  - `config/` - 配置管理
- **Success Criteria**: 目录结构创建完成
- **Test Requirements**:
  - `programmatic` TR-1.1: 所有目标目录存在
- **Notes**: 使用 `mkdir -p` 创建目录

---

## [ ] 任务 2: 移动UI组件到ui/目录
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 移动以下文件到 `ui/`
  - `*_ui.py` 文件
  - `app.py` (保留在根目录作为入口)
- **Success Criteria**: 所有UI文件移动完成
- **Test Requirements**:
  - `programmatic` TR-2.1: UI文件在ui/目录中
- **Notes**: 保持文件名不变

---

## [ ] 任务 3: 移动数据模块到data/目录
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 移动以下文件到 `data/`
  - `stock_data.py`
  - `*_data.py` 文件
  - `fund_flow_akshare.py`
  - `market_sentiment_data.py`
  - `news_announcement_data.py`
  - `qstock_news_data.py`
  - `quarterly_report_data.py`
  - `risk_data_fetcher.py`
- **Success Criteria**: 所有数据文件移动完成
- **Test Requirements**:
  - `programmatic` TR-3.1: 数据文件在data/目录中

---

## [ ] 任务 4: 移动AI智能体到agents/目录
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 移动以下文件到 `agents/`
  - `ai_agents.py`
  - `*_agents.py` 文件
  - `deepseek_client.py`
- **Success Criteria**: 所有智能体文件移动完成
- **Test Requirements**:
  - `programmatic` TR-4.1: 智能体文件在agents/目录中

---

## [ ] 任务 5: 移动数据库模块到db/目录
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 移动以下文件到 `db/`
  - `database.py`
  - `*_db.py` 文件
- **Success Criteria**: 所有数据库文件移动完成
- **Test Requirements**:
  - `programmatic` TR-5.1: 数据库文件在db/目录中

---

## [ ] 任务 6: 移动监控服务到services/目录
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 移动以下文件到 `services/`
  - `monitor_service.py`
  - `monitor_manager.py`
  - `monitor_scheduler.py`
  - `notification_service.py`
  - `*_scheduler.py` 文件
  - `*_service.py` 文件
  - `*_engine.py` 文件
- **Success Criteria**: 所有服务文件移动完成
- **Test Requirements**:
  - `programmatic` TR-6.1: 服务文件在services/目录中

---

## [ ] 任务 7: 移动PDF生成到utils/目录
- **Priority**: P1
- **Depends On**: 任务1
- **Description**: 移动以下文件到 `utils/`
  - `pdf_generator.py`
  - `pdf_generator_fixed.py`
  - `pdf_generator_pandoc.py`
  - `*_pdf.py` 文件
  - `*_scoring.py` 文件
- **Success Criteria**: 所有工具文件移动完成
- **Test Requirements**:
  - `programmatic` TR-7.1: 工具文件在utils/目录中

---

## [ ] 任务 8: 移动配置到config/目录
- **Priority**: P1
- **Depends On**: 任务1
- **Description**: 移动以下文件到 `config/`
  - `config.py`
  - `config_manager.py`
  - `model_config.py`
  - `data_source_manager.py`
- **Success Criteria**: 配置文件移动完成
- **Test Requirements**:
  - `programmatic` TR-8.1: 配置文件在config/目录中

---

## [ ] 任务 9: 创建__init__.py文件
- **Priority**: P0
- **Depends On**: 任务2-8
- **Description**: 在每个子目录中创建 `__init__.py`，导出公共API
- **Success Criteria**: 所有__init__.py文件创建完成
- **Test Requirements**:
  - `programmatic` TR-9.1: 每个目录都有__init__.py

---

## [ ] 任务 10: 更新import语句
- **Priority**: P0
- **Depends On**: 任务9
- **Description**: 更新所有文件中的import语句以反映新的目录结构
- **Success Criteria**: 所有import语句更新完成
- **Test Requirements**:
  - `programmatic` TR-10.1: 应用可以正常启动
  - `human-judgement` TR-10.2: 没有导入错误

---

## [ ] 任务 11: 测试重构后的应用
- **Priority**: P0
- **Depends On**: 任务10
- **Description**: 运行应用并测试主要功能
- **Success Criteria**: 应用功能正常
- **Test Requirements**:
  - `programmatic` TR-11.1: 应用启动成功
  - `programmatic` TR-11.2: 主要页面可以访问
  - `human-judgement` TR-11.3: 功能正常工作

---

## 最终目录结构

```
aiagents-stock/
├── app.py                          # 主入口
├── run.py                          # 启动脚本
├── config/                         # 配置模块
│   ├── __init__.py
│   ├── config.py
│   ├── config_manager.py
│   ├── model_config.py
│   └── data_source_manager.py
├── ui/                             # UI组件
│   ├── __init__.py
│   ├── *_ui.py
│   └── ...
├── data/                           # 数据模块
│   ├── __init__.py
│   ├── stock_data.py
│   ├── *_data.py
│   └── ...
├── agents/                         # AI智能体
│   ├── __init__.py
│   ├── ai_agents.py
│   ├── *_agents.py
│   └── deepseek_client.py
├── db/                             # 数据库
│   ├── __init__.py
│   ├── database.py
│   └── *_db.py
├── services/                       # 服务层
│   ├── __init__.py
│   ├── monitor_service.py
│   ├── notification_service.py
│   ├── *_engine.py
│   ├── *_scheduler.py
│   └── ...
├── utils/                          # 工具类
│   ├── __init__.py
│   ├── pdf_generator.py
│   ├── *_pdf.py
│   └── ...
├── strategies/                     # 策略模块 (可选)
│   ├── __init__.py
│   ├── *_selector.py
│   ├── *_strategy.py
│   └── ...
├── requirements.txt
├── Dockerfile
└── ...
```
