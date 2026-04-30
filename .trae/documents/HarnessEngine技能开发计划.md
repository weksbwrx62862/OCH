# HarnessEngine 技能开发计划

## 📋 项目概述

**目标**: 创建一个名为 "harness-engine" 的 OpenClaw 技能，实现 Claude Code 源码中的 Harness 工程功能，作为附加项目安装到 OpenClaw。

**原则**: 
- 不修改 OpenClaw 核心代码
- 完全通过技能机制实现
- 保持向后兼容

---

## 🎯 技能架构

```
harness-engine/
├── SKILL.md                          # 技能主文件
├── scripts/                          # 可执行脚本
│   ├── __init__.py
│   ├── compression/                  # 三层压缩模块
│   │   ├── __init__.py
│   │   ├── token_counter.py
│   │   ├── thresholds.py
│   │   ├── micro_compact.py
│   │   ├── auto_compact.py
│   │   └── storage.py
│   ├── tasks/                        # Task V2 模块
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── manager.py
│   │   └── storage.py
│   ├── worktree/                     # Worktree 模块
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── git_integration.py
│   ├── background/                   # 后台任务模块
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   └── queue.py
│   └── utils/                        # 工具函数
│       ├── __init__.py
│       └── state_manager.py
├── references/                       # 参考文档
│   ├── claude_code_architecture.md   # Claude Code 架构分析
│   ├── compression_guide.md          # 压缩系统使用指南
│   ├── task_v2_guide.md              # Task V2 使用指南
│   └── api_reference.md              # API 参考
├── assets/                           # 资源文件
│   └── templates/
│       └── compression_prompt.txt   # 压缩提示词模板
└── evals/                            # 测试用例
    ├── evals.json
    └── test_cases/
```

---

## 📋 开发计划

### Phase 1: 技能基础框架（1天）

#### 任务 1.1: 创建 SKILL.md
- [ ] 编写技能 YAML frontmatter
- [ ] 编写技能使用说明
- [ ] 定义技能触发条件

#### 任务 1.2: 创建目录结构
- [ ] 创建 scripts/ 目录
- [ ] 创建 references/ 目录
- [ ] 创建 assets/ 目录
- [ ] 创建 evals/ 目录

---

### Phase 2