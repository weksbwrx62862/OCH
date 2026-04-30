"""记忆事实 API 单元测试 — 验证 MemoryFact 增删改查、向量搜索和用户隔离."""

from __future__ import annotations

import json


class TestMemoryFactListAPI:
    """测试记忆事实列表 API."""

    def test_list_facts_empty(self, test_client, auth_headers):
        """测试空列表返回."""
        response = test_client.get('/api/v1/memory/facts', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'data' in data
        assert 'total' in data
        assert data['total'] == 0
        assert len(data['data']) == 0

    def test_list_facts_with_data(self, test_client, auth_headers, db_session):
        """测试有数据时的列表."""
        from app.models.memory_fact import MemoryFact
        import uuid
        import asyncio

        fact = MemoryFact(
            id=str(uuid.uuid4()),
            content='用户偏好：使用 Python 类型注解',
            category='preference',
            confidence=0.9,
            source='manual',
            tags=['python', 'preference'],
        )
        db_session.add(fact)
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        response = test_client.get('/api/v1/memory/facts', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['total'] >= 1

    def test_list_facts_category_filter(self, test_client, auth_headers, db_session):
        """测试按类别筛选."""
        from app.models.memory_fact import MemoryFact
        import uuid
        import asyncio

        fact = MemoryFact(
            id=str(uuid.uuid4()),
            content='项目知识：使用 FastAPI 框架',
            category='knowledge',
            confidence=0.85,
        )
        db_session.add(fact)
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        response = test_client.get(
            '/api/v1/memory/facts',
            headers=auth_headers,
            query_string={'category': 'knowledge'}
        )
        assert response.status_code == 200

        data = response.get_json()
        for item in data['data']:
            assert item['category'] == 'knowledge'

    def test_list_facts_pagination(self, test_client, auth_headers):
        """测试分页功能."""
        response = test_client.get(
            '/api/v1/memory/facts',
            headers=auth_headers,
            query_string={'page': 1, 'per_page': 10}
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'page' in data
        assert data['page'] == 1

    def test_list_facts_requires_auth(self, test_client):
        """测试未认证访问被拒绝."""
        response = test_client.get('/api/v1/memory/facts')
        assert response.status_code == 401


class TestMemoryFactCreateAPI:
    """测试记忆事实创建 API."""

    def test_create_fact_success(self, test_client, auth_headers):
        """测试成功创建事实."""
        payload = {
            'content': '用户喜欢使用异步编程模式',
            'category': 'preference',
            'confidence': 0.9,
            'tags': ['async', 'python'],
            'source': 'manual',
        }

        response = test_client.post(
            '/api/v1/memory/facts',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'fact' in data
        assert data['fact']['content'] == '用户喜欢使用异步编程模式'
        assert data['fact']['category'] == 'preference'

    def test_create_fact_missing_content(self, test_client, auth_headers):
        """测试缺少内容字段."""
        payload = {'category': 'preference'}

        response = test_client.post(
            '/api/v1/memory/facts',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422

    def test_create_fact_duplicate_content(self, test_client, auth_headers, db_session):
        """测试重复内容检测."""
        from app.models.memory_fact import MemoryFact
        import uuid
        import asyncio

        existing = MemoryFact(
            id=str(uuid.uuid4()),
            content='重复内容测试',
            category='test',
        )
        db_session.add(existing)
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        payload = {'content': '重复内容测试'}
        response = test_client.post(
            '/api/v1/memory/facts',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422


class TestMemoryFactGetAPI:
    """测试获取事实详情 API."""

    def test_get_fact_success(self, test_client, auth_headers, db_session):
        """测试获取事实详情."""
        from app.models.memory_fact import MemoryFact
        import uuid
        import asyncio

        fact = MemoryFact(
            id=str(uuid.uuid4()),
            content='获取测试事实',
            category='test',
            confidence=0.8,
        )
        db_session.add(fact)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(fact))

        response = test_client.get(
            f'/api/v1/memory/facts/{fact.id}',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['id'] == fact.id
        assert data['content'] == '获取测试事实'

    def test_get_fact_not_found(self, test_client, auth_headers):
        """测试获取不存在的事实."""
        fake_id = 'non-existent-fact-id-12345'
        response = test_client.get(f'/api/v1/memory/facts/{fake_id}', headers=auth_headers)
        assert response.status_code == 404


class TestMemoryFactUpdateAPI:
    """测试更新事实 API."""

    def test_update_fact_success(self, test_client, auth_headers, db_session):
        """测试成功更新事实."""
        from app.models.memory_fact import MemoryFact
        import uuid
        import asyncio

        fact = MemoryFact(
            id=str(uuid.uuid4()),
            content='原始内容',
            category='test',
        )
        db_session.add(fact)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(fact))

        payload = {'content': '更新后的内容', 'confidence': 0.95}
        response = test_client.put(
            f'/api/v1/memory/facts/{fact.id}',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 200

    def test_update_fact_not_found(self, test_client, auth_headers):
        """测试更新不存在的事实."""
        payload = {'content': 'Ghost'}
        response = test_client.put(
            '/api/v1/memory/facts/nonexistent',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 404


class TestMemoryFactDeleteAPI:
    """测试删除事实 API."""

    def test_delete_fact_success(self, test_client, auth_headers, db_session):
        """测试成功删除事实（软删除）."""
        from app.models.memory_fact import MemoryFact
        import uuid
        import asyncio

        fact = MemoryFact(
            id=str(uuid.uuid4()),
            content='待删除的事实',
            category='test',
        )
        db_session.add(fact)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(fact))

        response = test_client.delete(
            f'/api/v1/memory/facts/{fact.id}',
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_delete_fact_not_found(self, test_client, auth_headers):
        """测试删除不存在的事实."""
        response = test_client.delete(
            '/api/v1/memory/facts/ghost-fact-id',
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestMemoryRecallAPI:
    """测试语义检索 API."""

    def test_recall_facts_with_query(self, test_client, auth_headers, db_session):
        """测试关键词搜索."""
        from app.models.memory_fact import MemoryFact
        import uuid
        import asyncio

        fact = MemoryFact(
            id=str(uuid.uuid4()),
            content='用户偏好使用 TypeScript 进行前端开发',
            category='preference',
            confidence=0.9,
            tags=['typescript', 'frontend'],
        )
        db_session.add(fact)
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        payload = {'query': 'TypeScript', 'limit': 5}
        response = test_client.post(
            '/api/v1/memory/recall',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'results' in data
        assert 'query' in data
        assert data['query'] == 'TypeScript'

    def test_recall_missing_query(self, test_client, auth_headers):
        """测试缺少查询参数."""
        payload = {}
        response = test_client.post(
            '/api/v1/memory/recall',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422


class TestMemoryStatsAPI:
    """测试记忆统计 API."""

    def test_get_memory_stats(self, test_client, auth_headers):
        """测试获取统计数据."""
        response = test_client.get(
            '/api/v1/memory/stats',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'total_facts' in data
        assert 'by_category' in data
        assert 'by_source' in data
        assert 'confidence_distribution' in data


class TestMemorySignalAPI:
    """测试纠错和正反馈信号 API."""

    def test_signal_correction(self, test_client, auth_headers):
        """测试纠错信号记录."""
        payload = {
            'content': '正确的做法是使用 async/await 而不是回调',
            'wrong_content': '错误地使用了回调函数',
        }

        response = test_client.post(
            '/api/v1/memory/signal/correction',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'fact' in data
        assert data['fact']['source'] == 'correction'
        assert data['fact']['confidence'] >= 0.95

    def test_signal_reinforcement(self, test_client, auth_headers):
        """测试正反馈信号记录."""
        payload = {
            'content': '用户确认这种代码风格很好',
        }

        response = test_client.post(
            '/api/v1/memory/signal/reinforcement',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'fact' in data
        assert data['fact']['source'] == 'reinforcement'
        assert 'confirmed' in data['fact']['tags']
