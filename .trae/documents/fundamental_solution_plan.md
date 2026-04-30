# 微信公众号文章知识库沉淀 - 根本解决方案计划

## 问题根源分析

### 当前问题
1. **微信公众号链接有反爬虫机制**：直接访问会返回"参数错误"，需要真实浏览器环境
2. **obsidian_integration.py 脚本不存在**：知识库保存功能缺失
3. **Playwright 浏览器依赖未安装**：情报中心无法使用 wechat-article-reader 技能
4. **调度中心分配任务失败**：可能存在 LLM 额度或配置问题

## 根本解决方案

### 核心思路
既然微信有反爬虫机制，我们需要：
1. ✅ 安装并配置 Playwright 浏览器（这是最终解决方案）
2. ✅ 创建缺失的 obsidian_integration.py 脚本
3. ✅ 确保调度中心和情报中心可以正常工作
4. ✅ 测试整个工作流程

---

## 实施步骤

### [ ] 任务 1：创建 obsidian_integration.py 脚本
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 创建完整的 obsidian_integration.py 脚本
  - 支持 create、read、update、search、generate-moc 等命令
  - 与 agent_tools.py 中的 _create_obsidian_note 等函数兼容
- **Success Criteria**:
  - 脚本文件存在于 /home/xxh/obsidian_integration.py
  - 脚本可以正常执行所有命令
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证脚本文件存在
  - `programmatic` TR-1.2: 验证脚本可以执行 --help 命令
  - `human-judgement` TR-1.3: 检查脚本功能完整性

### [ ] 任务 2：安装 Playwright 浏览器依赖
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查系统环境是否支持 Playwright
  - 安装 Playwright Python 包
  - 安装 Playwright 浏览器二进制文件
  - 解决可能的系统依赖问题
- **Success Criteria**:
  - Playwright 可以正常导入和使用
  - 浏览器可以正常启动
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证 playwright 包已安装
  - `programmatic` TR-2.2: 验证浏览器二进制文件已安装
  - `programmatic` TR-2.3: 验证可以启动简单的浏览器测试

### [ ] 任务 3：检查并修复调度中心配置
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查调度中心的状态和配置
  - 检查 LLM 额度使用情况
  - 重置可能已用完的额度
  - 确保调度中心可以正常分配任务
- **Success Criteria**:
  - 调度中心状态为 running
  - LLM 额度充足
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证调度中心存在且状态正常
  - `programmatic` TR-3.2: 验证 LLM 额度充足

### [ ] 任务 4：检查情报中心和 wechat-article-reader 技能
- **Priority**: P0
- **Depends On**: 任务 2
- **Description**: 
  - 检查情报中心的状态
  - 检查 wechat-article-reader 技能是否存在
  - 确保技能可以正常调用
- **Success Criteria**:
  - 情报中心状态正常
  - wechat-article-reader 技能可用
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证情报中心存在且状态正常
  - `programmatic` TR-4.2: 验证 wechat-article-reader 技能存在

### [ ] 任务 5：创建测试脚本验证完整流程
- **Priority**: P0
- **Depends On**: 任务 1, 2, 3, 4
- **Description**: 
  - 创建测试脚本验证整个工作流程
  - 测试：使用 Playwright 抓取微信文章 → 保存到知识库
  - 验证所有环节都可以正常工作
- **Success Criteria**:
  - 完整流程测试通过
  - 文章成功保存到知识库
- **Test Requirements**:
  - `programmatic` TR-5.1: 验证测试脚本可以正常运行
  - `programmatic` TR-5.2: 验证文章成功保存到知识库
  - `human-judgement` TR-5.3: 检查保存的文章内容完整性

### [ ] 任务 6：（可选）优化：同时保留 jina_read 作为备选方案
- **Priority**: P1
- **Depends On**: None
- **Description**: 
  - 确保 jina_read 工具可以正常工作
  - 在 Playwright 不可用时作为备选方案
  - 提供双重保障
- **Success Criteria**:
  - jina_read 工具可以正常使用
  - 两种方案都可用
- **Test Requirements**:
  - `programmatic` TR-6.1: 验证 jina_read 可以正常读取网页
  - `human-judgement` TR-6.2: 验证两种方案都可行

---

## 技术细节

### obsidian_integration.py 功能要求
脚本需要支持以下命令：
```bash
python3 obsidian_integration.py create <title> <content> [directory] [tags...]
python3 obsidian_integration.py read <filepath>
python3 obsidian_integration.py update <title> <content> [--mode append|overwrite] [directory] [tags...]
python3 obsidian_integration.py search <query> [directory]
python3 obsidian_integration.py generate-moc [directory]
```

### 知识库存储位置
- **企业级知识库**：`/home/xxh/Clawith/backend/data/agents/enterprise_info/knowledge_base/`
- **代理级知识库**：`/home/xxh/Clawith/backend/data/agents/{agent_id}/workspace/knowledge_base/`

### Playwright 安装步骤
1. 安装 Playwright Python 包：`pip install playwright`
2. 安装浏览器：`playwright install chromium`
3. 安装系统依赖（如需要）

---

## 预期结果

完成本计划后，您将获得：
1. ✅ **完整的知识库功能**：obsidian_integration.py 脚本创建完成
2. ✅ **Playwright 浏览器支持**：可以正常抓取微信公众号文章
3. ✅ **调度中心正常工作**：可以正常分配任务
4. ✅ **情报中心正常工作**：可以执行 wechat-article-reader 技能
5. ✅ **完整工作流程**：从抓取文章到保存知识库的完整流程可用
6. ✅ **双重保障**：Playwright + jina_read 两种方案都可用
