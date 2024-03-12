#   v1.

import os
import shutil
import requests     # apt install python3-requests
from datetime import datetime, timedelta


def get_directory_size(directory):
    """
    Function returning total size of public cache directory in gigabytes.
    :param directory: path-like object pointing to cache directory
    :return:
    """
    total_size = 0
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size / pow(1024, 3)


#   VARIABLES   #
cache_dir = os.path.normpath('/exports/ramdisk/us.edu.pl')   # cache location
max_cache_size = 8  # maximum cache capacity in GB
critical_cache_size = 9.2  # critical cache size which will force full cache removal
#               #

green = "\033[92m"
red = "\033[91m"
blue = "\033[94m"
yellow = "\033[93m"
reset = "\033[0m"

cache_size_gb = get_directory_size(cache_dir)
now = datetime.now()

total = 0
forced = 0
orphaned = 0

try:
    print(now.strftime("%Y-%m-%d %H:%M:%S"))
    print("Current cache size: ", cache_size_gb, "GB")

    if cache_size_gb >= critical_cache_size:
        # this will trigger mostly due to unwanted traffic on website (bots, crawlers, harvesters etc.)
        print("{}CACHE CRITICAL, DUMPING CACHE...{}".format(red, reset))
        shutil.rmtree(cache_dir)
    elif cache_size_gb > max_cache_size:
        print("{}Cache overload, cleaning...{}".format(yellow, reset))
        for content in os.listdir(cache_dir):
            # if cache was modified more than 3 days ago, it will be deleted
            if (now - datetime.fromtimestamp(os.path.getmtime(os.path.join(cache_dir, content)))) > timedelta(days=3):
                shutil.rmtree(os.path.join(cache_dir, content))
                total += 1
                orphaned += 1
            # else if cache was created 7 days ago, but modified less than 3 days ago, it will be deleted
            elif (now - datetime.fromtimestamp(os.path.getctime(os.path.join(cache_dir, content)))) > timedelta(days=7):
                shutil.rmtree(os.path.join(cache_dir, content))
                total += 1
                forced += 1

            print("\tTotal directories removed: ", total)
            print("\t\tForced: ", forced)
            print("\t\tOrphaned: ", orphaned)
    else:
        print("{}Cache size below {}GB threshold, no action taken.{}".format(green, max_cache_size, reset))


except Exception as err:
    print("{}Cache cleaning error: {}".format(red, reset), err)

try:
    response = requests.get("https://us.edu.pl/wp-cron.php?doing_wp_cron")
    if response.status_code == 200:
        print("{}WordPress cron job triggered successfully.{}\n\n".format(green, reset))
    else:
        print("{}Error triggering WordPress cron job: {}{}\n\n".format(red, reset, response.status_code))
except Exception as err:
    print("{}Error sending GET request to trigger WordPress cronjob: {}{}\n\n".format(red, reset, err))
