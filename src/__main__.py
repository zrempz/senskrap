import asyncio
from senskrap.scrapers.twitcasting import TwitcastingPremier, PremierGenre


async def main():
    async with TwitcastingPremier() as scraper:
        data = await scraper.scrape(genre=PremierGenre.JAZZ_FUSION, max_pages=1)
        for d in data:
            print(d)


if __name__ == "__main__":
    asyncio.run(main())
