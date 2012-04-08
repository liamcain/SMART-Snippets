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

    # 
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
        for r in view.get_regions('quick_completions'):
            if sublime.Region(r.begin()+1,r.end()-1).contains(sel):
                self.view = view
                qp = RunSmartSnippetCommand.global_quickcompletions
                l = qp.get(view.id())
                view.window().show_quick_panel(l, self.replace)

    # adds a context for 'tab' in the keybindings
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "smart_snippet_found":
            return self.prev_word_is_trigger(view) == operand
        if key == "has_smart_tabstop":
            return self.has_tabstop(view) == operand

    # if cursor overlaps with AC region, get the available completions
    def on_query_completions(self, view, prefix, locations):
        sel = view.sel()[0].a
        for r in view.get_regions('smart_completions'):
            if r.contains(sel):
                ac = RunSmartSnippetCommand.global_autocompletions
                l = ac.get(view.id())
                return [(x,x) for x in l]

# If has_tabstop, this class allows for tabbing between tabstops.
# To avoid duplicate code between the eventlistener and textcommand, it gets its own class
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
    # global dictionaries to give access the autocompletions and quickcompletions
    # key = view id
    global_autocompletions = {}
    global_quickcompletions = {}

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

    # ignore for now... this is left over from an older commit
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

    # used to parse snippets to extract the string that will be printed out
    # ex. ${0:snippet}
    #           ^
    # The method finds the word snippet and returns it to be inserted into the view
    def get_vis(self, word):
        if word.startswith('$'):
            if ':' in word[4:]:
                start = word[4:].find(':')+5
                end = word[4:].find('}')+4
            else:
                start = word.find(':')+1
                end = word.find('}')
            return word[start:end]
        else:
            start = word.find('{')+1
            end = word.find(':')
            return word[start:end]

    def parse_snippet(self,edit,contents,scope):
        is_valid_scope = False
        new_contents = ''
        self.pos = self.get_trigger_reg().a
        self.view.erase(edit, self.get_trigger_reg())

        # Divides the string so that only code with a matching scope will be inserted
        for line in contents.splitlines(True):
            if '###scope' in line:
                is_valid_scope = self.matches_scope(line,scope)
            elif is_valid_scope:
                new_contents += line

        self.edit = edit
        for word in re.split(r'((?:\$|AC|QP)\{[\w,:\s]+?(?:(?=\{)[\w:,\{]+\}|[\w:,\s]+)\s*\}|`.*`)',new_contents):  
            if word.startswith(('$','AC','QP')):
                visible_word = self.get_vis(word)
            elif word.startswith('`'):
                self.run_code(edit, word)
                visible_word = ''
            else:
                visible_word = word

            self.view.insert(edit,self.pos,visible_word)
            self.pos += len(visible_word)

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
        self.parse_snippet(edit,snippet, scope)

        # if there is a tabstop, set the cursor to the first tabstop.
        if view.get_regions('smart_snippets'):
            self.view.run_command("next_smart_tabstop")