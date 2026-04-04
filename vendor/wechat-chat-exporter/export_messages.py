#!/usr/bin/env python3
"""
Export WeChat chat messages from decrypted databases.

Usage:
    python3 decrypt_db.py                          # first, decrypt databases
    python3 export_messages.py                     # list all conversations
    python3 export_messages.py -c wxid_xxx         # export a specific chat
    python3 export_messages.py -c 12345@chatroom   # export a group chat
    python3 export_messages.py --all               # export all chats
    python3 export_messages.py -c wxid_xxx -n 50   # last 50 messages
    python3 export_messages.py -s "keyword"        # search keyword
"""

import sqlite3
import os
import re
import sys
import hashlib
import argparse
import glob
from datetime import datetime
import unittest


DECRYPTED_DIR = "decrypted"
MSG_TYPE_MAP = {
    1: "text",
    3: "image",
    34: "voice",
    42: "card",
    43: "video",
    47: "emoji",
    48: "location",
    49: "link/file",
    10000: "system",
    10002: "revoke",
}

PLACEHOLDER_MAP = {
    3: "[img]",
    34: "[voice]",
    42: "[card]",
    43: "[video]",
    47: "[emoji]",
    48: "[loc]",
    49: "[file]",
    50: "[call]",
}


# ── Contact name resolution ──────────────────────────────────────────────────


def load_contacts(decrypted_dir):
    """Load contact display names from contact.db.
    Returns dict: username -> display_name (remark > nick_name > username)
    """
    contact_db = os.path.join(decrypted_dir, "contact", "contact.db")
    contacts = {}

    if not os.path.isfile(contact_db):
        return contacts

    conn = sqlite3.connect(contact_db)
    try:
        for username, remark, nick_name in conn.execute(
            "SELECT username, remark, nick_name FROM contact"
        ):
            # Priority: remark (备注名) > nick_name (昵称) > username
            name = remark or nick_name or username
            if name:
                contacts[username] = name

        # Also load from stranger table for non-contacts
        for username, remark, nick_name in conn.execute(
            "SELECT username, remark, nick_name FROM stranger"
        ):
            if username not in contacts:
                name = remark or nick_name or username
                if name:
                    contacts[username] = name
    finally:
        conn.close()

    return contacts


def load_contact_ids(decrypted_dir):
    """Load contact integer id -> username mapping from contact.db."""
    contact_db = os.path.join(decrypted_dir, "contact", "contact.db")
    id_to_username = {}
    if not os.path.isfile(contact_db):
        return id_to_username

    conn = sqlite3.connect(contact_db)
    try:
        for contact_id, username in conn.execute(
            "SELECT id, username FROM contact WHERE username != ''"
        ):
            id_to_username[contact_id] = username
    finally:
        conn.close()

    return id_to_username


def load_chatroom_members(decrypted_dir, contacts, id_to_username):
    """Load chatroom member display names keyed by room username and member id."""
    contact_db = os.path.join(decrypted_dir, "contact", "contact.db")
    room_members = {}
    if not os.path.isfile(contact_db):
        return room_members

    conn = sqlite3.connect(contact_db)
    try:
        room_id_to_username = {
            room_id: username
            for room_id, username in conn.execute("SELECT id, username FROM chat_room")
        }
        for room_id, member_id in conn.execute(
            "SELECT room_id, member_id FROM chatroom_member"
        ):
            room_username = room_id_to_username.get(room_id)
            member_username = id_to_username.get(member_id)
            if not room_username or not member_username:
                continue
            room_members.setdefault(room_username, {})[member_id] = contacts.get(
                member_username, member_username
            )
    finally:
        conn.close()

    return room_members


def resolve_username(chat_name, contacts):
    """Resolve chat_name (display name, remark, or wxid) to username."""
    # Direct match
    if chat_name in contacts or chat_name.startswith("wxid_") or "@chatroom" in chat_name:
        return chat_name

    # Exact match on display name
    chat_lower = chat_name.lower()
    for uname, display in contacts.items():
        if chat_lower == display.lower():
            return uname

    # Fuzzy match (contains)
    for uname, display in contacts.items():
        if chat_lower in display.lower():
            return uname

    return None


# ── Multi-database support ───────────────────────────────────────────────────


def get_all_msg_dbs(decrypted_dir):
    """Find all message_N.db or biz_message_N.db files (N = 0, 1, 2, ...)."""
    import re
    msg_dir = os.path.join(decrypted_dir, "message")
    if not os.path.isdir(msg_dir):
        return []
    dbs = []
    for f in sorted(os.listdir(msg_dir)):
        if re.match(r"^(biz_)?message_\d+\.db$", f):
            dbs.append(os.path.join(msg_dir, f))
    return dbs


def get_session_db_path(decrypted_dir):
    return os.path.join(decrypted_dir, "session", "session.db")


def username_to_table(username):
    """Convert username to Msg_<md5hash> table name."""
    h = hashlib.md5(username.encode()).hexdigest()
    return f"Msg_{h}"


def find_msg_dbs_for_username(msg_dbs, username):
    """Find all message DBs containing the table for this username."""
    table = username_to_table(username)
    matches = []
    for db_path in msg_dbs:
        conn = sqlite3.connect(db_path)
        try:
            exists = conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()[0]
            if exists:
                matches.append(db_path)
        finally:
            conn.close()
    return matches


def collect_all_usernames(msg_dbs):
    """Collect all usernames from all message DBs, with the DBs they appear in."""
    username_to_dbs = {}
    for db_path in msg_dbs:
        conn = sqlite3.connect(db_path)
        try:
            rows = conn.execute(
                "SELECT user_name FROM Name2Id WHERE user_name != ''"
            ).fetchall()
            for (username,) in rows:
                username_to_dbs.setdefault(username, []).append(db_path)
        finally:
            conn.close()
    return username_to_dbs


# ── Message formatting ───────────────────────────────────────────────────────


def _decode_text(value):
    if value is None:
        return "", False
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace"), True
        except Exception:
            return "", True
    return str(value), False


def _clean_text(text):
    return " ".join((text or "").replace("\x00", " ").split())


def _looks_noisy(text):
    if not text:
        return False
    replacements = text.count("\ufffd")
    suspicious = sum(1 for ch in text if ord(ch) < 32 and ch not in "\n\t\r")
    return replacements >= 2 or suspicious > 0


def _split_group_sender(text, contacts):
    if text and ":\n" in text:
        raw_sender, body = text.split(":\n", 1)
        return contacts.get(raw_sender, raw_sender), body
    return None, text


def _summarize_content(local_type, content, contacts, is_group):
    text, was_binary = _decode_text(content)
    group_sender = None
    if is_group:
        group_sender, text = _split_group_sender(text, contacts)
    text = _clean_text(text)

    if local_type == 1:
        if was_binary and _looks_noisy(text):
            return group_sender, "[bin]"
        return group_sender, text or "[text]"

    if local_type == 10002:
        return group_sender, "[revoke]"

    if local_type == 10000:
        if "revokemsg" in text or "撤回了一条消息" in text or "recalled a message" in text:
            return group_sender, "[revoke]"
        if text and not _looks_noisy(text):
            return group_sender, f"[sys] {text[:120]}"
        return group_sender, "[sys]"

    placeholder = PLACEHOLDER_MAP.get(local_type)
    if placeholder:
        return group_sender, placeholder

    return group_sender, f"[t:{local_type}]"


def _infer_private_sender_ids(rows):
    stats = {}
    for _, _, _, _, sender_id, status, _, _ in rows:
        sender = stats.setdefault(sender_id, {"total": 0, "s2": 0, "s4": 0})
        sender["total"] += 1
        if status == 2:
            sender["s2"] += 1
        elif status == 4:
            sender["s4"] += 1

    sender_ids = list(stats)
    if not sender_ids:
        return None, None

    self_id = max(sender_ids, key=lambda sid: (stats[sid]["s2"] - stats[sid]["s4"], stats[sid]["total"]))
    other_candidates = [sid for sid in sender_ids if sid != self_id]
    if not other_candidates:
        return self_id, None
    other_id = max(other_candidates, key=lambda sid: (stats[sid]["s4"] - stats[sid]["s2"], stats[sid]["total"]))
    return self_id, other_id


def _private_sender_side(rows):
    stats = {}
    for row in rows:
        sender_id = row[4]
        status = row[5]
        sender = stats.setdefault(sender_id, {"total": 0, "s2": 0, "s4": 0})
        sender["total"] += 1
        if status == 2:
            sender["s2"] += 1
        elif status == 4:
            sender["s4"] += 1

    sides = {}
    for sender_id, sender_stats in stats.items():
        if sender_stats["s2"] > sender_stats["s4"]:
            sides[sender_id] = "self"
        elif sender_stats["s4"] > sender_stats["s2"]:
            sides[sender_id] = "other"
    return sides


def _build_export_context(rows, username, contacts, room_members):
    is_group = "@chatroom" in username
    display_name = contacts.get(username, username)
    speaker_map = {}
    speaker_labels = {}
    next_code = 1

    if not is_group:
        speaker_labels["1"] = "我"
        speaker_labels["2"] = display_name
        next_code = 3
        db_rows = {}
        for row in rows:
            db_rows.setdefault(row[0], []).append(row)
        for db_name, one_db_rows in db_rows.items():
            self_id, other_id = _infer_private_sender_ids(one_db_rows)
            if self_id is not None:
                speaker_map[(db_name, self_id)] = "1"
            if other_id is not None:
                speaker_map[(db_name, other_id)] = "2"
            side_map = _private_sender_side(one_db_rows)
            for sender_id, side in side_map.items():
                speaker_map.setdefault((db_name, sender_id), "1" if side == "self" else "2")

    formatted_rows = []
    for row in rows:
        db_name, _, local_type, create_time, sender_id, _, content, _ = row
        group_sender, body = _summarize_content(local_type, content, contacts, is_group)
        if is_group:
            if sender_id in speaker_map:
                code = speaker_map[sender_id]
            else:
                label = room_members.get(username, {}).get(sender_id) or group_sender or f"sid:{sender_id}"
                code = str(next_code)
                next_code += 1
                speaker_map[sender_id] = code
                speaker_labels[code] = label
        else:
            code = speaker_map.get((db_name, sender_id))
            if code is None:
                code = str(next_code)
                next_code += 1
                speaker_map[(db_name, sender_id)] = code
                speaker_labels[code] = f"{db_name}:sid:{sender_id}"

        ts = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S") if create_time else "?"
        formatted_rows.append(f"{ts} {code} {body}")

    participants = " | ".join(f"{code}={speaker_labels[code]}" for code in sorted(speaker_labels, key=int))
    return formatted_rows, participants


# ── Core operations ──────────────────────────────────────────────────────────


def list_conversations(msg_dbs, session_db_path, contacts):
    """List all conversations with display names."""
    sessions = {}
    if os.path.isfile(session_db_path):
        conn = sqlite3.connect(session_db_path)
        try:
            rows = conn.execute(
                "SELECT username, type, summary, last_sender_display_name, "
                "last_timestamp FROM SessionTable ORDER BY sort_timestamp DESC"
            ).fetchall()
            for username, stype, summary, sender, ts in rows:
                sessions[username] = {
                    "type": "group" if "@chatroom" in username else "private",
                    "summary": (summary or "")[:60],
                    "sender": sender or "",
                    "time": datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "",
                }
        finally:
            conn.close()

    # Collect all usernames across all message DBs
    username_to_dbs = collect_all_usernames(msg_dbs)

    # Build all message tables set per DB
    all_tables = {}
    for db_path in msg_dbs:
        conn = sqlite3.connect(db_path)
        try:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%'"
                ).fetchall()
            }
            all_tables[db_path] = tables
        finally:
            conn.close()

    results = []
    for username, db_paths in username_to_dbs.items():
        table = username_to_table(username)
        has_msgs = any(table in all_tables.get(db_path, set()) for db_path in db_paths)
        info = sessions.get(username, {})
        display_name = contacts.get(username, "")
        results.append({
            "username": username,
            "display_name": display_name,
            "db": ",".join(os.path.basename(db_path) for db_path in db_paths),
            "has_msgs": has_msgs,
            **info,
        })

    results.sort(key=lambda x: x.get("time", ""), reverse=True)
    return results


def export_chat(msg_dbs, username, contacts, room_members, limit=None, since_ts=None, until_ts=None):
    """Export messages for a specific conversation from all message DBs."""
    table = username_to_table(username)
    is_group = "@chatroom" in username

    db_paths = find_msg_dbs_for_username(msg_dbs, username)
    if not db_paths:
        return None, f"No message table found for {username}", ""

    where_clauses = []
    params = []
    if since_ts is not None:
        where_clauses.append("create_time >= ?")
        params.append(since_ts)
    if until_ts is not None:
        where_clauses.append("create_time <= ?")
        params.append(until_ts)
    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = 0
    rows = []
    db_names = []
    for db_path in db_paths:
        conn = sqlite3.connect(db_path)
        try:
            total += conn.execute(f"SELECT count(*) FROM [{table}]").fetchone()[0]
            query = (
                f"SELECT ?, local_id, local_type, create_time, real_sender_id, status, "
                f"message_content, source FROM [{table}] {where_sql} ORDER BY create_time DESC"
            )
            db_rows = conn.execute(query, [os.path.basename(db_path)] + params).fetchall()
            rows.extend(db_rows)
            db_names.append(os.path.basename(db_path))
        finally:
            conn.close()

    rows.sort(key=lambda row: row[3], reverse=True)
    if limit:
        rows = rows[:limit]
    rows.reverse()

    lines, participants = _build_export_context(rows, username, contacts, room_members)

    display_name = contacts.get(username, username)
    info = f"{display_name} | total: {total}, showing: {len(lines)} | db: {','.join(db_names)}"
    return lines, info, participants


def safe_filename(display_name, username):
    """Generate a safe filename from display name, fallback to username."""
    name = display_name or username
    # Remove characters not safe for filenames
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    name = name.strip('. ')
    if not name:
        name = username.replace('@', '_at_')
    # Truncate to reasonable length
    if len(name) > 80:
        name = name[:80]
    return name


def export_to_file(msg_dbs, username, output_dir, contacts, room_members, limit=None, since_ts=None, until_ts=None):
    """Export messages to a text file named by display name."""
    lines, info, participants = export_chat(msg_dbs, username, contacts, room_members, limit, since_ts, until_ts)
    if lines is None:
        return False, info

    if not lines:
        return False, f"skipped (no messages in range) | {info}"

    os.makedirs(output_dir, exist_ok=True)

    display_name = contacts.get(username, "")
    fname = safe_filename(display_name, username)
    output_path = os.path.join(output_dir, f"{fname}.txt")

    # Avoid collision
    if os.path.exists(output_path):
        output_path = os.path.join(output_dir, f"{fname}_{username.replace('@', '_at_')}.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Chat: {display_name or username} ({username})\n")
        f.write(f"# P: {participants}\n")
        f.write(f"# {info}\n")
        f.write(f"# Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("\n".join(lines))
        f.write("\n")

    return True, f"{os.path.basename(output_path)} | {info}"


def main():
    parser = argparse.ArgumentParser(description="Export WeChat chat messages")
    parser.add_argument(
        "-d", "--dir", default=DECRYPTED_DIR,
        help=f"Decrypted database directory (default: {DECRYPTED_DIR})",
    )
    parser.add_argument("-c", "--chat", help="Username or chatroom ID to export")
    parser.add_argument("--all", action="store_true", help="Export all conversations")
    parser.add_argument(
        "-n", "--limit", type=int, default=None, help="Number of recent messages",
    )
    parser.add_argument(
        "-o", "--output", default="exported", help="Output directory (default: exported)",
    )
    parser.add_argument(
        "-s", "--search", help="Search keyword across all conversations",
    )
    parser.add_argument(
        "--since", help="Start date (inclusive), format: YYYY-MM-DD",
    )
    parser.add_argument(
        "--until", help="End date (inclusive), format: YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--personal", action="store_true",
        help="Only export personal chats and groups (exclude public accounts starting with gh_)",
    )
    args = parser.parse_args()

    # Parse date range into Unix timestamps
    since_ts = None
    until_ts = None
    if args.since:
        since_ts = int(datetime.strptime(args.since, "%Y-%m-%d").timestamp())
    if args.until:
        from datetime import timedelta
        until_ts = int((datetime.strptime(args.until, "%Y-%m-%d") + timedelta(days=1)).timestamp()) - 1
    elif args.since:
        # if --since given but no --until, default until = end of today
        from datetime import timedelta
        until_ts = int((datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)).timestamp())

    # Load databases
    msg_dbs = get_all_msg_dbs(args.dir)
    if not msg_dbs:
        print(f"[-] No message databases found in {args.dir}/message/")
        print(f"    Run 'python3 decrypt_db.py' first.")
        sys.exit(1)

    print(f"[*] Loaded {len(msg_dbs)} message databases: {', '.join(os.path.basename(d) for d in msg_dbs)}")

    session_db = get_session_db_path(args.dir)
    contacts = load_contacts(args.dir)
    id_to_username = load_contact_ids(args.dir)
    room_members = load_chatroom_members(args.dir, contacts, id_to_username)
    print(f"[*] Loaded {len(contacts)} contacts")

    if args.search:
        # Search across all conversations
        print(f"[*] Searching for '{args.search}'...\n")
        username_to_dbs = collect_all_usernames(msg_dbs)
        found = 0
        for username, db_paths in username_to_dbs.items():
            table = username_to_table(username)
            rows = []
            extra_where = []
            extra_params = [f"%{args.search}%"]
            if since_ts is not None:
                extra_where.append("create_time >= ?")
                extra_params.append(since_ts)
            if until_ts is not None:
                extra_where.append("create_time <= ?")
                extra_params.append(until_ts)
            date_sql = (" AND " + " AND ".join(extra_where)) if extra_where else ""

            for db_path in db_paths:
                conn = sqlite3.connect(db_path)
                try:
                    exists = conn.execute(
                        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",
                        (table,),
                    ).fetchone()[0]
                    if not exists:
                        continue
                    db_rows = conn.execute(
                        f"SELECT ?, local_id, local_type, create_time, real_sender_id, status, "
                        f"message_content, source FROM [{table}] "
                        f"WHERE message_content LIKE ?{date_sql} ORDER BY create_time DESC LIMIT 10",
                        [os.path.basename(db_path)] + extra_params,
                    ).fetchall()
                    rows.extend(db_rows)
                finally:
                    conn.close()

            if rows:
                rows.sort(key=lambda row: row[3], reverse=True)
                rows = rows[:10]
                lines, participants = _build_export_context(rows, username, contacts, room_members)
                display = contacts.get(username, username)
                print(f"── {display} ({username}) ──")
                print(f"  P: {participants}")
                for line in lines:
                    print(f"  {line}")
                print()
                found += len(rows)
        print(f"[*] Found {found} messages matching '{args.search}'")

    elif args.chat:
        # Export specific chat (with fuzzy matching)
        username = resolve_username(args.chat, contacts)
        if not username:
            print(f"[-] Could not find chat: {args.chat}")
            print(f"    Try: python3 export_messages.py -s '{args.chat}'")
            sys.exit(1)

        if username != args.chat:
            display = contacts.get(username, username)
            print(f"[*] Matched '{args.chat}' -> {display} ({username})")

        lines, info, participants = export_chat(msg_dbs, username, contacts, room_members, args.limit, since_ts, until_ts)
        if lines is None:
            print(f"[-] {info}")
            sys.exit(1)

        print(f"[*] {info}\n")
        print(f"[*] P: {participants}\n")
        for line in lines:
            print(line)

        success, result_info = export_to_file(msg_dbs, username, args.output, contacts, room_members, args.limit, since_ts, until_ts)
        print(f"\n[*] Saved: {result_info}")

    elif args.all:
        # Export all conversations
        convos = list_conversations(msg_dbs, session_db, contacts)
        os.makedirs(args.output, exist_ok=True)
        exported = 0
        skipped = 0
        for c in convos:
            if not c["has_msgs"]:
                continue
            if args.personal and c["username"].startswith("gh_"):
                skipped += 1
                continue
            success, info = export_to_file(
                msg_dbs, c["username"], args.output, contacts, room_members, args.limit, since_ts, until_ts,
            )
            if success:
                print(f"  ✅ {info}")
                exported += 1
        if skipped:
            print(f"[*] Skipped {skipped} public accounts (gh_*)")
        print(f"\n[*] Exported {exported} conversations to {args.output}/")

    else:
        # List conversations
        convos = list_conversations(msg_dbs, session_db, contacts)
        active = [c for c in convos if c.get("time") or c["has_msgs"]]
        print(f"[*] Found {len(active)} active conversations (from {len(convos)} total)\n")
        print(f"{'Display Name':<20} {'Username':<35} {'DB':<15} {'Time':<18} {'Last Message'}")
        print("-" * 120)
        for c in active:
            if not c.get("time"):
                continue
            marker = "💬" if c.get("type") == "private" else "👥"
            display = c.get("display_name", "")[:18] or ""
            summary = c.get("summary", "")[:40]
            time_str = c.get("time", "")
            db_name = c.get("db", "")
            print(f"{marker} {display:<18} {c['username']:<35} {db_name:<15} {time_str:<18} {summary}")

        print(f"\n[*] To export a chat: python3 export_messages.py -c <username>")
        print(f"[*] To export all:    python3 export_messages.py --all")
        print(f"[*] To search:        python3 export_messages.py -s <keyword>")


if __name__ == "__main__":
    main()
