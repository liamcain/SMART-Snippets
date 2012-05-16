'''
SMART Snippets
Licensed under MIT
Copyright (c) 2012 William Cain
'''

import sublime
import sublime_plugin
import os.path
import re
import _snippetloader as SS

if not 'SS.snip_files' in vars():  # for testing only, to remove dups
    SS.init_snipfiles()
SETTINGS = "smartsnippets.sublime-settings"

class SmartSnippetListener(sublime_plugin.EventListener):

    del_regions = []
    busy = False
    s = 0

    def on_activated(self,view):
        if view.settings().get('is_widget'):
            return
        self.view = view
        self.s = view.size()
        r = RunSmartSnippetCommand
        self.auto_expand = sublime.load_settings(SETTINGS).get("smart_snippets_without_tab")

        dicts = [r.autocompletions,r.quickcompletions,
                 r.ts_order,r.code_blocks,r.code_minions]
        for l in dicts:
            if not l.get(view.id()):
                l[view.id()] = []

    def on_close(self, view):
        del RunSmartSnippetCommand.ts_order[view.id()]
        del RunSmartSnippetCommand.code_minions[view.id()]

    def has_tabstop(self, view):
        return bool(RunSmartSnippetCommand.ts_order.get(view.id()))

    def first(self, item):
        if isinstance(item, basestring):
            return item
        return item[0]

    def insert(self,view,index,string):
        edit = view.begin_edit()
        regions = view.get_regions('code_minions')
        region = regions.pop(index)
        view.replace(edit, region, string)
        view.end_edit(edit)
        view.add_regions('code_minions',regions,'smart_tabstops',sublime.PERSISTENT)

    def activate(self,view,name):
        r = RunSmartSnippetCommand
        for i,x in reversed(list(enumerate(r.code_minions[view.id()]))):
            if x[0] == name:
                exec x[1] in locals()
                r.code_minions[view.id()].pop(i)

    def replace(self, item):
        if item < 0: return
        view = self.view
        r = view.get_regions('quick_completions')
        word = r[self.i]
        text = self.first(RunSmartSnippetCommand.quickcompletions.get(view.id())[self.i][item])
        if '\t' in text:
            exec text.split('\t')[1]
        edit = view.begin_edit()
        view.replace(edit, word, text)
        r = view.get_regions('quick_completions')
        r[self.i] = sublime.Region(word.a,word.a+len(text))
        view.end_edit(edit)
        view.add_regions('quick_completions', r, 'smart.tabstops',sublime.PERSISTENT)
        view.sel().clear()
        view.sel().add(word.a+len(text))

    def match_scope(self, view, snip_file):
        scope = view.scope_name(view.sel()[0].a)
        has_no_scope = True
        f = open(snip_file, 'r')
        for line in f:
            if line.startswith('###scope'):
                has_no_scope = False
                param, snip_scope = line.split(":",1)
                if snip_scope.strip() in scope:
                    f.close()
                    return True
        f.close()
        return has_no_scope

    # Checks the SMART Snippet package for a snippet with the name of the preceding text
    def prev_word_is_trigger(self, view):
        if re.match('\w',view.substr(view.sel()[0].b)): return
        trigger = view.substr(view.word(view.sel()[0].a)).strip()
        for s in SS.snip_files.keys():
            if s.startswith('y'):
                if re.match(s[2:]+'$', trigger):
                    if self.match_scope(view, SS.snip_files.get(s)):
                        return s
            else:
                if s[2:] == trigger:
                    if self.match_scope(view, SS.snip_files.get(s)):
                        return s
        return None

    def inside_qc_region(self,view):
        sel = self.view.sel()[0]
        for c in view.get_regions('quick_completions'):
            if c.contains(sel):
                return True
        return False

    def get_selected_regions(self,view,sel,name):
        regions = []
        for i,r in enumerate(view.get_regions(name)):
            if sel.contains(r):
                regions.append(i)
        if len(regions) > 1: return regions
        return []

    # For checking if the cursor selection overlaps with a QP region
    def on_selection_modified(self, view):
        if self.busy or view.size() == 0: return
        r = RunSmartSnippetCommand
        sel = view.sel()[0]
        del self.del_regions[:]

        if sel.size() > 0:
            for name in r.region_names:
                self.del_regions.append(self.get_selected_regions(view,sel,name))

        regions = view.get_regions('quick_completions')
        for i,r in enumerate(regions[:]):
            if sel == r:
                self.i = i
                qp = RunSmartSnippetCommand.quickcompletions.get(view.id())[i]
                view.window().show_quick_panel(qp, self.replace)

        regions = view.get_regions('code_regions')
        for i,reg in reversed(list(enumerate(regions))):
            if reg.contains(sel):
                key_index = -1
                key = re.search('on\s\'([^\']+)\'',r.code_blocks[view.id()][i].replace('\n',r'\n'))
                if key:
                    if not view.substr(sel.a-1) == key.group(1).replace('\\n','\n'):
                        continue
                    key_index = r.code_blocks[view.id()][i].find('on ')
                regions.pop(i)
                self.busy = True
                exec (r.code_blocks[view.id()].pop(i)[:key_index]) in locals()
        self.busy = False
        view.add_regions('code_regions', regions, 'smart.tabstops',sublime.PERSISTENT)

    def manage_region(self,view,d,name,rule):
        did_something = False
        sel = view.sel()[0]
        regions = []
        if view.size() > 0:
            for i,r in enumerate(view.get_regions(name)):
                if eval(rule):
                    did_something = True
                    d[view.id()].pop(i)
                else: regions.append(r)
        view.add_regions(name, regions,'smart.tabstops',sublime.PERSISTENT)
        return did_something

    def on_modified(self, view):
        if view.is_loading(): return
        r = RunSmartSnippetCommand

        if self.del_regions and self.del_regions[0]:
            for x,y in zip(r.dict_names,self.del_regions):
                for reg in reversed(y):
                    x[view.id()].pop(reg)
        del self.del_regions[:]
 
        self.manage_region(view,r.quickcompletions,'quick_completions','r.empty() and sel == r')
        self.manage_region(view,r.autocompletions,'smart_completions','r.empty() and not \' \' in view.substr(sel.a-1) and not sel.a == 0')
        self.manage_region(view,r.ts_order,'smart_tabstops','r.intersects(sel)')
        SS.update_statusbar(view)

        if view.size() > self.s:
            if not view.settings().get('is_widget') and self.ready_for_completion(view):
                view.run_command('run_smart_snippet')
        self.s = view.size()

    def ready_for_completion(self,view):
        s = self.prev_word_is_trigger(view)
        if s:
            return s[1] == 'n' or self.auto_expand
        return False

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "smart_snippet_found":
            return bool(self.prev_word_is_trigger(view)) == operand
        if key == "has_smart_tabstop":
            return self.has_tabstop(view) == operand
        if key == "inside_qc_region":
            return self.inside_qc_region(view) == operand
        if key == "has_active_tabstop":
            return bool(RunSmartSnippetCommand.active_snips > 0) == operand

    # if cursor overlaps with AC region, get the available completions
    def on_query_completions(self, view, prefix, locations):
        sel = view.sel()[0]
        regions = view.get_regions('smart_completions')
        for i,r in enumerate(regions):
            if r.contains(sel):
                if r == sel:
                    edit = view.begin_edit()
                    view.erase(edit, r)
                    view.end_edit(edit)
                ac = RunSmartSnippetCommand.autocompletions.get(view.id())[i]
                return [(x,x) for x in ac]

        l = []
        for s in SS.snip_files.keys():
            if self.match_scope(view, SS.snip_files.get(s)):
                t = (s[2:]+'\tSMART Snippet',s[2:])
                l.append(t)
        return l

# If has_tabstop, this class allows for tabbing between tabstops.
# To avoid duplicate code between the eventlistener and textcommand, it gets its own class
class NextSmartTabstopCommand(sublime_plugin.TextCommand):
    def run(self,edit):
        view = self.view
        tabstops = self.view.get_regions('smart_tabstops')
        ts_order = RunSmartSnippetCommand.ts_order.get(view.id())
        next = tabstops.pop(ts_order.index(min(ts_order)))  # pops the next lowest value
        RunSmartSnippetCommand.ts_order[view.id()].remove(min(ts_order))
        view.add_regions('smart_tabstops', tabstops, 'smart.tabstops',sublime.PERSISTENT)
        view.sel().clear()
        view.sel().add(next)
        SS.update_statusbar(view)

class EscapeTabstop(sublime_plugin.TextCommand):
    def run(self,edit):
        view = self.view
        r = RunSmartSnippetCommand
        r.active_snips -= 1
        l = []
        regs = []
        old_regs = view.get_regions('smart_tabstops')
        for i,x in enumerate(r.ts_order.get(view.id())):
            if x > r.active_snips*-100:
                l.append(x)
                regs.append(old_regs[i])
        r.ts_order[view.id()] = l
        view.add_regions('smart_tabstops',regs,'smart.tabstops',sublime.PERSISTENT)
        SS.update_statusbar(view)

class ExpandSelectionToQcRegionCommand(sublime_plugin.TextCommand):
    def run(self,edit):
        sel = self.view.sel()[0]
        for c in self.view.get_regions('quick_completions'):
            if c.contains(sel):
                self.view.sel().clear()
                self.view.sel().add(c)

class RunSmartSnippetCommand(sublime_plugin.TextCommand):
    # global dictionaries to give access the autocompletions and quickcompletions
    # key = view id
    autocompletions  = {}
    quickcompletions = {}
    code_blocks      = {}
    ts_order         = {}
    code_minions     = {}
    minion_regions   = []
    temp_tabstops    = []
    ac_regions       = []
    qc_regions       = []
    code_regions     = []
    active_snips     = 0
    inner_reg_count  = [-1,-1,-1,-1,-1]
    region_names = ['smart_tabstops','smart_completions',
                        'quick_completions','code_regions',
                        'code_minions']
    dict_names = [ts_order,autocompletions,
                        quickcompletions,code_blocks,
                        code_minions]

    # This is a working list of substitutions for embedded code.
    # It will serve as shorthand for people who want quick access to common python functions and commands
    reps = [
            ('(when.+)insert\('         , '\\1self.insert(view,i,'),
            ('(?<!\.)insert\('           , 'self.insert(edit,'),
            ('%line'                    , 'line(%sel)'),
            ('%prev_word'               , 'substr(word(%sel))'),
            ('(?<!_)word\('             , 'view.word('),
            ('substr'                   , 'view.substr'),
            ('line\('                   , 'view.line('),
            ('\%clip'                   , 'sublime.get_clipboard()'),
            ('when\s([\w]+):\s*([^`]+)' , 'self.new_region(edit,%minion,("\\1","\\2"))'),
            ('\%select\((.*)\)'         , 'view.sel().add(\\1)'),
            ('region\(([^,]+),([^,]+)\)', 'self.new_region(edit,%code,"\\2",placeholder="\\1")'),
            ('activate\('               , 'self.activate(view,'),
            ('\%date'                   , 'self.new_region(edit,%quick, u.list_time(),placeholder=\'date\')'),
            ('\%auto'                   , 'self.autocompletions,1'),
            ('\%quick'                  , 'self.quickcompletions,2'),
            ('\%code'                   , 'self.code_blocks,3'),
            ('\%minion'                 , 'self.code_minions,4'),
            ('%sel'                     , 'view.sel()[0]'),
            ('view'                     , 'self.view')
            ]

    def new_region(self,edit,d,num,values,placeholder = ''):
        view = self.view
        r = sublime.Region(self.pos,self.pos+len(placeholder))
        if placeholder: self.insert(edit, placeholder)
        if num == 0:
            self.temp_tabstops.append(r)
        elif num == 1:
            self.ac_regions.append(sublime.Region(r.a-1,r.b+1))
        elif num == 2:
            self.qc_regions.append(r)
        elif num == 3:
            self.code_regions.append(sublime.Region(r.a-1,r.b+1))
        else:
            self.minion_regions.append(r)
        if self.inner_reg_count[num] > -1:
            d[view.id()].insert(self.inner_reg_count[num],values)
            self.inner_reg_count[num] += 1
        else:
            d[view.id()].append(values)

    def add_sel(self, string):
        region = self.view.find(string, self.pos)
        self.view.sel().add(region)

    def replace_all(self, text, rlist):
        for i, j in rlist:
            text = re.sub(i, j, text)
        return text

    def insert(self, edit, string):
        if self.code_in_snip[0]:
            self.code_in_snip[1] = string
            return
        self.view.insert(edit, self.pos, string)
        self.pos += len(string)

    def matches_scope(self, line, scope):
        param, snip_scope = line.split(":",1)
        return snip_scope.strip() in scope

    def add_word_to_globals(self, edit, view, word, start, end, insert=True):
        other_end = word.find('}')
        placeholder = word[start:end]
        rlist = word[end+1:other_end]
        if not insert:  # if it's an inner region
            word = word[start-3:start]
        if word.startswith('AC'):
            self.new_region(edit, self.autocompletions,1,rlist.split(','),placeholder)
        else: # QP
            self.new_region(edit, self.quickcompletions,2,rlist.split(','),placeholder)

    # used to parse snippets to extract the string that will be printed out
    # ex. ${0:snippet}
    #           ^
    # The method finds the word snippet and returns it to be inserted into the view
    def extract_regions(self,edit,view,word):
        placeholder = ''
        if word.startswith('$'):
            if len(word) > 2:
                overlap = word[4:].find('{')
                if overlap > 0 and not '\\' in word[overlap:overlap+1]: # means there is an overlapping region.
                    start = overlap + 5
                    end = word[4:].find(':')+4
                    self.add_word_to_globals(edit,view,word,start,end,False)
                else:
                    start = word.find(':')+1
                    end = word.find('}')
                placeholder = word[start:end]
            ts_index = int(re.search('\d{1,2}',word).group())
            if ts_index == 0:
                ts_index = 100
            ts_index -= 100 * self.active_snips
            self.new_region(edit,self.ts_order,0,ts_index,placeholder)
        else:
            start = word.find('{')+1
            end = word.find(':')
            self.add_word_to_globals(edit,view,word,start,end)

    def parse_snippet(self,edit,contents,scope):
        view = self.view
        is_valid_scope = True
        new_contents = ''
        self.code_in_snip = [False,'']
        self.pos = self.get_trigger_reg().a
        view.erase(edit, self.get_trigger_reg())

        # Divides the string so that only code with a matching scope will be inserted
        for line in contents.splitlines(True):
            if line.startswith('###'):
                if line.startswith('###scope:'):
                    is_valid_scope = self.matches_scope(line,scope)
            elif is_valid_scope:
                new_contents += line

        for word in re.split(r'((?:\$|AC|QP)\{[\w,:\s]+?(?:(?=\{)[^}]+\}|[^\{\}]+)\s*\}|```[^`]+```|(?<!\\)\$\d{1,2})',new_contents):
            if word.startswith(('$','AC','QP')):
                for code in re.findall('```[^`]+```', word, flags=re.DOTALL):
                    self.code_in_snip[0] = True
                    exec self.replace_all(code, self.reps)[3:-3]
                    word = word.replace(code,str(self.code_in_snip[1]))
                self.code_in_snip[0] = False
                self.extract_regions(edit,view,word)
            elif word.startswith('```'):
                exec self.replace_all(word, self.reps)[3:-3]
            else:
                view.insert(edit,self.pos,word)
                self.pos += len(word)
                view.sel().clear()
                view.sel().add(sublime.Region(self.pos,self.pos))

        self.temp_tabstops[:0] = view.get_regions('smart_tabstops')
        self.qc_regions.extend(view.get_regions('quick_completions'))
        view.add_regions('smart_tabstops', self.temp_tabstops, 'smart.tabstops',sublime.PERSISTENT)
        view.add_regions('smart_completions', self.ac_regions, 'smart.tabstops',sublime.PERSISTENT)
        view.add_regions('quick_completions', self.qc_regions, 'smart.tabstops',sublime.PERSISTENT)
        view.add_regions('code_regions', self.code_regions, 'smart.tabstops',sublime.PERSISTENT)
        view.add_regions('code_minions', self.minion_regions, 'smart_tabstops', sublime.PERSISTENT)
        del self.temp_tabstops[:]
        del self.ac_regions[:]
        del self.qc_regions[:]
        del self.code_regions[:]
        del self.minion_regions[:]
    
    def snippet_contents(self):
        trigger = self.get_trigger()
        for s in SS.snip_files.keys():
            if s.startswith('y'):
                if re.match(s[2:]+'$', trigger):
                    with open(SS.snip_files.get(s), 'r') as f:
                        return f.read()
            else:
                if s[2:] == trigger:
                    with open(SS.snip_files.get(s), 'r') as f:
                        return f.read()

    # gets the previous word
    def get_trigger(self):
        return self.view.substr(self.get_trigger_reg())

    # returns the region of the previous word
    def get_trigger_reg(self):
        sel = self.view.sel()[0]
        return self.view.word(sel.a)

    def get_reg_pos(self,view,reg_name,stor_index):
        sel     = view.sel()[0]
        looking = True
        for i,t in enumerate(view.get_regions(reg_name)):
            if sel.a < t.a:
                self.inner_reg_count[stor_index] = i
                looking = False
                break
        if looking: self.inner_reg_count[stor_index] = -1

    def run(self, edit):
        view         = self.view
        sel          = view.sel()[0]
        scope        = view.scope_name(sel.a)
        snippet      = self.snippet_contents()

        for i,n in enumerate(self.region_names):
            self.get_reg_pos(view,n,i)

        gt = self.ts_order.get(view.id())
        if gt and len(gt) > 0:
            RunSmartSnippetCommand.active_snips += 1
        else: 
            RunSmartSnippetCommand.active_snips = 1

        self.parse_snippet(edit,snippet, scope)

        if view.get_regions('smart_tabstops'):  # if there is a tabstop,
            self.view.run_command("next_smart_tabstop")