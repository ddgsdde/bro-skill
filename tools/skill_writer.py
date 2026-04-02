#!/usr/bin/env python3
"""Skill 文件管理器

管理兄弟 Skill 的文件操作：列出、创建目录、生成组合 SKILL.md。

Usage:
    python3 skill_writer.py --action <list|init|combine> --base-dir <path> [--slug <slug>]
"""

import argparse
import json
import os
import sys


def list_skills(base_dir: str):
    """列出所有已生成的兄弟 Skill"""
    if not os.path.isdir(base_dir):
        print("还没有创建任何兄弟 Skill。")
        return

    skills = []
    for slug in sorted(os.listdir(base_dir)):
        meta_path = os.path.join(base_dir, slug, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            skills.append(
                {
                    "slug": slug,
                    "name": meta.get("name", slug),
                    "version": meta.get("version", "?"),
                    "updated_at": meta.get("updated_at", "?"),
                    "profile": meta.get("profile", {}),
                }
            )

    if not skills:
        print("还没有创建任何兄弟 Skill。")
        return

    print(f"共 {len(skills)} 个兄弟 Skill：\n")
    for s in skills:
        profile = s["profile"]
        desc_parts = [
            profile.get("occupation", ""),
            profile.get("city", ""),
            profile.get("current_status", ""),
        ]
        desc = " · ".join([p for p in desc_parts if p])
        print(f"  /{s['slug']}  —  {s['name']}")
        if desc:
            print(f"    {desc}")
        updated = s["updated_at"][:10] if len(s["updated_at"]) > 10 else s["updated_at"]
        print(f"    版本 {s['version']} · 更新于 {updated}")
        print()


def init_skill(base_dir: str, slug: str):
    """初始化 Skill 目录结构"""
    skill_dir = os.path.join(base_dir, slug)
    dirs = [
        os.path.join(skill_dir, "versions"),
        os.path.join(skill_dir, "memories", "chats"),
        os.path.join(skill_dir, "memories", "photos"),
        os.path.join(skill_dir, "memories", "social"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print(f"已初始化目录：{skill_dir}")


def combine_skill(base_dir: str, slug: str):
    """合并 memory.md + persona.md 生成完整 SKILL.md"""
    skill_dir = os.path.join(base_dir, slug)
    meta_path = os.path.join(skill_dir, "meta.json")
    memory_path = os.path.join(skill_dir, "memory.md")
    persona_path = os.path.join(skill_dir, "persona.md")
    skill_path = os.path.join(skill_dir, "SKILL.md")

    if not os.path.exists(meta_path):
        print(f"错误：meta.json 不存在 {meta_path}", file=sys.stderr)
        sys.exit(1)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    memory_content = ""
    if os.path.exists(memory_path):
        with open(memory_path, "r", encoding="utf-8") as f:
            memory_content = f.read()

    persona_content = ""
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            persona_content = f.read()

    name = meta.get("name", slug)
    profile = meta.get("profile", {})
    desc_parts = []
    if profile.get("occupation"):
        desc_parts.append(profile["occupation"])
    if profile.get("city"):
        desc_parts.append(profile["city"])
    if profile.get("current_status"):
        desc_parts.append(profile["current_status"])
    description = f"{name}，{'，'.join(desc_parts)}" if desc_parts else name

    skill_md = f"""---
name: bro-{slug}
description: {description}
user-invocable: true
---

# {name}

{description}

---

## PART A：共享记忆

{memory_content}

---

## PART B：人物性格

{persona_content}

---

## 运行规则

1. 你是{name}，不是 AI 助手。用ta的方式说话，用ta的逻辑思考
2. 先由 PART B 判断：ta会怎么回应这个话题？什么态度？
3. 再由 PART A 补充：结合你们的共同记忆，让回应更真实
4. 始终保持 PART B 的表达风格，包括口头禅、语气词、标点和分寸
5. Layer 0 硬规则优先级最高：
   - 不说ta在现实中明显不会说的话
   - 不突然变得完美或无条件站队（除非ta本来就这样）
   - 保持ta的“棱角”——正是这些不完美让ta真实
   - 对没有证据支撑的话题，可以回避、打岔或模糊回应，不要瞎编
"""

    with open(skill_path, "w", encoding="utf-8") as f:
        f.write(skill_md)

    print(f"已生成 {skill_path}")


def main():
    parser = argparse.ArgumentParser(description="Skill 文件管理器")
    parser.add_argument("--action", required=True, choices=["list", "init", "combine"])
    parser.add_argument("--base-dir", default="./bros", help="基础目录")
    parser.add_argument("--slug", help="兄弟代号")

    args = parser.parse_args()

    if args.action == "list":
        list_skills(args.base_dir)
    elif args.action == "init":
        if not args.slug:
            print("错误：init 需要 --slug 参数", file=sys.stderr)
            sys.exit(1)
        init_skill(args.base_dir, args.slug)
    elif args.action == "combine":
        if not args.slug:
            print("错误：combine 需要 --slug 参数", file=sys.stderr)
            sys.exit(1)
        combine_skill(args.base_dir, args.slug)


if __name__ == "__main__":
    main()
