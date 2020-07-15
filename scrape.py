#!/user/bin/env python3

import sys
from typing import *
import requests
import re


def scrape_url(url: str):
    index_page = requests.get(url)
    genus_links = set()

    # Get the links to each genera
    for line in index_page.text.splitlines():
        if "<li><a href=/photo/apii/genus/></a></li>" != line \
                and "<a href=" in line \
                and "</a></li>" in line \
                and "*>" not in line:

            # Typical line:
            #       <li><a href=/photo/apii/genus/Ziziphus>Ziziphus</a></li>
            # What we're after out of that:
            #       /photo/apii/genus/Ziziphus
            url_suffix = re.search('/[^>]*', line)
            genus_links.add(f"https://anbg.gov.au{url_suffix[0]}")

    # TODO: scrape each genera for images under it


if __name__ == '__main__':
    if len(sys.argv) < 2:  # URL not provided
        print("Please provide destination URL to scrape images from")
    else:
        scrape_url(sys.argv[1])
