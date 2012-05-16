'''
SMART Snippets
Licensed under MIT
Copyright (c) 2012 William Cain
'''

import os
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
	def on_pre_save(self,view):
		sel = view.sel()[0].a
		if 'smart_snippet' in view.scope_name(sel):
			is_regex = 'n'
			requires_tab = 'y'
			if view.find('###params:.*regex', 0):
				is_regex = 'y'
			if view.find('###params:.*auto_expand', 0):
				requires_tab = 'n'
			trig_reg = view.find('(?<=###trigger:).*', 0)
			trig = is_regex + requires_tab + view.substr(trig_reg).strip()

			# for k,v in SS.snip_files.items():
			# 	if v == view.file_name() and k != trig:
			# 		del SS.snip_files[k]
			
			if trig in SS.snip_files.keys():
				if not view.file_name() in SS.snip_files.values():
					with open(SS.snip_files.get(trig), 'r') as f:
					    other_snippet = f.read()
					edit = view.begin_edit()
					view.insert(edit,view.size(),'\n\n'+other_snippet)
					view.end_edit(edit)
					os.remove(SS.snip_files.get(trig))
			# else:
			# 	SS.snippet_triggers.append(trig)
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
		# for s in SS.snippet_triggers:
		for s in SS.snip_files.keys():
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
				# for t in SS.snippet_triggers:
				for t in SS.snip_files.keys():
					if self.matches_scope(t):
						regex = 'Regex' if t[:1] =='y' else 'Not Regex'
						req_tab = '; Requires tab' if t[1] =='y' else '; Does\'t require tab'
						snip_trigs.append([t[2:],regex + req_tab])
				self.window.show_quick_panel(snip_trigs, self.open_coor_snip_file)
			else:
				self.at_default = True
				self.window.run_command('list_smart_snippets')
		else:
			# self.window.open_file(SS.snip_files.get(SS.snippet_triggers[item-1]))
			self.window.open_file(SS.snip_files.get(SS.snip_files.keys()[item-1]))