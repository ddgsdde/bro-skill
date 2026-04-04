# 兄弟.skill / bro-skill — 产品需求文档（PRD）

## 产品定位

兄弟.skill 是一个运行在 Claude Code 上的 meta-skill。
用户通过对话式交互提供原材料（聊天记录 + 照片 + 手动描述），系统自动生成一个可独立运行的兄弟 Persona Skill。

## 核心概念

### 两层架构

| 层 | 名称 | 职责 |
|----|------|------|
| Part A | Shared Memory | 存储事实性记忆：共同经历、固定场子、内部梗、互相帮忙、冲突与和好 |
| Part B | Persona | 驱动对话行为：说话风格、幽默方式、处事模式、义气边界 |
| Part C | User Model | 描述“你是谁”，以及你会如何触发他 |
| Part D | Relationship Dynamics | 描述这段关系如何运转：谁主动、谁收尾、何时认真、何时嘴硬 |

两部分可以独立使用，也可以组合运行。

### 运行逻辑

```text
用户发消息
  ↓
Part B（Persona）判断：他会怎么回应？什么态度？用什么语气？
  ↓
Part C（User Model）判断：面对你时他会如何调整
  ↓
Part D（Dynamics）判断：这段关系在当前话题下会怎么运转
  ↓
Part A（Memory）补充：结合共同记忆，让回应更真实
  ↓
输出：用他的方式说话
```

### 进化机制

```text
追加原材料 → 增量分析 → merge 进现有 Skill
对话纠正 → 识别修正点 → 写入 Correction 层
版本管理 → 每次更新自动存档 → 支持回滚
```

## 用户旅程

```text
用户触发 /create-bro
  ↓
[Step 1] 基础信息录入（3 个问题，除花名外均可跳过）
  - 花名/代号
  - 基本信息（怎么认识、认识多久、现在什么状态、职业等）
  - 性格画像（说话风格、性格标签、主观印象）
  ↓
[Step 2] 原材料导入（可跳过）
  - 微信聊天记录导出
  - QQ 聊天记录导出
  - 社交媒体截图
  - 照片
  - 直接粘贴/口述
  ↓
[Step 3] 自动分析
  - 线路 A：提取共享记忆 → Memory
  - 线路 B：提取性格行为 → Persona
  - 线路 C：提取用户本人画像 → User Model
  - 线路 D：提取互动规则 → Relationship Dynamics
  ↓
[Step 4] 生成预览，用户确认
  ↓
[Step 5] 写入文件，立即可用
  - 生成 bros/{slug}/ 目录
  - 包含 SKILL.md（完整组合版）
  - 包含 memory.md 和 persona.md（独立部分）
  ↓
[持续] 进化模式
  - 追加新文件 → merge 进对应部分
  - 对话纠正 → patch 对应层
  - 版本自动存档
```

## 安全边界

1. **仅用于个人记忆整理、创作式对话与关系回顾**
2. **不主动联系真人**
3. **不鼓励冒充或骚扰**
4. **数据仅本地存储**
5. **Layer 0 硬规则**保证不说这个人明显不会说的话

## 数据源支持矩阵

| 来源 | 格式 | 提取内容 | 优先级 |
|------|------|---------|--------|
| 微信聊天记录 | WeChatMsg / 留痕 / PyWxDump | 完整对话、语气词、回复模式 | ⭐⭐⭐ |
| QQ 聊天记录 | txt / mht | 完整对话 | ⭐⭐⭐ |
| 照片 | JPEG / PNG + EXIF | 时间线、地点 | ⭐⭐ |
| 社交媒体截图 | 图片 | 公开人设、兴趣、表达习惯 | ⭐⭐ |
| 口述/粘贴 | 纯文本 | 主观记忆 | ⭐ |

## 文件结构

```text
bros/
  └── {slug}/
      ├── SKILL.md
      ├── memory.md
      ├── persona.md
      ├── meta.json
      ├── versions/
      └── memories/
          ├── chats/
          ├── photos/
          └── social/
```

## 与相关项目的关系

| 项目 | Part A | Part B | 场景 |
|------|--------|--------|------|
| 自己.skill | Self Memory | Self Persona | 自我蒸馏 |
| 同事.skill | Work Skill | Persona | 职场协作 |
| 前任.skill | Relationship Memory | Persona | 亲密关系回忆 |
| 兄弟.skill | Shared Memory | Persona | 兄弟/死党/老朋友关系 |

## 设计目标

1. 保持人物真实，不神化
2. 保留幽默、嘴硬、义气和边界
3. 既能回忆共同经历，也能模拟说话方式
4. 支持持续追加和修正
5. 支持从微信资料中自动深挖更高质量的关系线索
6. 将微信导出后端 vendored 进仓库，做到开箱即用
