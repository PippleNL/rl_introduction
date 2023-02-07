"""
The application config is stored in a yaml file:
    * config_prod.yml for production
    * config_acc.yml for acceptation
    * config_test.yml for test
    * config_dev.yml for development
Make sure the environment variables CONFIG_FILENAME and LOGSTASH_HTTP_PWD are set.
The environment variable CONFIG_FILENAME should point to this file.
If CONFIG_FILENAME is not defined, the application falls back on config_dev.yaml
"""

import os

from pathlib import Path
from pyaml import yaml
from typing import Any

import logging.config

from version import get_version


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        project_root: the project root directory
    """
    project_root = Path(__file__).parents[2]

    return project_root


def read_config(path: Path) -> dict[str, Any]:
    """
    Read the config file.

    Args:
        path: the path of the config file

    Returns:
        config_file: the config file with environment specific configuration and general parameters

    Raises:
        ValueError: if config file is not found
    """
    # If config file does not exist raise ValueError
    if not os.path.exists(path):
        raise ValueError(f"No config file found: {path}")

    with open(path, 'rt') as f:
        config_file = yaml.safe_load(f.read())

    # Add general parameters if file exists
    project_root = get_project_root()
    params_path = Path.joinpath(project_root, 'config/parameters.yml')

    if os.path.exists(params_path):
        with open(params_path, 'rt') as f:
            params_file = yaml.safe_load(f.read())

        config_file.update(params_file)

    return config_file


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with the specified name and create the logger if needed

    Args:
        name: the name of the logger

    Returns:
        logger_instance: logger with specified name
    """
    logger_instance = logging.getLogger(name)

    return logger_instance


def shutdown_logging():
    """
    Shutdown logging of application on close.
    """
    logging.shutdown()


# Get the config filename that is used: config_dev.yml, config_test.yml, config_acc.yml or config_prod.yml
config_filename = os.getenv('CONFIG_FILENAME')
root = get_project_root()

# If no 'CONFIG_FILENAME' is set, then fall back on development config
if config_filename is None:
    print("CONFIG_FILENAME environment variable not defined. Falling back on development config.")
    config_filename = Path.joinpath(root, 'config/config_dev.yml')
else:
    config_filename = Path.joinpath(root, 'config', config_filename)

# Read the config file
config = read_config(config_filename)

# Check if logstash handler is enabled and if password is set when the logstash handler is enabled
if config['logging']['handlers']['logstash_handler']['enable'] and os.getenv('LOGSTASH_HTTP_PWD') is None:
    raise ValueError("LOGSTASH_HTTP_PWD environment variable is not defined")

# Check if logging is set in config file
if 'logging' not in config:
    raise ValueError("Missing logging configuration in {}".format(config_filename))

# Set the instance_id in the simple formatter
instance_id = os.getenv('INSTANCE_ID')
if 'simple' in config['logging']['formatters']:
    simple = config['logging']['formatters']['simple']
    if 'format' in simple:
        if instance_id is not None:
            simple['format'] = simple['format'].format(f' ({instance_id})')
        else:
            simple['format'] = simple['format'].format('')

# Set the application version for the logstash formatter
version = get_version()
if 'logstash_formatter' in config['logging']['formatters']:
    formatter_config = config['logging']['formatters']['logstash_formatter']
    if 'version' in formatter_config['extra']:
        formatter_config['extra']['version'] = formatter_config['extra']['version'].format(version)

# Set the instance_id for the logstash formatter
if 'logstash_formatter' in config['logging']['formatters']:
    formatter_config = config['logging']['formatters']['logstash_formatter']
    if 'instance_id' in formatter_config['extra']:
        if instance_id is not None:
            formatter_config['extra']['instance_id'] = formatter_config['extra']['instance_id'].format(instance_id)
        else:
            del formatter_config['extra']['instance_id']

# Create logs directory if it does not exist yet
if not os.path.exists(os.path.join(root, 'logs')):
    os.mkdir(os.path.join(os.getcwd(), 'logs'))

# Set up logging
logging.config.dictConfig(config['logging'])
logger = logging.getLogger(__name__)

logger.info(f"Config loaded from {config_filename}")
logger.info(f"Application version: {version}")
