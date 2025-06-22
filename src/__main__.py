from datetime import datetime
from senskrap.scrapers.twitcasting import TwitcastingScraper

tw = TwitcastingScraper(datetime.now())
tw.scrape()
