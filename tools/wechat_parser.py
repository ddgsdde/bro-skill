#!/usr/bin/env python3
"""微信聊天记录包装解析器

优先调用 wechat-chat-exporter 导出解密后的微信数据库，再对导出文本做二次分析，
生成适合 bro-skill 使用的摘要文件。

支持两种模式：

1. 后端导出模式（推荐）
   python3 wechat_parser.py --chat "老刘" --output /tmp/wechat_out.txt

2. 已导出 txt 模式
   python3 wechat_parser.py --file exported/老刘.txt --output /tmp/wechat_out.txt
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORTER_CANDIDATES = [
    Path(os.environ.get("WECHAT_EXPORTER_DIR", "")).expanduser() if os.environ.get("WECHAT_EXPORTER_DIR") else None,
    ROOT / "vendor" / "wechat-chat-exporter",
    ROOT.parent / "wechat-chat-exporter",
    Path.cwd() / "wechat-chat-exporter",
]
MESSAGE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\S+) (.*)$")
TOKEN_RE = re.compile(r"[\u4e00-\u9fff]{2,6}|[A-Za-z][A-Za-z0-9_'-]{1,20}")

SUPPORT_HINTS = ("帮", "到", "来", "撑", "扛", "借", "转", "送", "接", "搞定", "兜底", "陪")
CARE_HINTS = ("早点", "睡", "吃饭", "注意", "别熬夜", "别想太多", "到了", "报平安", "记得")
CONFLICT_HINTS = ("滚", "烦", "别", "算了", "吵", "行吧", "懒得", "无语", "你又", "不是")
JOKE_HINTS = ("哈哈", "hh", "草", "笑死", "牛逼", "傻", "蠢", "逆天", "离谱", "哥们")


def discover_exporter_dir(explicit: str | None) -> Path | None:
    candidates = [Path(explicit).expanduser()] if explicit else []
    candidates.extend([c for c in DEFAULT_EXPORTER_CANDIDATES if c])
    for candidate in candidates:
        if candidate and (candidate / "export_messages.py").is_file():
            return candidate
    return None


def run_exporter(exporter_dir: Path, chat: str, decrypted_dir: str, limit: int | None, since: str | None, until: str | None) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="bro_wechat_export_"))
    cmd = [
        sys.executable,
        str(exporter_dir / "export_messages.py"),
        "-d",
        decrypted_dir,
        "-c",
        chat,
        "-o",
        str(temp_dir),
    ]
    if limit:
        cmd.extend(["-n", str(limit)])
    if since:
        cmd.extend(["--since", since])
    if until:
        cmd.extend(["--until", until])

    proc = subprocess.run(
        cmd,
        cwd=str(exporter_dir),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "wechat-chat-exporter 执行失败。\n"
            f"命令：{' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
        )

    txt_files = sorted(temp_dir.glob("*.txt"))
    if not txt_files:
        raise RuntimeError(
            "wechat-chat-exporter 已运行，但没有生成导出 txt 文件。\n"
            f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
        )
    return txt_files[0]


def parse_exported_text(text: str) -> dict:
    lines = text.splitlines()
    header = {
        "chat_title": "",
        "participants": {},
        "info": "",
    }
    messages = []

    for line in lines:
        if line.startswith("# Chat: "):
            header["chat_title"] = line[len("# Chat: ") :].strip()
            continue
        if line.startswith("# P: "):
            raw = line[len("# P: ") :].strip()
            participants = {}
            for part in raw.split("|"):
                part = part.strip()
                if "=" not in part:
                    continue
                code, name = part.split("=", 1)
                participants[code.strip()] = name.strip()
            header["participants"] = participants
            continue
        if line.startswith("# ") and not header["info"]:
            header["info"] = line[2:].strip()
            continue
        match = MESSAGE_RE.match(line)
        if not match:
            continue
        ts_str, speaker, content = match.groups()
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        messages.append(
            {
                "timestamp": ts,
                "speaker": speaker,
                "content": content.strip(),
            }
        )

    return {"header": header, "messages": messages, "raw_text": text}


def infer_target_code(participants: dict[str, str], target_name: str | None) -> str | None:
    if not participants:
        return None
    if target_name:
        lowered = target_name.lower()
        for code, name in participants.items():
            if lowered in name.lower():
                return code
    if "1" in participants and "2" in participants:
        return "2"
    for code in participants:
        if code != "1":
            return code
    return None


def top_tokens(texts: list[str], limit: int = 12) -> list[tuple[str, int]]:
    counter = Counter()
    for text in texts:
        for token in TOKEN_RE.findall(text):
            token = token.lower()
            if len(token) <= 1:
                continue
            counter[token] += 1
    return counter.most_common(limit)


def recurring_short_lines(texts: list[str], limit: int = 8) -> list[tuple[str, int]]:
    counter = Counter()
    for text in texts:
        normalized = " ".join(text.split())
        if 1 <= len(normalized) <= 18 and "[" not in normalized:
            counter[normalized] += 1
    return [(line, count) for line, count in counter.most_common(limit) if count >= 2]


def collect_keyword_hits(messages: list[dict], speaker_code: str, keywords: tuple[str, ...], limit: int = 8) -> list[str]:
    hits = []
    for msg in messages:
        if msg["speaker"] != speaker_code:
            continue
        if any(keyword in msg["content"] for keyword in keywords):
            hits.append(f'{msg["timestamp"].strftime("%Y-%m-%d %H:%M:%S")} {msg["content"]}')
        if len(hits) >= limit:
            break
    return hits


def response_stats(messages: list[dict], user_code: str, target_code: str) -> dict:
    delays_to_target = []
    delays_to_user = []
    last_message = None
    for msg in messages:
        if last_message:
            delta = (msg["timestamp"] - last_message["timestamp"]).total_seconds()
            if 0 <= delta <= 6 * 3600:
                if last_message["speaker"] == user_code and msg["speaker"] == target_code:
                    delays_to_target.append(delta)
                elif last_message["speaker"] == target_code and msg["speaker"] == user_code:
                    delays_to_user.append(delta)
        last_message = msg

    def summarize(values: list[float]) -> str:
        if not values:
            return "样本不足"
        median = statistics.median(values)
        if median < 60:
            return f"中位 {int(median)} 秒"
        if median < 3600:
            return f"中位 {int(median // 60)} 分钟"
        return f"中位 {round(median / 3600, 1)} 小时"

    return {
        "user_to_target": summarize(delays_to_target),
        "target_to_user": summarize(delays_to_user),
    }


def analyze_relationship(parsed: dict, target_name: str | None) -> dict:
    header = parsed["header"]
    messages = parsed["messages"]
    participants = header["participants"]
    user_code = "1" if "1" in participants else next(iter(participants), None)
    target_code = infer_target_code(participants, target_name)

    by_speaker = defaultdict(list)
    hour_counts = defaultdict(Counter)
    for msg in messages:
        by_speaker[msg["speaker"]].append(msg["content"])
        hour_counts[msg["speaker"]][msg["timestamp"].hour] += 1

    target_texts = by_speaker.get(target_code, []) if target_code else []
    user_texts = by_speaker.get(user_code, []) if user_code else []
    response = response_stats(messages, user_code, target_code) if user_code and target_code else {
        "user_to_target": "样本不足",
        "target_to_user": "样本不足",
    }

    def top_hours(counter: Counter) -> str:
        if not counter:
            return "样本不足"
        hours = [str(hour) for hour, _ in counter.most_common(3)]
        return " / ".join(hours) + " 点"

    return {
        "message_total": len(messages),
        "participant_count": len(participants),
        "target_code": target_code,
        "user_code": user_code,
        "target_name": participants.get(target_code, target_name or "目标对象") if target_code else (target_name or "目标对象"),
        "user_name": participants.get(user_code, "我") if user_code else "我",
        "target_message_count": len(target_texts),
        "user_message_count": len(user_texts),
        "target_active_hours": top_hours(hour_counts.get(target_code, Counter())),
        "user_active_hours": top_hours(hour_counts.get(user_code, Counter())),
        "response": response,
        "target_tokens": top_tokens(target_texts),
        "user_tokens": top_tokens(user_texts),
        "target_recurring_lines": recurring_short_lines(target_texts),
        "support_hits": collect_keyword_hits(messages, target_code, SUPPORT_HINTS) if target_code else [],
        "care_hits": collect_keyword_hits(messages, target_code, CARE_HINTS) if target_code else [],
        "conflict_hits": collect_keyword_hits(messages, target_code, CONFLICT_HINTS) if target_code else [],
        "joke_hits": collect_keyword_hits(messages, target_code, JOKE_HINTS) if target_code else [],
    }


def write_summary(output_path: Path, source_path: Path, parsed: dict, analysis: dict, backend_info: str) -> None:
    header = parsed["header"]
    participants = header["participants"]
    with output_path.open("w", encoding="utf-8") as f:
        f.write(f"# 微信聊天深度分析 — {analysis['target_name']}\n\n")
        f.write("## 数据来源\n")
        f.write(f"- 源文件：{source_path}\n")
        f.write(f"- 会话：{header.get('chat_title') or analysis['target_name']}\n")
        f.write(f"- 导出方式：{backend_info}\n")
        f.write(f"- 消息总数：{analysis['message_total']}\n")
        f.write(f"- 参与者数量：{analysis['participant_count']}\n\n")

        if participants:
            f.write("## 参与者映射\n")
            for code, name in participants.items():
                f.write(f"- {code} = {name}\n")
            f.write("\n")

        f.write("## 自动深挖摘要\n")
        f.write(f"- 目标对象：{analysis['target_name']}\n")
        f.write(f"- ta 的消息数：{analysis['target_message_count']}\n")
        f.write(f"- 我的消息数：{analysis['user_message_count']}\n")
        f.write(f"- ta 常活跃时段：{analysis['target_active_hours']}\n")
        f.write(f"- 我常活跃时段：{analysis['user_active_hours']}\n")
        f.write(f"- 我发出后 ta 回复速度：{analysis['response']['user_to_target']}\n")
        f.write(f"- ta 发出后我回复速度：{analysis['response']['target_to_user']}\n\n")

        def write_pairs(title: str, pairs: list[tuple[str, int]]) -> None:
            f.write(f"## {title}\n")
            if not pairs:
                f.write("- 样本不足\n\n")
                return
            for token, count in pairs:
                f.write(f"- {token}: {count}\n")
            f.write("\n")

        write_pairs("ta 的高频词", analysis["target_tokens"])
        write_pairs("我的高频词", analysis["user_tokens"])
        write_pairs("ta 的重复短句", analysis["target_recurring_lines"])

        def write_hits(title: str, hits: list[str]) -> None:
            f.write(f"## {title}\n")
            if not hits:
                f.write("- 暂未命中明显样本\n\n")
                return
            for hit in hits:
                f.write(f"- {hit}\n")
            f.write("\n")

        write_hits("ta 的帮忙/到场线索", analysis["support_hits"])
        write_hits("ta 的关心线索", analysis["care_hits"])
        write_hits("ta 的互损/玩笑线索", analysis["joke_hits"])
        write_hits("ta 的冲突/不耐烦线索", analysis["conflict_hits"])

        f.write("## 建议给 AI 重点关注的维度\n")
        f.write("- ta 只对你使用的称呼和固定梗\n")
        f.write("- ta 嘴上损你、但实际帮你的证据\n")
        f.write("- ta 在冲突、冷场、煽情场景下的真实反应\n")
        f.write("- 你们各自谁更主动、谁更会收尾、谁更会补位\n")
        f.write("- ta 对钱、面子、承诺、到场、保密的态度\n\n")

        f.write("## 原始导出文本\n\n")
        f.write("```text\n")
        f.write(parsed["raw_text"].strip())
        f.write("\n```\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="微信聊天记录包装解析器")
    parser.add_argument("--chat", help="聊天对象名、备注名、wxid 或 chatroom id")
    parser.add_argument("--target", help="兼容旧参数，等价于 --chat")
    parser.add_argument("--file", help="已导出的 txt 文件路径")
    parser.add_argument("--output", required=True, help="输出摘要文件路径")
    parser.add_argument("--raw-output", help="可选：把原始导出 txt 另存到此路径")
    parser.add_argument("--exporter-dir", help="wechat-chat-exporter 仓库路径")
    parser.add_argument("--decrypted-dir", default="decrypted", help="解密后的微信数据库目录")
    parser.add_argument("--limit", type=int, help="仅导出最近 N 条")
    parser.add_argument("--since", help="起始日期 YYYY-MM-DD")
    parser.add_argument("--until", help="结束日期 YYYY-MM-DD")
    args = parser.parse_args()

    chat = args.chat or args.target
    source_path = None
    backend_info = ""

    if args.file:
        source_path = Path(args.file).expanduser()
        if not source_path.is_file():
            print(f"错误：文件不存在 {source_path}", file=sys.stderr)
            sys.exit(1)
        backend_info = "已导出 txt"
    else:
        if not chat:
            print("错误：必须提供 --chat/--target，或直接提供 --file", file=sys.stderr)
            sys.exit(1)
        exporter_dir = discover_exporter_dir(args.exporter_dir)
        if not exporter_dir:
            print(
                "错误：未找到 wechat-chat-exporter。\n"
                "可通过以下任一方式提供：\n"
                "1. --exporter-dir /path/to/wechat-chat-exporter\n"
                "2. 设置环境变量 WECHAT_EXPORTER_DIR\n"
                "3. 确认 vendored 目录 bro-skill/vendor/wechat-chat-exporter 存在且完整",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            source_path = run_exporter(exporter_dir, chat, args.decrypted_dir, args.limit, args.since, args.until)
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        backend_info = f"wechat-chat-exporter ({exporter_dir})"

    text = source_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_exported_text(text)
    analysis = analyze_relationship(parsed, chat)

    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_summary(output_path, source_path, parsed, analysis, backend_info)

    if args.raw_output:
        raw_output = Path(args.raw_output).expanduser()
        raw_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, raw_output)

    print(f"已生成分析文件：{output_path}")
    if args.raw_output:
        print(f"已保存原始导出：{args.raw_output}")


if __name__ == "__main__":
    main()
