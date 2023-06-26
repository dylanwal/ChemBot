import os
import subprocess
import sys


def launch_terminals(folder_path: str):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if sys.platform == "win32":
                    subprocess.Popen(["start", "cmd", "/K", "python", file_path], shell=True)
                elif sys.platform == "darwin":
                    subprocess.Popen(["osascript", "-e", 'tell application "Terminal" to do script "python3 '
                                      + file_path + '"'])
                elif sys.platform == "linux":
                    subprocess.Popen(["gnome-terminal", "--", "python3", file_path])
                else:
                    raise NotImplementedError("Unsupported platform: " + sys.platform)
