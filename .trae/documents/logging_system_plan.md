# 统一日志系统 - 实施计划

## 概述
为整个aiagents-stock项目建立统一的日志系统，所有日志输出到项目根目录 `log/app.log` 文件中。

## [ ] 任务1: 创建统一的日志配置模块
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 `utils/` 目录下创建 `logger.py` 模块
  - 配置日志格式：时间戳 | 日志级别 | 模块名 | 消息
  - 同时输出到控制台和文件 `log/app.log`
  - 自动创建 `log` 目录
  - 配置日志轮转（按大小或日期）
- **Success Criteria**:
  - 日志模块可正常导入和使用
  - 日志同时输出到控制台和文件
  - 日志目录自动创建
- **Test Requirements**:
  - `programmatic` TR-1.1: 可以导入 logger 模块
  - `programmatic` TR-1.2: 可以获取 logger 实例
  - `programmatic` TR-1.3: log/app.log 文件被创建
  - `human-judgement` TR-1.4: 日志格式清晰易读

## [ ] 任务2: 更新 app.py 使用统一日志
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 
  - 在 app.py 顶部导入并初始化统一日志系统
  - 为关键操作添加日志记录（页面加载、API调用、错误等）
- **Success Criteria**:
  - app.py 使用统一日志系统
  - 关键操作有日志记录
- **Test Requirements**:
  - `programmatic` TR-2.1: app.py 导入 logger 模块
  - `programmatic` TR-2.2: 关键操作有日志输出

## [ ] 任务3: 更新 config 模块使用统一日志
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 更新 config/ 目录下所有模块使用统一日志
  - 移除重复的 logging.basicConfig 配置
- **Success Criteria**:
  - config 模块使用统一日志
  - 无重复配置
- **Test Requirements**:
  - `programmatic` TR-3.1: config 模块导入统一 logger
  - `programmatic` TR-3.2: 移除重复的 basicConfig

## [ ] 任务4: 更新 data 模块使用统一日志
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 更新 data/ 目录下所有模块使用统一日志
  - 移除重复的 logging.basicConfig 配置
  - 为数据获取操作添加关键日志
- **Success Criteria**:
  - data 模块使用统一日志
  - 数据操作有日志记录
- **Test Requirements**:
  - `programmatic` TR-4.1: data 模块导入统一 logger
  - `programmatic` TR-4.2: 数据操作有日志输出

## [ ] 任务5: 更新 db 模块使用统一日志
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 更新 db/ 目录下所有模块使用统一日志
  - 移除重复的 logging.basicConfig 配置
  - 为数据库操作添加关键日志
- **Success Criteria**:
  - db 模块使用统一日志
  - 数据库操作有日志记录
- **Test Requirements**:
  - `programmatic` TR-5.1: db 模块导入统一 logger
  - `programmatic` TR-5.2: 数据库操作有日志输出

## [ ] 任务6: 更新 agents 模块使用统一日志
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 更新 agents/ 目录下所有模块使用统一日志
  - 移除重复的 logging.basicConfig 配置
  - 为AI调用添加关键日志
- **Success Criteria**:
  - agents 模块使用统一日志
  - AI调用有日志记录
- **Test Requirements**:
  - `programmatic` TR-6.1: agents 模块导入统一 logger
  - `programmatic` TR-6.2: AI调用有日志输出

## [ ] 任务7: 更新 services 模块使用统一日志
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 更新 services/ 目录下所有模块使用统一日志
  - 移除重复的 logging.basicConfig 配置
  - 为服务操作添加关键日志
- **Success Criteria**:
  - services 模块使用统一日志
  - 服务操作有日志记录
- **Test Requirements**:
  - `programmatic` TR-7.1: services 模块导入统一 logger
  - `programmatic` TR-7.2: 服务操作有日志输出

## [ ] 任务8: 更新 strategies 模块使用统一日志
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 更新 strategies/ 目录下所有模块使用统一日志
  - 移除重复的 logging.basicConfig 配置
  - 为策略操作添加关键日志
- **Success Criteria**:
  - strategies 模块使用统一日志
  - 策略操作有日志记录
- **Test Requirements**:
  - `programmatic` TR-8.1: strategies 模块导入统一 logger
  - `programmatic` TR-8.2: 策略操作有日志输出

## [ ] 任务9: 更新 ui 模块使用统一日志
- **Priority**: P2
- **Depends On**: 任务1
- **Description**:
  - 更新 ui/ 目录下所有模块使用统一日志
  - 移除重复的 logging.basicConfig 配置
  - 为UI交互添加关键日志
- **Success Criteria**:
  - ui 模块使用统一日志
  - UI交互有日志记录
- **Test Requirements**:
  - `programmatic` TR-9.1: ui 模块导入统一 logger
  - `programmatic` TR-9.2: UI交互有日志输出

## [ ] 任务10: 更新 utils 模块使用统一日志
- **Priority**: P2
- **Depends On**: 任务1
- **Description**:
  - 更新 utils/ 目录下其他模块使用统一日志
  - 移除重复的 logging.basicConfig 配置
  - 为工具操作添加关键日志
- **Success Criteria**:
  - utils 模块使用统一日志
  - 工具操作有日志记录
- **Test Requirements**:
  - `programmatic` TR-10.1: utils 模块导入统一 logger
  - `programmatic` TR-10.2: 工具操作有日志输出

## [ ] 任务11: 验证完整日志系统
- **Priority**: P0
- **Depends On**: 任务1-10
- **Description**:
  - 启动应用验证日志系统工作正常
  - 检查 log/app.log 文件内容
  - 验证所有模块正常工作
- **Success Criteria**:
  - 日志系统完整工作
  - 所有模块正常运行
- **Test Requirements**:
  - `programmatic` TR-11.1: 应用正常启动
  - `programmatic` TR-11.2: log/app.log 有内容
  - `programmatic` TR-11.3: 无日志相关错误
  - `human-judgement` TR-11.4: 日志格式统一规范
