import sublime
import sublime_plugin
import os.path
import re

class SmartSnippetListener(sublime_plugin.EventListener):

    def has_tabstop(self, view):
        return bool(view.get_regions('smart_snippets'))

    def replace(self, item):
        view = self.view
        sel = view.sel()[0]
        word = view.word(sel)
        text = RunSmartSnippetCommand.global_quickcompletions.get(view.id())[item]
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

    def prev_word_is_trigger(self, view):
        trigger = view.substr(view.word(view.sel()[0].a)).strip()
        snip_file = sublime.packages_path() + "/SMART_Snippets/" + trigger + ".smart_snippet"
        return os.path.isfile(snip_file) and self.match_scope(view, snip_file)

    def on_selection_modified(self, view):
        sel = view.sel()[0]
        for r in view.get_regions('quick_completions'):
            if sublime.Region(r.begin()+1,r.end()-1).contains(sel):
                self.view = view
                qp = RunSmartSnippetCommand.global_quickcompletions
                l = qp.get(view.id())
                view.window().show_quick_panel(l, self.replace)

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "smart_snippet_found":
            return self.prev_word_is_trigger(view) == operand
        if key == "has_smart_tabstop":
            return self.has_tabstop(view) == operand

    def on_query_completions(self, view, prefix, locations):
        sel = view.sel()[0].a
        for r in view.get_regions('smart_completions'):
            if r.contains(sel):
                ac = RunSmartSnippetCommand.global_autocompletions
                l = ac.get(view.id())
                return [(x,x) for x in l]

class NextSmartTabstopCommand(sublime_plugin.TextCommand):
    def run(self,edit):
        tabstops = self.view.get_regions('smart_snippets')
        try:
            next = tabstops.pop(1)
        except IndexError:
            next = tabstops.pop(0)
        self.view.add_regions('smart_snippets', tabstops, 'comment')
        self.view.sel().clear()
        self.view.sel().add(next)

class RunSmartSnippetCommand(sublime_plugin.TextCommand):
    global_autocompletions = {}
    global_quickcompletions = {}
    snip_regs = []
    final_snip = ''

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

    def generate_completions(self, edit, name, start, matches):
        regions = []
        for m in matches:
            full_region = self.view.find(re.escape(m.group(0)),start)
            pos = full_region.a
            active_region = sublime.Region(pos, pos + len(m.group(2)))
            regions.append(active_region)
            if name == 'smart_completions':
                self.global_autocompletions[self.view.id()] = m.group(4).split(',')
            elif name == 'quick_completions':
                self.global_quickcompletions[self.view.id()] = m.group(4).split(',')
            self.view.replace(edit,full_region,m.group(2))

        self.view.add_regions(name, regions, "comment")

    # def generate_tabstops(self, edit, start, matches):
    #     regions = []
    #     for m in matches:
    #         full_region = self.view.find(re.escape(m.group(0)),start)
    #         pos = full_region.a
    #         active_region = sublime.Region(pos, pos + len(m.group(4)))
    #         regions.insert(int(m.group(2)), active_region)
    #         self.view.replace(edit,full_region,m.group(4))

    #     self.view.add_regions('smart_snippets', regions, "comment")

    def replace_all(self, text, list):
        for i, j in list:
            text = re.sub(i, j, text)
        return text

    def insert(self, string):
        self.final_snip += string

    def matches_scope(self, line, scope):
        param, snip_scope = line.split(":",1)
        return snip_scope.strip() in scope

    def parse_snippet(self,edit,contents,scope):
        is_valid_scope = False
        new_contents = ''
        auto_comp_reg = False
        snip_reg = False
        quick_pan_reg = False
        sel = self.get_trigger_reg()
        cur = sel.b

        for line in contents.splitlines(True):
            if '###scope' in line:
                is_valid_scope = self.matches_scope(line,scope)
            elif is_valid_scope:
                new_contents += line

        for x in re.split(r'(\$\{|AC\{|QP\{|\})',new_contents):
            print x
        for word in re.split(r'(\$\{|AC\{|QP\{|\})',new_contents):
            if '}' in word:
                if auto_comp_reg or quick_pan_reg:
                    auto_comp_reg = False
                    quick_pan_reg = False
                elif snip_reg:
                    snip_reg = False
                self.view.replace(edit, sel, prev_word)
                cur += len(prev_word)
                sel = sublime.Region(cur,cur)
            elif 'AC{' in word:
                auto_comp_reg = True
            elif '${' in word:
                snip_reg = True
            elif 'QP{' in word:
                quick_pan_reg = True
            # elif auto_comp_reg:
            #     s = word.split(':')
            #     print s
            #     word_to_insert = s[0]
            #     self.global_autocompletions[self.view.id()]=s[1]
            # elif snip_reg:
            #     s = word.split(':')
            #     print s
            #     self.snip_regs.insert(int(s[0]),s[1])
            else:
                self.view.replace(edit, sel, word)
                cur += len(word)
                sel = sublime.Region(cur,cur)
            prev_word = word

        self.view.sel().clear()
        self.view.sel().add(sel)
    
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
        start_pos = view.word(sel).begin()
        reg       = self.get_trigger_reg()
        snippet   = self.snippet_contents()
        self.parse_snippet(edit,snippet, scope)

        if view.get_regions('smart_snippets'):
            self.view.run_command("next_smart_tabstop")