import sublime
import sublime_plugin
import os.path
import re

class Tabstop():
    tabstops = []
    iter = 1

    @staticmethod
    def next_tabstop():
        try:
            stop = Tabstop.tabstops[Tabstop.iter]
        except IndexError:
            stop = Tabstop.tabstops[0]

        Tabstop.iter+=1
        return stop

class SmartSnippetListener(sublime_plugin.EventListener):

    def has_tabstop(self):
        return bool(Tabstop.tabstops)

    def prev_word_is_trigger(self, view):
        trigger = view.substr(view.word(view.sel()[0].a)).strip()
        snip_file = sublime.packages_path() + "/SMART_Snippets/" + trigger + ".smart_snippet"
        return os.path.isfile(snip_file)

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "smart_snippet_found":
            return self.prev_word_is_trigger(view) == operand
        if key == "has_smart_tabstop":
            return self.has_tabstop() == operand


class NextSmartTabstopCommand(sublime_plugin.TextCommand):
    def run(self,edit):
        self.view.sel().clear()
        self.view.sel().add(Tabstop.next_tabstop())

class RunSmartSnippetCommand(sublime_plugin.TextCommand):

    tabstops = []

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

    def add_tabstop(self,matchobj):
        num = int(matchobj.group(2))
        text = matchobj.group(4)
        self.tabstops.insert(num, text)
        # self.final_snip += text
        return text

    def generate_tabstops(self, start):
        for t in self.tabstops:
            Tabstop.tabstops.append(self.view.find(t, start))

    def replace_all(self, text, list):
        for i, j in list:
            text = re.sub(i, j, text)
            print text
        return text

    def insert(self, string):
        # self.view.insert(self.edit, self.view.sel()[0].b, string)
        print 'string'+string
        self.final_snip += string

    def parse_snippet(self,contents):
        new_contents = self.replace_all(contents, self.reps)
        new_contents = re.sub('(\$\{)([0-9]+)(:)([a-zA-Z0-9 \"\'"]+)(\})',self.add_tabstop, new_contents)
        new_contents = re.split('(`)([a-zA-Z\s\'\"\(\).]+)(`)', new_contents)

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


        # self.final_snip += new_contents
    
    def snippet_contents(self, trigger):
        package_dir = sublime.packages_path() + "/SMART_Snippets/"
        snip_file = package_dir + trigger + ".smart_snippet"
        with open(snip_file, 'r') as f:
                    return f.read()

    # method is deprecated, might go back to it if I want to change how the trigger is determined.
    def get_snippets(self):
        snippets = []
        package_dir = sublime.packages_path() + "/SMART_Snippets/"
        for d in os.listdir(package_dir):
            if '.smart_snippet' in d:
                snippets.append(d)

        return snippets

    # gets the previous word
    def get_trigger(self):
        return self.view.substr(self.get_trigger_reg())

    # returns the region of the previous word
    def get_trigger_reg(self):
        sel = self.view.sel()[0]
        return self.view.word(sel.a)

    def run(self, edit):
        self.edit = edit
        view = self.view
        sel = view.sel()[0]
        start_pos = sel.a - len(view.substr(view.word(sel)))
        self.final_snip = ''
        reg = self.get_trigger_reg()
        trig = self.get_trigger()
        snippet = self.snippet_contents(trig)
        self.parse_snippet(snippet)
        self.view.replace(edit, reg, self.final_snip)
        self.generate_tabstops(start_pos)
        if Tabstop.tabstops:
            self.view.sel().clear()
            next_pos = Tabstop.next_tabstop()
            self.view.sel().add(next_pos)