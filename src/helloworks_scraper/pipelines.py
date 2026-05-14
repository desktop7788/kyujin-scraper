"""Scrapy item pipelines: classify (authoritative filter) + jsonl writer.

Pipelines must be referenced by their full module path in Scrapy's ITEM_PIPELINES
setting (NOT __main__ — that breaks when Scrapy imports them). Runtime context
(RunStats singleton, jsonl path) is injected via module-level setters that main.py
calls before launching the crawler.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from helloworks_scraper.classify import classify_item


@dataclass
class RunStats:
    parsed_count: int = 0
    rejected_count: int = 0
    rejected_reasons: dict = field(default_factory=lambda: defaultdict(int))


# Module-level singletons set by main.py before crawler launch.
_run_stats: "RunStats | None" = None
_jsonl_path: "str | None" = None


def set_run_stats(stats: RunStats) -> None:
    global _run_stats
    _run_stats = stats


def set_jsonl_path(path: str) -> None:
    global _jsonl_path
    _jsonl_path = path


class ClassifyPipeline:
    def __init__(self, stats: RunStats):
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        assert _run_stats is not None, "pipelines.set_run_stats() must be called before crawler start"
        return cls(_run_stats)

    def process_item(self, item, spider):
        self.stats.parsed_count += 1
        data = ItemAdapter(item).asdict()
        verdict = classify_item(data)
        if not verdict.accepted:
            self.stats.rejected_count += 1
            self.stats.rejected_reasons[verdict.reject_reason] += 1
            raise DropItem(f"rejected: {verdict.reject_reason}")
        return item


class JsonLinesPipeline:
    def __init__(self, path: str):
        self.path = path
        self._fp = None

    @classmethod
    def from_crawler(cls, crawler):
        assert _jsonl_path is not None, "pipelines.set_jsonl_path() must be called before crawler start"
        return cls(_jsonl_path)

    def open_spider(self, spider):
        self._fp = open(self.path, "w", encoding="utf-8")

    def close_spider(self, spider):
        if self._fp:
            self._fp.close()
            self._fp = None

    def process_item(self, item, spider):
        line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False)
        self._fp.write(line + "\n")
        return item
