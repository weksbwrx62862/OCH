#!/bin/bash
# OpenClaw-Harness 全面功能调试脚本（修正版）

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInVzZXJuYW1lIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NzYwODkwNzEsImlhdCI6MTc3NjAwMjY3MX0.In3cdS-9AivlZwCvzJLC83nL3tbg0VkTGqlhS1PXe9M"
AUTH="Authorization: Bearer $TOKEN"
BASE="http://localhost:8008/api/v1"
PASS=0
FAIL=0
ISSUES=""

check() {
    local desc="$1"
    local expected="$2"
    local actual="$3"
    if [ "$actual" = "$expected" ]; then
        echo "  ✅ $desc"
        PASS=$((PASS+1))
    else
        echo "  ❌ $desc (期望: $expected, 实际: $actual)"
        FAIL=$((FAIL+1))
        ISSUES="$ISSUES\n- $desc: 期望 $expected, 实际 $actual"
    fi
}

echo "=========================================="
echo "  T2: 认证模块调试"
echo "=========================================="

RESP=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" -d '{"password":"J-n8Q2EY3dumVeLu7kE_HQ"}')
HAS_TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print('yes' if json.load(sys.stdin).get('access_token') else 'no')" 2>/dev/null)
check "正确密码登录" "yes" "$HAS_TOKEN"

HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST $BASE/auth/login -H "Content-Type: application/json" -d '{"password":"wrong"}')
check "错误密码登录返回401" "401" "$HTTP"

HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/agents)
check "无Token访问返回401" "401" "$HTTP"

HTTP=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer invalidtoken" $BASE/agents)
check "无效Token返回401" "401" "$HTTP"

echo ""
echo "=========================================="
echo "  T3: Agent 模块调试"
echo "=========================================="

RESP=$(curl -s -X POST $BASE/agents -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"debug-test-agent","description":"调试测试Agent"}')
AGENT_ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent',d).get('id',''))" 2>/dev/null)
check "创建Agent" "non-empty" "$([ -n "$AGENT_ID" ] && echo 'non-empty' || echo 'empty')"

RESP=$(curl -s $BASE/agents -H "$AUTH")
HAS_AGENT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); data=d.get('data',d.get('agents',[])); print('yes' if any(a.get('id')=='$AGENT_ID' for a in data) else 'no')" 2>/dev/null)
check "Agent列表包含新建Agent" "yes" "$HAS_AGENT"

RESP=$(curl -s -X PUT $BASE/agents/$AGENT_ID -H "$AUTH" -H "Content-Type: application/json" -d '{"description":"更新后的描述"}')
UPDATED=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); a=d.get('agent',d); print('yes' if '更新' in a.get('description','') else 'no')" 2>/dev/null)
check "Agent更新生效" "yes" "$UPDATED"

HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/agents/$AGENT_ID -H "$AUTH")
check "Agent详情返回200" "200" "$HTTP"

HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE $BASE/agents/$AGENT_ID -H "$AUTH")
check "删除Agent返回200" "200" "$HTTP"

HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/agents/$AGENT_ID -H "$AUTH")
check "删除后查询返回404" "404" "$HTTP"

HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST $BASE/agents -H "$AUTH" -H "Content-Type: application/json" -d '{}')
check "缺少name字段返回422" "422" "$HTTP"

echo ""
echo "=========================================="
echo "  T4: Session 和 Chat 模块调试"
echo "=========================================="

RESP=$(curl -s -X POST $BASE/sessions -H "$AUTH" -H "Content-Type: application/json" -d '{"title":"调试测试会话"}')
SESSION_ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session',d).get('id',''))" 2>/dev/null)
check "创建Session" "non-empty" "$([ -n "$SESSION_ID" ] && echo 'non-empty' || echo 'empty')"

if [ -z "$SESSION_ID" ]; then
    echo "  ⚠️ Session创建失败，跳过Chat测试"
    echo "  创建响应: $RESP"
else
    echo "  --- 流式Chat测试（调用DeepSeek API）---"
    CHAT_RESP=$(curl -s -N -X POST $BASE/sessions/$SESSION_ID/chat -H "$AUTH" -H "Content-Type: application/json" -d '{"message":"你好，请用一句话介绍你自己","stream":true}' 2>&1 | head -30)
    HAS_TEXT_DELTA=$(echo "$CHAT_RESP" | grep -c "text_delta" || true)
    HAS_TURN_COMPLETE=$(echo "$CHAT_RESP" | grep -c "turn_complete" || true)
    HAS_DONE=$(echo "$CHAT_RESP" | grep -c "\[DONE\]" || true)
    check "SSE包含text_delta事件" "yes" "$([ $HAS_TEXT_DELTA -gt 0 ] && echo 'yes' || echo 'no')"
    check "SSE包含turn_complete事件" "yes" "$([ $HAS_TURN_COMPLETE -gt 0 ] && echo 'yes' || echo 'no')"
    check "SSE包含[DONE]标记" "yes" "$([ $HAS_DONE -gt 0 ] && echo 'yes' || echo 'no')"

    RESP=$(curl -s -X POST $BASE/sessions/$SESSION_ID/chat -H "$AUTH" -H "Content-Type: application/json" -d '{"message":"1+1等于几？","stream":false}')
    HAS_RESPONSE=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('yes' if d.get('response') or d.get('message') else 'no')" 2>/dev/null)
    check "非流式Chat返回response" "yes" "$HAS_RESPONSE"

    RESP=$(curl -s $BASE/sessions/$SESSION_ID/messages -H "$AUTH")
    MSG_COUNT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])))" 2>/dev/null || echo "0")
    check "消息持久化（至少2条消息）" "yes" "$([ "$MSG_COUNT" -ge 2 ] 2>/dev/null && echo 'yes' || echo 'no')"

    RESP=$(curl -s $BASE/sessions/$SESSION_ID/stats -H "$AUTH")
    HAS_STATS=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('yes' if d.get('total_messages',0) > 0 else 'no')" 2>/dev/null || echo "no")
    check "Session统计数据有值" "yes" "$HAS_STATS"

    HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X PUT $BASE/sessions/$SESSION_ID/pause -H "$AUTH")
    check "Session暂停返回200" "200" "$HTTP"

    HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X PUT $BASE/sessions/$SESSION_ID/resume -H "$AUTH")
    check "Session恢复返回200" "200" "$HTTP"

    HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE $BASE/sessions/$SESSION_ID -H "$AUTH")
    check "删除Session返回200" "200" "$HTTP"
fi

echo ""
echo "=========================================="
echo "  T5: 辅助模块调试（修正路由）"
echo "=========================================="

# 5.1 工具
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/tools -H "$AUTH")
check "工具发现API" "200" "$HTTP"

# 5.2 技能
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/skills -H "$AUTH")
check "技能管理API" "200" "$HTTP"

# 5.3 权限（路由是 /permissions/modes 和 /permissions/rules）
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/permissions/modes -H "$AUTH")
check "权限管理API (/permissions/modes)" "200" "$HTTP"

# 5.4 任务
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/tasks -H "$AUTH")
check "任务管理API" "200" "$HTTP"

# 5.5 审计
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/audit -H "$AUTH")
check "审计日志API" "200" "$HTTP"

# 5.6 记忆（路由是 /memory/facts 和 /memory/stats）
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/memory/facts -H "$AUTH")
check "记忆管理API (/memory/facts)" "200" "$HTTP"

# 5.7 MCP（路由是 /mcp/servers）
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/mcp/servers -H "$AUTH")
check "MCP服务器API (/mcp/servers)" "200" "$HTTP"

# 5.8 渠道（路由是 /channels/types 和 /channels/registered）
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/channels/types -H "$AUTH")
check "消息渠道API (/channels/types)" "200" "$HTTP"

# 5.9 沙箱（路由是 /sandbox/status）
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/sandbox/status -H "$AUTH")
check "沙箱管理API (/sandbox/status)" "200" "$HTTP"

# 5.10 配置
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/config -H "$AUTH")
check "配置管理API" "200" "$HTTP"

# 5.11 协调器（路由是 /coordinator/teams）
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/coordinator/teams -H "$AUTH")
check "协调器API (/coordinator/teams)" "200" "$HTTP"

# 5.12 插件
HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/plugins -H "$AUTH")
check "插件管理API" "200" "$HTTP"

echo ""
echo "=========================================="
echo "  T6: 错误处理调试"
echo "=========================================="

HTTP=$(curl -s -o /dev/null -w "%{http_code}" $BASE/agents/nonexistent-id-99999 -H "$AUTH")
check "不存在Agent返回404" "404" "$HTTP"

HTTP=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer " $BASE/agents)
check "空Token返回401" "401" "$HTTP"

RESP=$(curl -s -X POST $BASE/sessions -H "$AUTH" -H "Content-Type: application/json" -d '{"title":"空消息测试"}')
EMPTY_SESSION=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session',d).get('id',''))" 2>/dev/null)
if [ -n "$EMPTY_SESSION" ]; then
    HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST $BASE/sessions/$EMPTY_SESSION/chat -H "$AUTH" -H "Content-Type: application/json" -d '{"message":""}')
    check "空消息Chat返回错误" "yes" "$([ "$HTTP" != "200" ] && echo 'yes' || echo 'no')"
    curl -s -X DELETE $BASE/sessions/$EMPTY_SESSION -H "$AUTH" > /dev/null 2>&1
else
    check "空消息Chat返回错误" "skip" "skip"
fi

echo ""
echo "=========================================="
echo "  T7: 前端集成调试"
echo "=========================================="

HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
check "前端页面可访问" "200" "$HTTP"

HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:3000/api/v1/auth/login -H "Content-Type: application/json" -d '{"password":"wrong"}')
check "前端API代理联通" "yes" "$([ "$HTTP" = "401" -o "$HTTP" = "200" ] && echo 'yes' || echo 'no')"

HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login)
check "前端登录页面可访问" "200" "$HTTP"

echo ""
echo "=========================================="
echo "  测试结果汇总"
echo "=========================================="
echo "  通过: $PASS"
echo "  失败: $FAIL"
echo "  总计: $((PASS+FAIL))"
if [ $FAIL -gt 0 ]; then
    echo ""
    echo "  ❌ 失败项："
    echo -e "$ISSUES"
fi
