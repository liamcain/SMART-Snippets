import sublime
import sublime_plugin

class NewSmartSnippet(sublime_plugin.WindowCommand):
	def run(self):
		snip_file = self.window.new_file()
		snip_file.set_syntax_file('Packages/SMART_Snippets/smartsnippet.tmLanguage')
		edit = snip_file.begin_edit()
		snip_file.insert(edit,0,"smart_template")
		snip_file.run_command('run_smart_snippet')
		snip_file.end_edit(edit)