# -*- coding: utf-8 -*-
"""Brewtils Logging Utilities

This module streamlines loading logging configuration from Beergarden.

Example:
    To use this just call ``configure_logging`` sometime before you initialize
    your Plugin object:

    .. code-block:: python

        from brewtils import configure_logging, get_connection_info, Plugin

        # Load BG connection info from environment and command line args
        connection_info = get_connection_info(sys.argv[1:])

        configure_logging(system_name='systemX', **connection_info)

        plugin = Plugin(
            my_client,
            name='systemX,
            version='0.0.1',
            **connection_info
        )
        plugin.run()
"""

import copy
import json
import logging.config
import os
import string
import warnings

import brewtils

# Loggers to always use. These are things that generally,
# people do not want to see and/or are too verbose.

DEFAULT_LOGGERS = {
    "pika": {"level": "ERROR"},
    "requests.packages.urllib3.connectionpool": {"level": "WARN"},
    "yapconf": {"level": "WARN"},
}

# A simple default format/formatter. Generally speaking, the API should return
# formatters, but since users can configure their logging it's better if the
# formatter has a logical backup.
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_FORMATTERS = {"default": {"format": DEFAULT_FORMAT}}


SUPPORTED_HANDLERS = ("stdout", "file", "logstash")

# A simple default handler. Generally speaking, the API should return
# handlers, but since users can configure their logging it's better if the
# handler has a logical backup.
DEFAULT_HANDLERS = {
    "default": {
        "class": "logging.StreamHandler",
        "formatter": "default",
        "stream": "ext://sys.stdout",
    }
}

# The template that plugins will use to log
DEFAULT_PLUGIN_LOGGING_TEMPLATE = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {},
    "handlers": {},
    "loggers": DEFAULT_LOGGERS,
}


def default_config(level="INFO"):
    """Will be used if no logging configuration was specified"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": DEFAULT_FORMATTERS,
        "handlers": DEFAULT_HANDLERS,
        "loggers": DEFAULT_LOGGERS,
        "root": {"level": level, "handlers": ["default"]},
    }


def configure_logging(
    raw_config,
    namespace=None,
    system_name=None,
    system_version=None,
    instance_name=None,
):
    """Load and enable a logging configuration from Beergarden

    WARNING: This method will modify the current logging configuration.

    The configuration will be template substituted using the keyword arguments passed
    to this function. For example, a handler like this:

    .. code-block:: yaml

        handlers:
            file:
                backupCount: 5
                class: "logging.handlers.RotatingFileHandler"
                encoding: utf8
                formatter: default
                level: INFO
                maxBytes: 10485760
                filename: "$system_name.log"

    Will result in logging to a file with the same name as the given system_name.

    This will also ensure that directories exist for any file-based handlers. Default
    behavior for the Python logging module is to not create directories that do not
    already exist, which would dramatically lower the utility of templating.

    Args:
        raw_config: Configuration to apply
        namespace: Used for configuration templating
        system_name: Used for configuration templating
        system_version: Used for configuration templating
        instance_name: Used for configuration templating

    Returns:
        None
    """
    templated = string.Template(json.dumps(raw_config)).safe_substitute(
        namespace=namespace,
        system_name=system_name,
        system_version=system_version,
        instance_name=instance_name,
    )
    logging_config = json.loads(templated)

    # Now make sure that directories for all file handlers exist
    for handler in logging_config["handlers"].values():
        if "filename" in handler:
            dir_name = os.path.dirname(os.path.abspath(handler["filename"]))
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

    logging.config.dictConfig(logging_config)


def get_logging_config(system_name=None, **kwargs):
    """Retrieve a logging configuration from Beergarden

    Args:
        system_name: Name of the system to load
        **kwargs: Beergarden connection parameters

    Returns:
        dict: The logging configuration for the specified system
    """
    config = brewtils.get_easy_client(**kwargs).get_logging_config(system_name)

    return convert_logging_config(config)


def convert_logging_config(logging_config):
    """Transform a LoggingConfig object into a Python logging configuration

    Args:
        logging_config: Beergarden logging config

    Returns:
        dict: The logging configuration
    """
    config_to_return = copy.deepcopy(DEFAULT_PLUGIN_LOGGING_TEMPLATE)

    if logging_config.handlers:
        handlers = logging_config.handlers
    else:
        handlers = copy.deepcopy(DEFAULT_HANDLERS)
    config_to_return["handlers"] = handlers

    if logging_config.formatters:
        formatters = logging_config.formatters
    else:
        formatters = copy.deepcopy(DEFAULT_FORMATTERS)
    config_to_return["formatters"] = formatters

    config_to_return["root"] = {
        "level": logging_config.level,
        "handlers": list(config_to_return["handlers"]),
    }

    return config_to_return


def setup_logger(
    bg_host, bg_port, system_name, ca_cert=None, client_cert=None, ssl_enabled=None
):
    """DEPRECATED: Set Python logging to use configuration from Beergarden API

    This method is deprecated - consider using :func:`configure_logging`

    This method will overwrite the current logging configuration.

    Args:
        bg_host (str): Beergarden host
        bg_port (int): Beergarden port
        system_name (str): Name of the system
        ca_cert (str): Path to CA certificate file
        client_cert (str): Path to client certificate file
        ssl_enabled (bool): Use SSL when connection to Beergarden

    Returns: None
    """
    warnings.warn(
        "This function is deprecated and will be removed in version "
        "4.0, please consider using 'configure_logging' instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    config = get_python_logging_config(
        bg_host=bg_host,
        bg_port=bg_port,
        system_name=system_name,
        ca_cert=ca_cert,
        client_cert=client_cert,
        ssl_enabled=ssl_enabled,
    )
    logging.config.dictConfig(config)


def get_python_logging_config(
    bg_host, bg_port, system_name, ca_cert=None, client_cert=None, ssl_enabled=None
):
    """DEPRECATED: Get Beergarden's logging configuration

    This method is deprecated - consider using :func:`get_logging_config`

    Args:
        bg_host (str): Beergarden host
        bg_port (int): Beergarden port
        system_name (str): Name of the system
        ca_cert (str): Path to CA certificate file
        client_cert (str): Path to client certificate file
        ssl_enabled (bool): Use SSL when connection to Beergarden

    Returns:
        dict: The logging configuration for the specified system
    """
    warnings.warn(
        "This function is deprecated and will be removed in version "
        "4.0, please consider using 'get_logging_config' instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    client = brewtils.get_easy_client(
        host=bg_host,
        port=bg_port,
        ssl_enabled=ssl_enabled,
        ca_cert=ca_cert,
        client_cert=client_cert,
    )

    logging_config = client.get_logging_config(system_name=system_name)

    return convert_logging_config(logging_config)
