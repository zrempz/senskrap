import asyncio
import json
import time
from datetime import datetime
from senskrap.scrapers.twitcasting import TwitcastingShop
from json import dumps


async def main():
    """
    Scrapes Twitcasting shop items for the current date,
    gathers information for each item concurrently,
    and prints benchmark results.
    """
    start_total_time = time.perf_counter()

    print("Initializing scraper...")
    scraper = TwitcastingShop()

    start_links_time = time.perf_counter()
    links = await scraper.scrape_by_date(datetime.now())
    end_links_time = time.perf_counter()

    if not links:
        print("No links found to process.")
        return

    num_links = len(links)
    print(f"Found {num_links} links to process.")

    start_gather_time = time.perf_counter()
    tasks = [scraper.get_info(url) for url in links]
    results = await asyncio.gather(*tasks)
    end_gather_time = time.perf_counter()
    end_total_time = time.perf_counter()

    links_duration = end_links_time - start_links_time
    gather_duration = end_gather_time - start_gather_time
    total_duration = end_total_time - start_total_time

    print("\n" + "=" * 30)
    print(" BENCHMARK RESULTS")
    print("=" * 30)
    print(f"Time to fetch {num_links} links: {links_duration:.2f} seconds.")
    print(f"Time to gather info for {num_links} items: {gather_duration:.2f} seconds.")
    print(f"Total execution time: {total_duration:.2f} seconds.")
    if num_links > 0:
        print(f"Average time per item: {gather_duration / num_links:.2f} seconds.")
    print("=" * 30)

    filename = f"twitcasting_results_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Results saved to '{filename}'.")

    await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
