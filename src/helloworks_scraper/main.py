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
    return {
        "BOT_NAME": "helloworks_scraper",
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.5,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 403, 404, 400],
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
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")

    upload.assert_safe_supabase_url()

    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    os.makedirs("output", exist_ok=True)
    jsonl_path = args.upload_from or f"output/kyujinbox_v2-{run_id}.jsonl"

    stats = RunStats()
    status = "running"
    error_text = None

    if not args.no_crawl and not args.upload_from:
        upload.insert_run_start(run_id, started_at)
        pipelines.set_run_stats(stats)
        pipelines.set_jsonl_path(jsonl_path)
        try:
            process = CrawlerProcess(settings=_scrapy_settings())
            process.crawl(KyujinboxV2Spider, run_id=run_id)
            process.start()
        except Exception as e:
            logger.exception("crawl failed")
            error_text = str(e)
            status = "failed"
    else:
        # uploading from existing file — recreate the run row
        upload.insert_run_start(run_id, started_at)

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
