# wechat-chat-exporter

从解密后的本地微信数据库中导出聊天记录，自动合并多数据库消息，并生成适合 AI 读取的干净文本文件。

## 特性

- 自动合并同一会话分散在多个 `message_N.db` / `biz_message_N.db` 中的消息
- 导出适合 AI 处理的紧凑文本格式
- 为每条消息附带短发言人编号，并在文件头提供映射
- 图片、语音、视频、表情、文件、撤回、未知类型统一导出为简短占位符
- 支持按联系人、群聊、关键词、日期范围导出
- 默认忽略密钥、解密数据库和导出结果，避免误提交隐私内容

## 输出格式

导出的 txt 文件会尽量减少无用字符，同时保留完整的时间线和说话人信息。

```text
# Chat: 联系人A (wxid_xxx)
# P: 1=我 | 2=联系人A
# 联系人A | total: 57754, showing: 57754 | db: message_0.db,message_1.db,message_2.db

2025-01-22 10:56:35 2 ？
2025-01-22 13:59:44 1 [img]
2025-01-22 13:59:46 1 哥们
```

群聊会自动扩展成 `1=我 | 2=成员A | 3=成员B ...` 这种映射格式。

## 前置条件

- macOS arm64
- 微信 4.x
- 已禁用 SIP：`csrutil disable`
- 已安装依赖：`brew install llvm sqlcipher`

## 使用流程

### 1. 提取密钥

确保微信已登录并正在运行：

```bash
PYTHONPATH="$(lldb -P)" /usr/bin/python3 find_key_memscan.py
```

密钥会保存到 `wechat_keys.json`。

### 2. 解密数据库

```bash
/usr/bin/python3 decrypt_db.py
```

### 3. 导出聊天记录

```bash
# 列出所有会话
python3 export_messages.py

# 导出指定会话（支持模糊匹配）
python3 export_messages.py -c "联系人A"
python3 export_messages.py -c wxid_xxx
python3 export_messages.py -c 12345@chatroom

# 导出最近 N 条
python3 export_messages.py -c "联系人A" -n 200

# 按日期范围导出
python3 export_messages.py -c "联系人A" --since 2026-03-01 --until 2026-03-31

# 导出所有会话
python3 export_messages.py --all

# 只导出个人聊天和群聊（过滤公众号）
python3 export_messages.py --all --personal

# 搜索关键词
python3 export_messages.py -s "关键词"
```

### 4. 合并多个导出文件

如果你导出了整批会话，可以把结果合并成一个文本文件：

```bash
python3 merge_and_clean.py exported
python3 merge_and_clean.py exported output.txt
python3 merge_and_clean.py exported output.txt --clean
```

## 测试

```bash
python3 -m unittest -v test_export_messages.py
python3 -m py_compile export_messages.py test_export_messages.py
```

## 隐私与安全

仓库默认忽略以下敏感内容：

- `wechat_keys.json`
- `decrypted/`
- `exported/`
- `exported_*/`
- `*_cleaned.txt`

上传代码前，建议再确认一次工作区里没有聊天记录、密钥或解密数据库文件。

## MCP Server

仓库仍然保留 `mcp_server.py`，可用于把解密后的微信数据接入支持 MCP 的工具。

```bash
pip3 install fastmcp
claude mcp add wechat -- python3 "$(pwd)/mcp_server.py"
```

## Thanks

- [ylytdeng/wechat-decrypt](https://github.com/ylytdeng/wechat-decrypt)
