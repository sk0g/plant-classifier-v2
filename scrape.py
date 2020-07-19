#!/user/bin/env python3

import csv
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from random import randint
from time import sleep
from typing import *

import requests
from tqdm import tqdm


def short_sleep(duration: float):
    sleep(duration)


def dump_images_and_faults(image_links: Dict[str, set], faults: List[Tuple[str, str]]):
    print(f"Recording {len(image_links.keys())} species' links", end="... ")
    with open('links.json', 'w') as f:
        # set is not JSON serialisable, and skip species if one or zero images are found
        json.dump({k: list(v) for (k, v) in image_links.items() if len(v) > 1}, f)
    print("done")

    print("Recording faults", end="... ")
    with open('faults.json', 'w') as f:
        json.dump(faults, f)
    print("done")


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

    image_links: Dict[str, set] = {}  # Dict[genus species, image pages]]
    rejected: List[Tuple[str, str]] = []

    # Traverse each genus index, and extract image page URLs
    for url in tqdm(genus_links):
        genus_index_page = requests.get(url).text.splitlines()
        href_lines = [href for href in genus_index_page
                      if 'href="' in href
                      and "/photo/apii" in href
                      and (  # search descriptors to weed out any sketches, microscopic images, or other misc. images
                              "fruit" in href or
                              "plant" in href or
                              "close up" in href or
                              "flowers" in href or
                              "leaves" in href or
                              "leaf" in href
                      )]

        # FROM
        #   <!-- Marianthus tenuis --><a href="/photo/apii/id/dig/45444">Marianthus tenuis</a>, close up, flowers<br/>
        # TO
        #   https://anbg.gov.au/photo/apii/id/dig/45444
        image_page_urls = set()
        for line in href_lines:
            image_location = re.search('/[^"]*', line)[0]
            # matched substring already includes leading forward slash, &size=3 returns the page for the bigger image
            image_page_urls.add(f"https://anbg.gov.au{image_location}&size=3")

        # Build the species: image_links dict
        def process_image_page(link: str):
            page = requests.get(link).text

            # Regex magic ¯\_(ツ)_/¯
            # Extract image href
            image_href = re.search("/images/photo_cd/.*?jpg*", page)
            # Extract value between h2 tag, which describes the class
            class_tag = re.search("(?!(<h2>))[^>]*(?=(</h2>))", page)

            if image_href is None or class_tag is None:
                rejected.append(Tuple["Unknown", page])
            elif "see Illustrator" in page:
                rejected.append(Tuple["Illustration", page])
            else:
                class_tag_text = class_tag[0]
                # Skip image if:
                #   species is not defined,
                #   multiple classes are present
                #   plant is a cross species (formatted as specie1 x specie2)
                if len(class_tag_text.split(" ")) <= 1 or \
                        "," in class_tag_text or \
                        " x " in class_tag_text:
                    return

                # remove subspecies/ variety information, and metadata within brackets
                class_tag_text = re. \
                    sub(r"( sub| f\.| var| \().*", "", class_tag_text). \
                    replace(" sp.", ""). \
                    strip()
                current_image_url = root + image_href[0]

                if len(class_tag_text.split(" ")) <= 1:
                    rejected.append((class_tag_text, current_image_url))
                else:
                    if class_tag_text not in image_links.keys():
                        image_links[class_tag_text] = set()
                    image_links[class_tag_text].add(current_image_url)

        with ThreadPoolExecutor(max_workers=32) as executor:
            executor.map(process_image_page, image_page_urls)

        if randint(0, 50) == 10:
            dump_images_and_faults(image_links, rejected)

    dump_images_and_faults(image_links, rejected)


def download_images():
    pass
    # TODO: download images


def generate_image_count_csv():
    with open("links.json", "r") as f:
        links: Dict[str, set] = json.load(f)
        species = sorted(links.keys())

    with open("data.csv", "w") as f:
        writer = csv.writer(f)

        for class_name in species:
            genus = class_name.split(" ")[0]
            specie = " ".join(class_name.split(" ")[1:])
            writer.writerow((genus, specie, len(links[class_name])))


if __name__ == '__main__':
    if len(sys.argv) < 2:  # URL not provided
        print("Please provide destination URL to scrape images from")
    elif sys.argv[1] == "csv":
        generate_image_count_csv()
    elif sys.argv[1] == "download":
        download_images()
    else:
        scrape_url(sys.argv[1])
