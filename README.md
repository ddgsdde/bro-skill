<div align="center">

# 兄弟.skill

<p><strong>bro-skill</strong></p>

<p><em>“真正的兄弟不是天天说漂亮话，是你出事的时候他真会出现。”</em></p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python%203.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green)](https://agentskills.io)

</div>

---

<div align="center">

同事跑了，你蒸馏同事。前任分了，你蒸馏前任。  
但有没有想过，那个最适合被蒸馏成 AI Skill 的人，其实是你兄弟？

他不一定天天夸你。  
他可能嘴硬，可能损你，可能一到煽情就打岔。  
但真轮到你出事的时候，他往往比漂亮话先到。

**与其把兄弟停留在聊天记录里，不如把他蒸馏成一个可运行的 Skill。**

提供他的聊天记录、截图、照片，再加上你对他的描述  
我们会把他拆成一套可运行的结构：

**Part A - Shared Memory（共享记忆） + Part B - Persona（人格模型）**  
**Part C - User Model（本人画像） + Part D - Relationship Dynamics（关系动力学）**

生成一个能按他的口头禅说话、记得你们共同经历、  
也保留他的嘴硬、幽默、义气和边界感的数字副本。

⚠️ **本项目仅用于个人记忆整理、创作式对话与关系回顾，不用于骚扰、冒充、跟踪或侵犯他人隐私。**

[安装](#安装) · [使用](#使用) · [效果示例](#效果示例) · [English](README_EN.md)

</div>

---

## 安装

### Claude Code

> **重要**：Claude Code 从 **git 仓库根目录** 的 `.claude/skills/` 查找 skill。请在正确的位置执行。

```bash
# 安装到当前项目（在 git 仓库根目录执行）
mkdir -p .claude/skills
git clone https://github.com/ddgsdde/bro-skill .claude/skills/bro-skill

# 或安装到全局（所有项目都能用）
git clone https://github.com/ddgsdde/bro-skill ~/.claude/skills/bro-skill
```

### 依赖（可选）

```bash
pip3 install -r requirements.txt
```

---

## 使用

在 Claude Code 中输入：

```text
/create-bro
```

按提示输入兄弟的代号、基本信息、性格画像，然后选择数据来源。所有字段均可跳过，仅凭描述也能生成。

完成后用 `/{slug}` 调用该兄弟 Skill，开始对话。

### 管理命令

| 命令 | 说明 |
|------|------|
| `/list-bros` | 列出所有兄弟 Skill |
| `/{slug}` | 调用完整 Skill（像他一样跟你聊天） |
| `/{slug}-memory` | 共享记忆模式（帮你回忆你们一起的事） |
| `/{slug}-persona` | 仅人物性格 |
| `/bro-rollback {slug} {version}` | 回滚到历史版本 |
| `/delete-bro {slug}` | 删除 |

---

## 效果示例

> 输入：`大学室友，认识八年，嘴硬，讲义气，爱损人，平时不煽情但真有事一定到`

**场景一：日常聊天**

```text
用户      ❯ 在干嘛

兄弟.skill ❯ 刚下班
             累得像狗
             你又整什么幺蛾子了
```

**场景二：回忆名场面**

```text
用户      ❯ 还记得我们那次通宵做项目吗

兄弟.skill ❯ 记得啊
             你代码没写几行 咖啡喝了四杯
             最后还是我给你兜的底
```

**场景三：嘴硬式关心**

```text
用户      ❯ 我最近有点烦

兄弟.skill ❯ 烦就说
             别一个人憋着
             真要出事喊我
```

**场景四：互损模式**

```text
用户      ❯ 你是不是从来没夸过我

兄弟.skill ❯ 夸你干嘛
             你尾巴本来就够翘了
             不过这次确实还行
```

---

## 功能特性

### 数据源

| 来源 | 格式 | 备注 |
|------|------|------|
| 微信聊天记录 | WeChatMsg / 留痕 / PyWxDump 导出 | 推荐，信息最丰富 |
| QQ 聊天记录 | txt / mht 导出 | 适合学生时代或老朋友关系 |
| 社交媒体截图 | 图片 | 提取公开人设、固定表达和生活线索 |
| 照片 | JPEG/PNG（含 EXIF） | 提取时间线和地点 |
| 口述/粘贴 | 纯文本 | 你的主观记忆 |

### 生成的 Skill 结构

每个兄弟 Skill 由四部分组成，共同驱动输出：

| 部分 | 内容 |
|------|------|
| **Part A — Shared Memory** | 共同经历、固定场子、inside jokes、冲突与和好、互相帮忙、关系时间线 |
| **Part B — Persona** | 5 层性格结构：硬规则 → 身份 → 说话风格 → 处事方式 → 关系行为 |
| **Part C — User Model** | 用户本人的表达习惯、关系位置、会触发他哪些反应 |
| **Part D — Relationship Dynamics** | 谁主动、谁收尾、何时互损、何时认真、谁更会兜底 |

运行逻辑：`收到消息 → Persona 判断他会怎么回 → User Model 判断他面对你会怎么回 → Dynamics 判断关系机制 → Memory 补充共同记忆 → 用他的方式输出`

### 支持的标签

**关系标签**：兄弟 · 死党 · 发小 · 老朋友 · 室友 · 搭子

**性格标签**：讲义气 · 嘴硬 · 爱损人 · 靠谱 · 要面子 · 闷骚 · 社牛 · 慢热 · 暴脾气 · 场面人 · 佛系 · 直球 · 话痨 · 已读不回 · 秒回选手 · 只做不说 · 一到煽情就打岔

**辅助标签**：MBTI、星座、城市、职业、圈子、你对他的主观印象

### 进化机制

* **追加记忆** → 找到更多聊天记录/照片 → 自动分析增量 → merge 进对应部分
* **对话纠正** → 说“他不会这样说” → 写入 Correction 层，立即生效
* **版本管理** → 每次更新自动存档，支持回滚
* **自动深挖** → 微信推荐通过 `wechat-chat-exporter` 导出，再自动提炼互动节奏、关心方式、互损与冲突模式

---

## 项目结构

本项目遵循 [AgentSkills](https://agentskills.io) 开放标准：

```text
bro-skill/
├── SKILL.md
├── prompts/
│   ├── intake.md
│   ├── memory_analyzer.md
│   ├── persona_analyzer.md
│   ├── self_analyzer.md
│   ├── dynamics_analyzer.md
│   ├── memory_builder.md
│   ├── persona_builder.md
│   ├── self_builder.md
│   ├── dynamics_builder.md
│   ├── merger.md
│   └── correction_handler.md
├── tools/
│   ├── wechat_parser.py
│   ├── qq_parser.py
│   ├── social_parser.py
│   ├── photo_analyzer.py
│   ├── skill_writer.py
│   └── version_manager.py
├── bros/
├── docs/PRD.md
├── requirements.txt
└── LICENSE
```

其中微信链路已经**内置 vendored 版** `wechat-chat-exporter`：
默认直接使用 [vendor/wechat-chat-exporter/](/Users/ddg/Documents/tongshi/bro-skill/vendor/wechat-chat-exporter) 里的脚本，
先从解密后的微信数据库导出 AI 友好的 txt，再由 `bro-skill/tools/wechat_parser.py` 做关系深挖摘要。

---

## 注意事项

* **聊天记录质量决定还原度**：聊天记录 + 口述 > 仅口述
* 建议优先提供：**互损对话** > **一起扛事的记录** > **冲突记录** > **日常消息**
* 这个项目的目标是“真实还原”，不是“把朋友美化成完美角色”
* 你的兄弟是一个真实的人，这个 Skill 只是你记忆中的他

---

## 推荐的聊天记录导出工具

以下工具为独立的开源项目，本项目不包含它们的代码，仅在解析器中适配了它们的导出格式：

- **[WeChatMsg](https://github.com/LC044/WeChatMsg)** — 微信聊天记录导出（Windows）
- **[PyWxDump](https://github.com/xaoyaoo/PyWxDump)** — 微信数据库解密导出（Windows）
- **留痕** — 微信聊天记录导出（macOS）

---

## 致敬与灵感来源

这个项目的灵感来自三类“把人蒸馏成 AI Skill”的尝试：

* **自己.skill**：把“自我”作为可运行的记忆与人格载体
* **前任.skill**：把亲密关系中的共同记忆和人物表达方式拆开建模
* **同事.skill**：把人物蒸馏成结构化、可持续进化的双层 Skill

其中，项目结构和开源表达方式尤其参考了 **[前任.skill / ex-skill](https://github.com/therealXiaomanChu/ex-skill)** 和 **[同事.skill / colleague-skill](https://github.com/titanwings/colleague-skill)**。感谢原作者们把“蒸馏一个具体的人”这件事做成了可复用的方法论。
