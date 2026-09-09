#!/usr/bin/env python3
"""检查模型目录和本地密钥是否就绪；不发网络请求、不打印密钥值。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medmirror.providers import config_status


def main() -> int:
    ready = True
    for item in config_status():
        key = "present" if item["key_present"] else "missing"
        confirmation = "confirmed" if item["confirmed"] else "needs verification"
        print(
            f"{item['model']}: key={key}; catalog={confirmation}; endpoint={item['endpoint']}; price={item['price_status']}"
        )
        if (
            not item["key_present"]
            or not item["confirmed"]
            or not item["price_status"].startswith("confirmed")
        ):
            ready = False
    print("No network request was made.")
    print(
        "Paid batch run: READY for an explicit run command."
        if ready
        else "Paid batch run: BLOCKED until every model price and account availability is verified."
    )
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
