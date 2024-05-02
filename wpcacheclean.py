#   v1.4.3

import os
import shutil
import requests  # apt install python3-requests
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


def tmp_write():
    with open(temp_file, "w") as temp:
        temp.write(str(cache_size_gb))


#
#
#   VARIABLES   #
cache_dir = os.path.normpath('/exports/ramdisk/us.edu.pl')  # cache location
temp_file = os.path.normpath("/tmp/wpcc.tmp")
critical_cache_size = 9.0  # critical cache size which will force full cache removal
top_cache_size = 90  # percentage of critical_cache_size which will trigger soft cleaning attempts
#
#
#

cache_size_gb = get_directory_size(cache_dir)
now = datetime.now()
last_cache_size = 0
prompt = ""
cron_prompt = ""

if os.path.exists(temp_file):
    try:
        with open(temp_file, "r") as tmp:
            last_cache_size = float(tmp.read())
    except ValueError:
        pass
else:
    tmp_write()

total = 0
forced = 0
orphaned = 0

try:
    soft_limit = critical_cache_size * top_cache_size / 100

    if cache_size_gb >= soft_limit:
        # this will trigger mostly due to unwanted traffic on website (bots, crawlers, harvesters etc.)
        prompt = "CACHE CRITICAL: {:.3f}, DROPPING CACHE...".format(cache_size_gb)
        shutil.rmtree(cache_dir, True)
        prompt += "\tdelta: {:.3f}".format(get_directory_size(cache_dir) - cache_size_gb)
    elif cache_size_gb > soft_limit:
        prompt = "Cache size reached peak: {:.3f}, attempting cleaning... ".format(cache_size_gb)
        for content in os.listdir(cache_dir):
            # if cache was modified more than 3 days ago, it will be deleted
            if now - datetime.fromtimestamp(os.path.getmtime(os.path.join(cache_dir, content))) > timedelta(days=3):
                shutil.rmtree(os.path.join(cache_dir, content))
                total += 1
                orphaned += 1
                continue
            # else if cache was created 7 days ago, but modified less than 3 days ago, it will be deleted
            elif now - datetime.fromtimestamp(os.path.getctime(os.path.join(cache_dir, content))) > timedelta(days=5):
                shutil.rmtree(os.path.join(cache_dir, content))
                total += 1
                forced += 1

        if cache_size_gb - get_directory_size(cache_dir) >= 0.001:
            prompt += "R: {}, F: {}, O: {}, delta: {:.3f} GB".format(total, forced, orphaned,
                                                                     cache_size_gb - get_directory_size(cache_dir))
        else:
            prompt += "but there was nothing to clean."

    else:
        prompt = "Cache size below {:.3f} GB threshold, nothing to do.".format(soft_limit)

    tmp_write()


except Exception as err:
    prompt = "Cache cleaning ERROR: {}".format(err)

try:
    response = requests.get("https://us.edu.pl/wp-cron.php?doing_wp_cron")
    if response.status_code == 200:
        cron_prompt = "WP-Cron OK"
    else:
        cron_prompt = "WP-Cron ERROR: {}".format(response.status_code)

except Exception as err:
    print("ERROR sending GET request to trigger WordPress cronjob: {}".format(err))
finally:
    msg = "{} - curr: {:.3f}; delta:\t{:.3f}\t|{}\t| {}".format(now.strftime("%Y-%m-%d %H:%M:%S"), cache_size_gb,
                                                                cache_size_gb - last_cache_size, prompt, cron_prompt)
    print(msg)
