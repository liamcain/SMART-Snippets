import sublime
import sublime_plugin

class NewSmartSnippet(sublime_plugin.WindowCommand):
	def run(self):
		snip_file = self.window.new_file()
		edit = snip_file.begin_edit()
		snip_file.insert(edit,0,"###trigger:\n###scope:\n")