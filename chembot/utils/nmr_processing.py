import time
import pathlib

import numpy as np


def find_most_recent_folder(directory_path, max_repeats=4) -> pathlib.Path:
    directory = pathlib.Path(directory_path)

    for _ in range(max_repeats):
        # Get a list of all subdirectories in the specified directory
        subdirectories = [d for d in directory.iterdir() if d.is_dir()]

        # Sort the subdirectories by modification time (latest first)
        sorted_subdirectories = sorted(subdirectories, key=lambda d: d.stat().st_mtime, reverse=True)

        # Check if there are any subdirectories
        if sorted_subdirectories:
            most_recent_folder = sorted_subdirectories[0]

            # Check if the most recent folder was created within the last 3 seconds
            if time.time() - most_recent_folder.stat().st_mtime <= 3:
                return most_recent_folder
            else:
                pass
                # print(f"Most recent folder '{most_recent_folder}' is older than 3 seconds. Retrying...")
        else:
            pass
            # print("No subdirectories found. Retrying...")

        time.sleep(1)  # Wait for 1 second before retrying

    raise RuntimeError(f"Exceeded maximum repeats ({max_repeats}). No recent folder found.")


def nmr_check(folder_path: str) -> bool:
    """

    Parameters
    ----------
    folder_path:

    Returns
    -------
    True: good
    False: bad
    """
    # grab csv from folder
    folder = find_most_recent_folder(folder_path)

    file_path = folder / "spectrum_processed.csv"
    data = np.loadtxt(file_path, delimiter=',', skiprows=1)
    if np.max(data[:, 1]) > 10:
        return True

    return False
