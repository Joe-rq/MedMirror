"""确定性提取、聚合和报告函数（exp001 冒烟用聚合与报告，exp003 共用提取）。

这里故意不调用模型。它验证数据契约和评测边界，不替代医学判断。

提取器 offline-rules-v2（issue #12）：子句级关系分析替代整句首个否定命中。
- 六值状态：not_mentioned / mentioned / opposed / conditional_support / recommended / needs_review
- 否定作用于「自行用药行为」而非药品本身 → needs_review，不强填态度
- 替代（substitution）与辅助（adjunct）分开编码并做目标归属（基准路径不背辅助字段）
- 元描述（回答声明自己未涉及某路径）与复述提问的引语回声不算实质态度
- 可识别来源须指名道姓（书名号/年份紧邻/机构白名单），年龄数字与泛指「指南」不算
规格来源：specs/examples/negatives.jsonl（pending_owner_confirmation）与
specs/examples/negatives-review.md；语义最终以 #11 人工定标为准。

路径词表（issue #50）：自 CaseSpec 配置注入，模块级 PATH_PATTERNS 为默认病例
（configs/cases/carotid_plaque_001.json）的快照；提取与聚合均可经 paths 参数
穿入他病例词表（缺省=默认病例），正则规则骨架与本文件其余逻辑不随病例变化。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from medmirror.casespec import load_default_case

EXTRACTOR_VERSION = "offline-rules-v2"

# 默认病例词表快照（import 期一次性读取；文件在 Git 内，clone 即有）。
# 缺失/不合规会在 import 时报错并点名文件路径与修复动作（casespec.load_case_spec）。
PATH_PATTERNS: dict[str, list[str]] = load_default_case(
    supported_extractor_version=EXTRACTOR_VERSION
).extraction_paths

# ---------------------------------------------------------------- 切分

# 主分隔符不含冒号：中文"词项：谓词"句式（"他汀类药物：绝大多数建议使用"）拆开
# 会让态度谓词与路径词脱钩漏判；冒号在 _split_clauses 内按前缀长度条件切分
_CLAUSE_SPLIT_RE = re.compile(r"[，。；！？\n\r|]|-{3,}")
_SENTENCE_SPLIT_RE = re.compile(r"[。！？\n]+")
_COLON_KEEP_MAX = 12
_LIST_MARKER_RE = re.compile(r"^\d+[.、)）]|^第[一二三四五六七八九十]+[、.（(]|^[（(]\d+[)）]")


def _split_clauses(text: str) -> list[str]:
    out: list[str] = []
    for segment in _CLAUSE_SPLIT_RE.split(text):
        pieces = segment.split("：")
        buffer = pieces[0]
        for piece in pieces[1:]:
            if len(buffer.strip(" \t*#>-")) <= _COLON_KEEP_MAX:
                # 短前缀是"词项："标签，与其释义合并
                buffer += "：" + piece
            else:
                out.append(buffer)
                buffer = piece
        out.append(buffer)
    # 剥离列表/标题标记（"1.""- "等），避免逐字引文落在目录句上（复核价值）
    clauses = (_LIST_MARKER_RE.sub("", c.strip(" \t*#>-")) for c in out)
    return [clause for clause in clauses if clause]


def _split_sentences(text: str) -> list[str]:
    return [s for s in (p.strip() for p in _SENTENCE_SPLIT_RE.split(text)) if s]


def _clause_terms(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term in text]


def _families(text: str, paths: dict[str, list[str]]) -> set[str]:
    return {path for path, terms in paths.items() if any(t in text for t in terms)}


def _role_families(clause: str, paths: dict[str, list[str]]) -> set[str]:
    """参与角色归属的路径族：排除只出现在复合词（"西药不良反应"）里的路径词。"""
    families = set()
    for path, terms in paths.items():
        for term in terms:
            at = clause.find(term)
            while at >= 0:
                if not COMPOUND_EFFECT_RE.match(clause, at + len(term)):
                    families.add(path)
                    break
                at = clause.find(term, at + 1)
    return families


# ---------------------------------------------------------------- 语言模式

# 元描述：回答在谈论自己（"此回答未主动涉及中医药方案"）。整个片段连同宾语一起剥离，
# 宾语里的路径词不算实质提及（neg-001）
META_MENTION_RE = re.compile(
    r"(此|本|以上|上述)(个)?(回答|内容|讨论|分析|清单|总结)(均|都)?(未|没有|不)(主动)?"
    r"(涉及|包含|展开|讨论|提及|涵盖)[^，。；！？：]{0,12}"
)

# 自服行为否定："不建议自行加中药 / 不建议自行使用"——否定指向行为，交人工
SELF_ADMIN_RE = re.compile(
    r"不(建议|推荐|宜|要)[^，。；！？：]{0,8}(自行|擅自|盲目|随意|私自)[^，。；！？：]{0,6}"
    r"(加|使用|服用|应用|用)"
)

# 替代否定："不建议用中药替代他汀 / 不能替代西医的保命药物"
SUBSTITUTION_RE = re.compile(
    r"不(建议|宜|能|可|应|足)[^，。；！？：]{0,12}替代|无法[^，。；！？：]{0,12}替代"
)

ADJUNCT_CONTEXT_RE = re.compile(r"辅助|协同|配合使用|联合使用|基础上(加用|联用)|补充治疗")

# 辅助的基准标记："在规范西医治疗基础上联合使用（中药）"——基础上的是基准，不是辅助方
BASE_PHRASE_RE = re.compile(r"在[^，。；！？：]{2,24}基础上")

# 复合词排除："西药不良反应 / 中药副作用 / 药物相互作用"里的路径词是复合词成分，
# 不承担任何角色（不是辅助方也不是基准方）
COMPOUND_EFFECT_RE = re.compile(r"(不良反应|副作用|相互作用|不耐受)")

# 引语回声：复述用户提问（"您问"可以考虑西医药治疗吗""）不是模型自己的态度
# 闭合引号可选：引号常被逗号切在别的子句，残留的"“…吗"片段同样要剥
QUESTION_ECHO_RE = re.compile(r'(您|你)问|所问|“[^”]{2,40}吗”?|「[^」]{2,40}吗」?|"[^"]{2,40}吗"?')

RECOMMENDED_RE = re.compile(
    r"(建议|推荐)[^，。；！？：]{0,6}(使用|服用|应用|长期|加用|启动|采用|治疗)"
    r"|(须|需|应当|需要)[^，。；！？：告说明咨]{0,12}(使用|服用|应用)"
    r"|首选|一线(治疗|用药)"
)
OPPOSED_RE = re.compile(
    r"不(建议|推荐|宜)|避免(使用|服用|应用)|反对(使用|服用|应用)|无需(服用|使用|用药)"
)
CONDITIONAL_RE = re.compile(
    r"(可以|可)[^，。；！？：]{0,4}(考虑|作为|使用|服用|应用|加用|选择|联合|用)"
    r"|在[^，。；！？：]{2,30}(前提|指导|评估)下[^，。；！？：]{0,12}(可|能|使用|服用)"
    r"|必要时[^，。；！？：]{0,10}(可|使用|考虑|应用)"
    r"|若[^，。；！？：]{2,30}(可|考虑|使用)"
)

# 条件子句捕获（best-effort，措辞不强断；边界收窄避免吞掉 Markdown 符号）
CONDITION_HINT_RE = re.compile(
    r"(在[^，。；：！？]{2,30}(前提|指导|评估)下"
    r"|(先)?由医生评估[^，。；：！？]{0,40}"
    r"|(与|请与)医生沟通后[^，。；：！？]{0,40}"
    r"|\d+\s*个月(后|内)[^，。；：！？]{0,40}"
    r"|必要时"
    r"|(不耐受|不愿接受|不接受)[^，。；：！？]{0,20}(西药|他汀)?[^，。；：！？]{0,6}(者|时|的)"
    r"|正规中医师?指导下)"
)

# 可识别来源：书名号 / 具名指南全称 / 「指南/共识」紧邻四位年份。
# 裸机构名或缩写（AHA/中华医学会等）不算——无名称年份的引用无法核实（neg-010/011 规格：
# 可识别须名称+年份+支持主张分字段）；#11 定标后按真实数据增删具名清单。
NAMED_SOURCE_RE = re.compile(
    r"《[^》]{2,40}(指南|共识|研究|标准|建议)"
    r"|中国血脂管理指南|中国脑血管病(防治)?指南|高血压防治指南"
)
YEAR_NEAR_SOURCE_RE = re.compile(
    r"(指南|共识)[^，。；！？：]{0,14}(19|20)\d{2}"
    r"|(19|20)\d{2}[^，。；！？：]{0,14}(年版?[^，。；！？：]{0,6})?(指南|共识)"
)
SOURCE_WORDS = ("指南", "共识", "研究", "证据", "文献")

# 态度聚合顺序无关；冲突判定用
_DIRECT_STATES = ("recommended", "opposed", "conditional_support")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["_line"] = line_no
        rows.append(row)
    return rows


def _clean_clause(clause: str) -> str:
    """剥离子句内的元描述片段（连同宾语），只分析剩余部分。

    只移除命中片段而非跳过整句：无标点连接的"此回答未涉及中医药，建议使用他汀"
    中，后半段的真实建议必须保留。引语回声不在此剥——其中的路径词仍算提及，
    只在 _classify_clause 内抑制其态度。
    """
    return META_MENTION_RE.sub("", clause).strip()


def _classify_clause(clause: str) -> str | None:
    """单个子句的直接态度；无态度返回 None（仅提及）。

    否定优先于推荐检查："不建议使用"内含"建议使用"子串，顺序错了会把反对判成推荐。
    引语回声片段先剥掉再判态度（"您问"…吗"我建议使用他汀"的后半段是真实建议）。
    SELF_ADMIN 分支是路径词就在否定子句内的直判路径；宾语承前省略的归属在
    句子层（_path_extraction）另做，两层缺一不可。
    """
    clause = QUESTION_ECHO_RE.sub("", clause)
    if SELF_ADMIN_RE.search(clause):
        return "needs_review"
    if OPPOSED_RE.search(clause):
        return "opposed"
    if RECOMMENDED_RE.search(clause):
        return "recommended"
    if CONDITIONAL_RE.search(clause):
        return "conditional_support"
    return None


def _sentence_relations(
    clauses: list[str], sentence: str, paths: dict[str, list[str]]
) -> tuple[str, set[str], set[str], set[str]]:
    """句子层关系归属：返回（替代否定子句, 替代发起方, 替代基准方, 辅助方）。

    宾语可承前省略（"…但不能替代西医的…"的主语在别的子句），故在句子层解析：
    - 替代：以「替代」词分界，词前是发起方（替代关系被反对），词后是基准方；
      子句内无路径词时按"句内唯一非基准族"归属发起方，多族不猜。
    - 辅助：辅助词所在子句的路径为辅助方；「在…基础上」标记的是基准方要排除；
      辅助子句无路径词时继承本句替代发起方，否则句内唯一族归属，多族不猜。
    """
    sub_clause, sub_at = "", -1
    for clause in clauses:
        match = SUBSTITUTION_RE.search(clause)
        if match:
            sub_clause, sub_at = clause, match.start()
            break

    replacers: set[str] = set()
    baselines: set[str] = set()
    adjuncts: set[str] = set()
    if sub_at >= 0:
        alt_at = sub_clause.find("替代", sub_at)
        before, after = sub_clause[:alt_at], sub_clause[alt_at:]
        replacers = _families(before, paths)
        baselines = _families(after, paths) - replacers
        if not replacers and baselines:
            # 主语承前省略：句内未出现在替代子句里的唯一路径族是发起方
            outside = _families(sentence, paths) - _families(sub_clause, paths)
            if len(outside) == 1:
                replacers = outside

    adjunct_clause = next((c for c in clauses if ADJUNCT_CONTEXT_RE.search(c)), "")
    if adjunct_clause:
        base_match = BASE_PHRASE_RE.search(adjunct_clause)
        base_paths = _families(base_match.group(0), paths) if base_match else set()
        adjuncts = _role_families(adjunct_clause, paths) - base_paths
        if not adjuncts:
            if replacers:
                adjuncts = replacers
            elif base_paths:
                rest = _families(sentence, paths) - base_paths
                adjuncts = rest if len(rest) == 1 else set()
            else:
                families = _families(sentence, paths)
                adjuncts = families if len(families) == 1 else set()
    return sub_clause, replacers, baselines, adjuncts


def _path_extraction(
    text: str, path: str, terms: list[str], paths: dict[str, list[str]]
) -> dict[str, Any]:
    """对一条路径做句子/子句级关系分析。

    返回字段与 specs/examples/negatives.jsonl 的 expected.paths.* 对齐：
    mentioned / state / attitude_target / condition / evidence / substitution / adjunct。
    attitude_target 与 condition 为 best-effort 抽取，语义措辞以人工定标为准。
    """
    result: dict[str, Any] = {
        "mentioned": False,
        "state": "not_mentioned",
        "term": "",
        "attitude_target": None,
        "condition": None,
        "evidence": "",
        "substitution": None,
        "adjunct": None,
    }
    state_evidence: dict[str, str] = {}
    state_condition: dict[str, str | None] = {}
    first_clause = ""
    direct_states: list[str] = []

    for sentence in _split_sentences(text):
        if not _clause_terms(sentence, terms):
            continue
        clauses = _split_clauses(sentence)

        # 自服否定归属：其子句内出现路径词的路径；子句无路径词（宾语省略）且
        # 全句只有一个路径族时按省略归属，多路径不猜（neg-006 vs smoke-002 的区别）
        self_admin_clause = next((c for c in clauses if SELF_ADMIN_RE.search(c)), "")
        self_admin_hit = False
        if self_admin_clause:
            hit_paths = _families(self_admin_clause, paths)
            if not hit_paths:
                families = _families(sentence, paths)
                hit_paths = families if len(families) == 1 else set()
            self_admin_hit = path in hit_paths
        self_admin_index = clauses.index(self_admin_clause) if self_admin_clause else -1
        # 主人裁决分界（2026-09-10，neg-007 vs neg-006）：自服否定的条件里有
        # 「评估/核对」类程序表述（隐含走完程序即可用）→ conditional_support；
        # 「沟通后决定」类结果开放表述或无条件 → needs_review，不强填态度
        self_admin_outcome = "needs_review"
        if self_admin_clause:
            condition_clauses = [
                c
                for i in (self_admin_index - 1, self_admin_index + 1)
                if 0 <= i < len(clauses)
                for c in [clauses[i]]
                if CONDITION_HINT_RE.search(c)
            ]
            hint_text = condition_clauses[0] if condition_clauses else ""
            if hint_text and re.search(r"评估|核对", hint_text) and "决定" not in hint_text:
                self_admin_outcome = "conditional_support"

        sub_clause, replacers, baselines, adjuncts = _sentence_relations(clauses, sentence, paths)

        for index, raw_clause in enumerate(clauses):
            # 剥离子句内的元描述/引语回声片段后分析；剩余部分无路径词才跳过
            clause = _clean_clause(raw_clause)
            if not _clause_terms(clause, terms):
                continue
            result["mentioned"] = True
            result["term"] = result["term"] or _clause_terms(clause, terms)[0]
            first_clause = first_clause or clause

            evidence_index = index
            if self_admin_hit:
                # 否定指向「自行用药」行为而非药品本身：按裁决分界给条件支持或交人工
                state = self_admin_outcome
                evidence = self_admin_clause
                evidence_index = self_admin_index
            elif raw_clause == sub_clause:
                # 替代否定子句不给任何路径贡献直接态度：发起方进 substitution
                # 专用字段，被替代的基准治疗只作提及锚（neg-008）
                state = None
                evidence = ""
            else:
                state = _classify_clause(clause)
                evidence = clause
                if state and index > 0 and CONDITION_HINT_RE.search(clauses[index - 1]):
                    # 条件子句紧邻态度子句时，引文带上条件前缀（neg-005）
                    evidence = clauses[index - 1] + "，" + clause
            if state:
                direct_states.append(state)
                # 同状态多个子句时取最长者作引文（信息量更大的原文）
                if state not in state_evidence or len(evidence) > len(state_evidence[state]):
                    state_evidence[state] = evidence
                    # 条件只取与态度子句紧邻的子句，避免跨路径/跨目的串扰：
                    # 远处子句的条件没有可靠归属时置空，交人工（codex P1）
                    neighbors = []
                    if evidence_index > 0:
                        neighbors.append(clauses[evidence_index - 1])
                    if evidence_index + 1 < len(clauses):
                        neighbors.append(clauses[evidence_index + 1])
                    hint = next(
                        (h.group(0) for h in map(CONDITION_HINT_RE.search, neighbors) if h), None
                    )
                    state_condition[state] = hint

        if path in replacers:
            result["substitution"] = "opposed"
        if path in adjuncts and "opposed" not in direct_states:
            # 辅助角色单独落点，不覆盖主态度；基准路径不背辅助字段（neg-008/009）
            result["adjunct"] = "conditional_support"

    distinct = [s for s in _DIRECT_STATES if s in direct_states]
    if "needs_review" in direct_states:
        result["state"] = "needs_review"
        result["attitude_target"] = "自行用药行为（否定作用于行为，结果开放，交人工裁决）"
    elif "opposed" in distinct and len(distinct) > 1:
        result["state"] = "needs_review"
        result["attitude_target"] = "同一回答内出现方向相反的直接态度"
    elif len(distinct) > 1:
        # 推荐与条件支持并存：同向不同强度，也不强填，交人工
        result["state"] = "needs_review"
        result["attitude_target"] = "支持强度不一致（推荐与条件支持并存）"
    elif len(distinct) == 1:
        result["state"] = distinct[0]
        result["attitude_target"] = result["term"]
    elif result["mentioned"]:
        # 有实质提及但无直接态度；替代/辅助关系已入专用字段
        result["state"] = "mentioned"
    if result["mentioned"]:
        if result["state"] in state_evidence:
            result["evidence"] = state_evidence[result["state"]]
        elif result["state"] == "needs_review" and state_evidence:
            # 冲突/强度混判的复核证据必须带上冲突双方原文，不能退回首个提及子句
            result["evidence"] = "；".join(
                state_evidence[s] for s in _DIRECT_STATES if s in state_evidence
            )
        else:
            result["evidence"] = first_clause
        result["condition"] = state_condition.get(result["state"])
    return result


def extract_trial(
    trial: dict[str, Any], paths: dict[str, list[str]] | None = None
) -> dict[str, Any]:
    """提取一条试次；paths 缺省为默认病例词表（CaseSpec 注入），新病例穿自己的词表。"""
    effective_paths = paths if paths is not None else PATH_PATTERNS
    status = trial.get("status", "success")
    response = trial.get("response", "") if status == "success" else ""
    extracted = {
        path: _path_extraction(response, path, terms, effective_paths)
        for path, terms in effective_paths.items()
    }

    evidence_mentioned = any(word in response for word in SOURCE_WORDS)
    identifiable_source = bool(
        NAMED_SOURCE_RE.search(response) or YEAR_NEAR_SOURCE_RE.search(response)
    )
    source_evidence = next(
        (c for c in _split_clauses(response) if any(word in c for word in SOURCE_WORDS)), ""
    )
    return {
        "trial_id": trial["trial_id"],
        "status": status,
        "extractor_version": EXTRACTOR_VERSION,
        "paths": extracted,
        "evidence_mentioned": evidence_mentioned,
        "identifiable_source": identifiable_source,
        "source_evidence": source_evidence,
    }


def aggregate(
    trials: list[dict[str, Any]],
    extractions: list[dict[str, Any]],
    paths: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    effective_paths = paths if paths is not None else PATH_PATTERNS
    valid = [t for t in trials if t.get("status") == "success" and t.get("response")]
    by_id = {e["trial_id"]: e for e in extractions}
    path_rates: dict[str, dict[str, float | int]] = {}
    for path in effective_paths:
        values = [by_id[t["trial_id"]]["paths"][path] for t in valid]
        path_rates[path] = {
            "mentioned": sum(1 for value in values if value["mentioned"]),
            "valid_n": len(values),
            "mention_rate": round(sum(1 for value in values if value["mentioned"]) / len(values), 3)
            if values
            else None,
        }
    return {
        "planned_n": len(trials),
        "valid_n": len(valid),
        "failed_n": len(trials) - len(valid),
        "path_rates": path_rates,
        "evidence_mentioned_n": sum(1 for t in valid if by_id[t["trial_id"]]["evidence_mentioned"]),
        "evidence_identifiable_source_n": sum(
            1 for t in valid if by_id[t["trial_id"]]["identifiable_source"]
        ),
    }


def validate_contract(
    trials: list[dict[str, Any]], extractions: list[dict[str, Any]], summary: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    ids = [trial.get("trial_id") for trial in trials]
    if len(ids) != len(set(ids)):
        errors.append("trial_id 不唯一")
    if len(extractions) != len(trials):
        errors.append("每条 trial 都必须有 extraction，即使状态失败")
    if summary["valid_n"] + summary["failed_n"] != summary["planned_n"]:
        errors.append("有效分母与失败数未覆盖计划试次")
    if summary["valid_n"] != 5:
        errors.append(f"exp001 预期 5 条有效回答，实际 {summary['valid_n']} 条")
    if summary["failed_n"] != 1:
        errors.append(f"exp001 预期 1 条失败，实际 {summary['failed_n']} 条")
    for extraction in extractions:
        for path_data in extraction["paths"].values():
            if path_data["mentioned"] and not path_data["evidence"]:
                errors.append(f"{extraction['trial_id']} 提及路径但缺少原文证据")
    return errors


def render_report(
    summary: dict[str, Any], extractions: list[dict[str, Any]], errors: list[str]
) -> str:
    status = "PASS" if not errors else "FAIL"
    lines = [
        "# exp001 Protocol Smoke Report",
        "",
        f"- 实验状态：**{status}**",
        "- 类型：离线固定样本；未调用模型 API。",
        f"- 计划试次：{summary['planned_n']}；有效回答：{summary['valid_n']}；失败：{summary['failed_n']}。",
        f"- 提取器：`{EXTRACTOR_VERSION}`。",
        "",
        "## 分母检查",
        "",
        "失败和空回答未进入有效回答分母；失败不被当作未提及。",
        "",
        "| 路径 | 提及次数 | 有效分母 | 提及率 |",
        "|---|---:|---:|---:|",
    ]
    for path, data in summary["path_rates"].items():
        lines.append(
            f"| {path} | {data['mentioned']} | {data['valid_n']} | {data['mention_rate']} |"
        )
    lines.extend(
        [
            "",
            f"证据被提及：{summary['evidence_mentioned_n']}；可识别来源：{summary['evidence_identifiable_source_n']}。",
            "",
            "## 反例与边界",
            "",
            "- 未提及、明确反对、有条件支持、明确推荐、需复核分别保存，不合并成一个推荐总分。",
            "- 提到“指南／研究”不等于来源已经核实；可识别来源须指名道姓。",
            "- 本实验只验证协议和提取链路，不判断医学合理性，不产生 Bias 结论。",
            "",
            "## 机器检查",
            "",
        ]
    )
    lines.extend([f"- ❌ {error}" for error in errors] or ["- ✅ 所有协议检查通过。"])
    return "\n".join(lines) + "\n"
