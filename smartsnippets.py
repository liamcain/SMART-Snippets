import sublime
import sublime_plugin
import os.path
import re
import _snippetloader as SS
import smart_utils as u

SS.init_snipfiles()
SETTINGS = "smartsnippets.sublime-settings"

class SmartSnippetListener(sublime_plugin.EventListener):
    def on_activated(self,view):
        if view.settings().get('is_widget'):
            return
        self.view = view
        self.ss_without_tab = sublime.load_settings(SETTINGS).get("smart_snippets_without_tab")
        if not RunSmartSnippetCommand.global_autocompletions.get(view.id()):
            RunSmartSnippetCommand.global_autocompletions[view.id()] = []
        if not RunSmartSnippetCommand.global_quickcompletions.get(view.id()):
            RunSmartSnippetCommand.global_quickcompletions[view.id()] = []
        if not RunSmartSnippetCommand.global_ts_order.get(view.id()):
            RunSmartSnippetCommand.global_ts_order[view.id()] = []

    def on_close(self, view):
        del RunSmartSnippetCommand.global_ts_order[view.id()]

    def has_tabstop(self, view):
        return bool(RunSmartSnippetCommand.global_ts_order.get(view.id()))

    def first(self, item):
        if isinstance(item, basestring):
            return item
        return item[0]

    def replace(self, item):
        if item < 0: return
        view = self.view
        r = view.get_regions('quick_completions')
        word = r[self.i]
        text = self.first(RunSmartSnippetCommand.global_quickcompletions.get(view.id())[self.i][item])
        edit = view.begin_edit()
        view.replace(edit, word, text)
        r = view.get_regions('quick_completions')
        r[self.i] = sublime.Region(word.a,word.a+len(text))
        view.end_edit(edit)
        view.add_regions('quick_completions', r, 'smart.tabstops')
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
        trigger = view.substr(view.word(view.sel()[0].a)).strip()
        for s in SS.snippet_triggers:
            if s.startswith('y'):
                if re.match(s[1:]+'$', trigger):
                # if re.match('.*'+s[1:], trigger):
                    return self.match_scope(view, SS.snip_files.get(s))
            else:
                if s[1:] == trigger:
                    return self.match_scope(view, SS.snip_files.get(s))
        return False

    def inside_qc_region(self,view):
        sel = self.view.sel()[0]
        for c in view.get_regions('quick_completions'):
            if c.contains(sel):
                return True
        return False

    # For checking if the cursor selection overlaps with a QP region
    def on_selection_modified(self, view):
        sel = view.sel()[0]
        regions = view.get_regions('quick_completions')
        for i,r in enumerate(regions):
            if sel == r:
                self.i = i
                qp = RunSmartSnippetCommand.global_quickcompletions.get(view.id())[i]
                view.window().show_quick_panel(qp, self.replace)

    def on_modified(self, view):
        sel = view.sel()[0]
        regions = view.get_regions('quick_completions')
        for i,r in enumerate(regions[:]):
            if r.empty() and sel == r:
                regions.remove(r)
                qp = RunSmartSnippetCommand.global_quickcompletions[view.id()].pop(i)
                view.add_regions('quick_completions', regions, 'smart.tabstops')

        regions = view.get_regions('smart_completions')
        for i,r in enumerate(regions[:]):
            if r.empty() and not ' ' in view.substr(sel.a-1) and not sel.a == 0:
                regions.remove(r)
                qp = RunSmartSnippetCommand.global_autocompletions[view.id()].pop(i)
                view.add_regions('smart_completions', regions, 'smart.tabstops')

        regions = view.get_regions('smart_tabstops')
        for i,r in enumerate(regions[:]):
            if sel.intersects(r):
                regions.remove(r)
                RunSmartSnippetCommand.global_ts_order[view.id()].pop(i)
                view.add_regions('smart_tabstops', regions, 'smart.tabstops')

        if not view.is_loading() and self.prev_word_is_trigger(view) and self.ss_without_tab:
            view.run_command('run_smart_snippet')


    # adds a context for 'tab' in the keybindings
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "smart_snippet_found":
            return self.prev_word_is_trigger(view) == operand
        if key == "has_smart_tabstop":
            return self.has_tabstop(view) == operand
        if key == "inside_qc_region":
            return self.inside_qc_region(view) == operand

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
                ac = RunSmartSnippetCommand.global_autocompletions.get(view.id())[i]
                return [(x,x) for x in ac]

# If has_tabstop, this class allows for tabbing between tabstops.
# To avoid duplicate code between the eventlistener and textcommand, it gets its own class
class NextSmartTabstopCommand(sublime_plugin.TextCommand):
    def run(self,edit):
        view = self.view
        tabstops = self.view.get_regions('smart_tabstops')
        view.set_status('smart_tabstops', 'Field '+str(self.field)+' of '+str(self.length))
        ts_order = RunSmartSnippetCommand.global_ts_order.get(view.id())
        next = tabstops.pop(ts_order.index(min(ts_order)))  # pops the next lowest value
        RunSmartSnippetCommand.global_ts_order[view.id()].remove(min(ts_order))
        view.add_regions('smart_tabstops', tabstops, 'smart.tabstops')
        view.sel().clear()
        view.sel().add(next)
        self.field += 1

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
    global_autocompletions = {}
    global_quickcompletions = {}
    global_ts_order = {}
    temp_tabstops = []
    ac_regions    = []
    qc_regions    = []
    num_active_snips = 0
    inner_reg_count = [-1,-1,-1]

    # This is a working list of substitutions for embedded code.
    # It will serve as shorthand for people who want quick access to common python functions and commands
    reps = [
            # ('([\w]+)\s*='             , 'global \\1\n\\1 ='),
            ('insert\('                ,'self.insert(edit,'),
            ('\%line\%'                ,'substr(line(sel))'),
            ('%prev_word%'             ,'substr(word(sel))'),
            ('(?<!_)word\('            , 'view.word('),
            ('substr'                  , 'view.substr'),
            ('sel(?!f)'                , 'view.sel()[0]'),
            ('line\('                  , 'view.line('),
            ('view'                    , 'self.view'),
            ('\$date'                  , 'self.new_region(edit,%quick,\'date\', u.list_time())'),
            ('\%quick'                 , 'self.global_quickcompletions,2'),
            ('\%auto'                  , 'self.global_autocompletions,1')
            ]

    def new_region(self,edit,d,num,placeholder,reglist, insert = True):
        view = self.view
        r = sublime.Region(self.pos,self.pos+len(placeholder))
        if insert: self.insert(edit, placeholder)
        if num == 0:
            self.temp_tabstops.append(r)
        elif num == 1:
            self.ac_regions.append(r)
        else:
            self.qc_regions.append(r)
        if self.inner_reg_count[num] > -1:
            d[view.id()].insert(self.inner_reg_count[num],reglist)
            self.inner_reg_count[num] += 1
        else:
            d[view.id()].append(reglist)

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
        if word.startswith('AC'):
            self.new_region(edit, self.global_autocompletions, 1, placeholder, rlist.split(','), insert)
        else: # QP
            self.new_region(edit, self.global_quickcompletions, 2, placeholder, rlist.split(','), insert)

    # replace the shorthand code with the reps,
    # then exec the code segment
    # def run_code(self, edit, string):
    #     new_string = self.replace_all(string, self.reps)
    #     exec new_string[3:-3]

    # used to parse snippets to extract the string that will be printed out
    # ex. ${0:snippet}
    #           ^
    # The method finds the word snippet and returns it to be inserted into the view
    def extract_regions(self,edit,view,word):
        if word.startswith('$'):
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
            ts_index -= 100 * self.num_active_snips
            ts_region = sublime.Region(self.pos,self.pos+len(placeholder))
            self.new_region(edit,self.global_ts_order,0,placeholder,ts_index)
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

        for word in re.split(r'((?:\$|AC|QP)\{[\w,:\s]+?(?:(?=\{)[^}]+\}|[^\{\}]+)\s*\}|```[^`]+```)',new_contents):
            if word.startswith(('$','AC','QP')):
                for code in re.findall('```[^`]+```', word, flags=re.DOTALL):
                    self.code_in_snip[0] = True
                    exec self.replace_all(code, self.reps)[3:-3]
                    word = word.replace(code,str(self.code_in_snip[1]))
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
        view.add_regions('smart_tabstops', self.temp_tabstops, 'smart.tabstops')
        view.add_regions('smart_completions', self.ac_regions, 'smart.tabstops')
        view.add_regions('quick_completions', self.qc_regions, 'smart.tabstops')
        del self.temp_tabstops[:]
        del self.ac_regions[:]
        del self.qc_regions[:]
    
    def snippet_contents(self):
        trigger = self.get_trigger()
        for s in SS.snippet_triggers:
            if s.startswith('y'):
                if re.match(s[1:]+'$', trigger):
                # if re.match('.*'+s[1:], trigger):
                    with open(SS.snip_files.get(s), 'r') as f:
                        return f.read()
            else:
                if s[1:] == trigger:
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
        view      = self.view
        sel       = view.sel()[0]
        scope     = view.scope_name(sel.a)
        snippet   = self.snippet_contents()
        self.temp_tabstops = []

        self.get_reg_pos(view,'smart_tabstops'   , 0)
        self.get_reg_pos(view,'smart_completions', 1)
        self.get_reg_pos(view,'quick_completions', 2)

        gt = self.global_ts_order.get(view.id())
        if gt and len(gt) > 0:  self.num_active_snips += 1
        else:                   self.num_active_snips = 0

        self.parse_snippet(edit,snippet, scope)

        # if there is a tabstop, set the cursor to the first tabstop.
        if view.get_regions('smart_tabstops'):
            NextSmartTabstopCommand.field = 1
            NextSmartTabstopCommand.length = len(view.get_regions('smart_tabstops'))
            self.view.run_command("next_smart_tabstop")