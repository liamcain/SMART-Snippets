import sublime
import sublime_plugin
import os.path
import re

class SmartSnippetListener(sublime_plugin.EventListener):
    def has_tabstop(self, view):
        return bool(view.get_regions('smart_tabstops'))

    def ish(self,r):
        return str(r.a)+'-'+str(r.b)

    def replace(self, item):
        view = self.view
        sel = view.sel()[0]
        word = view.word(sel)
        text = RunSmartSnippetCommand.global_quickcompletions.get(view.id()).get(self.ish(self.r))[item]
        del self.r
        edit = view.begin_edit()
        view.replace(edit, word, text)
        view.end_edit(edit)
        self.view = None

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
        snip_file = sublime.packages_path() + "/SMART_Snippets/" + trigger + ".smart_snippet"
        return os.path.isfile(snip_file) and self.match_scope(view, snip_file)

    # For checking if the cursor selection overlaps with a QP region
    def on_selection_modified(self, view):
        sel = view.sel()[0]
        regions = view.get_regions('quick_completions')
        for r in view.get_regions('quick_completions'):
            if sublime.Region(r.a+1,r.b-1).contains(sel):
                regions.remove(r)
                self.view = view
                self.r = r
                qp = RunSmartSnippetCommand.global_quickcompletions.get(view.id()).get(self.ish(r))
                view.window().show_quick_panel(qp, self.replace)
                regions.append(view.word(sel))
                view.add_regions('quick_completions', regions, 'comment')

    # adds a context for 'tab' in the keybindings
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "smart_snippet_found":
            return self.prev_word_is_trigger(view) == operand
        if key == "has_smart_tabstop":
            return self.has_tabstop(view) == operand

    # if cursor overlaps with AC region, get the available completions
    def on_query_completions(self, view, prefix, locations):
        sel = view.sel()[0]
        for r in view.get_regions('smart_completions'):
            if r.contains(sel.a):
                edit = view.begin_edit()
                # view.erase(edit, view.word(sel))
                view.end_edit(edit)
                ac = RunSmartSnippetCommand.global_autocompletions.get(view.id()).get(self.ish(r))
                print ac
                return [(x,x) for x in ac]

# If has_tabstop, this class allows for tabbing between tabstops.
# To avoid duplicate code between the eventlistener and textcommand, it gets its own class
class NextSmartTabstopCommand(sublime_plugin.TextCommand):
    def run(self,edit):
        tabstops = self.view.get_regions('smart_tabstops')
        try:
            next = tabstops.pop(1)
        except IndexError:
            next = tabstops.pop(0)
        self.view.add_regions('smart_tabstops', tabstops, 'comment')
        self.view.sel().clear()
        self.view.sel().add(next)
        
class RunSmartSnippetCommand(sublime_plugin.TextCommand):
    # global dictionaries to give access the autocompletions and quickcompletions
    # key = view id
    # values are dictionaries
    #     key   = region
    #     value = list of completions
    global_autocompletions = {}
    global_quickcompletions = {}
    temp_tabstops = []

    # This is a working list of substitutions for embedded code.
    # It will serve as shorthand for people who want quick access to common python functions and commands
    reps = [
            ('insert'                  ,'self.insert'),
            ('\%line\%'                ,'substr(line(sel))'),
            ('%prev_word%'             ,'substr(word(sel))'),
            ('(?<!_)word\('            , 'view.word('),
            ('substr'                  , 'view.substr'),
            ('sel(?!f)'                , 'view.sel()[0]'),
            ('line\('                  , 'view.line('),
            ('view'                    , 'self.view')
            ]

    def replace_all(self, text, list):
        for i, j in list:
            text = re.sub(i, j, text)
        return text

    def insert(self, string):
        self.view.insert(self.edit, self.pos, string)
        self.pos += len(string)

    def matches_scope(self, line, scope):
        param, snip_scope = line.split(":",1)
        return snip_scope.strip() in scope

    # replace the shorthand code with the reps,
    # then exec the code segment
    def run_code(self,edit,string):
        new_string = self.replace_all(string, self.reps)
        exec new_string[1:-1]  # 1:-1 removes the ` around the code

    def ish(self,r):
        return str(r.a)+'-'+str(r.b)

    # used to parse snippets to extract the string that will be printed out
    # ex. ${0:snippet}
    #           ^
    # The method finds the word snippet and returns it to be inserted into the view
    def get_vis(self, word):
        if word.startswith('$'):
            if ':' in word[4:]:  # means there is an overlapping region.
                start = word[4:].find('{')+5
                end = word[4:].find(':')+4
                other_end = word.find('}')
                new_word = word[start:end]
                r = sublime.Region(self.pos,self.pos+len(new_word)) #added -1
                rlist = word[end+1:other_end]
                if word.startswith('AC'):
                    self.global_autocompletions[self.view.id()][self.ish(r)] = rlist.split(',')
                else:
                    self.global_quickcompletions[self.view.id()][self.ish(r)] = rlist.split(',')
            else:
                start = word.find(':')+1
                end = word.find('}')
            new_word = word[start:end]
            ts_index = re.search('\d{1,2}',word).group()
            ts_region = sublime.Region(self.pos,self.pos+len(new_word))
            self.temp_tabstops.insert(int(ts_index),ts_region)
        else:
            start = word.find('{')+1
            end = word.find(':')
            other_end = word.find('}')
            new_word = word[start:end]
            r = sublime.Region(self.pos,self.pos+len(new_word)) # added -1
            rlist = word[end+1:other_end]
            if word.startswith('AC'):
                self.global_autocompletions[self.view.id()][self.ish(r)] = rlist.split(',')
            else:
                self.global_quickcompletions[self.view.id()][self.ish(r)] = rlist.split(',')
        return new_word

#convert list of strings to regions
    def to_region(self,str_list):
        temp_list = []
        for t in str_list:
            r = t.split('-')
            temp_list.append(sublime.Region(int(r[0]),int(r[1])))
        return temp_list

    def parse_snippet(self,edit,contents,scope):
        view = self.view
        is_valid_scope = False
        new_contents = ''
        self.pos = self.get_trigger_reg().a
        view.erase(edit, self.get_trigger_reg())

        # Divides the string so that only code with a matching scope will be inserted
        for line in contents.splitlines(True):
            if '###scope' in line:
                is_valid_scope = self.matches_scope(line,scope)
            elif is_valid_scope:
                new_contents += line

        self.edit = edit
        for word in re.split(r'((?:\$|AC|QP)\{[\w,:\s]+?(?:(?=\{)[\w\s:,\{]+\}|[\w:,\s]+)\s*\}|`.*`)',new_contents):  
            if word.startswith(('$','AC','QP')):
                visible_word = self.get_vis(word)
            elif word.startswith('`'):
                self.run_code(edit, word)
                visible_word = ''
            else:
                visible_word = word

            view.insert(edit,self.pos,visible_word)
            self.pos += len(visible_word)

        view.add_regions('smart_tabstops', self.temp_tabstops, 'comment')
        str_regions  = self.global_autocompletions.get(view.id()).keys()
        str_regions2 = self.global_quickcompletions.get(view.id()).keys()
        regions  = self.to_region(str_regions)
        regions2 = self.to_region(str_regions2)
        view.add_regions('smart_completions', regions, 'comment')
        view.add_regions('quick_completions', regions2, 'comment')
        del self.temp_tabstops[:]
        self.edit = None
    
    def snippet_contents(self):
        trigger = self.get_trigger()
        package_dir = sublime.packages_path() + "/SMART_Snippets/"
        snip_file = package_dir + trigger + ".smart_snippet"
        with open(snip_file, 'r') as f:
            return f.read()

    # gets the previous word
    def get_trigger(self):
        return self.view.substr(self.get_trigger_reg())

    # returns the region of the previous word
    def get_trigger_reg(self):
        sel = self.view.sel()[0]
        return self.view.word(sel.a)

    def run(self, edit):
        view      = self.view
        sel       = view.sel()[0]
        scope     = view.scope_name(sel.a)
        snippet   = self.snippet_contents()
        self.global_autocompletions[view.id()] = {}
        self.global_quickcompletions[view.id()] = {}
        self.parse_snippet(edit,snippet, scope)

        # if there is a tabstop, set the cursor to the first tabstop.
        if view.get_regions('smart_tabstops'):
            self.view.run_command("next_smart_tabstop")