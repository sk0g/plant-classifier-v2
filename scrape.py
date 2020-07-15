#!/user/bin/env python3

import sys
from typing import *


def scrape_url(url: AnyStr):
    print(url)


if __name__ == '__main__':
    if len(sys.argv) < 2:  # URL not provided
        print("Please provide destination URL to scrape images from")
    else:
        scrape_url(sys.argv[1])
