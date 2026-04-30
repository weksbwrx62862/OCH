"""消息渠道管理 API 单元测试 — 验证多平台渠道 CRUD、配置和健康检查."""

from __future__ import annotations

import json


class TestChannelTypesAPI:
    """测试渠道类型列表 API."""

    def test_list_channel_types(self, test_client, auth_headers):
        """测试获取支持的渠道类型列表."""
        response = test_client.get('/api/v1/channels/types', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'channel_types' in data
        assert 'total' in data
        assert data['total'] >= 11  # 至少包含 11 种类型

        expected_types = ['telegram', 'discord', 'slack', 'feishu']
        for t in expected_types:
            assert t in data['channel_types']

    def test_list_channel_types_requires_auth(self, test_client):
        """测试未认证访问被拒绝."""
        response = test_client.get('/api/v1/channels/types')
        assert response.status_code == 401


class TestChannelRegistrationAPI:
    """测试渠道注册 API."""

    def test_register_telegram_channel(self, test_client, auth_headers):
        """测试注册 Telegram 渠道."""
        payload = {
            'type': 'telegram',
            'name': 'my_test_bot',
            'config': {
                'bot_token': 'test-token-12345',
                'chat_id': 'test-chat-id',
            },
            'enabled': True,
        }

        response = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'channel_id' in data
        assert 'channel' in data
        assert data['channel']['type'] == 'telegram'
        assert data['channel']['name'] == 'my_test_bot'
        assert data['channel']['enabled'] is True

    def test_register_discord_channel(self, test_client, auth_headers):
        """测试注册 Discord 渠道."""
        payload = {
            'type': 'discord',
            'name': 'discord_bot',
            'config': {
                'bot_token': 'discord-test-token',
                'guild_id': 'test-guild',
            },
        }

        response = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert data['channel']['type'] == 'discord'

    def test_register_slack_channel(self, test_client, auth_headers):
        """测试注册 Slack 渠道."""
        payload = {
            'type': 'slack',
            'name': 'slack_workspace',
            'config': {
                'bot_token': 'xoxb-test-token',
                'signing_secret': 'test-secret',
            },
        }

        response = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

    def test_register_feishu_channel(self, test_client, auth_headers):
        """测试注册飞书渠道."""
        payload = {
            'type': 'feishu',
            'name': 'feishu_bot',
            'config': {
                'app_id': 'cli_test_id',
                'app_secret': 'test_secret',
            },
        }

        response = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

    def test_register_missing_type(self, test_client, auth_headers):
        """测试缺少渠道类型."""
        payload = {'name': 'no_type_channel'}

        response = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code in (422, 500)

    def test_register_unsupported_type(self, test_client, auth_headers):
        """测试不支持的渠道类型."""
        payload = {
            'type': 'unsupported_platform',
            'name': 'invalid_channel',
        }

        response = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 500

    def test_register_duplicate_channel(self, test_client, auth_headers):
        """测试重复注册检测."""
        payload = {
            'type': 'telegram',
            'name': 'duplicate_bot',
            'config': {'bot_token': 'token1'},
        }

        # 第一次注册成功
        response1 = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response1.status_code == 201

        # 第二次注册应该失败
        response2 = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response2.status_code == 500

    def test_register_requires_auth(self, test_client):
        """测试未认证访问被拒绝."""
        payload = {'type': 'telegram', 'name': 'test'}
        response = test_client.post(
            '/api/v1/channels/register',
            data=json.dumps(payload),
        )
        assert response.status_code == 401


class TestChannelListAPI:
    """测试已注册渠道列表 API."""

    def test_list_registered_empty(self, test_client, auth_headers):
        """测试空列表返回（或已注册渠道列表）."""
        response = test_client.get('/api/v1/channels/registered', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'channels' in data
        assert 'total' in data
        assert data['total'] >= 0
        assert isinstance(data['channels'], list)

    def test_list_registered_with_data(self, test_client, auth_headers):
        """测试有数据时的列表."""
        # 先注册一个渠道
        payload = {
            'type': 'telegram',
            'name': 'listable_bot',
            'config': {},
        }
        test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )

        response = test_client.get('/api/v1/channels/registered', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['total'] >= 1


class TestChannelDetailAndUpdateAPI:
    """测试渠道详情和更新 API."""

    def test_get_channel_success(self, test_client, auth_headers):
        """测试获取渠道详情."""
        # 先注册
        payload = {
            'type': 'slack',
            'name': 'detail_test',
            'config': {'token': 'secret'},
        }
        reg_resp = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        channel_id = reg_resp.get_json()['channel_id']

        response = test_client.get(f'/api/v1/channels/{channel_id}', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['channel_id'] == channel_id
        assert data['type'] == 'slack'

    def test_get_channel_not_found(self, test_client, auth_headers):
        """测试获取不存在的渠道."""
        response = test_client.get(
            '/api/v1/channels/nonexistent:ghost',
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_channel_config(self, test_client, auth_headers):
        """测试更新渠道配置."""
        # 先注册
        payload = {
            'type': 'telegram',
            'name': 'updatable_bot',
            'config': {'bot_token': 'old_token'},
        }
        reg_resp = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        channel_id = reg_resp.get_json()['channel_id']

        # 更新配置
        update_payload = {
            'config': {'bot_token': 'new_token', 'chat_id': 'new_chat'},
            'enabled': False,
        }
        response = test_client.put(
            f'/api/v1/channels/{channel_id}',
            headers=auth_headers,
            data=json.dumps(update_payload),
        )
        assert response.status_code == 200

    def test_update_channel_not_found(self, test_client, auth_headers):
        """测试更新不存在的渠道."""
        payload = {'enabled': False}
        response = test_client.put(
            '/api/v1/channels/ghost:channel',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 404


class TestChannelDeleteAPI:
    """测试渠道注销 API."""

    def test_delete_channel_success(self, test_client, auth_headers):
        """测试成功注销渠道."""
        # 先注册
        payload = {
            'type': 'discord',
            'name': 'deletable_bot',
            'config': {},
        }
        reg_resp = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        channel_id = reg_resp.get_json()['channel_id']

        # 删除
        response = test_client.delete(f'/api/v1/channels/{channel_id}', headers=auth_headers)
        assert response.status_code == 200

        # 验证已删除
        get_resp = test_client.get(f'/api/v1/channels/{channel_id}', headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_channel_not_found(self, test_client, auth_headers):
        """测试删除不存在的渠道."""
        response = test_client.delete(
            '/api/v1/channels/ghost:deleted',
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestChannelSendAndTestAPI:
    """测试消息发送和连接测试 API."""

    def test_send_message_success(self, test_client, auth_headers):
        """测试通过渠道发送消息."""
        # 先注册
        payload = {
            'type': 'telegram',
            'name': 'sender_bot',
            'config': {},
        }
        reg_resp = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        channel_id = reg_resp.get_json()['channel_id']

        # 发送消息
        send_payload = {
            'text': 'Hello from test!',
            'recipient': 'user_123',
        }
        response = test_client.post(
            f'/api/v1/channels/{channel_id}/send',
            headers=auth_headers,
            data=json.dumps(send_payload),
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert 'message_id' in data
        assert 'sent_at' in data

    def test_send_message_missing_text(self, test_client, auth_headers):
        """测试缺少消息文本."""
        # 先注册
        payload = {'type': 'telegram', 'name': 'no_text_bot', 'config': {}}
        reg_resp = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        channel_id = reg_resp.get_json()['channel_id']

        send_payload = {}
        response = test_client.post(
            f'/api/v1/channels/{channel_id}/send',
            headers=auth_headers,
            data=json.dumps(send_payload),
        )
        assert response.status_code == 500

    def test_test_connection(self, test_client, auth_headers):
        """测试渠道连接状态检查."""
        # 先注册
        payload = {
            'type': 'slack',
            'name': 'testable_channel',
            'config': {'token': 'test'},
        }
        reg_resp = test_client.post(
            '/api/v1/channels/register',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        channel_id = reg_resp.get_json()['channel_id']

        response = test_client.post(
            f'/api/v1/channels/{channel_id}/test',
            headers=auth_headers,
            data=json.dumps({}),
        )
        # 允许 200（成功）或 500（适配器不可用）
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.get_json()
            assert 'adapter_available' in data or 'connected' in data


class TestChannelStatsAPI:
    """测试渠道统计 API."""

    def test_get_channels_stats(self, test_client, auth_headers):
        """测试获取聚合统计数据."""
        # 注册几个渠道
        for i in range(3):
            payload = {
                'type': 'telegram',
                'name': f'stats_bot_{i}',
                'config': {},
                'enabled': i % 2 == 0,
            }
            test_client.post(
                '/api/v1/channels/register',
                headers=auth_headers,
                data=json.dumps(payload),
            )

        response = test_client.get('/api/v1/channels/stats', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'total_channels' in data
        assert 'enabled_channels' in data
        assert 'total_messages_sent' in data
        assert 'by_type' in data
        assert data['total_channels'] >= 3
