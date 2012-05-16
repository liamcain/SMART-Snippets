'''
SMART Snippets
Licensed under MIT
Copyright (c) 2012 William Cain
'''

import os
import fnmatch
import sublime
import sublime_plugin

# snippet_triggers = []
snip_files = {}

def update_statusbar(view):
    num_tabstops = len(view.get_regions('smart_tabstops'))
    if num_tabstops > 0:
        view.set_status('smart_tabstops',str(num_tabstops)+' Remaining Tabstops')
    else:
        view.erase_status('smart_tabstops')

def init_snipfiles():
    pkg = sublime.packages_path()+'/SMART_Snippets/'
    for root, dirnames, filenames in os.walk(pkg):
        if '.git' in dirnames:
              dirnames.remove('.git')
        for filename in fnmatch.filter(filenames, '*.smart_snippet'):
            fn = os.path.join(root, filename)
            is_regex = 'n'  # n is no
            requires_tab = 'y' # y is yes
            f = open(fn, 'r')
            for line in f:
                if line.startswith('###params:'):
                    if 'auto_expand' in line:
                        requires_tab = 'n'  # n is no
                    if 'regex' in line:
                        is_regex = 'y'  # y is yes
                elif line.startswith('###trigger:'):
                    param, trig = line.split(":",1)
                    trigger = is_regex + requires_tab + trig.strip()
                    # snippet_triggers.append(trigger)
                    snip_files[trigger] = fn
                    break
            f.close()