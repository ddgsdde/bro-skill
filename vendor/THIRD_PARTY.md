# Third-Party Components

## wechat-chat-exporter

- Source: https://github.com/ddgsdde/wechat-chat-exporter
- Vendored under: `vendor/wechat-chat-exporter/`
- Upstream license: WTFPL
- Purpose in this project:
  - export messages from decrypted local WeChat databases
  - merge multi-database chat history
  - provide AI-friendly plaintext that `bro-skill/tools/wechat_parser.py` can deepen into relationship analysis

The vendored files are included to make `bro-skill` work out of the box for WeChat ingestion without requiring a separate clone.
