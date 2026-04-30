# 恢复 SSH 原始配置 - 实现计划

# 确保 SSH 密码登录可用 - 实现计划

## 当前配置状态分析

| 配置项 | 当前值 | 状态 |
|--------|--------|------|
| PasswordAuthentication | yes | ✅ 已启用 |
| UsePAM | **no** | ❌ **已禁用（问题所在）** |
| PubkeyAuthentication | 注释（默认yes） | ✅ 已启用 |

**问题**：`UsePAM no` 会导致密码认证无法正常工作（即使 PasswordAuthentication yes）

---

## 恢复方案

将 `UsePAM` 设置为 `yes`，确保密码认证通过 PAM 模块正常工作。

---

## 具体实施步骤

### 步骤 1：修改 UsePAM 配置
```bash
sudo sed -i 's/^UsePAM no/UsePAM yes/' /etc/ssh/sshd_config
```

### 步骤 2：验证配置语法
```bash
sudo sshd -t
```

### 步骤 3：重启 SSH 服务
```bash
sudo systemctl restart ssh
```

### 步骤 4：确认配置已生效
```bash
grep "UsePAM" /etc/ssh/sshd_config
```

---

## 恢复后的配置状态

| 配置项 | 恢复后值 | 说明 |
|--------|---------|------|
| PasswordAuthentication | yes | 启用密码认证 |
| UsePAM | **yes** | 启用 PAM 认证（关键修复） |
| PubkeyAuthentication | 注释（默认 yes） | 启用密钥认证 |

---

## 注意事项

1. **需要 sudo 权限**：修改配置需要管理员权限
2. **保留当前 SSH 会话**：建议保留当前会话，先测试新连接
3. **UsePAM 是关键**：Ubuntu 默认使用 PAM 进行密码认证，必须启用
