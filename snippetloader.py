import os
import fnmatch
import sublime

snippet_triggers = []
snip_files = {}

def init_snipfiles():
    pkg = sublime.packages_path()+'/SMART_Snippets/'
    for root, dirnames, filenames in os.walk(pkg):
        for filename in fnmatch.filter(filenames, '*.smart_snippet'):
            fn = os.path.join(root, filename)
            f = open(fn, 'r')
            for line in f:
                if line.startswith('###trigger:'):
                    param, trig = line.strip().split(":",1)
                    snippet_triggers.append(trig)
                    snip_files[trig] = fn
                    break
            f.close()