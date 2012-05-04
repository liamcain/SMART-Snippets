import sublime
import sublime_plugin
import _snippetloader as SS

class NewSmartSnippet(sublime_plugin.WindowCommand):
	def run(self):
		snip_file = self.window.new_file()
		snip_file.set_syntax_file('Packages/SMART_Snippets/smartsnippet.tmLanguage')
		edit = snip_file.begin_edit()
		snip_file.insert(edit,0,"smart_template")
		snip_file.end_edit(edit)
		snip_file.run_command('run_smart_snippet')

class NewSmartSnippetListener(sublime_plugin.EventListener):
	def on_post_save(self,view):
		if view.file_name().endswith('.smart_snippet'):
			is_regex = 'n'
			regex_reg = view.find('(?<=###regex:).*', 0)
			if view.substr(regex_reg).strip() == 'yes':
				is_regex = 'y'
			trig_reg = view.find('(?<=###trigger:).*', 0)
			trig = is_regex + view.substr(trig_reg).strip()
			if not trig in SS.snippet_triggers:
				SS.snippet_triggers.append(trig)
			SS.snip_files[trig] = view.file_name()

class ListSmartSnippets(sublime_plugin.WindowCommand):
	def run(self):
		snip_trigs = []
		for s in SS.snippet_triggers:
			regex = '\nRegex' if s.startswith('y') else 'Not Regex'
			snip_trigs.append([s[1:],regex])
		self.window.show_quick_panel(snip_trigs, self.open_coor_snip_file)
	def open_coor_snip_file(self, item):
		if item > -1:
			self.window.open_file(SS.snip_files.get(SS.snippet_triggers[item]))