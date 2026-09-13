"""病例声明式配置（CaseSpec，issue #50）：把散在代码里的协议事实抽为配置文件。

一份 CaseSpec 描述一个病例的全部协议事实：病例文本、提示变体、trial_id 前缀、
提取词表与版本钉子。第三方自带病例 = 填一份 `configs/cases/<case_id>.json`，
不再改代码（词表经 paths 参数全链路可穿参）。

红线（issue #50 / specs/calibration.md）：
- 同病例改词表 = 新 extractor/protocol 版本号，不回改历史产物；
- CaseSpec 的 extractor_version 与 protocol.py 支持版本不一致时拒绝加载
  （受检版本由调用方传入 protocol.EXTRACTOR_VERSION，本模块不复制版本字符串，
  杜绝第二处版本漂移）。

schema 严格化：未知顶层键与 extraction 内未知键一律拒绝——第三方配置宁报错
勿默吞，加字段 = schema 变更，须显式走版本纪律。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CASE_ID = "carotid_plaque_001"
_TRIAL_PREFIX_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

_TOP_LEVEL_KEYS = {
    "case_id",
    "protocol_version",
    "trial_prefix",
    "case_text",
    "variants",
    "extraction",
    "notes",
}
_EXTRACTION_KEYS = {"extractor_version", "paths"}


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    protocol_version: str
    trial_prefix: str
    case_text: str
    variants: dict[str, str]
    extractor_version: str
    paths: dict[str, list[str]]
    notes: str

    @property
    def extraction_paths(self) -> dict[str, list[str]]:
        return dict(self.paths)

    def as_dict(self) -> dict[str, Any]:
        """完整快照（入 plan.json 供审计对账：当年用什么词表与变体跑的）。"""
        return {
            "case_id": self.case_id,
            "protocol_version": self.protocol_version,
            "trial_prefix": self.trial_prefix,
            "case_text": self.case_text,
            "variants": dict(self.variants),
            "extraction": {
                "extractor_version": self.extractor_version,
                "paths": {k: list(v) for k, v in self.paths.items()},
            },
            "notes": self.notes,
        }


def default_case_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "configs" / "cases"


def default_case_path() -> Path:
    return default_case_dir() / f"{DEFAULT_CASE_ID}.json"


def load_case_spec(path: Path, *, supported_extractor_version: str) -> CaseSpec:
    """加载并校验一份 CaseSpec；结构或版本不合规立即拒绝（fail-fast）。

    supported_extractor_version 由调用方传入（protocol.EXTRACTOR_VERSION），
    本模块不持有版本字符串。
    """
    if not path.exists():
        raise FileNotFoundError(
            f"CaseSpec 文件不存在：{path}。新病例须先在 configs/cases/ 落一份"
            " <case_id>.json（字段与校验规则见 configs/cases/README.md）"
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"CaseSpec 不是合法 JSON：{path}（{error}）") from error
    if not isinstance(raw, dict):
        raise ValueError(f"CaseSpec 顶层必须是对象：{path}")

    unknown = sorted(set(raw) - _TOP_LEVEL_KEYS)
    if unknown:
        raise ValueError(
            f"CaseSpec 含未知顶层键 {unknown}：{path}。schema 封闭，加字段须走版本纪律"
        )

    for key in ("case_id", "protocol_version", "trial_prefix", "case_text", "notes"):
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"CaseSpec 字段 {key} 缺失或为空字符串：{path}")
    if not _TRIAL_PREFIX_RE.match(raw["trial_prefix"]):
        raise ValueError(
            f"CaseSpec trial_prefix {raw['trial_prefix']!r} 不合规范"
            f"（须匹配 {_TRIAL_PREFIX_RE.pattern}）：{path}"
        )

    variants = raw.get("variants")
    if not isinstance(variants, dict) or not variants:
        raise ValueError(f"CaseSpec variants 须为非空对象：{path}")
    for name, prompt in variants.items():
        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(prompt, str)
            or not prompt.strip()
        ):
            raise ValueError(f"CaseSpec variants[{name!r}] 的名称与提示均须为非空字符串：{path}")

    extraction = raw.get("extraction")
    if not isinstance(extraction, dict):
        raise ValueError(f"CaseSpec extraction 须为对象：{path}")
    unknown_extraction = sorted(set(extraction) - _EXTRACTION_KEYS)
    if unknown_extraction:
        raise ValueError(
            f"CaseSpec extraction 含未知键 {unknown_extraction}：{path}。schema 封闭，"
            "加字段须走版本纪律"
        )
    extractor_version = extraction.get("extractor_version")
    if not isinstance(extractor_version, str) or not extractor_version:
        raise ValueError(f"CaseSpec extraction.extractor_version 缺失或为空：{path}")
    if extractor_version != supported_extractor_version:
        raise ValueError(
            f"CaseSpec 钉住的 extractor_version={extractor_version!r} 与当前代码支持版本"
            f" {supported_extractor_version!r} 不一致：{path}。词表与提取器语义绑定，"
            "不匹配不得加载（同病例改词表=新版本号，不回改历史）"
        )
    paths = extraction.get("paths")
    if not isinstance(paths, dict) or not paths:
        raise ValueError(f"CaseSpec extraction.paths 须为非空对象：{path}")
    for path_name, terms in paths.items():
        if not isinstance(path_name, str) or not path_name:
            raise ValueError(f"CaseSpec paths 键须为非空字符串：{path}")
        if not isinstance(terms, list) or not terms:
            raise ValueError(f"CaseSpec paths[{path_name!r}] 须为非空词表列表：{path}")
        for term in terms:
            if not isinstance(term, str) or not term:
                raise ValueError(f"CaseSpec paths[{path_name!r}] 含空词项：{path}")

    return CaseSpec(
        case_id=raw["case_id"],
        protocol_version=raw["protocol_version"],
        trial_prefix=raw["trial_prefix"],
        case_text=raw["case_text"],
        variants=dict(variants),
        extractor_version=extractor_version,
        paths={k: list(v) for k, v in paths.items()},
        notes=raw["notes"],
    )


def load_default_case(*, supported_extractor_version: str) -> CaseSpec:
    return load_case_spec(
        default_case_path(), supported_extractor_version=supported_extractor_version
    )
