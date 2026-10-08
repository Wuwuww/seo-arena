# seo-arena

一个生成站点的 agent。它按目录里的页面级步骤补全标题、说明、正文、规范链接、面包屑和站点地图，然后写出 `docs/`。

公司的 SEO 检测系统不在这里运行。生成结果交给检测系统，检测结论填到 `records/serp.json` 的 `detector_label`。谷歌名次用 Chrome 打开谷歌，只数自然结果，填到 `google_position`。

目录里的步骤来自 Google Search Central 的公开说明，每一步在 `records/agent-trace.json` 里带有来源地址。这个仓库不根据检测结果回改页面。

## 运行

```bash
PYTHONPATH=src python -m seo_arena --brief briefs/nanmen.json
PYTHONPATH=src python -m pytest -q
```

换一个站时，复制 `briefs/nanmen.json`，改品牌、问题和每页不同的说明。页面内容要彼此不同，否则检测系统看到的会是一组重复页。

默认发布地址是 https://wuwuww.github.io/seo-arena/ 。`site_url` 要和实际上线的地址一致，canonical 和 sitemap 才指向同一条网址。
