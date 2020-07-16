#!/user/bin/env python3

import re
import sys
from time import sleep
from typing import *

import requests


def short_sleep(duration: float):
    sleep(duration)


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
        short_sleep(0.2)  # Please don't ban me

        current_genus_index = requests.get(url).text.splitlines()
        href_lines = [l for l in current_genus_index
                      if 'href="' in l
                      and "/dig/" in l
                      and (  # search descriptors to weed out any sketches, microscopic images, or other misc. images
                              "fruit" in l or
                              "close up" in l or
                              "flowers" in l or
                              "whole plant" in l or
                              "leaves" in l or
                              "leaf" in l
                      )]

        # FROM
        #   <!-- Marianthus tenuis --><a href="/photo/apii/id/dig/45444">Marianthus tenuis</a>, close up, flowers<br/>
        # TO
        #   https://anbg.gov.au/photo/apii/id/dig/45444
        image_urls = set()
        for line in href_lines:
            image_location = re.search('/[^"]*', line)[0]
            image_urls.add(f"https://anbg.gov.au{image_location}")  # matched substring already includes leading /

        if len(image_urls) > 1:  # Skip when one or fewer images are found
            genus_image_pages[current_genus] = image_urls
            print(image_urls)

    # TODO: build map of per-species image links

    # TODO: download images


if __name__ == '__main__':
    if len(sys.argv) < 2:  # URL not provided
        print("Please provide destination URL to scrape images from")
    else:
        scrape_url(sys.argv[1])
