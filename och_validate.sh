#!/bin/bash
source /tmp/och_token.env
BASE="http://localhost:8008/api/v1"
AUTH="Authorization: Bearer $TOKEN"

echo "========== T5.1: 数据一致性验证 =========="

echo "=== 1. 创建Agent后列表包含 ==="
CREATE_RESP=$(curl -s -X POST "$BASE/agents" -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"consistency-test-agent","description":"数据一致性测试"}')
echo "创建响应: $CREATE_RESP"
AGENT_ID=$(echo "$CREATE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent',{}).get('id','') if 'agent' in d else d.get('id',''))" 2>/dev/null)
echo "创建Agent ID: $AGENT_ID"

LIST_RESP=$(curl -s "$BASE/agents" -H "$AUTH")
FOUND=$(echo "$LIST_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); data=d.get('data',d); print('yes' if any(a.get('id')=='$AGENT_ID' for a in data) else 'no')" 2>/dev/null)
echo "列表中包含新建Agent: $FOUND (期望yes)"

echo "=== 2. 更新Agent后详情反映 ==="
curl -s -X PUT "$BASE/agents/$AGENT_ID" -H "$AUTH" -H "Content-Type: application/json" -d '{"description":"更新后的描述-一致性验证"}' > /dev/null
DETAIL_RESP=$(curl -s "$BASE/agents/$AGENT_ID" -H "$AUTH")
UPDATED_DESC=$(echo "$DETAIL_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); a=d.get('agent',d); print(a.get('description',''))" 2>/dev/null)
echo "更新后描述: $UPDATED_DESC"
echo "描述包含更新内容: $(echo '$UPDATED_DESC' | grep -q '一致性验证' && echo 'yes' || echo 'no')"

echo "=== 3. 删除Agent后列表不包含 ==="
curl -s -X DELETE "$BASE/agents/$AGENT_ID" -H "$AUTH" > /dev/null
LIST_AFTER_RESP=$(curl -s "$BASE/agents" -H "$AUTH")
FOUND_AFTER=$(echo "$LIST_AFTER_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); data=d.get('data',d); print('yes' if any(a.get('id')=='$AGENT_ID' for a in data) else 'no')" 2>/dev/null)
echo "删除后列表包含该Agent: $FOUND_AFTER (期望no)"

echo "=== 4. 创建Session后统计 ==="
SESSION_RESP=$(curl -s -X POST "$BASE/sessions" -H "$AUTH" -H "Content-Type: application/json" -d '{"title":"统计验证会话"}')
echo "Session创建响应: $SESSION_RESP"
SESSION_ID=$(echo "$SESSION_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
echo "Session ID: $SESSION_ID"
STATS_RESP=$(curl -s "$BASE/sessions/$SESSION_ID/stats" -H "$AUTH")
echo "Session统计: $STATS_RESP"
curl -s -X DELETE "$BASE/sessions/$SESSION_ID" -H "$AUTH" > /dev/null

echo ""
echo "========== T5.2: 错误处理验证 =========="

echo "=== 5. 不存在资源 ==="
NOT_FOUND_RESP=$(curl -s -w "\n%{http_code}" "$BASE/agents/nonexistent-id-12345" -H "$AUTH")
NOT_FOUND_CODE=$(echo "$NOT_FOUND_RESP" | tail -1)
echo "状态码: $NOT_FOUND_CODE (期望404)"

echo "=== 6. 缺少必填字段 ==="
MISSING_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents" -H "$AUTH" -H "Content-Type: application/json" -d '{}')
MISSING_CODE=$(echo "$MISSING_RESP" | tail -1)
echo "状态码: $MISSING_CODE (期望422)"

echo "=== 7. 同名冲突 ==="
curl -s -X POST "$BASE/agents" -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"dup-test-agent"}' > /dev/null
DUP_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents" -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"dup-test-agent"}')
DUP_CODE=$(echo "$DUP_RESP" | tail -1)
echo "状态码: $DUP_CODE (期望422)"
LIST_FOR_CLEAN=$(curl -s "$BASE/agents" -H "$AUTH")
DUP_ID=$(echo "$LIST_FOR_CLEAN" | python3 -c "import sys,json; d=json.load(sys.stdin); data=d.get('data',d); print(next((a['id'] for a in data if a.get('name')=='dup-test-agent'), ''))" 2>/dev/null)
if [ -n "$DUP_ID" ]; then curl -s -X DELETE "$BASE/agents/$DUP_ID" -H "$AUTH" > /dev/null; fi

echo ""
echo "========== T5.3: 跨模块集成场景 =========="

echo "=== 8. 跨模块集成: Agent→Session→Chat→Audit ==="
AGENT_RESP=$(curl -s -X POST "$BASE/agents" -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"integration-test-agent","description":"集成测试Agent"}')
INT_AGENT_ID=$(echo "$AGENT_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent',{}).get('id','') if 'agent' in d else d.get('id',''))" 2>/dev/null)
echo "创建Agent: $INT_AGENT_ID"

INT_SESSION_RESP=$(curl -s -X POST "$BASE/sessions" -H "$AUTH" -H "Content-Type: application/json" -d "{\"title\":\"集成测试会话\",\"agent_id\":\"$INT_AGENT_ID\"}")
INT_SESSION_ID=$(echo "$INT_SESSION_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
echo "创建Session: $INT_SESSION_ID"

if [ -n "$INT_SESSION_ID" ]; then
  CHAT_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/sessions/$INT_SESSION_ID/chat" -H "$AUTH" -H "Content-Type: application/json" -d '{"message":"集成测试消息","stream":false}')
  CHAT_CODE=$(echo "$CHAT_RESP" | tail -1)
  echo "发送消息: $CHAT_CODE"
fi

echo "=== 9. 审计日志记录 ==="
AUDIT_RESP=$(curl -s "$BASE/audit" -H "$AUTH")
AUDIT_HAS_DATA=$(echo "$AUDIT_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); data=d.get('data',d); print('yes' if data else 'no')" 2>/dev/null)
echo "审计日志有数据: $AUDIT_HAS_DATA"

echo "=== 10. 跨模块集成: Task→Audit ==="
TASK_RESP=$(curl -s -X POST "$BASE/tasks" -H "$AUTH" -H "Content-Type: application/json" -d '{"command":"echo integration-test","task_type":"shell"}')
INT_TASK_ID=$(echo "$TASK_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
echo "创建Task: $INT_TASK_ID"
if [ -n "$INT_TASK_ID" ]; then
  curl -s -X PUT "$BASE/tasks/$INT_TASK_ID/update" -H "$AUTH" -H "Content-Type: application/json" -d '{"status":"running"}' > /dev/null
  curl -s -X PUT "$BASE/tasks/$INT_TASK_ID/update" -H "$AUTH" -H "Content-Type: application/json" -d '{"status":"completed"}' > /dev/null
  echo "Task状态更新完成"
  curl -s -X DELETE "$BASE/tasks/$INT_TASK_ID" -H "$AUTH" > /dev/null
fi

if [ -n "$INT_SESSION_ID" ]; then curl -s -X DELETE "$BASE/sessions/$INT_SESSION_ID" -H "$AUTH" > /dev/null; fi
if [ -n "$INT_AGENT_ID" ]; then curl -s -X DELETE "$BASE/agents/$INT_AGENT_ID" -H "$AUTH" > /dev/null 2>&1; fi

echo ""
echo "=== 验证完成 ==="
