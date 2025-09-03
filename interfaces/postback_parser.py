# interfaces/postback_parser.py
import json
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedPostback:
    ns: Optional[str]      # "summary" / None
    action: str            # "get_grade" | "re_grade" | "apply_manual" | 舊格式 action
    contents_name: Optional[str]
    raw: str


_SUMMARY_RE = re.compile(
    r'^summary:(get_grade|re_grade|apply_manual|confirm_manual):([^:]+)$'
)


def parse_postback(data: str) -> ParsedPostback:
    raw = data.strip()

    # 新：summary:<action>:<contents>
    m = _SUMMARY_RE.match(raw)
    if m:
        return ParsedPostback(ns="summary", action=m.group(1), contents_name=m.group(2), raw=raw)

    # 兼容：JSON payload（若你未來改成 JSON 可在此處支援）
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and obj.get("type") == "INFO" and "action" in obj:
            return ParsedPostback(
                ns=None,
                action=obj["action"],
                contents_name=obj.get("contents_name"),
                raw=raw
            )
    except Exception:
        pass

    # 舊：例如 "[INFO]get_summary_grading C4"
    if raw.startswith("[INFO]"):
        parts = raw[6:].strip().split()
        action = parts[0] if parts else ""
        contents = parts[1] if len(parts) > 1 else None
        # 映射到新語意
        mapping = {
            "get_summary_gradding": "get_grade",      # 有些專案拼法不一，兩個都映射
            "get_summary_grading": "get_grade",
            "summary_re-gradding": "re_grade",
            "summary_re-gradding_by_TA": "apply_manual",
        }
        action2 = mapping.get(action, action)
        return ParsedPostback(ns=None, action=action2, contents_name=contents, raw=raw)

    # 其他：保底
    return ParsedPostback(ns=None, action=raw, contents_name=None, raw=raw)
