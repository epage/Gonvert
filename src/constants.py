import os

__pretty_app_name__ = "Gonvert"
__app_name__ = "gonvert"
__version__ = "0.9.2"
__build__ = 2
__app_magic__ = 0xdeadbeef
_data_path_ = os.path.join(os.path.expanduser("~"), ".gonvert")
_user_settings_ = "%s/settings.ini" % _data_path_
_user_logpath_ = "%s/gonvert.log" % _data_path_

PROFILE_STARTUP = False
FORCE_HILDON_LIKE = False
