import sublime
import sublime_plugin
import os.path
import re

class SmartSnippetListener(sublime_plugin.EventListener):

    def has_tabstop(self, view):
        return bool(view.get_regions('smart_snippets'))

    def prev_word_is_trigger(self, view):
        trigger = view.substr(view.word(view.sel()[0].a)).strip()
        snip_file = sublime.packages_path() + "/SMART_Snippets/" + trigger + ".smart_snippet"
        return os.path.isfile(snip_file)

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "smart_snippet_found":
            return self.prev_word_is_trigger(view) == operand
        if key == "has_smart_tabstop":
            return self.has_tabstop(view) == operand


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

    def generate_tabstops(self, edit, start, tabstop_matches):
        tabstops = []
        for t in tabstop_matches:
            full_ts_region = self.view.find(re.escape(t.group(0)),start)
            pos = full_ts_region.a
            ts_region = sublime.Region(pos, pos + len(t.group(4)))
            tabstops.insert(int(t.group(2)), ts_region)
            self.view.replace(edit,full_ts_region,t.group(4))

        self.view.add_regions('smart_snippets', tabstops, "comment")

    def replace_all(self, text, list):
        for i, j in list:
            text = re.sub(i, j, text)
        return text

    def insert(self, string):
        self.final_snip += string

    def parse_snippet(self,contents):
        new_contents = self.replace_all(contents, self.reps)
        tabstops = re.finditer('(\$\{)([0-9]+)(:)([a-zA-Z0-9 \"\']+)(\})', contents)
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
        return tabstops
    
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
        start_pos = view.word(sel).begin()
        reg       = self.get_trigger_reg()
        snippet   = self.snippet_contents(trig)
        tabstops  = self.parse_snippet(snippet)

        view.replace(edit, reg, self.final_snip)
        self.generate_tabstops(edit, start_pos, tabstops)

        if view.get_regions('smart_snippets'):
            self.view.run_command("next_smart_tabstop")