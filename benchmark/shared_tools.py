import random
import logging
import time
import os
from string import ascii_lowercase

import plotly.io as pio


def export_plot(plot: dict, wight: int = 600, height: int = 400, path: str = './results/reports/',
                file_format: str = '.svg'):
    """ Export plot in another format. Support vector and raster - svg, pdf, png, jpg, webp.

    Args:
        plot (Plotly dictionary): Layout of plot with data
        wight (int, optional): Wight of output image. Defaults to 600.
        height (int, optional): Height of output image. Defaults to 400.
        path (str, optional): Path to export the file. Defaults to './results/reports/'.
        file_format (str, optional): Export file format. Defaults to '.svg'.
    """
    name = ''.join(random.choice(ascii_lowercase) for _ in range(10)) + file_format
    pio.write_image(plot, path + name, width=wight, height=height)


def get_resource_as_string(name: str, charset: str = 'utf-8'):
    with open(name, "r", encoding=charset) as f:
        return f.read()


def chown_files_in_dir(directory):
    for root, dirs, files in os.walk(directory):
        for f in files:
            os.chown(os.path.abspath(os.path.join(root, f)),
                     int(os.environ.get('host_uid', os.getuid())),
                     int(os.environ.get('host_gid', os.getgid())))
        break  # do not traverse recursively


def check_file_appearance_rate(folder: str = 'results/serialized/', interval_length: int = 60 * 60):
    """
    Logs out the rate of file appearance within a given folder. Could be useful when running benchmark to see how many
        Experiments were performed hourly / daily since startup. Does not traverses recursively.

    :param folder: (str). Folder with files of interest.
    :param interval_length: (int). Time interval within number of files are aggregating.
    :return: None
    """
    previous_logging_level = logging.getLogger().level
    logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger(__name__)
    files = os.listdir(folder)
    files_and_date = dict((file, os.path.getmtime(folder + file)) for file in files)

    files.sort(key=lambda filename: files_and_date[filename])
    first_file_creation_time = files_and_date[files[0]]
    curtime = time.time()

    for time_interval in range(int(first_file_creation_time), int(curtime), interval_length):
        counter = 0
        while files and files_and_date[files[0]] < time_interval + interval_length:
            counter += 1
            files.pop(0)
        logger.info(" " + time.ctime(time_interval) + " |->| " + time.ctime(
            time_interval + interval_length) + ': Runned %s experiments.' % counter)

    logging.basicConfig(level=previous_logging_level)


if __name__ == "__main__":
    check_file_appearance_rate()
