"""Plugin Service 单元测试 — 验证插件生命周期管理."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path


class TestPluginServiceInit:
    """测试 PluginService 初始化."""

    def test_init_creates_plugins_directory(self):
        """测试初始化时创建插件目录."""
        with patch('app.services.plugin_service.PLUGINS_DIR') as mock_dir:
            mock_dir.__truediv__ = MagicMock(return_value=mock_dir)
            mock_dir.mkdir = MagicMock()

            from app.services.plugin_service import PluginService
            PluginService()

            mock_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_init_empty_plugins_dict(self):
        """测试初始化时插件字典为空."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            assert len(service._plugins) == 0


class TestListPlugins:
    """测试插件列表功能."""

    @pytest.fixture
    def service_with_plugins(self):
        """创建包含示例插件的 Service 实例."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()
            service._plugins = {
                'plugin-a': {
                    'name': 'plugin-a',
                    'enabled': True,
                    'version': '1.0.0',
                },
                'plugin-b': {
                    'name': 'plugin-b',
                    'enabled': False,
                    'version': '2.0.0',
                },
            }
            return service

    @pytest.mark.asyncio
    async def test_list_all_plugins(self, service_with_plugins):
        """测试列出所有已安装插件."""
        plugins = await service_with_plugins.list_plugins()

        assert len(plugins) == 2
        names = [p['name'] for p in plugins]
        assert 'plugin-a' in names
        assert 'plugin-b' in names

    @pytest.mark.asyncio
    async def test_list_enabled_only(self, service_with_plugins):
        """测试仅列出启用的插件."""
        plugins = await service_with_plugins.list_plugins(enabled_only=True)

        assert len(plugins) == 1
        assert plugins[0]['name'] == 'plugin-a'
        assert plugins[0]['enabled'] is True

    @pytest.mark.asyncio
    async def test_list_empty_plugins(self):
        """测试空插件列表."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            plugins = await service.list_plugins()
            assert len(plugins) == 0


class TestGetPlugin:
    """测试获取插件详情."""

    @pytest.fixture
    def service_with_installed_plugin(self):
        """创建包含已安装插件的 Service."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()
            service._plugins = {
                'test-plugin': {
                    'name': 'test-plugin',
                    'enabled': True,
                    'install_path': '/fake/path/test-plugin',
                    'version': '1.0.0',
                },
            }
            return service

    @pytest.mark.asyncio
    async def test_get_existing_plugin(self, service_with_installed_plugin):
        """测试获取存在的插件详情."""
        plugin = await service_with_installed_plugin.get_plugin('test-plugin')

        assert plugin is not None
        assert plugin['name'] == 'test-plugin'
        assert plugin['enabled'] is True

    @pytest.mark.asyncio
    async def test_get_nonexistent_plugin(self):
        """测试获取不存在的插件."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            plugin = await service.get_plugin('nonexistent')
            assert plugin is None

    @pytest.mark.asyncio
    async def test_get_plugin_loads_manifest(self, service_with_installed_plugin):
        """测试加载插件清单文件."""
        manifest_data = {
            'description': 'Test plugin description',
            'author': 'Test Author',
            'config': {'key': 'value'},
        }

        with patch.object(Path, 'exists', return_value=True), \
             patch('builtins.open', MagicMock()), \
             patch('json.load', return_value=manifest_data):

            plugin = await service_with_installed_plugin.get_plugin('test-plugin')

            assert plugin['description'] == 'Test plugin description'
            assert plugin['author'] == 'Test Author'

    @pytest.mark.asyncio
    async def test_get_plugin_manifest_load_failure(self, service_with_installed_plugin):
        """测试清单文件加载失败时的容错处理."""
        with patch.object(Path, 'exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("Read error")):

            plugin = await service_with_installed_plugin.get_plugin('test-plugin')

            # 应返回基本信息，不会崩溃
            assert plugin is not None
            assert plugin['name'] == 'test-plugin'


class TestInstallPlugin:
    """测试插件安装功能."""

    @pytest.fixture
    def service(self):
        """创建干净的 Service 实例."""
        with patch('app.services.plugin_service.PLUGINS_DIR') as mock_dir:
            mock_dir.__truediv__ = MagicMock(return_value=MagicMock(spec=Path))
            mock_dir.mkdir = MagicMock()

            from app.services.plugin_service import PluginService
            return PluginService()

    @pytest.mark.asyncio
    async def test_install_from_local_success(self, service):
        """测试从本地路径成功安装插件."""
        mock_dest = MagicMock(spec=Path)
        mock_dest.__truediv__ = MagicMock(return_value=mock_dest)
        mock_dest.mkdir = MagicMock()

        with patch.object(service, '_install_from_local', new_callable=AsyncMock), \
             patch.object(service, '_compute_integrity_hash', new_callable=AsyncMock, return_value='abc123'), \
             patch.object(service, '_parse_plugin_metadata', new_callable=AsyncMock, return_value={
                 'name': 'local-plugin',
                 'version': '1.0.0',
                 'description': 'Local test plugin',
             }), \
             patch('app.services.plugin_service.PLUGINS_DIR') as mock_plugins_dir:

            mock_plugins_dir.__truediv__ = MagicMock(return_value=mock_dest)

            result = await service.install_plugin(
                source='/path/to/plugin',
                source_type='local',
            )

            assert result['name'] == 'local-plugin'
            assert result['version'] == '1.0.0'
            assert result['enabled'] is False  # 默认禁用
            assert result['source'] == 'local'
            assert result['integrity_hash'] == 'abc123'

            # 验证插件已注册
            assert 'local-plugin' in service._plugins

    @pytest.mark.asyncio
    async def test_install_from_github(self, service):
        """测试从 GitHub 安装插件."""
        mock_dest = MagicMock(spec=Path)
        mock_dest.__truediv__ = MagicMock(return_value=mock_dest)
        mock_dest.mkdir = MagicMock()

        with patch.object(service, '_install_from_github', new_callable=AsyncMock), \
             patch.object(service, '_compute_integrity_hash', new_callable=AsyncMock, return_value='hash456'), \
             patch.object(service, '_parse_plugin_metadata', new_callable=AsyncMock, return_value={
                 'name': 'github-plugin',
                 'version': '2.0.0',
             }), \
             patch('app.services.plugin_service.PLUGINS_DIR') as mock_plugins_dir:

            mock_plugins_dir.__truediv__ = MagicMock(return_value=mock_dest)

            result = await service.install_plugin(
                source='https://github.com/user/repo',
                source_type='github',
            )

            assert result['name'] == 'github-plugin'
            assert result['source_url'] == 'https://github.com/user/repo'

    @pytest.mark.asyncio
    async def test_install_unsupported_source_type(self, service):
        """测试不支持的安装源类型."""
        with pytest.raises(ValueError, match="Unsupported source type"):
            await service.install_plugin(
                source='some-source',
                source_type='invalid_type',
            )

    @pytest.mark.asyncio
    async def test_install_cleanup_on_failure(self, service):
        """测试安装失败时清理临时目录."""
        mock_dest = MagicMock(spec=Path)
        mock_dest.exists.return_value = True
        mock_dest.__truediv__ = MagicMock(return_value=mock_dest)
        mock_dest.mkdir = MagicMock()

        with patch.object(service, '_install_from_local', new_callable=AsyncMock, side_effect=RuntimeError("Install failed")), \
             patch('app.services.plugin_service.PLUGINS_DIR') as mock_plugins_dir, \
             patch('shutil.rmtree') as mock_rmtree:

            mock_plugins_dir.__truediv__ = MagicMock(return_value=mock_dest)

            with pytest.raises(RuntimeError):
                await service.install_plugin('/bad/path', 'local')

            # 验证失败后清理了目录
            mock_rmtree.assert_called_once()


class TestUninstallPlugin:
    """测试插件卸载功能."""

    @pytest.fixture
    def service_with_plugin(self):
        """创建包含可卸载插件的 Service."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()
            service._plugins = {
                'removable-plugin': {
                    'name': 'removable-plugin',
                    'enabled': True,
                    'install_path': '/tmp/plugins/removable-plugin',
                },
            }
            return service

    @pytest.mark.asyncio
    async def test_uninstall_existing_plugin(self, service_with_plugin):
        """测试成功卸载已安装的插件."""
        with patch.object(Path, 'exists', return_value=True), \
             patch('shutil.rmtree') as mock_rmtree, \
             patch.object(service_with_plugin, 'disable_plugin', new_callable=AsyncMock, return_value=True):

            result = await service_with_plugin.uninstall_plugin('removable-plugin')

            assert result is True
            assert 'removable-plugin' not in service_with_plugin._plugins
            mock_rmtree.assert_called_once()

    @pytest.mark.asyncio
    async def test_uninstall_nonexistent_plugin(self):
        """测试卸载不存在的插件."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            result = await service.uninstall_plugin('ghost-plugin')
            assert result is False

    @pytest.mark.asyncio
    async def test_uninstall_disabled_plugin_first(self, service_with_plugin):
        """测试卸载前先禁用插件."""
        service_with_plugin._plugins['removable-plugin']['enabled'] = True

        with patch.object(Path, 'exists', return_value=True), \
             patch('shutil.rmtree'), \
             patch.object(service_with_plugin, 'disable_plugin', new_callable=AsyncMock) as mock_disable:

            await service_with_plugin.uninstall_plugin('removable-plugin')

            # 验证在卸载前调用了 disable
            mock_disable.assert_called_once_with('removable-plugin')


class TestEnableDisablePlugin:
    """测试插件启用/禁用功能."""

    @pytest.fixture
    def service_with_toggleable_plugin(self):
        """创建支持启用/禁用的插件."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()
            service._plugins = {
                'toggleable': {
                    'name': 'toggleable',
                    'enabled': False,
                },
            }
            return service

    @pytest.mark.asyncio
    async def test_enable_plugin_success(self, service_with_toggleable_plugin):
        """测试成功启用插件."""
        result = await service_with_toggleable_plugin.enable_plugin('toggleable')

        assert result is True
        assert service_with_toggleable_plugin._plugins['toggleable']['enabled'] is True
        assert 'updated_at' in service_with_toggleable_plugin._plugins['toggleable']

    @pytest.mark.asyncio
    async def test_disable_plugin_success(self, service_with_toggleable_plugin):
        """测试成功禁用插件."""
        # 先启用
        await service_with_toggleable_plugin.enable_plugin('toggleable')

        result = await service_with_toggleable_plugin.disable_plugin('toggleable')

        assert result is True
        assert service_with_toggleable_plugin._plugins['toggleable']['enabled'] is False

    @pytest.mark.asyncio
    async def test_enable_nonexistent_plugin(self):
        """测试启用不存在的插件."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            result = await service.enable_plugin('ghost')
            assert result is False

    @pytest.mark.asyncio
    async def test_disable_nonexistent_plugin(self):
        """测试禁用不存在的插件."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            result = await service.disable_plugin('ghost')
            assert result is False

    @pytest.mark.asyncio
    async def test_toggle_plugin_multiple_times(self, service_with_toggleable_plugin):
        """测试多次切换插件状态."""
        # 初始状态: disabled
        assert service_with_toggleable_plugin._plugins['toggleable']['enabled'] is False

        # 第一次启用
        await service_with_toggleable_plugin.enable_plugin('toggleable')
        assert service_with_toggleable_plugin._plugins['toggleable']['enabled'] is True

        # 禁用
        await service_with_toggleable_plugin.disable_plugin('toggleable')
        assert service_with_toggleable_plugin._plugins['toggleable']['enabled'] is False

        # 再次启用
        await service_with_toggleable_plugin.enable_plugin('toggleable')
        assert service_with_toggleable_plugin._plugins['toggleable']['enabled'] is True


class TestInstallFromLocal:
    """测试本地安装逻辑."""

    @pytest.mark.asyncio
    async def test_copy_file(self):
        """测试复制单个文件."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            mock_source = MagicMock(spec=Path)
            mock_source.exists.return_value = True
            mock_source.is_file.return_value = True
            mock_source.name = 'plugin.zip'

            mock_dest = MagicMock(spec=Path)
            mock_dest.__truediv__ = MagicMock(return_value=mock_dest)

            with patch('shutil.copy2') as mock_copy, \
                 patch('app.services.plugin_service.Path', return_value=mock_source):

                await service._install_from_local('/path/to/file.zip', mock_dest)
                mock_copy.assert_called_once()

    @pytest.mark.asyncio
    async def test_copy_directory(self):
        """测试复制整个目录."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            mock_source = MagicMock(spec=Path)
            mock_source.exists.return_value = True
            mock_source.is_file.return_value = False  # 是目录

            mock_dest = MagicMock(spec=Path)

            with patch('shutil.copytree') as mock_copytree, \
                 patch('app.services.plugin_service.Path', return_value=mock_source):

                await service._install_from_local('/path/to/dir', mock_dest)
                mock_copytree.assert_called_once()

    @pytest.mark.asyncio
    async def test_source_not_found(self):
        """测试源路径不存在."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            mock_dest = MagicMock(spec=Path)

            with patch('app.services.plugin_service.Path') as mock_path_cls:
                mock_instance = MagicMock(spec=Path)
                mock_instance.exists.return_value = False
                mock_path_cls.return_value = mock_instance

                with pytest.raises(FileNotFoundError, match="Source not found"):
                    await service._install_from_local('/nonexistent/path', mock_dest)


class TestComputeIntegrityHash:
    """测试完整性哈希计算."""

    @pytest.mark.asyncio
    async def test_compute_hash_for_directory(self):
        """测试计算目录哈希值 — 使用临时目录."""
        import tempfile

        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            # 创建真实临时目录用于哈希计算测试
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)

                # 创建测试文件
                (tmp_path / 'file1.txt').write_text('content1')
                (tmp_path / 'file2.txt').write_text('content2')

                hash_result = await service._compute_integrity_hash(tmp_path)

                assert isinstance(hash_result, str)
                assert len(hash_result) == 32  # 截断为32字符

    @pytest.mark.asyncio
    async def test_compute_hash_empty_directory(self):
        """测试空目录的哈希值."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            mock_dir = MagicMock(spec=Path)
            mock_dir.rglob.return_value = []  # 空目录

            hash_result = await service._compute_integrity_hash(mock_dir)

            assert isinstance(hash_result, str)
            assert len(hash_result) == 32


class TestParsePluginMetadata:
    """测试插件元数据解析."""

    @pytest.mark.asyncio
    async def test_parse_from_plugin_json(self):
        """测试从 plugin.json 解析元数据."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            expected_metadata = {
                'name': 'my-plugin',
                'version': '3.0.0',
                'description': 'A test plugin',
                'has_commands': True,
                'has_hooks': False,
            }

            mock_manifest = MagicMock(spec=Path)
            mock_manifest.exists.return_value = True

            with patch('builtins.open', MagicMock()), \
                 patch('json.load', return_value=expected_metadata), \
                 patch('app.services.plugin_service.Path') as mock_path_cls:

                mock_path_cls.return_value.__truediv__.return_value = mock_manifest

                result = await service._parse_plugin_metadata(MagicMock())

                assert result['name'] == 'my-plugin'
                assert result['version'] == '3.0.0'
                assert result['has_commands'] is True

    @pytest.mark.asyncio
    async def test_parse_fallback_to_pyproject(self):
        """测试回退到 pyproject.toml 解析."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            mock_dir = MagicMock(spec=Path)
            mock_dir.name = 'fallback-plugin'

            # plugin.json 不存在
            mock_manifest = MagicMock(spec=Path)
            mock_manifest.exists.return_value = False

            # pyproject.toml 存在
            mock_pyproject = MagicMock(spec=Path)
            mock_pyproject.exists.return_value = True
            mock_pyproject.read_text.return_value = '[tool.poetry]\nname = "test"'

            with patch('builtins.open', side_effect=IOError("No manifest")), \
                 patch('app.services.plugin_service.Path') as mock_path_cls:

                mock_path_cls.return_value.__truediv__.side_effect = [mock_manifest, mock_pyproject]

                result = await service._parse_plugin_metadata(mock_dir)

                assert result['name'] == 'fallback-plugin'
                assert result['version'] == '1.0.0'

    @pytest.mark.asyncio
    async def test_parse_no_metadata_files(self):
        """测试无任何元数据文件时的默认值."""
        with patch('app.services.plugin_service.PLUGINS_DIR'):
            from app.services.plugin_service import PluginService
            service = PluginService()

            mock_dir = MagicMock(spec=Path)
            mock_dir.name = 'unknown-plugin'

            # 直接调用方法并验证返回默认元数据（无清单文件时）
            result = await service._parse_plugin_metadata(mock_dir)

            assert result['name'] == 'unknown-plugin'
            assert result['version'] == '1.0.0'
            # 当没有任何元数据文件时，description 应该为空或包含插件名
