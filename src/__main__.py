import asyncio
from datetime import datetime
import time
import json
from senskrap import TwitcastingPremier

async def main():
    start_total_time = time.perf_counter()
    async with TwitcastingPremier() as scraper:
        start_links_time = time.perf_counter()
        links = await scraper.search_by_term("6月24日劇コ")
        end_links_time = time.perf_counter()
        num_links = len(links)

        print(f"Found {num_links} links")
        if not links:
            return

        start_gather_time = time.perf_counter()
        tasks = [scraper.get_item_details(url) for url in links]
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
        print(
            f"Time to gather info for {num_links} items: {gather_duration:.2f} seconds."
        )
        print(f"Total execution time: {total_duration:.2f} seconds.")
        if num_links > 0:
            print(f"Average time per item: {gather_duration / num_links:.2f} seconds.")
        print("=" * 30)

        filename = f"twitcasting_results_search.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        for a in results:
            print(a.get("description", "") if a else "")
            continue
        print(f"Results saved to '{filename}'.")


if __name__ == "__main__":
    asyncio.run(main())
