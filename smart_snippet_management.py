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
			requires_tab = 'y'
			regex_reg = view.find('(?<=###regex:).*', 0)
			if regex_reg and view.substr(regex_reg).strip() == 'yes':
				is_regex = 'y'
			req_tab_reg = view.find('(?<=###tab:).*', 0)
			if req_tab_reg and view.substr(req_tab_reg).strip() == 'no':
				req_tab_reg = 'n'
			trig_reg = view.find('(?<=###trigger:).*', 0)
			trig = is_regex + req_tab_reg + view.substr(trig_reg).strip()
			if not trig in SS.snippet_triggers:
				SS.snippet_triggers.append(trig)
			SS.snip_files[trig] = view.file_name()

class SmartViewSetterListener(sublime_plugin.EventListener):
	def on_activated(self,view):
		if not view.settings().get('is_widget'):
			ListSmartSnippetsCommand.view = view

class ListSmartSnippetsCommand(sublime_plugin.WindowCommand):
	at_default = True
	def run(self):
		view = self.view
		scope = scope = view.scope_name(view.sel()[0].a)
		default = ["Only show snippets that match scope", scope]
		snip_trigs = [default]
		for s in SS.snippet_triggers:
			regex = 'Regex' if s[0] =='y' else 'Not Regex'
			req_tab = '; Requires tab' if s[1] =='y' else '; Does\'t require tab'
			snip_trigs.append([s[2:],regex+req_tab])
		self.window.show_quick_panel(snip_trigs, self.open_coor_snip_file)

	def matches_scope(self,trigger):
		with open(SS.snip_files.get(trigger), 'r') as f:
		    snip = f.read()
		view = self.view
		scope = view.scope_name(view.sel()[0].a)
		for l in snip.splitlines(True):
			if l.startswith('###scope:'):
				param, snip_scope = l.split(":",1)
				if snip_scope.strip() in scope:
					return True
		return False

	def open_coor_snip_file(self, item):
		if item == -1: return
		if item == 0:
			if self.at_default:
				self.at_default = False
				snip_trigs = ["Back"]
				for t in SS.snippet_triggers:
					if self.matches_scope(t):
						regex = 'Regex' if t[:1] =='y' else 'Not Regex'
						req_tab = '; Requires tab' if t[2:2] =='y' else '; Does\'t require tab'
						snip_trigs.append([t[2:],regex + req_tab])
				self.window.show_quick_panel(snip_trigs, self.open_coor_snip_file)
			else:
				self.at_default = True
				self.window.run_command('list_smart_snippets')
		else:
			self.window.open_file(SS.snip_files.get(SS.snippet_triggers[item-1]))