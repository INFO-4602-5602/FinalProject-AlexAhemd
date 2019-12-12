import pandas as pd

from bokeh.layouts import widgetbox, column, row, layout, GridBox
from bokeh.models import CustomJS, Slider, HoverTool, ColumnDataSource
from bokeh.models import Circle, Text, TapTool

from bokeh.plotting import figure, output_file
from bokeh.palettes import Spectral6
from bokeh.models.widgets import Panel, Tabs,  Select
from bokeh.embed import components

import math

def read_all_dfs(engagement_column):
	'''
	engagement_column: either 'likes' or 'watches' or 'comments'
	'''
	engagement = pd.read_csv("time_vs_" + engagement_column + ".csv", index_col=0)
	followers = pd.read_csv('time_vs_followers.csv', index_col=0)
	posts = pd.read_csv('time_vs_posts.csv', index_col=0)
	groups = pd.read_csv('user_groups.csv', index_col=None)
	
	all_groups = groups['Group'].unique()
	days = engagement.columns.tolist()
	days_indices = list(range(len(days)))
	
	return engagement, followers, posts, groups, days, all_groups, days_indices


def create_source_dict(engagement_df, followers_df, posts_df, groups, days, days_indices, engagement_col):
	'''
	returns a dictionary where keys are dates and values are ColumnDataSource objects for the plot
	
	the dictionary will be used for the first figure
	'''
	source = {}
	
	colors = groups['group_color'].tolist()
	user_names = followers_df.index.tolist()
	
	for day, number in zip(days, days_indices):
		engagement       = engagement_df[day]
		engagement.name  = engagement_col
		
		followers = followers_df[day]
		followers.name = 'followers'
			
		posts      = posts_df[day]
		posts.name = 'posts'
		
		days_list = [day]*len(colors)
		days = pd.Series(days_list, index=user_names)
		days.name = 'days'

		frame = {
			engagement_col: engagement, 
			'followers-scaled': followers.apply(lambda x: x / 150),
			'followers': followers,
			'posts':posts, 
			'days':days, 
			'colors':colors, 
			'groups':groups['Group'].tolist()
		} 
		
		result = pd.DataFrame(frame, index=user_names) 

		source['_'+str(number)] = ColumnDataSource(result)

	return source


def create_user_source(engagement_df, days):
	'''
	returns a dictionary, where the key is an instagram username, and the value is a CDS object
	
	this will be used for the second figure
	'''
	user_sources = {}
	user_names = engagement_df.index.tolist()
	
	for user in user_names:
		engagement = engagement_df.loc[user, :].tolist()
		user_df = pd.DataFrame({'engagement':engagement, 'days':days})
		user_sources[user] = ColumnDataSource(user_df)
	
	return user_sources


def sources_to_js(sources, days_indices):
	'''
	convert dictionary to string for JS Callback
	'''
	dict_of_sources = dict(
						zip(
							[day for day in days_indices], 
							['_'+str(day) for day in days_indices]
						)
					)

	js_source_array = str(dict_of_sources).replace("'", "")
	
	return js_source_array


def create_plot(engagement, posts, days, engagement_sources, user_sources_engagement, engagement_column, js_source_array_engagement):
	
	max_engagement, min_engagement = max(engagement.max()), min(engagement.min())
	max_posts, min_posts = max(posts.max()), min(posts[posts > .01].min(axis=1))

	plot_properties = {
		'x_one':min_posts-1, 
		'x_two':max_posts+1, 
		'y_one':min_engagement-0.5, 
		'y_two':max_engagement
	}

	''' ############ PLOT ONE ############ '''
	x_one = plot_properties['x_one']
	x_two = plot_properties['x_two']
	y_one = plot_properties['y_one']
	y_two = plot_properties['y_two']

	plot = figure(
		x_range=(x_one, x_two), 
		y_range=(y_one, y_two), 
		x_axis_label='Scaled Total Posts',
		y_axis_label='Scaled Engagement Rate',
		sizing_mode='scale_width',
		tools='',
		toolbar_location=None
	)

	plot.yaxis.axis_label_text_font_size = '16px'
	plot.xaxis.axis_label_text_font_size = '16px'
	plot.yaxis.major_label_text_font_size = '14px'
	plot.xaxis.major_label_text_font_size = '14px'
	plot.xaxis.axis_label_standoff = 16;
	plot.yaxis.axis_label_standoff = 16;
	plot.xaxis.axis_label_text_font_style = "bold"
	plot.yaxis.axis_label_text_font_style = "bold"

	plot.title.text = 'Engagement Rate Per User'
	plot.title.align = 'center'
	plot.title.text_font_size = '20px'
	plot.title.render_mode = 'css'

	''' ############ PLOT TWO ############ '''
	plot_two = figure(
		y_range=(y_one, y_two), 
		x_axis_label='Date', 
		y_axis_label='Engagement',
		sizing_mode='scale_width',
		tools='',
		toolbar_location=None
	)

	plot_two.yaxis.axis_label_text_font_size = '16px'
	plot_two.xaxis.axis_label_text_font_size = '16px'
	plot_two.yaxis.major_label_text_font_size = '14px'
	plot_two.xaxis.major_label_text_font_size = '14px'
	plot_two.xaxis.axis_label_standoff = 16;
	plot_two.yaxis.axis_label_standoff = 16;
	plot_two.xaxis.axis_label_text_font_style = "bold"
	plot_two.yaxis.axis_label_text_font_style = "bold"
	
	plot_two.title.text = 'Tapped Engagement Rate Vs. Time'
	plot_two.title.align = 'center'
	plot_two.title.text_font_size = '20px'
	plot_two.title.render_mode = 'css'

	plot_two.xaxis.major_label_overrides = dict(enumerate(days))
	
	''' ############ ADD BACKGROUND TEXT ############ '''
	text_source = ColumnDataSource({'days': ['%s' % days[0]]}) 

	y_position = (y_two - y_one)/2 + y_one - 0.5
	x_position = (x_two - x_one)/2 + x_one - 1.75

	text = Text(
		x=x_position, 
		y=y_position, 
		text='days', 
		text_font_size='50pt', 
		text_color='#EEEEEE'
	)
					
	plot.add_glyph(text_source, text)

	''' ############ ADD CIRCLE & LINE GLYPHS WITH LEGEND ############ '''
	days_indices = list(range(len(days)))
	renderer_source = engagement_sources['_0']

	circle_glyph = Circle(
		x='posts', 
		y=engagement_column, 
		radius='followers-scaled',
		fill_color='colors', 
		fill_alpha=0.5,
		line_color='#7c7e71', 
		line_width=0.2,
		line_alpha=0.6
	)

	cir = plot.circle(
		x="posts", 
		y=engagement_column, 
		radius='followers-scaled', 
		fill_color='colors', 
		line_color='black', 
		fill_alpha=0.6, 
		source=renderer_source, 
		legend='groups'
	)

	circle_renderer = plot.add_glyph(renderer_source, circle_glyph)

	lines = plot_two.line(
		x='index', 
		y='engagement', 
		line_width=4, 
		line_alpha=0.85, 
		source=user_sources_engagement['hanood.1']
	)

	plot.legend.border_line_color = "black"
	plot.legend.location = "bottom_right"
	
	''' ############ HOVER & TAP TOOL ############ '''
	hovertool = HoverTool(
		tooltips=[
			("Account", "@index"),
			("Followers", "@followers")
		], 
		renderers=[circle_renderer]
	)
	plot.add_tools(hovertool);


	hover = HoverTool(tooltips = [
		("Day", "@index"),
		("Engagement", "@engagement")
	])
	plot_two.add_tools(hover);


	tap_code = '''if (cb_data.source.selected.indices.length > 0){
				selected_index = cb_data.source.selected.indices[0];

				var data = cb_data.source.data;
				var name = data['index'][selected_index];
				var data2 = sources2[name].data;

				lines.data_source.data['engagement'] = data2['engagement']
				lines.data_source.data['index'] = data2['index']
				lines.data_source.change.emit(); 
			  }'''

	tap_tool_callback = CustomJS(
		args={
			'sources':engagement_sources, 
			'sources2':user_sources_engagement, 
			'lines':lines
		}, 
		code=tap_code
	)

	taptool = TapTool(callback = tap_tool_callback)
	plot.add_tools(taptool)


	''' ############ ADD SLIDER ############ '''
	code = """
		var day = slider.value,
			sources = %s,
			new_source_data = sources[day].data;
		renderer_source.data = new_source_data;
		text = new_source_data['days'][0];    
		text_source.data = {'days':[text]};
	""" % js_source_array_engagement

	callback = CustomJS(args=engagement_sources, code=code)
	
	slider = Slider(
		start=days_indices[0], 
		end=days_indices[-1], 
		value=0, 
		step=1, 
		title="Day", 
		callback=callback
	)

	callback.args["renderer_source"] = renderer_source
	callback.args["slider"] = slider
	callback.args["text_source"] = text_source

	layout_left = layout([[plot], [slider]], sizing_mode='scale_width', spacing=16, margin=32)
	layout_right = layout([[plot_two]], sizing_mode='scale_width', margin=32)

	plots = GridBox(children=[[layout_left, 1, 1], [layout_right, 1, 2]], margin=16)

	return plots


def main(engagement_column_list):
	'''
	this function ties everything together, taking in a list of interested metrics to use
	
	metrics include: likes, watches, comments
	'''
	tabs = []
	
	for engagement_column in engagement_column_list:
		engagement, followers, posts, groups, days, all_groups, days_indices = read_all_dfs(engagement_column)

		engagement_sources = create_source_dict(engagement, followers, posts, groups, days, days_indices, engagement_column)
		user_sources_engagement = create_user_source(engagement, days)

		js_source_array_engagement = sources_to_js(engagement_sources, days_indices)

		viz = create_plot(engagement, posts, days, engagement_sources, 
						  user_sources_engagement, engagement_column, js_source_array_engagement)
		
		tab = Panel(child=viz, title=engagement_column.capitalize())
		
		tabs.append(tab)

	tabs = Tabs(tabs=tabs)
	
	return tabs