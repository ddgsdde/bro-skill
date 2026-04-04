# 详细安装说明

## Claude Code 安装

### 项目级安装（推荐）

在你的 git 仓库根目录执行：

```bash
mkdir -p .claude/skills
git clone https://github.com/ddgsdde/bro-skill .claude/skills/bro-skill
```

### 全局安装

```bash
git clone https://github.com/ddgsdde/bro-skill ~/.claude/skills/bro-skill
```

### OpenClaw 安装

```bash
git clone https://github.com/ddgsdde/bro-skill ~/.openclaw/workspace/skills/bro-skill
```

---

## 依赖安装

### 基础依赖（可选）

```bash
cd .claude/skills/bro-skill  # 或你的安装路径
pip3 install -r requirements.txt
```

目前唯一的可选依赖是 `Pillow`，用于读取照片 EXIF 信息。如果你不需要照片分析功能，可以跳过。

---

## 微信推荐方案：内置 wechat-chat-exporter

`bro-skill` 里的 `tools/wechat_parser.py` 已经默认对接仓库内置的：

```text
vendor/wechat-chat-exporter/
```

也就是说，`bro-skill` 本身已经带了微信导出后端，不需要再额外 clone 一份。

然后先用内置的 `wechat-chat-exporter` 完成：

1. 密钥提取
2. 数据库解密
3. 指定联系人导出

再由 `bro-skill/tools/wechat_parser.py` 对导出的聊天进行二次分析，提炼：

- 互动节奏
- 互损风格
- 帮忙/到场线索
- 关心方式
- 冲突模式
- 用户本人触发他的方式

如果你想覆盖默认后端，也可以额外设置：

```bash
export WECHAT_EXPORTER_DIR=/your/custom/wechat-chat-exporter
```

---

## 微信聊天记录导出指南

要获取微信聊天记录，你需要使用第三方导出工具。以下是推荐的工具：

### WeChatMsg（推荐）

- GitHub: https://github.com/LC044/WeChatMsg
- 支持 Windows
- 导出格式：txt / html / csv
- 使用方法：下载安装 → 登录微信 PC 版 → 选择联系人 → 导出

### PyWxDump

- GitHub: https://github.com/xaoyaoo/PyWxDump
- 支持 Windows
- 导出格式：SQLite 数据库
- 适合有编程基础的用户

### 留痕

- 支持 macOS
- 导出格式：JSON
- 适合 Mac 用户

### 手动复制

如果以上工具都不方便，你也可以：

1. 打开和这位兄弟的聊天窗口
2. 手动选择并复制关键对话
3. 粘贴到一个 txt 文件中
4. 在 `/create-bro` 时作为上传文件导入

---

## QQ 聊天记录导出指南

1. 打开 QQ → 点击左下角 `≡` → 设置
2. 通用 → 聊天记录 → 导出聊天记录
3. 选择联系人 → 导出为 txt 格式
4. 在 `/create-bro` 时使用导出的文件

---

## 常见问题

### Q: 数据会上传到云端吗？
A: 不会。所有数据都存储在你的本地文件系统中，不会上传到任何服务器。

### Q: 可以同时创建多个兄弟的 Skill 吗？
A: 可以。每个兄弟会生成独立的 `bros/{slug}/` 目录。

### Q: 创建后还能修改吗？
A: 可以。说“他不会这样说”触发对话纠正，或“我有新文件”追加原材料。每次修改都有版本存档，可以回滚。

### Q: 这个项目适合哪些关系？
A: 最适合兄弟、死党、发小、老朋友、长期搭子。也能用于普通朋友，但不建议直接拿去套恋爱或上下级关系。
