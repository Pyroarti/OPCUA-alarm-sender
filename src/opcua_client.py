import json
from asyncua import Client, ua, Node
import asyncua.ua.uaerrors._auto as uaerrors
import asyncua.common

from create_logger import setup_logger
from data_encrypt import Data_encrypt


logger = setup_logger('opcua_client')

async def connect_opcua(url, encrypted_username, encrypted_password):

    """
    Connect to an OPC UA server.

    :param url: Server URL
    :param encrypted_username: Encrypted username
    :param encrypted_password: Encrypted password
    :return: Client object if connected, None otherwise
    """

    client = Client(url=url, timeout=4)

    try:
        logger.info(f"Connecting to OPC UA server at {url}")
        #await client.connect_sessionless()
        #await client.create_session()
        client.set_user(username=encrypted_username)
        client.set_password(pwd=encrypted_password)
        #await client.activate_session(username=encrypted_username, password=encrypted_password)
        await client.connect()
        logger.info("Successfully connected to OPC UA server.")

    except ua.uaerrors.BadUserAccessDenied as exeption:
        logger.error(f"BadUserAccessDenied: {exeption}")
        return None

    except ua.uaerrors.BadSessionNotActivated as exeption:
        logger.error(f"Session activation error: {exeption}")
        return None

    except ua.uaerrors.BadIdentityTokenRejected as exeption:
        logger.error(f"Identity token rejected. Check username and password.: {exeption}")
        return None

    except ua.uaerrors.BadIdentityTokenInvalid as exeption:
        logger.error(f"Bad Identity token invalid. Check username and password.: {exeption}")
        return None

    except ConnectionError as exeption:
        logger.error(f"Connection error: Please check the server url. Or other connection properties: {exeption}")
        return None

    except ua.UaError as exeption:
        logger.error(f"General OPCUA error {exeption}")
        return None

    except Exception as exeption:
        logger.error(f"Error in connection: {exeption} Type: {type(exeption)}")
        return None

    return client