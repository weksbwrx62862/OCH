# 修复金融技能问题 - 实施计划

## 问题分析

从错误日志中识别出以下问题：

1. **exec() 语法错误** - 智能体试图直接将 shell 命令作为 Python 代码执行
2. **依赖包未安装** - yfinance, akshare 等金融数据库未安装
3. **Python 环境问题** - PEP 668 外部环境管理要求使用虚拟环境
4. **setuptools 导入错误** - Python 包管理工具问题
5. **apt 权限问题** - 无系统权限安装系统级包

## 实施任务

### [x] 任务 1: 分析问题根源
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 分析所有错误日志
  - 识别问题的根本原因
- **Success Criteria**:
  - 完整理解所有问题
- **Test Requirements**:
  - `programmatic` TR-1.1: 问题分析完成
- **Notes**: 已完成

### [x] 任务 2: 创建 Python 虚拟环境
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 在代理工作区创建独立的 Python 虚拟环境
  - 避免系统级包管理冲突
- **Success Criteria**:
  - 虚拟环境创建成功
  - 可以在虚拟环境中安装包
- **Test Requirements**:
  - `programmatic` TR-2.1: 虚拟环境存在且可激活 ✓
  - `human-judgement` TR-2.2: 验证虚拟环境正常工作 ✓
- **Notes**: 使用 python -m venv 创建

### [x] 任务 3: 安装依赖包
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 在虚拟环境中安装 requirements.txt 中的所有依赖
  - 包括 yfinance, akshare, pandas, numpy 等
- **Success Criteria**:
  - 所有依赖包成功安装
  - 可以导入这些包
- **Test Requirements**:
  - `programmatic` TR-3.1: pip install 成功执行 ✓
  - `programmatic` TR-3.2: 可以 import yfinance 和 akshare ✓
- **Notes**: 使用虚拟环境安装成功

### [x] 任务 4: 修复技能适配器中的路径问题
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 修复 skill_adapter.py 中的硬编码路径
  - 确保使用正确的虚拟环境 Python
- **Success Criteria**:
  - 技能适配器使用正确的 Python 解释器
  - 可以找到并执行技能脚本
- **Test Requirements**:
  - `programmatic` TR-4.1: 技能适配器路径配置正确 ✓
  - `human-judgement` TR-4.2: 验证技能脚本路径正确 ✓
- **Notes**: 使用动态路径检测

### [x] 任务 5: 测试技能
- **Priority**: P1
- **Depends On**: Task 4
- **Description**: 
  - 测试分析技能是否能正常执行
- **Success Criteria**:
  - 技能可以被调用
  - 输出结果正确
- **Test Requirements**:
  - `programmatic` TR-5.1: 技能执行成功 ✓
  - `human-judgement` TR-5.2: 验证输出结果合理 ✓
- **Notes**: 已测试 deep_research.py，输出完整的 Apple 分析报告

## 修复总结

所有关键问题已成功解决：

1. ✅ **Python 虚拟环境** - 创建了 .venv，避免系统级包冲突
2. ✅ **依赖包安装** - 成功安装了 akshare, yfinance, pandas 等所有依赖
3. ✅ **路径问题修复** - skill_adapter.py 现在使用动态路径检测，找到正确的虚拟环境 Python
4. ✅ **技能功能验证** - deep_research.py 已正常运行，生成完整的 Apple 分析报告
