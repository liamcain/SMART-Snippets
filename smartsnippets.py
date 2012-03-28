import sublime
import sublime_plugin
import os.path
import re

class SmartSnippetListener(sublime_plugin.EventListener):

    def has_tabstop(self, view):
        return bool(view.get_regions('smart_snippets'))

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
                for i,c in enumerate(ac):
                    if c[0] == view.id():
                        return [(x,x) for x in ac[i][1].split(',')]

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
    global_autocompletions = []
    final_snip = ''

    reps = [
            ('insert'                  ,'self.insert'),
            ('line'                    ,'substr(line(sel))'),
            ('prev_word'               ,'substr(word(sel))'),
            ('(?<!_)word\('            , 'view.word('),
            ('substr'                  , 'view.substr'),
            ('sel(?!f)'                , 'view.sel()[0]'),
            ('line'                    , 'view.line'),
            ('view'                    , 'self.view')
            ]

    def generate_completions(self, edit, start, matches):
        regions = []
        for m in matches:
            full_region = self.view.find(re.escape(m.group(0)),start)
            pos = full_region.a
            active_region = sublime.Region(pos, pos + len(m.group(2)))
            regions.append(active_region)
            self.global_autocompletions.append((self.view.id(),m.group(4)))
            self.view.replace(edit,full_region,m.group(2))

        self.view.add_regions('smart_completions', regions, "comment")

    def generate_tabstops(self, edit, start, matches):
        regions = []
        for m in matches:
            full_region = self.view.find(re.escape(m.group(0)),start)
            pos = full_region.a
            active_region = sublime.Region(pos, pos + len(m.group(4)))
            regions.insert(int(m.group(2)), active_region)
            self.view.replace(edit,full_region,m.group(4))

        self.view.add_regions('smart_snippets', regions, "comment")

    def replace_all(self, text, list):
        for i, j in list:
            text = re.sub(i, j, text)
        return text

    def insert(self, string):
        self.final_snip += string

    def matches_scope(self, line, scope):
        param, snip_scope = line.split(":",1)
        return snip_scope.strip() in scope

    def parse_snippet(self,contents, scope):
        is_valid_scope = False
        new_contents = ''

        for line in contents.splitlines(True):
            if '###scope' in line:
                is_valid_scope = self.matches_scope(line,scope)
            elif is_valid_scope:
                new_contents += line

        new_contents = self.replace_all(new_contents, self.reps)
        tabstops = re.finditer('(\$\{)([0-9]+)(:)([a-zA-Z0-9\s\[\]:,\"\']+)(\})', new_contents)
        auto_completions = re.finditer('(AC\[)([a-zA-Z0-9\s]+)(:)([a-zA-Z0-9 \"\',]+)(\])', new_contents)
        new_contents = re.split('(`)([a-zA-Z0-9\s\'\"\(\)\[\].]+)(`)', new_contents)
        # my execution loop: alternates between exec & adding to snippet :)
        code = new_contents[0] == '`'
        if code: start = 1
        else:    start = 0

        for c in new_contents[start::2]:
            if code:
                exec c
            else:
                self.final_snip += c
            code = not code
        return [tabstops, auto_completions]
    
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
        tabstops, auto_completions  = self.parse_snippet(snippet, scope)

        view.replace(edit, reg, self.final_snip)
        del self.final_snip

        if tabstops:
            self.generate_tabstops(edit, start_pos, tabstops)
        if auto_completions:
            self.generate_completions(edit, start_pos, auto_completions)

        if view.get_regions('smart_snippets'):
            self.view.run_command("next_smart_tabstop")