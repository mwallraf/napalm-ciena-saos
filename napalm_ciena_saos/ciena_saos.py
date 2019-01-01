# -*- coding: utf-8 -*-
# Copyright 2016 Dravetech AB. All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""
Napalm driver for Skeleton.

Read https://napalm.readthedocs.io for more information.
"""

from napalm.base import NetworkDriver
from napalm.base.exceptions import (
    ConnectionException,
    SessionLockedException,
    MergeConfigException,
    ReplaceConfigException,
    CommandErrorException,
)
from napalm.base.utils import py23_compat
from napalm.base.netmiko_helpers import netmiko_args


class CienaSAOSDriver(NetworkDriver):
    """Napalm driver for Ciena SAOS."""

    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        """Constructor."""
        self.device = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout

        if optional_args is None:
            optional_args = {}

        self.netmiko_optional_args = netmiko_args(optional_args)
        self.netmiko_optional_args.setdefault('port', 22)

        self.profile = [ "ciena_saos_ssh" ]

    def open(self):
        """Implement the NAPALM method open (mandatory)"""
        device_type = 'ciena_saos'
        self.device = self._netmiko_open(device_type, netmiko_optional_args=self.netmiko_optional_args)


    def close(self):
        """Implement the NAPALM method close (mandatory)"""
        self._netmiko_close()


    def _send_command(self, command):
        """Wrapper for self.device.send.command().
        If command is a list will iterate through commands until valid command.
        """
        try:
            if isinstance(command, list):
                for cmd in command:
                    output = self.device.send_command(cmd)
                    if "Incorrect usage" not in output:
                        break
            else:
                output = self.device.send_command(command)
            return self._send_command_postprocess(output)
        except (socket.error, EOFError) as e:
            raise ConnectionClosedException(str(e))


    @staticmethod
    def _send_command_postprocess(output):
        return output.strip()


    def is_alive(self):
        """Returns a flag with the state of the connection."""
        null = chr(0)
        if self.device is None:
            return {'is_alive': False}
        # SSH
        try:
            # Try sending ASCII null byte to maintain the connection alive
            self.device.write_channel(null)
            return {'is_alive': self.device.remote_conn.transport.is_active()}
        except (socket.error, EOFError):
            # If unable to send, we can tell for sure that the connection is unusable
            return {'is_alive': False}
        return {'is_alive': False}


    def cli(self, commands):
        """
        Execute a list of commands and return the output in a dictionary format using the command
        as the key.
        Example input:
        ['show clock', 'show calendar']
        Output example:
        {   'show calendar': u'22:02:01 UTC Thu Feb 18 2016',
            'show clock': u'*22:01:51.165 UTC Thu Feb 18 2016'}
        """
        cli_output = dict()
        if type(commands) is not list:
            raise TypeError('Please enter a valid list of commands!')

        for command in commands:
            output = self._send_command(command)
            if 'Incorrect usage' in output:
                raise ValueError('Unable to execute command "{}"'.format(command))
            cli_output.setdefault(command, {})
            cli_output[command] = output

        return cli_output


    def save_config(self):
        """
        Saves the config of the WLC, uses the paramiko save_config() function
        """
        output = self.device.save_config()        
        return output


    def get_config(self, retrieve='all'):
        """Implementation of get_config for Cisco WLC.
        Returns the running configuration as dictionary.
        The keys of the dictionary represent the type of configuration
        (startup or running). The candidate is always empty string,
        since IOS does not support candidate configuration.
        """

        configs = {
            'startup': '',
            'running': '',
            'candidate': '',
        }

        if retrieve in ('running', 'all'):
            command = [ 'show running-config' ]
            output = self._send_command(command)
            configs['running'] = output

        return configs


    @staticmethod
    def parse_uptime(uptime_str):
        """
        Extract the uptime string from the given OneAccess.
        Return the uptime in seconds as an integer
        """
        # Initialize to zero
        (days, hours, minutes, seconds) = (0, 0, 0, 0)

        pass


    def get_facts(self):
        """Return a set of facts from the device."""
        pass


if __name__ == '__main__':
    import json
    o = CienaSAOSDriver("host", "user", "pass")
    print(json.dumps(o.get_facts()))



