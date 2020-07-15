#!/user/bin/env python3

import sys
from typing import *
from time import sleep
import requests
import re


def short_sleep():
    sleep(.2)


def scrape_url(url: str):
    """
    Scrapes ANBG's genus index page, and downloads the images to the dataset folder
        ../dataset/{genus}/{species}/{image_name}
    :param url: a link to ANBG's plant images index page
    :return: nothing!
    """

    root = "https://anbg.gov.au"
    index_page = requests.get(url)
    genus_links = set()

    # Get the links to each genera
    for line in index_page.text.splitlines():
        if "<li><a href=/photo/apii/genus/></a></li>" != line \
                and "<a href=" in line \
                and "</a></li>" in line \
                and "*>" not in line:

            # FROM:
            #       <li><a href=/photo/apii/genus/Ziziphus>Ziziphus</a></li>
            # TO:
            #       /photo/apii/genus/Ziziphus
            url_suffix = re.search('/[^>]*', line)
            genus_links.add(root + url_suffix[0])

    # Traverse each genus index, and extract image page URLs
    genus_image_pages: Dict[str, set] = {}
    for url in genus_links:
        current_genus = url.split("/")[-1]  # last element is species name
        short_sleep()  # Please don't ban me

        current_genus_index = requests.get(url).text.splitlines()
        href_lines = [l for l in current_genus_index if 'href="' in l and "/dig/" in l]

        # FROM
        #   <!-- Marianthus tenuis --><a href="/photo/apii/id/dig/45444">Marianthus tenuis</a>, close up, flowers<br/>
        # TO
        #   https://anbg.gov.au/cgi-bin/phtml?pc=dig&pn=45444&size=3
        image_urls = set()
        for line in href_lines:
            image_id = re. \
                search('/[^"]*', line)[0]. \
                split("/")[-1]
            image_urls.add(f"https://anbg.gov.au/cgi-bin/phtml?pc=dig&pn={image_id}&size=3")

        if len(image_urls) > 1:  # Skip when one or fewer images are found
            genus_image_pages[current_genus] = image_urls

    # TODO: download images

if __name__ == '__main__':
    if len(sys.argv) < 2:  # URL not provided
        print("Please provide destination URL to scrape images from")
    else:
        scrape_url(sys.argv[1])
