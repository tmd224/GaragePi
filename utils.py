import logging

LOG_LEVEL = logging.DEBUG
CONSOLE_LEVEL = logging.DEBUG


def init_logger(fullpath, console_level=CONSOLE_LEVEL, log_level=LOG_LEVEL):
    """
    Setup the logger object

    Args:
        fullpath (str): full path to the log file
    """
    logging.basicConfig(level=LOG_LEVEL,
                        format='%(asctime)s %(threadName)-10s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d-%y %H:%M:%S',
                        filename=fullpath,
                        filemode='w')

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(console_level)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    logging.debug("Creating log file")


def import_credentials(filepath):
    """
    reads a text file with the stored MQTT credentials and returns the username and password
    Text file format is:
    USERNAME=ThisIsAUserName
    PASSWORD=ThisIsAPassword

    All leading and trailing spaces will be stripped from the username/password

    Args:
        filepath (str): full file path to credential file

    Returns:
        username (str): MQTT username
        password (str): MQTT password
    """
    username = None
    password = None
    try:
        f = open(filepath, 'r')
        lines = f.readlines()
        for line in lines:
            # look for username, password and parse out the values.
            tmpLine = line.upper()
            if "USERNAME" in tmpLine:
                # this line contains the username, so parse it out.
                username = line.split('=')[
                    1].strip()  # split the line by '=', take the second part and strip whitespace
            elif "PASSWORD" in tmpLine:
                password = line.split('=')[1].strip()

        return username, password

    except Exception as e:
        logger.error("Error importing credentials file: %s" % e)
    finally:
        if f:
            f.close()