<div align="center">

# bro-skill

<p><strong>兄弟.skill</strong></p>

<p><em>"A real homie does not just say the right words. He actually shows up."</em></p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python%203.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green)](https://agentskills.io)

</div>

---

<div align="center">

Your colleague leaves, so you distill a colleague.  
Your ex is gone, so you distill an ex.  
But what about the one person who might deserve distillation just as much: your bro?

He may never say the perfect thing.  
He may roast you, dodge sincerity, or act cool when things get heavy.  
But when life actually hits, he tends to show up before the speeches do.

**Instead of leaving that person trapped inside old chat logs, turn him into a runnable Skill.**

Feed it chat history, screenshots, photos, and your own recollection  
and it will deconstruct him into:

**Part A - Shared Memory + Part B - Persona**

A digital version that talks in his rhythm, remembers what you lived through together,  
and keeps his humor, sharpness, loyalty, and boundaries intact.

Warning: This project is for personal memory work, creative dialogue, and relationship reflection only. Do not use it for harassment, impersonation, stalking, or privacy violations.

[Installation](#installation) · [Usage](#usage) · [Examples](#examples) · [中文](README.md)

</div>

---

## Installation

### Claude Code

```bash
# Install into the current repo
mkdir -p .claude/skills
git clone https://github.com/ddgsdde/bro-skill .claude/skills/bro-skill

# Or install globally
git clone https://github.com/ddgsdde/bro-skill ~/.claude/skills/bro-skill
```

### Optional dependencies

```bash
pip3 install -r requirements.txt
```

---

## Usage

In Claude Code:

```text
/create-bro
```

Follow the prompts: enter a codename, basic info, personality traits, then choose data sources. Everything except the codename can be skipped.

After creation, use `/{slug}` to chat with the generated bro Skill.

### Commands

| Command | Description |
|---------|-------------|
| `/list-bros` | List all generated bro Skills |
| `/{slug}` | Full skill mode |
| `/{slug}-memory` | Shared memory mode |
| `/{slug}-persona` | Persona-only mode |
| `/bro-rollback {slug} {version}` | Roll back to a previous version |
| `/delete-bro {slug}` | Delete |

---

## Examples

> Input: `college roommate, known each other for eight years, sharp-tongued, loyal, loves roasting people, never dramatic but always shows up`

### Casual chat

```text
User       ❯ what are you doing

bro-skill  ❯ just got off work
             dead tired
             what kind of nonsense are you up to now
```

### Shared memory

```text
User       ❯ remember that all-nighter when we shipped the project

bro-skill  ❯ of course
             you wrote five lines and drank four coffees
             i was the one who actually saved that mess
```

### Hard-shell concern

```text
User       ❯ i've been kind of stressed lately

bro-skill  ❯ then say it
             don't sit there and rot alone
             if something's wrong call me
```

---

## Features

### Data sources

| Source | Format | Notes |
|--------|--------|-------|
| WeChat | WeChatMsg / Liuhen / PyWxDump export | Recommended, richest data |
| QQ | txt / mht export | Great for school-era friendships |
| Social media | Screenshots | Public persona and expression patterns |
| Photos | JPEG/PNG with EXIF | Timeline and location extraction |
| Narration | Plain text | Your subjective memory |

### Skill architecture

Each generated bro Skill has two cooperating parts:

| Part | Purpose |
|------|---------|
| **Part A — Shared Memory** | Shared experiences, places, inside jokes, conflicts, mutual support, timeline |
| **Part B — Persona** | 5-layer structure: hard rules, identity, speaking style, way of doing things, relationship behavior |

Runtime logic: `incoming message -> Persona decides how he would respond -> Memory adds shared context -> output in his voice`

### Evolution

* Add more memories later
* Correct replies with "he would not say that"
* Keep versioned history and roll back when needed

---

## Project structure

```text
bro-skill/
├── SKILL.md
├── prompts/
├── tools/
├── bros/
├── docs/PRD.md
├── README.md
├── README_EN.md
├── INSTALL.md
├── requirements.txt
└── LICENSE
```

---

## Inspiration

This project is inspired by three adjacent ideas:

* **yourself.skill**: treating the self as a runnable memory and persona container
* **ex-skill / 前任.skill**: modeling both shared memory and personal expression
* **colleague-skill / 同事.skill**: turning a person into a structured, evolving dual-layer skill

The open-source presentation and repository shape especially reference **[ex-skill](https://github.com/therealXiaomanChu/ex-skill)** and **[colleague-skill](https://github.com/titanwings/colleague-skill)**.
