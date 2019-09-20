# -*- coding: utf-8 -*-

"""

ZUGBRUECKE
Calling routines in Windows DLLs from Python scripts running on unixlike systems
https://github.com/pleiszenburg/zugbruecke

	src/zugbruecke/core/config.py: Handles the modules configuration

	Required to run on platform / side: [UNIX]

	Copyright (C) 2017-2019 Sebastian M. Ernst <ernst@pleiszenburg.de>

<LICENSE_BLOCK>
The contents of this file are subject to the GNU Lesser General Public License
Version 2.1 ("LGPL" or "License"). You may not use this file except in
compliance with the License. You may obtain a copy of the License at
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt
https://github.com/pleiszenburg/zugbruecke/blob/master/LICENSE

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for the
specific language governing rights and limitations under the License.
</LICENSE_BLOCK>

"""


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
import json

from .const import CONFIG_FLD, CONFIG_FN
from .errors import config_parser_error
from .lib import generate_session_id


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CONFIGURATION CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class config_class(dict):


	def __init__(self, **override_dict):

		# Call parent constructur, just in case
		super().__init__()

		# Create session id
		self['id'] = generate_session_id() # Generate unique session id

		# Get config from files as a prioritized list
		for config in self.__get_config_from_files__():
			self.update(config)

		# Add override parameters
		if len(override_dict) > 0:
			self.update(override_dict)


	def __getitem__(self, key):

		if key in self.keys():
			return super().__getitem__(key)

		if key == 'stdout':
			return True # Display messages from stdout
		elif key == 'stderr':
			return True # Display messages from stderr
		elif key == 'log_write':
			return False # Write log messages into file
		elif key == 'log_level':
			return 0 # Overall log level: No logs are generated by default
		elif key == 'arch':
			return 'win32' # Define Wine & Wine-Python architecture
		elif key == 'version':
			return '3.7.4' # Define Wine-Python version
		elif key == 'dir':
			return self.__get_default_config_directory__() # Default config directory
		elif key == 'timeout_start':
			return 30 # Timeout for waiting on Wine-Python start
		elif key == 'timeout_stop':
			return 30 # Timeout for waiting on Wine-Python stop
		elif key == 'winedebug':
			return '-all' # Wine debug output off
		elif key == 'wineprefix':
			return os.path.join(self['dir'], self['arch'] + '-wine')
		elif key == 'pythonprefix':
			return os.path.join(self['dir'], '%s-python%s' % (self['arch'], self['version']))
		elif key == '_issues_50_workaround':
			return False # Workaround for zugbruecke issue #50 (symlinks ...)
		else:
			raise KeyError('not a valid configuration key')


	def __get_default_config_directory__(self):

		return os.path.join(os.path.expanduser('~'), CONFIG_FLD)


	def __get_config_from_files__(self):

		# Look for config in the usual spots
		for fn in [
			'/etc/zugbruecke',
			os.path.join('/etc/zugbruecke', CONFIG_FN),
			os.path.join(self.__get_default_config_directory__(), CONFIG_FN),
			os.environ.get('ZUGBRUECKE'),
			os.path.join(os.environ.get('ZUGBRUECKE'), CONFIG_FN) if os.environ.get('ZUGBRUECKE') is not None else None,
			os.path.join(os.getcwd(), CONFIG_FN),
			]:

			cnt_dict = self.__load_config_from_file__(fn)

			if cnt_dict is not None:
				yield cnt_dict


	def __load_config_from_file__(self, try_path):

		# If there is a path ...
		if try_path is None:
			return

		# Is this a file?
		if not os.path.isfile(try_path):
			return

		# Read file
		try:
			with open(try_path, 'r', encoding = 'utf-8') as f:
				cnt = f.read()
		except:
			raise config_parser_error('Config file could not be read: "%s"' % try_path)

		# Try to parse it
		try:
			cnt_dict = json.loads(cnt)
		except:
			raise config_parser_error('Config file could not be parsed: "%s"' % try_path)

		# Ensure that config has the right format
		if not isinstance(cnt_dict, dict):
			raise config_parser_error('Config file is malformed: "%s"' % try_path)

		return cnt_dict
