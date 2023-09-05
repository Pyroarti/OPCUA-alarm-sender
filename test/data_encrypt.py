from cryptography.fernet import Fernet
from pathlib import Path
import json
import os
from create_logger import setup_logger

logger = setup_logger('data_encrypt')

class Data_encrypt():
    """
    Class for handling encryption and decryption of sensitive data.

    This class provides methods to handle encryption and decryption of
    sensitive data files using Fernet encryption. The encryption key is
    retrieved from the operating system's environment variables.

    """

    def __init__(self):
        self.OUTPUT_PATH = Path(__file__).parent.parent

    def create_key(self):
        key = Fernet.generate_key()
        os.environ["NAME"] = key

    def encrypt_credentials(self, config_filename, env_key_name):
        """
        Encrypts and decrypts configuration files.

        This function checks if the given configuration file is encrypted. If not,
        it encrypts it using the key retrieved from the environment variables.
        Then, it decrypts the file and returns its content as a dictionary.

        Parameters
        ----------
        config_filename : str
            The name of the configuration file to be encrypted/decrypted.
        env_key_name : str
            The name of the environment variable where the encryption key is stored.

        Returns
        -------
        dict
            The decrypted contents of the configuration file.
        """

        config_path = self.OUTPUT_PATH / "configs" / config_filename
        key = os.environ.get(env_key_name)
        if key is None:
            logger.error(f"{env_key_name} is not set in the environment")
            return None
        key = key.encode()
        if not self.is_encrypted(config_path):
            self.encrypt_file(config_path, key)
        decrypted_data = self.decrypt_file(config_path, key)
        config = json.loads(decrypted_data)
        return config


    @staticmethod
    def encrypt_file(file_path, key):
        with open(file_path, 'rb') as f:
            data = f.read()

        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data)

        with open(file_path, 'wb') as f:
            f.write(encrypted_data)


    @staticmethod
    def decrypt_file(file_path, key):
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()

        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)

        return decrypted_data


    def is_encrypted(self, file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
        try:
            json.loads(data)
            return False
        except json.JSONDecodeError:
            return True