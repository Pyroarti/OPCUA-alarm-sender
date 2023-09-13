from asyncua import Client, ua

from create_logger import setup_logger


logger = setup_logger('opcua_client')

CLIENT_TIMEOUT = 4


async def connect_opcua(url: str, username: str, password: str):

    """
    Connect to an OPC UA server.

    :param url: Server URL
    :param username: username
    :param password: password
    :return: Client object if connected, None otherwise
    """

    client = Client(url=url, timeout=CLIENT_TIMEOUT)

    try:
        logger.info(f"Connecting to OPC UA server at {url}")

        client.set_user(username)
        client.set_password(password)

        await client.connect()

        logger.info("Successfully connected to OPC UA server.")

    except ua.uaerrors.BadUserAccessDenied as exception:
        logger.error(f"BadUserAccessDenied: {exception}")
        return None

    except ua.uaerrors.BadSessionNotActivated as exception:
        logger.error(f"Session activation error: {exception}")
        return None

    except ua.uaerrors.BadIdentityTokenRejected as exception:
        logger.error(f"Identity token rejected. Check username and password.: {exception}")
        return None

    except ua.uaerrors.BadIdentityTokenInvalid as exception:
        logger.error(f"Bad Identity token invalid. Check username and password.: {exception}")
        return None

    except ConnectionError as exception:
        logger.error(f"Connection error: Please check the server url. Or other connection properties: {exception}")
        return None

    except ua.UaError as exception:
        logger.error(f"General OPCUA error {exception}")
        return None

    except Exception as exception:
        logger.error(f"Error in connection: {exception} Type: {type(exception)}")
        return None

    return client