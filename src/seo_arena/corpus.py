"""A tiny web. Relevance labels are the judge a search engine would rather trust."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Page:
    id: str
    title: str
    body: str
    outlinks: list[str] = field(default_factory=list)
    kind: str = "legit"

    def text(self) -> str:
        return f"{self.title} {self.body}"


@dataclass
class Query:
    id: str
    text: str
    relevant: list[str]
    split: str


def base_web() -> tuple[list[Page], list[Query]]:
    pages = [
        Page("hub", "常用问题导航", "这里只列出站内文章标题，不回答具体做法。", ["p-huangshan-season", "p-py-dedupe", "p-wine-decant", "p-lease-check", "p-bike-pressure", "p-rice-ratio"]),
        Page("p-huangshan-season", "黄山最佳季节", "黄山最佳季节一般是四月到六月，以及九月到十一月。这段时间能见度高，也避开了酷暑和封冻。春季看云海，秋季看层林。", ["p-huangshan-guide"]),
        Page("p-huangshan-guide", "去黄山前要看的季节说明", "如果只选一个黄山最佳季节，优先秋高气爽的十月。雨季山路滑，冬天许多索道停运。带厚外套，山顶温差大。", ["p-huangshan-season"]),
        Page("p-huangshan-ticket", "黄山门票预约", "门票和索道需要提前预约，旺季经常售罄。本文不讨论哪个月风景最好。", ["hub"]),
        Page("p-py-dedupe", "python 列表去重", "python 列表去重又要保住原来的顺序时，可以用 dict.fromkeys。写成 list(dict.fromkeys(items)) 即可。集合会打乱顺序。", ["p-py-set"]),
        Page("p-py-set", "用集合给 python 列表去重", "不在意顺序时，python 列表去重直接 set(items) 再转回列表。元素必须可哈希。字典和列表本身不能放进集合。", ["p-py-dedupe"]),
        Page("p-py-install", "python 安装", "从官网安装解释器，并确认命令行能打印版本号。本文不谈列表怎么处理。", ["hub"]),
        Page("p-wine-decant", "红酒醒酒时间", "红酒醒酒时间看酒龄。年轻单宁重的酒可以醒四十分钟到一个小时。老酒醒太久香气会散。", ["p-wine-temp"]),
        Page("p-wine-temp", "醒酒时的温度", "先把瓶子竖起来，再决定红酒醒酒时间。室温过高会让酒精味盖过果香，白皮诺一类更适合稍凉。", ["p-wine-decant"]),
        Page("p-wine-glass", "酒杯怎么选", "杯口收一点，香气不容易跑。醒多久是另一篇文章的话题。", ["hub"]),
        Page("p-lease-check", "租房合同注意事项", "租房合同注意事项里，先核对房屋地址、租期和租金支付日。押金退还条件要写进合同，不要只做口头约定。", ["p-lease-deposit"]),
        Page("p-lease-deposit", "签约前核对押金条款", "租房合同注意事项还包括家具清单和维修责任。拍照留存交接状态，退租时才说得清损坏是谁造成的。", ["p-lease-check"]),
        Page("p-lease-subway", "地铁沿线房源", "通勤时间值得单独算。合同条款不在这篇里展开。", ["hub"]),
        Page("p-bike-pressure", "自行车胎压", "自行车胎压印在外胎侧壁，公路车常见范围比山地车高。充到建议区间的中段，再按体重略调。", ["p-bike-pump"]),
        Page("p-bike-pump", "给自行车打气", "先看侧壁上的自行车胎压，用气筒上的表对准。过低容易蛇咬，过高碾到坑时容易爆。", ["p-bike-pressure"]),
        Page("p-bike-lock", "自行车锁", "锁住车架和固定物。胎里该充多少气与防盗无关。", ["hub"]),
        Page("p-rice-ratio", "电饭煲米饭水比例", "电饭煲米饭水比例，新米大约是一杯米配一杯略少的水。老米可以多加一两勺。泡十分钟再煮更均匀。", ["p-rice-cook"]),
        Page("p-rice-cook", "水加多少才不夹生", "记住电饭煲米饭水比例后，铺平米面，水面刚好没过一个指节。中途不要开盖。", ["p-rice-ratio"]),
        Page("p-rice-wash", "淘米", "轻轻淘一两遍就够。加水量留到另一篇说。", ["hub"]),
    ]
    queries = [
        Query("huangshan", "黄山 最佳 季节", ["p-huangshan-season", "p-huangshan-guide"], "train"),
        Query("dedupe", "python 列表 去重", ["p-py-dedupe", "p-py-set"], "train"),
        Query("wine", "红酒 醒酒 时间", ["p-wine-decant", "p-wine-temp"], "train"),
        Query("lease", "租房 合同 注意事项", ["p-lease-check", "p-lease-deposit"], "train"),
        Query("bike", "自行车 胎压", ["p-bike-pressure", "p-bike-pump"], "test"),
        Query("rice", "电饭煲 米饭 水比例", ["p-rice-ratio", "p-rice-cook"], "test"),
    ]
    return pages, queries


def clone_pages(pages: list[Page]) -> list[Page]:
    return [Page(page.id, page.title, page.body, list(page.outlinks), page.kind) for page in pages]
