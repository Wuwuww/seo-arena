# seo-arena

一期一页的 AI 简报。LangGraph 先分别拉取论文、大模型和 Skill，再去掉没有标题、不是 https、以及重复的条目，编成当天这一期，最后检查有没有空栏目。

栏目按现在常见的技术简报来排：研究、模型和能直接用的工具。每条只保留标题、来源信息和接口里的原文片段，点标题打开原文。

- 论文：arXiv，`cs.CL` 和 `cs.AI` 的最新提交
- 大模型：Hugging Face 文本生成模型的趋势列表
- Skill：[anthropics/skills](https://github.com/anthropics/skills) 里写文档、做设计和搭 agent 会打开的几条

## 运行

```bash
PYTHONPATH=src python -m seo_arena
PYTHONPATH=src python -m pytest -q
```

页面写到 `docs/`，发布地址是 https://wuwuww.github.io/seo-arena/ 。GitHub Actions 在每天北京时间 9:00 跑一次，也可以手动触发 `daily-ai`。

搜索引擎自己决定收录和名次。
