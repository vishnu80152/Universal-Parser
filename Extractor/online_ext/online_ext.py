import asyncio
import logging
from halo import Halo
from colorama import Fore, Style, init

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)
from crawl4ai.content_filter_strategy import (
    PruningContentFilter,
    BM25ContentFilter,
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

init(autoreset=True)

# ---------------- LOGGER SETUP ---------------- #

class ColorFormatter(logging.Formatter):
    COLORS = {
        "INFO": Fore.CYAN,
        "SUCCESS": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

logging.addLevelName(25, "SUCCESS")

def success(self, message, *args, **kws):
    if self.isEnabledFor(25):
        self._log(25, message, args, **kws)

logging.Logger.success = success

logger = logging.getLogger("web-crawler")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)

# ---------------- CRAWLER SERVICE ---------------- #

class WebCrawlerService:
    def __init__(
        self,
        headless: bool = True,
        verbose: bool = True,
        cache_mode: CacheMode = CacheMode.ENABLED,
    ):
        logger.info("Initializing browser configuration")

        self.browser_config = BrowserConfig(
            headless=headless,
            verbose=verbose,
        )
        self.cache_mode = cache_mode

        logger.success("Browser configuration ready")

    async def crawl(
        self,
        url: str,
        filter_type: str = "pruning",
        threshold: float = 0.48,
        min_word_threshold: int = 0,
        user_query: str | None = None,
        bm25_threshold: float = 1.0,
    ):
        logger.info(f"Preparing crawl for URL: {url}")

        if filter_type == "bm25":
            if not user_query:
                logger.warning("BM25 selected but user_query is empty")

            content_filter = BM25ContentFilter(
                user_query=user_query or "",
                bm25_threshold=bm25_threshold,
            )
            logger.info("Using BM25 content filter")

        else:
            content_filter = PruningContentFilter(
                threshold=threshold,
                threshold_type="fixed",
                min_word_threshold=min_word_threshold,
            )
            logger.info("Using pruning content filter")

        run_config = CrawlerRunConfig(
            cache_mode=self.cache_mode,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=content_filter
            ),
        )

        spinner = Halo(
            text="Crawling and processing page",
            spinner="dots",
            color="cyan",
        )
        spinner.start()

        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=run_config,
                )

            spinner.succeed("Crawling completed")

            logger.success(
                f"Markdown generated | raw={len(result.markdown.raw_markdown)} "
                f"| filtered={len(result.markdown.fit_markdown)}"
            )

            return {
                "raw_markdown": result.markdown.raw_markdown,
                "fit_markdown": result.markdown.fit_markdown,
                "raw_length": len(result.markdown.raw_markdown),
                "fit_length": len(result.markdown.fit_markdown),
            }

        except Exception as e:
            spinner.fail("Crawling failed")
            logger.error(str(e))
            raise

# ---------------- ENTRY ---------------- #

if __name__ == "__main__":

    async def run():
        crawler = WebCrawlerService(
            headless=True,
            verbose=True,
        )

        result = await crawler.crawl(
            url="https://docs.micronaut.io/4.9.9/guide/",
            filter_type="pruning",
            threshold=0.48,
        )

        with open("output.md", "w", encoding="utf-8") as f:
            f.write(result["raw_markdown"])

        logger.success("Saved crawl output to output.md")

    asyncio.run(run())
