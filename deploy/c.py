#!/usr/bin/env python

import json
import shutil
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
import ansible.constants as C
from ansible.inventory.group import Group
from ansible.inventory.host import Host
import traceback
import sys
import os
from ansible.executor.playbook_executor import PlaybookExecutor
class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """
    def v2_runner_on_ok(self, result, **kwargs):
        """Print a json representation of the result

        This method could store the result in an instance attribute for retrieval later
        """
        host = result._host
        print(json.dumps({host.name: result._result}, indent=4))

# since API is constructed for CLI it expects certain options to always be set, named tuple 'fakes' the args parsing options object
'''
Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check', 'diff'])
options = Options(connection='smart', module_path=['/to/mymodules'], forks=10, become=None, become_method=None, become_user=None, check=False, diff=False)
'''



Options = namedtuple('Options',
                             ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection', 'module_path', 'forks',
                              'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                              'scp_extra_args', 'become', 'become_method', 'become_user', 'remote_user', 'verbosity',
                              'check','diff'])
options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh',
                          module_path=None, forks=100, private_key_file=None, ssh_common_args=None, ssh_extra_args=None,
                          sftp_extra_args=None, scp_extra_args=None, become=False, become_method=None, become_user=None,
                          remote_user=None, verbosity=None, check=False,diff=None)

# initialize needed objects
loader = DataLoader() # Takes care of finding and reading yaml, json and ini files
passwords = dict(vault_pass='secret')

# Instantiate our ResultCallback for handling results as they come in. Ansible expects this to be one of its main display outlets
results_callback = ResultCallback()

# create inventory, use path to host config file as source or hosts in a comma separated string

inventory = InventoryManager(loader=loader,)
inventory_data = inventory._inventory

inventory_data.add_group('a')
inventory_data.add_host('127.0.0.1',group='a')

inventory_data.groups['all'].add_child_group(inventory_data.groups['a'])
'''
all_groups = inventory_data.get_groups_dict()
all_groups['all'].append('a')
all_groups['all'].append('b')
'''
# variable manager takes care of merging all the different sources to give you a unifed view of variables available in each context
variable_manager = VariableManager(loader=loader, inventory=inventory)

# create datastructure that represents our play, including tasks, this is basically what our YAML loader does internally.
'''
play_source =  dict(
        name = "Ansible Play",
        hosts = 'all',
        gather_facts = 'no',
        tasks = [
            dict(action=dict(module='shell', args='ifconfig'), register='shell_out'),
            dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
         ]
    )

# Create play object, playbook objects use .load instead of init or new methods,
# this will also automatically create the task objects from the info provided in play_source
play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

# Run it - instantiate task queue manager, which takes care of forking and setting up all objects to iterate over host list and tasks
tqm = None
try:
    tqm = TaskQueueManager(
              inventory=inventory,
              variable_manager=variable_manager,
              loader=loader,
              options=options,
              passwords=passwords,
    #          stdout_callback=results_callback,  # Use our custom callback instead of the ``default`` callback plugin, which prints to stdout
          )
    result = tqm.run(play) # most interesting data for a play is actually sent to the callback's methods
finally:
    # we always need to cleanup child procs and the structres we use to communicate with them
    if tqm is not None:
        tqm.cleanup()

    # Remove ansible tmpdir
    shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)






'''

try:
    playbook_path = 'test.yml' # modify here, change playbook
    #self.variable_manager.extra_vars=extra_vars
    if not os.path.exists(playbook_path):
        sys.exit('[INFO] The playbook does not exist')

    passwords = {}
    executor = PlaybookExecutor(
        playbooks=[playbook_path],
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        options=options,
        passwords=passwords,
    )
    # executor._tqm._stdout_callback = self.results_callback
    # code = executor.run()
    # stats = executor._tqm._stats
    # hosts = sorted(stats)
    code = executor.run()
    stats = executor._tqm._stats
    hosts = sorted(stats.processed.keys())
    result = [{h: stats.summarize(h)} for h in hosts]
    results = {'code': code, 'result': result, 'playbook': playbook_path}

except Exception as e:
    msg = traceback.format_exc()
    sys.exit(msg)
