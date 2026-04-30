"""Plugin Service — manage extensions lifecycle."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PLUGINS_DIR = Path.home() / '.och' / 'plugins'


class PluginService:
    """插件管理服务 — 安装、卸载、启用、禁用插件."""

    def __init__(self):
        self._plugins: Dict[str, Dict] = {}
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

    async def list_plugins(
        self,
        enabled_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """列出已安装插件."""
        plugins = list(self._plugins.values())

        if enabled_only:
            plugins = [p for p in plugins if p.get('enabled')]

        return plugins

    async def get_plugin(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件详情."""
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            return None

        detail = {**plugin}

        # 加载插件元数据
        install_path = plugin.get('install_path')
        if install_path and Path(install_path).exists():
            manifest_path = Path(install_path) / 'plugin.json'
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    detail.update(manifest)
                except Exception as e:
                    logger.warning(f"Failed to load manifest for {plugin_name}: {e}")

        return detail

    async def install_plugin(
        self,
        source: str,
        source_type: str = 'local',
        options: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        安装插件.

        Args:
            source: URL 或本地路径
            source_type: 'local', 'github', 'npm'
            options: 安装选项
        """
        plugin_id = str(uuid.uuid4())
        install_dir = PLUGINS_DIR / plugin_id
        install_dir.mkdir(parents=True, exist_ok=True)

        try:
            if source_type == 'github':
                await self._install_from_github(source, install_dir)
            elif source_type == 'npm':
                await self._install_from_npm(source, install_dir)
            elif source_type == 'local':
                await self._install_from_local(source, install_dir)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")

            # 计算完整性哈希
            integrity_hash = await self._compute_integrity_hash(install_dir)

            # 解析插件元数据
            metadata = await self._parse_plugin_metadata(install_dir)

            plugin_info = {
                'id': plugin_id,
                'name': metadata.get('name', Path(source).stem),
                'version': metadata.get('version', '1.0.0'),
                'description': metadata.get('description', ''),
                'source': source_type,
                'source_url': source,
                'install_path': str(install_dir),
                'enabled': False,  # 默认禁用，需手动启用
                'config': metadata.get('config', {}),
                'has_commands': metadata.get('has_commands', False),
                'has_hooks': metadata.get('has_hooks', False),
                'has_agents': metadata.get('has_agents', False),
                'integrity_hash': integrity_hash,
                'installed_at': datetime.now(timezone.utc).isoformat(),
            }

            self._plugins[plugin_info['name']] = plugin_info

            logger.info(f"Plugin installed: {plugin_info['name']} v{plugin_info['version']}")
            return plugin_info

        except Exception as e:
            logger.error(f"Failed to install plugin from {source}: {e}")
            import shutil
            if install_dir.exists():
                shutil.rmtree(install_dir)
            raise

    async def uninstall_plugin(self, plugin_name: str) -> bool:
        """卸载插件."""
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            return False

        # 先禁用
        if plugin.get('enabled'):
            await self.disable_plugin(plugin_name)

        # 删除文件
        install_path = plugin.get('install_path')
        if install_path and Path(install_path).exists():
            import shutil
            shutil.rmtree(install_path)

        del self._plugins[plugin_name]
        logger.info(f"Plugin uninstalled: {plugin_name}")
        return True

    async def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件."""
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            return False

        # TODO: 执行插件的 enable hooks
        plugin['enabled'] = True
        plugin['updated_at'] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Plugin enabled: {plugin_name}")
        return True

    async def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件."""
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            return False

        # TODO: 执行插件的 disable hooks
        plugin['enabled'] = False
        plugin['updated_at'] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Plugin disabled: {plugin_name}")
        return True

    async def _install_from_github(self, url: str, dest: Path) -> None:
        """从 GitHub 安装插件."""
        import subprocess

        result = subprocess.run(
            ['git', 'clone', '--depth', '1', url, str(dest)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")

    async def _install_from_npm(self, package: str, dest: Path) -> None:
        """从 NPM 安装插件."""
        import subprocess

        result = subprocess.run(
            ['npx', '-y', 'create-openclaw-plugin', package, str(dest)],
            capture_output=True,
            text=True,
            cwd=str(dest.parent),
        )
        if result.returncode != 0:
            raise RuntimeError(f"NPM install failed: {result.stderr}")

    async def _install_from_local(self, path: str, dest: Path) -> None:
        """从本地安装插件."""
        import shutil

        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {path}")

        if source.is_file():
            shutil.copy2(source, dest / source.name)
        else:
            shutil.copytree(source, dest, dirs_exist_ok=True)

    @staticmethod
    async def _compute_integrity_hash(directory: Path) -> str:
        """计算目录内容的 SHA256 哈希."""
        hasher = hashlib.sha256()

        for file_path in sorted(directory.rglob('*')):
            if file_path.is_file():
                hasher.update(str(file_path.relative_to(directory)).encode())
                hasher.update(file_path.read_bytes())

        return hasher.hexdigest()[:32]

    @staticmethod
    async def _parse_plugin_metadata(directory: Path) -> Dict[str, Any]:
        """解析插件元数据."""
        manifest_path = directory / 'plugin.json'

        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass

        # 尝试从 pyproject.toml 解析
        pyproject_path = directory / 'pyproject.toml'
        if pyproject_path.exists():
            pyproject_path.read_text()
            return {
                'name': directory.name,
                'version': '1.0.0',
                'description': f'Plugin: {directory.name}',
            }

        return {
            'name': directory.name,
            'version': '1.0.0',
            'description': '',
        }
