"""
This file contains functions that retrieve the version of the application.
"""

import subprocess
import os

from pathlib import Path
from typing import List


def _call_git(cli_arguments: List[str]) -> str:
    """
    Get the commit of the current version.

    Args:
        cli_arguments: command line arguments for git

    Returns:
        commit: the commit of the current version

    Raises:
        FileNotFoundError: if git cannot be found
    """
    try:
        arguments = ['git']
        arguments.extend(cli_arguments)

        process = subprocess.Popen(arguments, stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        commit = stdout.decode('utf-8').split('\n')[0]

        return commit
    except FileNotFoundError as fe:
        print('Can not find Git. Install Git in your Conda environment by: conda install git')
        raise fe


def get_version() -> str:
    """
    Gets the version of the application. In case a version.txt is present, these contents are returned. Else, Git is
    used to obtain the version identifier.

    Returns:
        version: the version of the application
    """
    version_filepath = Path.joinpath(Path(__file__), 'version.txt')
    if os.path.exists(version_filepath):
        # Get version from version.txt
        with open(version_filepath, 'r') as f:
            version = f.read()
    else:
        # Get version from git
        version = _call_git(['describe', '--all', '--long'])

    return version
