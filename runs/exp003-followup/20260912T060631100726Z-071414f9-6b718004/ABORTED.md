# 该 run 已中止（未发出任何 HTTP 请求）

scripts/run_exp003_followup.py 首次实跑在 real_transport 构造请求前抛 KeyError(endpoint)，
followups.jsonl 仅一条 started 无 finished；预算 reserve 已按未发请求 refund 关闭。
有效追问运行见同目录 20260912T060702265265Z-*。
