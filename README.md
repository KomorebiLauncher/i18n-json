# i18n-json

Komorebi Launcher 的翻译数据，按语言导出为 JSON。

这个仓库是译文的手改入口：直接改 `json/{lang}.json` 里的 `translation` 并提 PR 即可。[KomorebiLauncher/i18n](https://github.com/KomorebiLauncher/i18n) 负责把这里的 JSON 合并回 `.ts` 目录，再编译成语言包发布到 <https://komorebilauncher.github.io/i18n/>，启动器启动时按需下载。

## 结构

```
json/{lang}.json     每个语言一个文件，条目与源串目录一一对应（当前 2747 条）
manifest.json        各语言的已译/缺译统计
tools/export.py      从 .ts 目录生成上面两者的脚本
```

## 条目格式

```json
[
  {
    "key": "APIPage:036e7f7baee8",
    "original": "&Pastebin Service",
    "translation": "Pastebin 服务 (&P)",
    "context": "APIPage"
  }
]
```

| 字段 | 说明 |
| --- | --- |
| `key` | `上下文:sha1(原文)[:12]`。同一字符串在所有语言里 key 相同，方便对照；原文变了 key 也会变，旧条目自然失效 |
| `original` | Qt 源串原文（已反转义） |
| `translation` | 现有译文。**空字符串表示尚未翻译**；复数条目用换行分隔多个形式 |
| `context` | 上下文类名，附加 `extracomment`（若源串有的话）；`[plural]` 表示复数条目，`[unfinished]` 表示现有译文是模糊条目、需要复核 |

已被源码移除的字符串（`.ts` 里的 `vanished`）不会导出。

## 改译文

1. 打开 `json/{lang}.json`，把要翻的条目的 `translation` 填上，`""` 保留给还没翻的条目。
2. 提 PR。

保留 HTML 标签、`%1`/`%n` 之类的占位符、首尾空格和换行。助记符（原文里的 `&X`）按 `(&X)` 的习惯放在词尾。

`Refresh` 工作流每周一 04:30 UTC 按 i18n 仓库的最新源串刷新 `key`/`original`，并用 `--keep json` 保留已有译文，所以手改的译文不会被覆盖。如果源码里某条原文改了，会生成新 key、译文留空，需要重新翻。

## 重新生成

```bash
git clone --depth 1 https://github.com/KomorebiLauncher/i18n.git ../i18n
python tools/export.py --catalogue ../i18n --out json --keep json
```

`--keep json` 让本仓库已有的译文优先于 `.ts` 里的值，这样手工补的译文不会丢。不带 `--keep` 时 JSON 会完全按 `.ts` 重写，首尾空格之类的细节会被归一化。

注意：`export.py` 会去掉非复数译文的首尾空白，而少数源串本身就带（比如 ` MiB`、`Unknown loader type: `）。这类空白只存在 `.ts` 里；合并时 `from_json.py` 遇到"只差空白"的条目会保留 `.ts` 的写法，不会把它们冲掉。

数值对不上时也可以手工核对：`git diff json/` 应该只出现真正改过的语言。

## 当前覆盖情况

| 范围 | 语言数 |
| --- | --- |
| 100% | 6（`zh`、`ja`、`en_AU`、`en_CA`、`en_GB`、`en_NZ`） |
| ≥90% | 0 |
| 50–90% | 43 |
| <50% | 52 |
| 0% | 1（`bar`） |

其余语言的缺口基本都是本项目相对 Prism Launcher 新增的功能文案（崩溃分析、镜像、OptiFine 安装、账号提示等），上游继承的基线翻译已覆盖约 92%。`en@pirate`、`en@uwu` 之类是整活语种，不追求翻全。

## 自动同步

- `.github/workflows/refresh.yml`（每周一 04:30 UTC，也可手动触发，`dry_run` 只跑不提交）：克隆 i18n 仓库、按最新源串重跑 `export.py --keep json` 并提交。
- i18n 仓库的 `update-strings`（周一 04:00）先按启动器源码刷新 `.ts`；`merge-translations`（周一 05:00）把本仓库的 JSON 合并进 `.ts`，再触发 `build.yml` 重新编译语言包。
