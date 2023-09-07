import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_dir = os.path.join(parent_dir, "configs")
phone_book_file = os.path.join(config_dir, 'phone_book.json')
opcua_config_file = os.path.join(config_dir, 'opcua_config.json')
print(phone_book_file)
print(opcua_config_file)