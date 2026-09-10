import logging
import os
import time

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
        Experiments were performed hourly / daily since startup. Does not traverse recursively.

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
            time_interval + interval_length) + ': Run %s experiments.' % counter)

    logging.basicConfig(level=previous_logging_level)


def cleanup_benchmark_results(results_dir: str = './results/reports'):
    """
    Clean up all generated benchmark files including serialized experiments, CSVs, HTML reports, and ZIP files.

    This function removes:
    - All .pkl files in the serialized/ folder
    - All .csv files in the reports/ folder (benchmark results)
    - All .html files in the reports/ folder (reports)
    - All .zip files in the reports/ folder (table archives)

    Args:
        results_dir: Path to the results directory. Defaults to './results/reports'.

    Returns:
        None
    """
    logger = logging.getLogger(__name__)

    if not os.path.exists(results_dir):
        logger.warning(f"Results directory does not exist: {results_dir}")
        return

    cleaned_files = 0

    # Clean serialized folder (remove all .pkl files)
    serialized_dir = os.path.join(results_dir, 'serialized')
    if os.path.exists(serialized_dir):
        for file in os.listdir(serialized_dir):
            if file.endswith('.pkl'):
                file_path = os.path.join(serialized_dir, file)
                try:
                    os.remove(file_path)
                    cleaned_files += 1
                    logger.debug(f"Removed: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove {file_path}: {e}")

    # Clean reports folder (remove all .csv, .html, and .zip files)
    reports_dir = os.path.join(results_dir, 'reports')
    if os.path.exists(reports_dir):
        for file in os.listdir(reports_dir):
            file_path = os.path.join(reports_dir, file)
            if os.path.isfile(file_path):
                # Remove CSV, HTML, and ZIP files
                if file.endswith(('.csv', '.html', '.zip')):
                    try:
                        os.remove(file_path)
                        cleaned_files += 1
                        logger.debug(f"Removed: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")

    logger.info(f"Cleanup completed: {cleaned_files} file(s) removed from {results_dir}")


if __name__ == "__main__":
    check_file_appearance_rate()
