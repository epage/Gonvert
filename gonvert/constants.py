import os

__pretty_app_name__ = "Gonvert"
__app_name__ = "gonvert"
__version__ = "1.1.4"
__build__ = 2
__app_magic__ = 0xdeadbeef
_data_path_ = os.path.join(os.path.expanduser("~"), ".%s" % __app_name__)
_user_settings_ = "%s/settings.json" % _data_path_
_user_logpath_ = "%s/%s.log" % (_data_path_, __app_name__)

PROFILE_STARTUP = False
IS_MAEMO = True