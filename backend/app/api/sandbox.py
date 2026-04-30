"""Sandbox API — 沙箱环境管理与安全执行.

基于 openharness/sandbox/adapter.py 的 srt (sandbox-runtime) 适配器:
- Linux / WSL / macOS 跨平台支持
- 命令包装: wrap_command_for_sandbox()
- 可用性检测: get_sandbox_availability()
"""

from __future__ import annotations

import logging
import platform
import shlex
import subprocess
import sys
import time
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request

from app.core.security import require_auth, require_role

logger = logging.getLogger(__name__)
sandbox_bp = Blueprint('sandbox', __name__)

_sandbox_status = None


def _get_sandbox_status() -> Dict[str, Any]:
    """获取沙箱状态（带缓存）."""
    global _sandbox_status

    if _sandbox_status is None:
        try:
            from openharness.sandbox.adapter import (
                get_sandbox_availability,
                get_sandbox_config,
                is_host_bash_allowed,
            )

            availability = get_sandbox_availability()
            config = get_sandbox_config()

            _sandbox_status = {
                'available': availability.available,
                'provider': availability.provider,
                'runtime_path': str(availability.runtime_path) if availability.runtime_path else None,
                'version': availability.version,
                'config': {
                    'enabled': config.enabled,
                    'type': config.type,
                    'allow_host_bash': config.allow_host_bash,
                    'image_name': config.image_name or 'default',
                    'timeout_sec': config.timeout_sec,
                    'memory_mb': config.memory_mb,
                },
                'host_bash_allowed': is_host_bash_allowed(config),
                'platform': platform.system(),
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
                'note': '基于 openharness/sandbox/adapter.py',
            }
        except Exception as e:
            logger.warning(f"沙箱状态获取失败: {e}")
            _sandbox_status = {
                'available': False,
                'error': str(e),
                'provider': 'none',
                'host_bash_allowed': True,
                'platform': platform.system(),
                'note': '沙箱模块不可用，使用本地模式',
            }

    return _sandbox_status


@require_auth
@sandbox_bp.route('/status', endpoint='status', methods=['GET'])
def sandbox_status():
    """
    获取沙箱运行时状态（基于 openharness/sandbox/adapter.py 的 srt 适配器）

    支持平台：Linux / WSL / macOS
    ---
    tags:
      - Sandbox
    security:
      - BearerAuth: []
    responses:
      200:
        description: 沙箱状态（available/provider/runtime_path/version/config/host_bash_allowed/platform）
      401:
        description: 未认证
    """
    status = _get_sandbox_status()
    return jsonify(status)


@require_auth
@require_role('admin')
@sandbox_bp.route('/execute', endpoint='execute', methods=['POST'])
def execute_command():
    """
    在沙箱中执行命令（或本地模式降级）

    执行策略：
    - use_sandbox=true 且沙箱可用 → 通过 srt 沙箱执行
- 否则 → 本地模式直接执行（有安全风险提示）
    ---
    tags:
      - Sandbox
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - command
          properties:
            command:
              type: string
              description: 要执行的命令
            cwd:
              type: string
              description: 工作目录
            timeout:
              type: integer
              default: 30
              description: 超时时间（秒）
            use_sandbox:
              type: boolean
              default: true
              description: 是否使用沙箱执行
    responses:
      200:
        description: 执行结果（exit_code/stdout/stderr/elapsed_ms/mode）
      400:
        description: 缺少必填参数 command
      500:
        description: 执行失败
      401:
        description: 未认证
      403:
        description: 需要 admin 角色
    """
    data = request.get_json(silent=True) or {}
    command = data.get('command', '')
    cwd = data.get('cwd')
    timeout = int(data.get('timeout', 30))
    use_sandbox = data.get('use_sandbox', True)

    if not command:
        raise ValueError('command is required')

    status = _get_sandbox_status()
    start_time = time.time()

    try:
        if use_sandbox and status.get('available'):
            result = _execute_in_sandbox(command, cwd, timeout)
        else:
            result = _execute_locally(command, cwd, timeout)

        elapsed_ms = (time.time() - start_time) * 1000

        return jsonify({
            'success': True,
            'exit_code': result.get('returncode', 0),
            'stdout': result.get('stdout', ''),
            'stderr': result.get('stderr', ''),
            'elapsed_ms': round(elapsed_ms, 1),
            'mode': 'sandbox' if (use_sandbox and status.get('available')) else 'local',
        })
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return jsonify({
            'success': False,
            'error': str(e),
            'elapsed_ms': round(elapsed_ms, 1),
            'mode': 'error',
        }), 500


def _execute_in_sandbox(command: str, cwd: Optional[str], timeout: int) -> Dict[str, Any]:
    """通过 srt 沙箱执行命令."""
    from openharness.sandbox.adapter import wrap_command_for_sandbox

    wrapped = wrap_command_for_sandbox(command)
    logger.info("沙箱执行: %s → %s", command[:80], wrapped[:80])

    proc = subprocess.run(
        shlex.split(wrapped),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )

    return {
        'returncode': proc.returncode,
        'stdout': proc.stdout,
        'stderr': proc.stderr,
    }


def _execute_locally(command: str, cwd: Optional[str], timeout: int) -> Dict[str, Any]:
    """本地模式直接执行命令."""
    logger.info("本地执行: %s", command[:80])

    proc = subprocess.run(
        shlex.split(command),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )

    return {
        'returncode': proc.returncode,
        'stdout': proc.stdout,
        'stderr': proc.stderr,
    }


@require_auth
@sandbox_bp.route('/wrap', endpoint='wrap', methods=['POST'])
def wrap_command():
    """预览命令的沙箱包装结果（不实际执行）.

    POST body: {"command": "rm -rf /tmp/test"}
    """
    data = request.get_json(silent=True) or {}
    command = data.get('command', '')

    if not command:
        raise ValueError('command is required')

    status = _get_sandbox_status()

    if not status.get('available'):
        return jsonify({
            'original': command,
            'wrapped': command,
            'sandbox_available': False,
            'warning': '沙箱不可用，命令将直接执行',
        })

    try:
        from openharness.sandbox.adapter import wrap_command_for_sandbox
        wrapped = wrap_command_for_sandbox(command)

        return jsonify({
            'original': command,
            'wrapped': wrapped,
            'sandbox_available': True,
            'provider': status['provider'],
        })
    except Exception as e:
        return jsonify({
            'original': command,
            'wrapped': command,
            'sandbox_available': True,
            'error': str(e),
        })


@require_auth
@sandbox_bp.route('/security-check', endpoint='security_check', methods=['POST'])
def security_check():
    """
    检测命令是否包含危险操作模式

    检测规则覆盖：
    - 系统破坏：rm -rf /, DROP TABLE, > /dev/sda, FORMAT, dd if=, mkfs.
    - 权限提升：chmod -R 777 /
    - 资源耗尽：Fork 炸弹 :(){ :|:& };:
    - 远程代码执行：wget | sh, curl | bash
    ---
    tags:
      - Sandbox
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - command
          properties:
            command:
              type: string
              description: 待检测的命令
    responses:
      200:
        description: 安全检测结果（risk_level/dangerous_findings/recommendation）
        schema:
          type: object
          properties:
            risk_level:
              type: string
              enum: [low, medium, high]
            dangerous_findings:
              type: array
              items:
                type: object
            finding_count:
              type: integer
            sandbox_protection:
              type: boolean
            recommendation:
              type: string
      401:
        description: 未认证
    """
    data = request.get_json(silent=True) or {}
    command = data.get('command', '')

    dangerous_patterns = [
        ('rm -rf /', '删除根目录'),
        ('rm -rf /*', '删除根目录'),
        ('DROP TABLE', 'SQL 删除表'),
        ('> /dev/sda', '覆盖磁盘'),
        ('FORMAT ', '格式化磁盘'),
        ('chmod -R 777 /', '全局可写权限'),
        ('dd if=', '磁盘写入'),
        ('mkfs.', '创建文件系统'),
        (':(){ :|:& };:', 'Fork 炸弹'),
        ('wget.* | sh', '远程脚本执行'),
        ('curl.* | bash', '远程脚本执行'),
    ]

    findings = []
    for pattern, description in dangerous_patterns:
        if pattern.lower() in command.lower():
            findings.append({'pattern': pattern, 'description': description})

    status = _get_sandbox_status()
    risk_level = 'high' if len(findings) >= 3 else ('medium' if len(findings) >= 1 else 'low')

    return jsonify({
        'command_preview': command[:200],
        'risk_level': risk_level,
        'dangerous_findings': findings,
        'finding_count': len(findings),
        'sandbox_protection': status.get('available', False),
        'recommendation': (
            '建议在沙箱中执行'
            if risk_level in ('high', 'medium') and status.get('available')
            else ('命令安全' if risk_level == 'low' else '建议拒绝执行')
        ),
    })
