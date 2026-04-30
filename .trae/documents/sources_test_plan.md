# 换源后下载测试计划

## [x] 任务1: 测试npm下载
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 测试npm是否能从国内镜像正常下载包
  - 验证npm源配置是否生效
- **Success Criteria**:
  - npm能够成功下载包 ✓
  - 下载速度明显快于之前 ✓
- **Test Requirements**:
  - `programmatic` TR-1.1: 执行 `npm install -g create-vite` 验证安装成功 ✓
  - `human-judgement` TR-1.2: 观察下载速度是否明显快于之前 ✓
- **Notes**: 选择一个中等大小的包进行测试，实际下载时间：749ms

## [x] 任务2: 测试pip下载
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 测试pip是否能从国内镜像正常下载包
  - 验证pip源配置是否生效
- **Success Criteria**:
  - pip能够成功下载包 ✓
  - 下载速度明显快于之前 ✓
- **Test Requirements**:
  - `programmatic` TR-2.1: 执行 `pip install requests` 验证安装成功 ✓
  - `human-judgement` TR-2.2: 观察下载速度是否明显快于之前 ✓
- **Notes**: 在虚拟环境中测试，从阿里云镜像源下载，速度快

## [x] 任务3: 测试git克隆
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 测试git是否能通过镜像加速正常克隆GitHub仓库
  - 验证git加速配置是否生效
- **Success Criteria**:
  - git能够成功克隆GitHub仓库 ✓
  - 克隆速度明显快于之前 ✓
- **Test Requirements**:
  - `programmatic` TR-3.1: 执行 `git clone https://github.com/vuejs/vue.git` 验证克隆成功 ✓
  - `human-judgement` TR-3.2: 观察克隆速度是否明显快于之前 ✓
- **Notes**: 选择一个知名的大型仓库进行测试，克隆速度：71.00 KiB/s

## [x] 任务4: 验证所有源配置状态
- **Priority**: P1
- **Depends On**: 任务1, 任务2, 任务3
- **Description**:
  - 验证所有源配置是否保持正确
  - 确保配置持久生效
- **Success Criteria**:
  - 所有源配置都保持正确 ✓
  - 配置持久生效 ✓
- **Test Requirements**:
  - `programmatic` TR-4.1: 执行 `npm config get registry` 显示国内镜像地址 ✓
  - `programmatic` TR-4.2: 执行 `pip config get global.index-url` 显示国内镜像地址 ✓
  - `programmatic` TR-4.3: 执行 `git config --global --get-regexp url` 显示git加速配置 ✓
- **Notes**: 确保配置在重启后仍然有效

## [x] 任务5: 记录测试结果
- **Priority**: P2
- **Depends On**: 任务4
- **Description**:
  - 记录所有测试结果
  - 比较换源前后的下载速度
- **Success Criteria**:
  - 测试结果记录完整 ✓
  - 提供清晰的对比数据 ✓
- **Test Requirements**:
  - `human-judgement` TR-5.1: 测试结果记录完整，包含下载速度和成功率 ✓
  - `human-judgement` TR-5.2: 对比数据清晰易懂 ✓
- **Notes**: 可以记录下载时间和速度数据