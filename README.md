# seo-arena

用 LangGraph 生成一个方便搜索引擎收录、用来提高自然排名的站点。`inspect` 看当前页还缺什么，缺就走 `lookup` → `choose` → `apply`，再回到 `inspect`。这一页齐了就 `next_page`。全部页面齐了以后 `cross_link` 写站内链接，最后 `sitemap` 收口。

目录里的步骤来自 Google Search Central 的公开说明：独立标题、摘要、主标题、首段回答、规范链接、描述性内链、面包屑和站点地图。每一步在 `records/agent-trace.json` 里带有来源地址。页面上线后，用 Chrome 打开谷歌，搜索对应问题，把自然结果名次记到 `records/serp.json` 的 `google_position`。

## 运行

```bash
PYTHONPATH=src python -m seo_arena --brief briefs/nanmen.json
PYTHONPATH=src python -m pytest -q
```

换一个站时，复制 `briefs/nanmen.json`，改品牌、问题和每页不同的说明。每页内容保持不同，搜索结果里才分得清。

默认发布地址是 https://wuwuww.github.io/seo-arena/ 。`site_url` 要和实际上线的地址一致，canonical 和 sitemap 才指向同一条网址。
