#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import re
import xmlrpc

DOCUMENTATION = r'''
---
module: hs_admin

short_description: This is a wrapper for Hostsharing eG Admin Interface 

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

from ansible.plugins.action import ActionBase
from hs.admin.api import API


class ActionModule(ActionBase):

    def _find_pac_name(self, task_vars):
        if 'pac' in task_vars:
            return task_vars['pac']
        pac_pattern = '[a-z]{3}\d{2}'
        for group in task_vars['group_names']:
            res = re.match(pac_pattern, str(group).lower())
            if res is not None:
                return str(group).lower()[:5]
        if 'inventory_hostname' in task_vars:
            pac = task_vars['inventory_hostname'][:5]  # take first 5 chars from inv-hostname
            if re.match(pac_pattern, pac) is not None:
                return pac

    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)

        pac = self._find_pac_name(task_vars)
        pac_pass = task_vars['pac_pass']

        api = API(cas=dict(
            uri='https://login.hostsharing.net/cas/v1/tickets',
            service='https://config.hostsharing.net:443/hsar/backend'),
            credentials=dict(username=str(pac), password=str(pac_pass)),
            backends=[
                'https://config.hostsharing.net:443/hsar/xmlrpc/hsadmin',
                'https://config2.hostsharing.net:443/hsar/xmlrpc/hsadmin'
            ]
        )

        module_args = self._task.args.copy()
        hs_module_name = module_args.pop('hs_module')
        # check if given module name exists in ansible
        if hs_module_name not in api.list_modules():
            return dict(failed=True, msg='Hs-Modul ' + hs_module_name + ' unknown')
        api_module = api.modules[hs_module_name]
        api_properties = api_module.properties
        # check if attributes are valid and do some casting
        hs_name = str(module_args.pop('hs_name'))
        if hs_name is None:
            return dict(failed=True, msg='Attribute hs_name is not set', hs_module=hs_module_name)
        if 'state' not in module_args:
            module_args['state'] = 'present'
        state = module_args.pop('state')

        # check if all ansible module params are accepted parameters by the api and cast them to string
        hs_properties = dict()
        for key, val in module_args.items():
            if key not in api_properties.keys():
                return dict(failed=True, msg=key + ' is not a vaild field', hs_module_name=hs_module_name)
            # cast ansible objects to string / the list items to string
            if type(val) is list:
                hs_properties[key] = [str(i) for i in val]
            else:
                hs_properties[key] = str(val)
        search_res = api_module.search(where={'name': hs_name})
        changed = False
        res = None

        # if item should be there but is not => add it
        if state == 'present' and len(search_res) == 0:
            changed = True
            hs_properties['name'] = hs_name
            try:
                res = api_module.add(set=hs_properties)
            except Exception as e:
                return dict(failed=True, msg=str(e), set=hs_properties)

        # if item should not be there, but it is => delete it
        elif state == 'absent' and len(search_res) > 0:
            changed = True
            try:
                res = api_module.delete(where={'name': hs_name})
            except Exception as e:
                return dict(failed=True, msg=str(e), set=hs_properties)

        # if item should be there, and it is there => check if update is needed
        elif state == 'present' and len(search_res) == 1:
            filtered = dict()
            for name, value in hs_properties.items():
                if name in search_res[0] and value != search_res[0][name]:
                    filtered[name] = value
            if len(filtered) > 0:
                changed = True
                try:
                    res = api_module.update(where={'name': hs_name}, set=filtered)
                except Exception as e:
                    return dict(failed=True, msg=str(e), set=set)

        return dict(
            changed=changed,
            search_res=search_res,
            res=res
        )
