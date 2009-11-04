import os

__pretty_app_name__ = "Gonvert"
__app_name__ = "gonvert"
__version__ = "0.2.24"
__build__ = 3
__app_magic__ = 0xdeadbeef
_data_path_ = os.path.join(os.path.expanduser("~"), ".gonvert")
_user_settings_ = "%s/settings.ini" % _data_path_
