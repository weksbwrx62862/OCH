"""Tools Management API — 43+ Tools registry query and management."""

from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request

from app.core.security import require_auth
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)
tools_bp = Blueprint('tools', __name__)

# Tool definitions (will be populated from OpenHarness core)
TOOL_CATEGORIES = {
    'file_io': [
        {'name': 'Bash', 'description': 'Execute shell commands', 'dangerous': True},
        {'name': 'Read', 'description': 'Read file contents', 'dangerous': False},
        {'name': 'Write', 'description': 'Write to files', 'dangerous': False},
        {'name': 'Edit', 'description': 'Edit files with search/replace', 'dangerous': False},
        {'name': 'Glob', 'description': 'Find files by pattern', 'dangerous': False},
        {'name': 'Grep', 'description': 'Search text in files', 'dangerous': False},
        {'name': 'NotebookEdit', 'description': 'Edit Jupyter notebooks', 'dangerous': False},
        {'name': 'Lsp', 'description': 'Language Server Protocol operations', 'dangerous': False},
    ],
    'web': [
        {'name': 'WebFetch', 'description': 'Fetch URL contents', 'dangerous': False},
        {'name': 'WebSearch', 'description': 'Search the web', 'dangerous': False},
    ],
    'agent': [
        {'name': 'Agent', 'description': 'Spawn sub-agent', 'dangerous': True},
        {'name': 'SendMessage', 'description': 'Send message to agent', 'dangerous': False},
        {'name': 'TeamCreate', 'description': 'Create a team', 'dangerous': True},
        {'name': 'TeamDelete', 'description': 'Delete a team', 'dangerous': True},
    ],
    'task': [
        {'name': 'TaskCreate', 'description': 'Create background task', 'dangerous': False},
        {'name': 'TaskGet', 'description': 'Get task details', 'dangerous': False},
        {'name': 'TaskList', 'description': 'List tasks', 'dangerous': False},
        {'name': 'TaskStop', 'description': 'Stop a task', 'dangerous': False},
        {'name': 'TaskOutput', 'description': 'Get task output', 'dangerous': False},
        {'name': 'TaskUpdate', 'description': 'Update task status', 'dangerous': False},
    ],
    'mcp': [
        {'name': 'MCPTool', 'description': 'Execute MCP server tool', 'dangerous': True},
        {'name': 'ListMcpResources', 'description': 'List MCP resources', 'dangerous': False},
        {'name': 'ReadMcpResource', 'description': 'Read MCP resource', 'dangerous': False},
    ],
    'mode': [
        {'name': 'EnterPlanMode', 'description': 'Enter planning mode', 'dangerous': False},
        {'name': 'ExitPlanMode', 'description': 'Exit planning mode', 'dangerous': False},
        {'name': 'EnterWorktree', 'description': 'Enter git worktree', 'dangerous': False},
        {'name': 'ExitWorktree', 'description': 'Exit git worktree', 'dangerous': False},
    ],
    'schedule': [
        {'name': 'CronCreate', 'description': 'Create cron job', 'dangerous': True},
        {'name': 'CronList', 'description': 'List cron jobs', 'dangerous': False},
        {'name': 'CronDelete', 'description': 'Delete cron job', 'dangerous': True},
        {'name': 'CronToggle', 'description': 'Toggle cron job', 'dangerous': False},
        {'name': 'RemoteTrigger', 'description': 'Trigger remote execution', 'dangerous': True},
    ],
    'meta': [
        {'name': 'Skill', 'description': 'Load skill from .md file', 'dangerous': False},
        {'name': 'Config', 'description': 'View/edit configuration', 'dangerous': False},
        {'name': 'Brief', 'description': 'Show brief context', 'dangerous': False},
        {'name': 'Sleep', 'description': 'Sleep for specified seconds', 'dangerous': False},
        {'name': 'AskUserQuestion', 'description': 'Ask user a question', 'dangerous': False},
        {'name': 'TodoWrite', 'description': 'Manage todo list', 'dangerous': False},
        {'name': 'ToolSearch', 'description': 'Search available tools', 'dangerous': False},
    ],
}


@tools_bp.route('', methods=['GET'])
@require_auth
def list_tools():
    """
    列出所有可用工具（43+），按 8 大分类返回
    ---
    tags:
      - Tools
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: category
        type: string
        enum: [file_io, web, agent, task, mcp, mode, schedule, meta]
        description: 按分类筛选（不传则返回全部分类）
      - in: query
        name: schema
        type: boolean
        default: false
        description: 是否包含输入 Schema (JSON Schema)
    responses:
      200:
        description: 工具列表（按分类组织，含危险等级标记）
      401:
        description: 未认证
    """
    category = request.args.get('category')
    include_schema = request.args.get('schema', False, type=bool)

    if category and category in TOOL_CATEGORIES:
        categories = {category: TOOL_CATEGORIES[category]}
    else:
        categories = TOOL_CATEGORIES

    result = {}
    total = 0

    for cat_name, tools in categories.items():
        result[cat_name] = []
        for tool in tools:
            tool_info = {
                'name': tool['name'],
                'description': tool['description'],
                'requires_permission': tool['dangerous'],
                'dangerous': tool['dangerous'],
                'category': cat_name,
            }

            if include_schema:
                tool_info['input_schema'] = _get_tool_schema(tool['name'])

            result[cat_name].append(tool_info)
            total += 1

    return jsonify({
        'total': total,
        'categories': result,
    })


@tools_bp.route('/categories', endpoint='categories', methods=['GET'])
@require_auth
def list_categories():
    """获取工具分类列表."""
    return jsonify({
        'categories': [
            {'id': 'file_io', 'name': 'File I/O', 'icon': '📁', 'count': len(TOOL_CATEGORIES.get('file_io', []))},
            {'id': 'web', 'name': 'Web', 'icon': '🌐', 'count': len(TOOL_CATEGORIES.get('web', []))},
            {'id': 'agent', 'name': 'Agent', 'icon': '🤖', 'count': len(TOOL_CATEGORIES.get('agent', []))},
            {'id': 'task', 'name': 'Task', 'icon': '📦', 'count': len(TOOL_CATEGORIES.get('task', []))},
            {'id': 'mcp', 'name': 'MCP', 'icon': '🔌', 'count': len(TOOL_CATEGORIES.get('mcp', []))},
            {'id': 'mode', 'name': 'Mode', 'icon': '🔄', 'count': len(TOOL_CATEGORIES.get('mode', []))},
            {'id': 'schedule', 'name': 'Schedule', 'icon': '📅', 'count': len(TOOL_CATEGORIES.get('schedule', []))},
            {'id': 'meta', 'name': 'Meta', 'icon': '⚙️', 'count': len(TOOL_CATEGORIES.get('meta', []))},
        ]
    })


@tools_bp.route('/<tool_name>', endpoint='tool_name', methods=['GET'])
@require_auth
def get_tool_detail(tool_name: str):
    """
    获取工具详细信息 + JSON Schema + 使用示例
    ---
    tags:
      - Tools
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: tool_name
        required: true
        type: string
        description: 工具名称 (如 Bash/Read/Write/Grep/WebFetch)
    responses:
      200:
        description: 工具详情（名称/描述/危险等级/输入Schema/示例）
      404:
        description: 工具不存在
      401:
        description: 未认证
    """
    tool_info = _find_tool(tool_name)
    if not tool_info:
        raise NotFoundError('Tool', tool_name)

    return jsonify({
        **tool_info,
        'input_schema': _get_tool_schema(tool_name),
        'examples': _get_tool_examples(tool_name),
    })


@tools_bp.route('/<tool_name>/schema', endpoint='tool_name_schema', methods=['GET'])
@require_auth
def get_tool_schema(tool_name: str):
    """获取工具输入 Schema (JSON Schema)."""
    schema = _get_tool_schema(tool_name)
    if not schema:
        raise NotFoundError('Tool', tool_name)
    return jsonify(schema)


@tools_bp.route('/<tool_name>/examples', endpoint='tool_name_examples', methods=['GET'])
@require_auth
def get_tool_examples(tool_name: str):
    """获取工具使用示例."""
    examples = _get_tool_examples(tool_name)
    return jsonify(examples or [])


@tools_bp.route('/<tool_name>/test', endpoint='tool_name_test', methods=['POST'])
@require_auth
def test_tool(tool_name: str):
    """
    测试工具执行（dry-run 模式，不实际执行危险操作）
    ---
    tags:
      - Tools
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: tool_name
        required: true
        type: string
      - in: body
        name: body
        schema:
          type: object
          properties:
            input:
              type: object
              description: 工具输入参数
    responses:
      200:
        description: Dry-run 结果（validation + estimated_risk）
      404:
        description: 工具不存在
      401:
        description: 未认证
    """
    data = request.get_json() or {}

    tool_info = _find_tool(tool_name)
    if not tool_info:
        raise NotFoundError('Tool', tool_name)

    return jsonify({
        'tool_name': tool_name,
        'status': 'dry_run',
        'input': data.get('input', {}),
        'validation': 'valid',
        'estimated_risk': 'low' if not tool_info.get('dangerous') else 'medium',
        'message': f"Tool '{tool_name}' is ready. In full implementation, this would run actual validation.",
    })


def _find_tool(tool_name: str) -> dict | None:
    """Find tool by name across all categories (case-insensitive)."""
    name_lower = tool_name.lower()
    for cat_name, tools in TOOL_CATEGORIES.items():
        for tool in tools:
            if tool['name'].lower() == name_lower:
                return {**tool, 'category': cat_name}
    return None


def _get_tool_schema(tool_name: str) -> dict:
    """Generate JSON Schema for a tool (simplified version)."""
    schemas = {
        'Bash': {
            'type': 'object',
            'properties': {
                'command': {'type': 'string', 'description': 'Shell command to execute'},
                'cwd': {'type': 'string', 'description': 'Working directory'},
            },
            'required': ['command'],
        },
        'Read': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'File path to read'},
                'offset': {'type': 'integer', 'description': 'Line offset'},
                'limit': {'type': 'integer', 'description': 'Number of lines'},
            },
            'required': ['path'],
        },
        'Write': {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'File path to write'},
                'content': {'type': 'string', 'description': 'Content to write'},
            },
            'required': ['path', 'content'],
        },
        'Grep': {
            'type': 'object',
            'properties': {
                'pattern': {'type': 'string', 'description': 'Regex pattern'},
                'path': {'type': 'string', 'description': 'Directory or file'},
                'include': {'type': 'string', 'description': 'File glob pattern'},
            },
            'required': ['pattern', 'path'],
        },
        'WebFetch': {
            'type': 'object',
            'properties': {
                'url': {'type': 'string', 'description': 'URL to fetch'},
                'max_length': {'type': 'integer', 'description': 'Max response length'},
            },
            'required': ['url'],
        },
        'Glob': {
            'type': 'object',
            'properties': {
                'pattern': {'type': 'string', 'description': 'Glob pattern'},
                'path': {'type': 'string', 'description': 'Base directory'},
            },
            'required': ['pattern'],
        },
    }
    return schemas.get(tool_name, {
        'type': 'object',
        'properties': {},
        'required': [],
    })


def _get_tool_examples(tool_name: str) -> list:
    """Get usage examples for a tool."""
    examples = {
        'Bash': [
            {'input': {'command': 'ls -la'}, 'description': 'List files'},
            {'input': {'command': 'npm test'}, 'description': 'Run tests'},
            {'input': {'command': 'python script.py --input data.csv'}, 'description': 'Run Python script'},
        ],
        'Read': [
            {'input': {'path': 'src/main.py'}, 'description': 'Read entire file'},
            {'input': {'path': 'src/main.py', 'offset': 1, 'limit': 100}, 'description': 'Read first 100 lines'},
        ],
        'Grep': [
            {'input': {'pattern': 'TODO|FIXME', 'path': './src'}, 'description': 'Find TODO comments'},
            {'input': {'pattern': r'\w+', 'path': './src'}, 'description': 'Find function definitions'},
        ],
    }
    return examples.get(tool_name, [])
