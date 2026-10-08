# 可索引

这个仓库只做网站本身：标题、说明、规范链接、站点地图、面包屑和站内链接。它不给页面打分，也不模拟排序。

站点发布之后，对照分两处看：

- 对抗和排位以 Chrome 里的谷歌搜索为准。打开 google.com，搜索 `records/serp.json` 里的查询，只数自然结果。广告、地图和「人们也问」不算。第 1 名就是第一条自然结果。
- 公司排序模型的效果在你自己的模型输出里看。把名次填进 `company_position`。本仓库填不了这一列。

两列现在都是空的。没有真实展现之前，不要写成已经排到第几。

## 页面

| 查询 | 路径 |
| --- | --- |
| 网页 title 和 h1 要一样吗 | `/seo/title-h1/` |
| canonical 和 sitemap 不一致怎么办 | `/seo/canonical-sitemap/` |
| 面包屑 JSON-LD 怎么写 | `/seo/breadcrumb-jsonld/` |
| 搜索引擎怎样识别网页正文 | `/seo/main-content/` |
| 站内链接的锚文本怎么写 | `/seo/anchor-text/` |

默认站点地址是 `https://wuwuww.github.io/seo-arena`。换成自己的域名时，改 `content/site.json` 的 `site_url`，再重新生成。canonical 和 sitemap 会跟着这个地址走。

## 生成

```bash
PYTHONPATH=src python -m seo_arena
PYTHONPATH=src python -m pytest -q
```

页面写到 `docs/`。GitHub Pages 用这个目录时，Chrome 里能打开的就是爬虫能抓的那一版。

## 记一次排位

1. 用 Chrome 打开谷歌，搜索表里的原句。
2. 从上往下只数自然结果，记下 `google_position` 和日期。
3. 把同一条 URL 放进公司排序模型，记下 `company_position`。

页面正文不写名次。名次只留在 `records/serp.json`。
