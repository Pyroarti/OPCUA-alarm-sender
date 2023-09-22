from data_encrypt import DataEncrypt
import os
####################################
# Set to True to enable SMS sending or False to just log the messages
SEND_SMS = True


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_dir = os.path.join(parent_dir, "configs")
phone_book_file = os.path.join(config_dir, 'phone_book.json')
opcua_server_config_file = os.path.join(config_dir, 'opcua_server_config.json')

opcua_server_windows_env_key_name = "opcua_key"

####################################

data_encrypt = DataEncrypt()
opcua_config = data_encrypt.decrypt_file_to_edit(opcua_server_config_file, opcua_server_windows_env_key_name)
