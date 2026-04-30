"""Coordinator Service — multi-agent team management."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BUILTIN_AGENT_DEFINITIONS: Dict[str, Dict] = {
    'code-reviewer': {
        'id': 'code-reviewer',
        'name': 'Code Reviewer',
        'description': 'Reviews code for bugs, security issues, and best practices',
        'system_prompt': '你是一个资深代码审查专家...',
        'capabilities': ['read_code', 'analyze_security', 'suggest_improvements'],
        'tools': ['Read', 'Grep', 'Glob', 'WebSearch'],
    },
    'debugger': {
        'id': 'debugger',
        'name': 'Debugger',
        'description': 'Diagnoses and fixes bugs systematically',
        'system_prompt': '你是一个调试专家，擅长定位和修复问题...',
        'capabilities': ['analyze_error', 'find_root_cause', 'propose_fix'],
        'tools': ['Read', 'Grep', 'Bash', 'WebSearch'],
    },
    'planner': {
        'id': 'planner',
        'name': 'Planner',
        'description': 'Designs implementation plans before coding',
        'system_prompt': '你是一个架构规划专家...',
        'capabilities': ['design_architecture', 'break_down_tasks', 'estimate_effort'],
        'tools': ['Glob', 'Read', 'Write'],
    },
}


class CoordinatorService:
    """多智能体协调服务 — 管理团队、子 Agent、任务分发."""

    def __init__(self):
        self._agent_definitions = BUILTIN_AGENT_DEFINITIONS

    async def list_teams(self) -> List[Dict[str, Any]]:
        from app.core.async_utils import get_db
        from app.models.team import Team
        from sqlalchemy import select

        async with await get_db() as db:
            result = await db.execute(
                select(Team).where(Team.status == 'active').order_by(Team.created_at.desc())
            )
            teams = result.scalars().all()
            return [t.to_dict() for t in teams]

    async def create_team(
        self,
        name: str,
        description: str = '',
        members: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        from app.core.async_utils import get_db
        from app.models.team import Team, TeamMember

        team_id = str(uuid.uuid4())
        async with await get_db() as db:
            team = Team(
                id=team_id,
                name=name,
                description=description,
                status='active',
            )
            db.add(team)
            if members:
                for m in members:
                    member = TeamMember(
                        id=str(uuid.uuid4()),
                        team_id=team_id,
                        agent_id=m.get('agent_id'),
                        role=m.get('role', 'member'),
                        capabilities=m.get('capabilities', []),
                    )
                    db.add(member)
            await db.commit()
            await db.refresh(team)
            return team.to_dict()

    async def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        from app.core.async_utils import get_db
        from app.models.team import Team
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async with await get_db() as db:
            result = await db.execute(
                select(Team)
                .options(selectinload(Team.members))
                .where(Team.id == team_id)
            )
            team = result.scalar_one_or_none()
            if not team:
                return None
            data = team.to_dict()
            data['members'] = [m.to_dict() for m in team.members]
            return data

    async def update_team(
        self,
        team_id: str,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        from app.core.async_utils import get_db
        from app.models.team import Team
        from sqlalchemy import select

        async with await get_db() as db:
            result = await db.execute(select(Team).where(Team.id == team_id))
            team = result.scalar_one_or_none()
            if not team:
                return None
            for key, value in kwargs.items():
                if hasattr(team, key):
                    setattr(team, key, value)
            team.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(team)
            return team.to_dict()

    async def delete_team(self, team_id: str) -> bool:
        from app.core.async_utils import get_db
        from app.models.team import Team
        from sqlalchemy import select

        async with await get_db() as db:
            result = await db.execute(select(Team).where(Team.id == team_id))
            team = result.scalar_one_or_none()
            if not team:
                return False
            team.status = 'dissolved'
            team.dissolved_at = datetime.now(timezone.utc)
            await db.commit()
            return True

    async def list_agent_definitions(self) -> List[Dict[str, Any]]:
        return list(self._agent_definitions.values())

    async def get_agent_definition(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._agent_definitions.get(agent_id)

    async def spawn_subagent(
        self,
        agent_definition_id: str,
        task: str,
        team_id: Optional[str] = None,
        parent_session_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        definition = self._agent_definitions.get(agent_definition_id)
        if not definition:
            raise ValueError(f"Agent definition '{agent_definition_id}' not found")

        task_id = str(uuid.uuid4())
        sub_task = {
            'id': task_id,
            'type': 'subagent',
            'agent_definition_id': agent_definition_id,
            'agent_name': definition['name'],
            'task': task,
            'team_id': team_id,
            'parent_session_id': parent_session_id,
            'status': 'spawning',
            'context': context or {},
            'created_at': datetime.now(timezone.utc).isoformat(),
            'result': None,
            'error': None,
        }

        return sub_task

    async def get_task_dependencies(self, task_id: str) -> Dict[str, Any]:
        return {
            'task_id': task_id,
            'nodes': [],
            'edges': [],
        }

    async def get_protocol_status(self) -> Dict[str, Any]:
        from app.core.async_utils import get_db
        from app.models.team import Team
        from sqlalchemy import select, func

        async with await get_db() as db:
            result = await db.execute(
                select(func.count()).select_from(Team).where(Team.status == 'active')
            )
            active_count = result.scalar() or 0

        return {
            'status': 'idle',
            'active_teams': active_count,
            'total_agents_spawned': 0,
            'shutdown_initiated': False,
        }

    async def initiate_shutdown(self) -> Dict[str, Any]:
        return {
            'status': 'shutdown_requested',
            'message': 'Shutdown handshake initiated',
            'pending_tasks': 0,
        }
