"""OpenClaw-Harness MSA 集成配置"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class OCHMSAConfig:
    """OpenClaw-Harness 侧 MSA 集成配置"""

    enabled: bool = False
    model_path: str = "EverMind-AI/MSA-4B"
    devices: list[int] = field(default_factory=lambda: [])
    doc_top_k: int = 16
    pooling_kernel_size: int = 64
    router_layer_idx: str = "all"
    max_generate_tokens: int = 256
    cache_dir: Path | None = None
    encode_on_write: bool = True
    auto_fallback: bool = True
    temperature: float = 0.0
    top_p: float = 0.9
    memory_file_path: str = ""

    def __post_init__(self):
        if self.cache_dir is None:
            from pathlib import Path as _Path

            object.__setattr__(self, "cache_dir", _Path.home() / ".openharness" / "msa_cache")

    @property
    def world_size(self) -> int:
        return len(self.devices) if self.devices else (1 if self._detect_gpu() else 0)

    def _detect_gpu(self) -> bool:
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False
