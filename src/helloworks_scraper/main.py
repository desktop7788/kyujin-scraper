"""Entry point: configure Scrapy, run spider, upload results, update run log."""

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess

from helloworks_scraper import pipelines, upload
from helloworks_scraper.pipelines import RunStats
from helloworks_scraper.spider import KyujinboxV2Spider


load_dotenv()

logger = logging.getLogger(__name__)


def _scrapy_settings() -> dict:
    # 旧 SetagayaLab スクレイパー (Windows) と同一のブラウザらしいヘッダ群。
    # USER_AGENT 単独だと kyujinbox は結果を間引いて返す (実測 旧の 20-35% しか
    # ヒットしない) ため、Sec-Fetch-*, sec-ch-ua, Accept-Language 等を完全移植して
    # 「Windows Chrome 126」相当に擬装する。Cookie は旧でもコメントアウト済 (未送信)。
    return {
        "BOT_NAME": "helloworks_scraper",
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        },
        "ROBOTSTXT_OBEY": False,
        # 旧 SetagayaLab (Scrapy default = 16) と一致させる
        "CONCURRENT_REQUESTS": 16,
        "DOWNLOAD_DELAY": 0.5,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 5,
        # 404 を除外: kyujinbox は「該当求人ゼロ」を 404 で返す (例: 警備-清掃-点検 ×
        # 地方県の e=5 派遣)。404 をリトライしても結果は同じなので時間の無駄。
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 403, 400],
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_POLICY": "helloworks_scraper.spider.CachePolicy",
        "HTTPCACHE_EXPIRATION_SECS": 30 * 24 * 3600,
        "HTTPCACHE_DIR": ".scrapy/httpcache",
        "DOWNLOADER_MIDDLEWARES": {
            "helloworks_scraper.spider.BackoffMiddleware": 543,
        },
        "ITEM_PIPELINES": {
            "helloworks_scraper.pipelines.ClassifyPipeline": 100,
            "helloworks_scraper.pipelines.JsonLinesPipeline": 200,
        },
        "LOG_LEVEL": "INFO",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-crawl", action="store_true", help="クロールせず upload のみ")
    parser.add_argument("--no-upload", action="store_true", help="アップロードせず crawl のみ")
    parser.add_argument("--upload-from", help="既存 jsonl ファイルから upload")
    parser.add_argument("--category", help="特定業種のみ実行 (e.g. light_warehouse). 未指定で全業種")
    parser.add_argument(
        "--employment-type", type=int, choices=[2, 5], default=None,
        help="特定雇用形態のみ実行 (2=アルバイト・パート, 5=派遣). 未指定で両方"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")

    upload.assert_safe_supabase_url()

    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    category_top = args.category if args.category else "legacy_all"
    os.makedirs("output", exist_ok=True)
    jsonl_path = args.upload_from or f"output/kyujinbox_v2-{run_id}.jsonl"

    stats = RunStats()
    status = "running"
    error_text = None

    if not args.no_crawl and not args.upload_from:
        upload.insert_run_start(run_id, started_at, category_top=category_top)
        pipelines.set_run_stats(stats)
        pipelines.set_jsonl_path(jsonl_path)
        try:
            process = CrawlerProcess(settings=_scrapy_settings())
            process.crawl(
                KyujinboxV2Spider,
                run_id=run_id,
                category=args.category,
                employment_type=args.employment_type,
            )
            process.start()
        except Exception as e:
            logger.exception("crawl failed")
            error_text = str(e)
            status = "failed"
    else:
        # uploading from existing file — recreate the run row
        upload.insert_run_start(run_id, started_at, category_top=category_top)

    inserted = 0
    if not args.no_upload and status != "failed" and os.path.exists(jsonl_path):
        try:
            rows = []
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    row = json.loads(line)
                    rows.append(row)
            batch_size = int(os.environ.get("SUPABASE_BATCH_SIZE", "500"))
            inserted = upload.upload_rows(rows, batch_size=batch_size)
            if status == "running":
                status = "success"
        except Exception as e:
            logger.exception("upload failed")
            error_text = str(e)
            status = "failed"

    finished_at = datetime.now(timezone.utc).isoformat()
    upload.update_run_finish(
        run_id=run_id,
        finished_at=finished_at,
        status=status,
        parsed_count=stats.parsed_count,
        inserted_count=inserted,
        rejected_count=stats.rejected_count,
        rejected_reasons=dict(stats.rejected_reasons),
        error_text=error_text,
    )

    logger.info(
        "run %s finished: status=%s parsed=%d inserted=%d rejected=%d reasons=%s",
        run_id, status, stats.parsed_count, inserted, stats.rejected_count, dict(stats.rejected_reasons),
    )

    if status == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
