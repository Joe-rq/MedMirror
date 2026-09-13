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

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CASE_ID = "carotid_plaque_001"
_TRIAL_PREFIX_RE = re.compile(r"[a-z0-9][a-z0-9_-]*")

_TOP_LEVEL_KEYS = {
    "case_id",
    "protocol_version",
    "trial_prefix",
    "case_text",
    "synthetic",
    "variants",
    "extraction",
    "notes",
}
_EXTRACTION_KEYS = {"extractor_version", "paths"}

# 词表不可变登记文件（configs/cases/vocab-registry.json）：版本三元组 → 词表摘要。
# 「同病例改词表=新版本号」红线的机械闸：同 (case_id, protocol_version, extractor_version)
# 的词表一经登记不可变，改词表必须升版本并新增登记。只约束 configs/cases/ 目录内的
# 配置；目录外的第三方自定义路径不强制（其自理纪律）。文件本身入 Git，靠评审审计。
_REGISTRY_NAME = "vocab-registry.json"


def vocab_digest(paths: dict[str, list[str]]) -> str:
    """词表摘要（排序规范化 JSON 的 sha256）：登记与提取/报告同源比对共用。"""
    canonical = json.dumps(paths, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise ValueError(
                f"JSON 含重复键 {key!r}（后者静默覆盖前者，配置表面与执行内容会不一致）"
            )
        seen.add(key)
    return dict(pairs)


def _is_safe_name(name: str) -> bool:
    """标识名（变体名/路径名）：拒绝控制字符与 Markdown 表格分隔符，防破坏 trial_id 与报告结构。"""
    return not any(unicodedata.category(ch) == "Cc" or ch == "|" for ch in name)


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    protocol_version: str
    trial_prefix: str
    case_text: str
    synthetic: bool
    variants: dict[str, str]
    extractor_version: str
    paths: dict[str, list[str]]
    notes: str

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """对象级不变量（评审 R2 P2）：构造期由 __post_init__ 调用，堵
        dataclasses.replace 直造对象绕过 load_case_spec 门禁的路径；
        执行入口（planned_trials/execute_run/as_dict）复检，堵构造后嵌套容器
        直接变异（frozen 只冻结属性重绑定，不冻结 dict/list 内容）。

        词表登记闸（_check_vocab_registry）不在此层：它约束 configs/cases/ 内的
        配置文件不可变，内存对象属调用方自担，入 plan.json 快照供审计。
        """
        for field in ("case_id", "protocol_version", "case_text", "notes"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"CaseSpec.{field} 须为非空字符串")
        if self.synthetic is not True:
            raise ValueError("CaseSpec.synthetic 必须为 true（真实患者数据不入实验）")
        if not _TRIAL_PREFIX_RE.fullmatch(self.trial_prefix):
            raise ValueError(f"CaseSpec.trial_prefix {self.trial_prefix!r} 不合规范")
        if not self.variants:
            raise ValueError("CaseSpec.variants 须为非空对象")
        for name, prompt in self.variants.items():
            if (
                not isinstance(name, str)
                or not name.strip()
                or not _is_safe_name(name)
                or not isinstance(prompt, str)
                or not prompt.strip()
            ):
                raise ValueError(f"CaseSpec.variants[{name!r}] 名称或提示非法")
        if not isinstance(self.extractor_version, str) or not self.extractor_version:
            raise ValueError("CaseSpec.extractor_version 须为非空字符串")
        if not self.paths:
            raise ValueError("CaseSpec.paths 须为非空对象")
        for path_name, terms in self.paths.items():
            if (
                not isinstance(path_name, str)
                or not path_name.strip()
                or not _is_safe_name(path_name)
            ):
                raise ValueError(f"CaseSpec.paths[{path_name!r}] 键非法")
            if not isinstance(terms, list) or not terms:
                raise ValueError(f"CaseSpec.paths[{path_name!r}] 须为非空词表列表")
            for term in terms:
                if not isinstance(term, str) or not term.strip():
                    raise ValueError(f"CaseSpec.paths[{path_name!r}] 含空白或空词项")

    @property
    def extraction_paths(self) -> dict[str, list[str]]:
        return {path: list(terms) for path, terms in self.paths.items()}

    def protocol_facts(self) -> dict[str, Any]:
        """协议事实子集（不含 notes 编辑性字段）：恢复时比对首跑快照用。

        trial_prefix/词表/变体/病例文本任一变化都意味着协议事实变更，不得混入
        同一 run 目录（config_fingerprint 有意不含词表与前缀——请求不受其影响，
        守护在此处补齐，见 runner.config_fingerprint 注释）。
        """
        data = self.as_dict()
        data.pop("notes")
        return data

    def as_dict(self) -> dict[str, Any]:
        """完整快照（入 plan.json 供审计对账：当年用什么词表与变体跑的）。"""
        self.validate()
        return {
            "case_id": self.case_id,
            "protocol_version": self.protocol_version,
            "trial_prefix": self.trial_prefix,
            "case_text": self.case_text,
            "synthetic": self.synthetic,
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


def load_case_spec(path: Path | str, *, supported_extractor_version: str) -> CaseSpec:
    """加载并校验一份 CaseSpec；结构或版本不合规立即拒绝（fail-fast）。

    supported_extractor_version 由调用方传入（protocol.EXTRACTOR_VERSION），
    本模块不持有版本字符串。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"CaseSpec 文件不存在：{path}。新病例须先在 configs/cases/ 落一份"
            " <case_id>.json（字段与校验规则见 configs/cases/README.md）"
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except ValueError as error:
        raise ValueError(f"CaseSpec 不是合法 JSON 或含重复键：{path}（{error}）") from error
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
    # 合成声明用显式布尔而非 notes 关键字：字符串匹配可被「非合成病例」类否定表述绕过，
    # 布尔只接受 true——本系统不接受真实患者数据（intent.md 红线），无可表达的合法假值
    if raw.get("synthetic") is not True:
        raise ValueError(
            f"CaseSpec synthetic 字段必须为 true（缺失或为假均拒绝；"
            f"真实患者数据不入实验，intent.md 红线）：{path}"
        )
    if not _TRIAL_PREFIX_RE.fullmatch(raw["trial_prefix"]):
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
            or not _is_safe_name(name)
            or not isinstance(prompt, str)
            or not prompt.strip()
        ):
            raise ValueError(
                f"CaseSpec variants[{name!r}] 的名称与提示均须为非空字符串，"
                f"且名称不得含控制字符或 |（防破坏 trial_id 与报告结构）：{path}"
            )

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
        if not isinstance(path_name, str) or not path_name.strip() or not _is_safe_name(path_name):
            raise ValueError(f"CaseSpec paths 键须为非空字符串且不含控制字符或 |：{path}")
        if not isinstance(terms, list) or not terms:
            raise ValueError(f"CaseSpec paths[{path_name!r}] 须为非空词表列表：{path}")
        for term in terms:
            if not isinstance(term, str) or not term.strip():
                raise ValueError(
                    f"CaseSpec paths[{path_name!r}] 含空白或空词项（空白词会命中任意文本）：{path}"
                )

    spec = CaseSpec(
        case_id=raw["case_id"],
        protocol_version=raw["protocol_version"],
        trial_prefix=raw["trial_prefix"],
        case_text=raw["case_text"],
        synthetic=True,
        variants=dict(variants),
        extractor_version=extractor_version,
        paths={k: list(v) for k, v in paths.items()},
        notes=raw["notes"],
    )
    _check_vocab_registry(path, spec)
    return spec


def _check_vocab_registry(path: Path, spec: CaseSpec) -> None:
    """同版本词表不可变闸（评审 P1）：cases 目录内的配置受 vocab-registry 约束。

    登记 key = case_id|protocol_version|extractor_version，value = vocab_digest。
    未登记 → 拒绝（新增病例/升版本须显式登记，评审可审计）；已登记但不一致 →
    拒绝（同版本改词表违反「改词表=新版本号」红线）。目录外路径不强制。
    """
    if path.resolve().parent != default_case_dir().resolve():
        return
    registry_path = default_case_dir() / _REGISTRY_NAME
    if not registry_path.exists():
        raise ValueError(
            f"词表登记文件不存在：{registry_path}。cases 目录内的 CaseSpec 须先登记词表摘要"
        )
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    key = f"{spec.case_id}|{spec.protocol_version}|{spec.extractor_version}"
    registered = registry.get(key)
    if registered is None:
        raise ValueError(
            f"CaseSpec {key} 未在 {registry_path} 登记词表摘要；"
            "新增病例或升版本请在登记文件显式追加（走评审）"
        )
    if registered != vocab_digest(spec.paths):
        raise ValueError(
            f"CaseSpec {key} 的词表与登记摘要不一致（登记 {registered[:12]}，"
            f"当前 {vocab_digest(spec.paths)[:12]}）；同病例改词表=新版本号，"
            "请新开版本并新增登记，不得就地改词表"
        )


def load_default_case(*, supported_extractor_version: str) -> CaseSpec:
    return load_case_spec(
        default_case_path(), supported_extractor_version=supported_extractor_version
    )
