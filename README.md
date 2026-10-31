# i18n-json

Komorebi Launcher 的翻译目录，按语言导出为 JSON，供翻译平台导入。

源数据在 [KomorebiLauncher/i18n](https://github.com/KomorebiLauncher/i18n) 的 Qt `.ts` 文件里；这个仓库只是把它转成平台需要的形状，**不要直接在这里改**。

## 结构

```
json/{lang}.json     每个语言一个文件，条目与源串目录一一对应（当前 2562 条）
manifest.json        各语言的已译/缺译统计
tools/export.py      生成器
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
| `key` | `上下文:sha1(原文)[:12]`。同一字符串在所有语言里 key 相同，便于平台做多语言对齐；原文变了 key 也会变，旧条目自然失效 |
| `original` | Qt 源串原文（已反转义） |
| `translation` | 现有译文。**空字符串表示尚未翻译**；复数条目用换行分隔多个形式 |
| `context` | 上下文类名，附加 `extracomment`（若源串有的话）；`[plural]` 表示复数条目，`[unfinished]` 表示现有译文是模糊条目、需要复核 |

已被源码移除的字符串（`.ts` 里的 `vanished`）不会导出。

## 重新生成

```bash
git clone --depth 1 https://github.com/KomorebiLauncher/i18n.git ../i18n
python tools/export.py --catalogue ../i18n --out json
```

`i18n` 仓库的 `update-strings` 工作流会从启动器源码重新提取字符串；字符串变动后重新跑一次上面的命令即可。

## 当前覆盖情况

| 范围 | 语言数 |
| --- | --- |
| 100% | 1（`zh`） |
| ≥90% | 22 |
| 50–90% | 27 |
| <50% | 52 |
| 0% | 1（`bar`） |

其余语言的缺口基本都是本项目相对 Prism Launcher 新增的功能文案（崩溃分析、镜像、OptiFine 安装、账号提示等），上游继承的基线翻译已覆盖约 92%。
