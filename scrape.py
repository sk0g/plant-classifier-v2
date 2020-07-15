#!/user/bin/env python3

import sys
from typing import *
from time import sleep
import requests
import re


def short_sleep():
    sleep(1)


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

            # Typical line:
            #       <li><a href=/photo/apii/genus/Ziziphus>Ziziphus</a></li>
            # What we're after out of that:
            #       /photo/apii/genus/Ziziphus
            url_suffix = re.search('/[^>]*', line)
            genus_links.add(root + url_suffix[0])

    for url in genus_links:
        short_sleep()  # Please don't ban me
        image_urls = set()

        current_genus_index = requests.get(url).text.splitlines()
        href_lines = [l for l in current_genus_index if 'href="' in l]

        for line in href_lines:
            image_urls.add(
                root + re.search('/[^"]*', line)[0])

        for (i, j) in zip(href_lines, image_urls):
            print(f"\n-------\n {i} \n {j} \n -------\n")
            # TODO: download images, figure out species names

if __name__ == '__main__':
    if len(sys.argv) < 2:  # URL not provided
        print("Please provide destination URL to scrape images from")
    else:
        scrape_url(sys.argv[1])
