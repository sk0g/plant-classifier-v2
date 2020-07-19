#!/user/bin/env python3

import json
import re
import sys
from time import sleep
from typing import *

import requests
from tqdm import tqdm


def short_sleep(duration: float):
    sleep(duration)


def dump_images_and_faults(image_links: Dict[str, set], faults: List[Tuple[str, str]]):
    print(f"Recording {len(image_links.keys())} classes links", end=" ")
    with open('links.json', 'w') as f:
        json.dump(image_links, f)
    print("done")

    print("Recording faults", end=" ")
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

    # Dict['genus species', url_set]]
    image_links: Dict[str, set] = {}
    rejected: List[Tuple[str, str]] = [("", "")]

    # Traverse each genus index, and extract image page URLs
    for url in tqdm(genus_links):
        current_genus = url.split("/")[-1]  # last element is species name
        print(f"Recording image links for genus => {current_genus} ... ", end="")

        short_sleep(0.05)  # Please don't ban me

        current_genus_index = requests.get(url).text.splitlines()
        href_lines = [href for href in current_genus_index
                      if 'href="' in href
                      and "/dig/" in href
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
        image_urls = set()
        for line in href_lines:
            image_location = re.search('/[^"]*', line)[0]
            # matched substring already includes leading forward slash, &size=3 returns the page for the bigger image
            image_urls.add(f"https://anbg.gov.au{image_location}&size=3")

        # Build the species: image_links dict
        if len(image_urls) > 1:  # Skip when one or fewer images are found
            for link in image_urls:
                page = requests.get(link).text

                # Regex magic ¯\_(ツ)_/¯
                # Extract image href
                image_href = re.search("/images/photo_cd/.*?jpg*", page)
                # Extract value between h2 tag, which describes the class
                class_tag = re.search("(?!(<h2>))[^>]*(?=(</h2>))", page)

                if image_href is None or class_tag is None:
                    print(f"Errored out: {image_href} {class_tag} on page \n {page}")
                else:
                    class_tag_text = class_tag[0]
                    # Skip image if:
                    #   species is not defined,
                    #   multiple classes are present
                    #   plant is a cross species (formatted as specie1 x specie2)
                    if len(class_tag_text.split(" ")) <= 1 or \
                            "," in class_tag_text or \
                            " x " in class_tag_text:
                        continue

                    # remove subspecies/ variety information, and metadata within brackets
                    class_tag_text = re. \
                        sub(r"( sub| f\.| var| \().*", "", class_tag_text). \
                        replace(" sp.", ""). \
                        strip()
                    current_image_url = root + image_href[0]

                    if len(class_tag_text.split(" ")) <= 1:
                        rejected.append((class_tag_text, current_image_url))
                    elif len(image_links) > 1:  # Can't train and validate/ test off just one image
                        if class_tag_text not in image_links.keys():
                            image_links[class_tag_text] = set()
                        image_links[class_tag_text].add(current_image_url)

        if len(image_links.keys()) % 6 == 0 and len(image_links.keys()) > 0:
            dump_images_and_faults(image_links, rejected)

    dump_images_and_faults(image_links, rejected)
    # TODO: finish


# TODO: download images


if __name__ == '__main__':
    if len(sys.argv) < 2:  # URL not provided
        print("Please provide destination URL to scrape images from")
    else:
        scrape_url(sys.argv[1])
