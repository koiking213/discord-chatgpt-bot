# Discord ChatGPT Bot

リプライで話しかけると応答するだけのbot

## 準備

Discord側での設定。
TODO: どういう設定が必要だったか思い出したら書く。

## config

`.env.sample` を `.env` にリネームし、OpenAIのAPI KeyとDiscordのBot Tokenを埋める。

`config.yaml.sample` を `config.yaml` にリネームする。

- `chat_gpt_model`: 使用するChatGPTのモデル名。
- `bot_name`: Discordに表示するボット名。
- `database.use_database`: OpenAI APIの使用量をデータベースに記録する場合はtrue。使用しない場合はこれ以下の設定はすべて無視される。
- `database.host`: 使用するデータベースのホスト名またはエンドポイント。
- `database.port`: データベースサーバーのポート番号。
- `database.dbname`: データベースの名前。
- `database.user`: データベースへの接続に使用するユーザー名。
- `database.password`: 上記ユーザーのパスワード。


## 自動起動設定

- `systemd/discord-chatgpt-bot.service` の `WorkingDirectory` を埋めて `/etc/systemd/system/` にコピー
- systemctlで設定

```
# sudo systemctl enable discord-chatgpt-bot.service
# sudo systemctl start discord-chatgpt-bot.service
```
