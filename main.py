
# coding: utf-8

# In[10]:


import pandas as pd
from os.path import dirname, join

import geopandas as gpd
import fiona
import numpy as np
from bokeh.io import show, output_file, curdoc, output_notebook, push_notebook
from bokeh.layouts import gridplot, layout,column
from bokeh.models import ColumnDataSource,HoverTool,LogColorMapper,Label, LabelSet
from bokeh.models.widgets import TextInput, Tabs
from bokeh.palettes import Reds6 as palette
from bokeh.plotting import figure,save
from bokeh.resources import CDN
from shapely.geometry import Polygon,Point,MultiPoint,MultiPolygon
from shapely.prepared import prep

from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application



df=pd.read_csv(join(dirname(__file__),'data','df.csv'))
df_st=pd.read_csv(join(dirname(__file__),'data','df_st.csv'))
df_name_st=pd.read_csv(join(dirname(__file__),'data','df_st_name.csv'))
df_name_sex=pd.read_csv(join(dirname(__file__),'data','df_name_sex.csv'))
st=gpd.read_file(join(dirname(__file__),'data','states.shp'))
#st=gpd.read_file('R:/R&D/NameTable/vis_app/data/states.shp')
st2=st.explode()
EXCLUDED=['Hawaii','Alaska']
st3=st2[~st2['STATE_NAME'].isin(EXCLUDED)]


def show_overall_stats(name):
    d1=df_name_sex[df_name_sex.name==name]
    M_pct=d1[d1.sex=='M']['pct'].values*0.01
    M_ct=d1[d1.sex=='M']['freq'].values
    F_ct=d1[d1.sex=='F']['freq'].values
    if M_pct.size==0:
        F_pct=np.array([1])
        M_pct=np.array([0.0])
        M_ct=np.array([0])
    F_pct=d1[d1.sex=='F']['pct'].values*0.01
    if F_pct.size==0:
        F_ct=np.array([0])
        F_pct=np.array([0.0])
        M_pct=np.array([1])
    source = ColumnDataSource(data=dict(
            bname=[name,],
            M_count=M_ct,
            F_count=F_ct,
            M_pct=M_pct,    
            F_pct=F_pct))
    return source
	


def show_name_hist(name):
	df_name=df[df.name==name]
	df_name_yr_sex=df_name.groupby(['yr','sex']).agg({'freq':np.sum})
	df_name_yr_sex['pct']=df_name_yr_sex.groupby(level=0)['freq'].apply(lambda x: 100*x/float(x.sum()))
	df_name_yr_sex_freq=df_name_yr_sex.unstack(level=1).fillna(0)['freq'].reset_index()
	df_name_yr_sex_pct=df_name_yr_sex.unstack(level=1).fillna(0)['pct'].reset_index()
	if not 'M' in df_name_yr_sex_freq.columns:
		df_name_yr_sex_freq['M']=0
		df_name_yr_sex_pct['M']=0.0
	if not 'F' in df_name_yr_sex_freq.columns:
		df_name_yr_sex_freq['F']=0
		df_name_yr_sex_pct['F']=0.0
		
	source = ColumnDataSource(data=dict(
            year=df_name_yr_sex_freq.yr,
            M_count=df_name_yr_sex_freq.M,
            F_count=df_name_yr_sex_freq.F,
            M_pct=df_name_yr_sex_pct.M,    
            F_pct=df_name_yr_sex_pct.F    
            ))
	return source



    
def show_name_by_st(name):	
	df_show=df_name_st[(df_name_st.name==name)].pivot(index='st',columns='sex',values='freq').reset_index()
	if not 'F' in df_show.columns:
		df_show['F']=np.nan
	if not 'M' in df_show.columns:
		df_show['M']=np.nan
	df_show=df_show.merge(df_st,on='st')	
	df_show['M_pct']=df_show['M']/df_show['total_freq']
	df_show['F_pct']=df_show['F']/df_show['total_freq']
	
	st4=pd.merge(st3,df_show,left_on='STATE_ABBR',right_on='st',how='left')
	state_name=st4['STATE_NAME']
	M_pct=st4['M_pct']
	F_pct=st4['F_pct']
	M_ct=st4['M']
	F_ct=st4['F']
	state_x=[[x[0] for x in feat.exterior.coords] for feat in st4.geometry]
	state_y=[[x[1] for x in feat.exterior.coords] for feat in st4.geometry]
	custom_colors = ['#f2f2f2', '#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26']
	color_mapper = LogColorMapper(palette=custom_colors)
	source = ColumnDataSource(data=dict(
        x=state_x, y=state_y,
        name=state_name,
        M_rate=M_pct,
        F_rate=F_pct,
        M_count=M_ct,
        F_count=F_ct
        ))
	return source
        
def vis_overall_stats(src0):
	s=figure(plot_width=500,plot_height=200)
	s.hbar(left=0,  right='M_pct', y=0,height=1, color='navy', name='Male',legend='M',source=src0)
	s.hbar(left='M_pct', right=1, y=0, height=1, color='firebrick',  name='Female',legend='F',source=src0)
	s.title.text = 'Overall stats'
	hover=HoverTool(tooltips=[('Name','@bname'),('Male Counts','@M_count'),('Female Counts','@F_count'),('Male Percent','@M_pct{%0.2f%%}'),('Female Percent','@F_pct{%0.2f%%}')])
	s.add_tools(hover)
    #mytext0 = LabelSet(x=15, y=0.2, text='Overall for name "%s":'%('bname'), 
                   #source=src0, text_color='white', text_font_size='16pt')
    #mytext1 = Label(x=15, y=0, text='%.2f%% male %.2f%% female'%('@M_pct','@F_pct'), 
                   #text_color='white', text_font_size='16pt')
    #mytext2 = Label(x=15, y=-0.2, text='%d male %d female '%('@M_count','@F_count'), 
                   #text_color='white', text_font_size='16pt')
    #s.add_layout(mytext0)
    #s.add_layout(mytext1)
    #s.add_layout(mytext2)
	return s

  

def vis_name_hist(src1):
    TOOLS='pan,wheel_zoom,reset,hover,save'
    s1=figure(plot_width=500, plot_height=200,tools=TOOLS)
    s1.title.text = 'Gender counts over the years'
    xs=['year','year']
    ys=['F_count','M_count']
    color_list=['firebrick','navy']
    legend_list=['F','M']

    for x,y,color,legend in zip(xs,ys,color_list,legend_list):
        s1.scatter(x, y, size=10, color=color, legend=legend,source=src1)
    s1.legend.location = "top_right"
    hover=s1.select_one(HoverTool)
    hover.mode='vline'
    hover.tooltips=[('year','@year'),('Female counts','@F_count'),('Male counts','@M_count')]

    s2=figure(plot_width=500, plot_height=200,tools=TOOLS)
    s2.title.text = 'Gender percentage over the years'
    xs=['year','year']
    ys=['F_pct','M_pct']
    color_list=['firebrick','navy']
    legend_list=['F','M']

    for x,y,color,legend in zip(xs,ys,color_list,legend_list):
        s2.scatter(x, y, size=10, color=color, legend=legend,alpha=0.8,source=src1)
    s2.legend.location = "top_right"
    hover=s2.select_one(HoverTool)
    hover.mode='vline'
    hover.tooltips=[('year','@year'),('Female percent','@F_pct'),('Male percent','@M_pct')]

    return column(s1,s2)
    


	
def vis_st_map(src2):
    TOOLS='pan,wheel_zoom,reset,hover,save'
    custom_colors = ['#f2f2f2', '#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26']
    color_mapper = LogColorMapper(palette=custom_colors) 
    p1=figure(plot_width=500,plot_height=300,
            tools=TOOLS, x_axis_location=None, y_axis_location=None)
    p1.grid.grid_line_color=None
    p1.title.text = 'as a female name'
    p1.patches('x','y',source=src2,
          fill_color={'field':'F_rate','transform':color_mapper},
          fill_alpha=0.8,line_color='black',line_width=0.3)
    hover=p1.select_one(HoverTool)
    hover.point_policy='follow_mouse'
    hover.tooltips=[('State','@name'),('Penetration within state','@F_rate{000.0000%}'),('Total counts','@F_count'),('(Long,Lat)','($x,$y)')]
    custom_colors = ['#CCE5FF', '#99CCFF', '#66B2FF', '#3399FF', '#0066CC', '#003366']
    color_mapper = LogColorMapper(palette=custom_colors)
    p2=figure(plot_width=500,plot_height=300,
            tools=TOOLS, x_axis_location=None, y_axis_location=None)
    p2.grid.grid_line_color=None
    p2.title.text = 'as a male name'
    p2.patches('x','y',source=src2,
          fill_color={'field':'M_rate','transform':color_mapper},
          fill_alpha=0.8,line_color='black',line_width=0.3)
    hover=p2.select_one(HoverTool)
    hover.point_policy='follow_mouse'
    hover.tooltips=[('State','@name'),('Penetration within state','@M_rate{000.0000%}'),('Total counts','@M_count'),('(Long,Lat)','($x,$y)')]
    return column(p1,p2)
        
        

def callback(attr,old,new):
	name1=text_input.value
	src0.data.update(show_overall_stats(text_input.value).data)
	src1.data.update(show_name_hist(text_input.value).data)
	src2.data.update(show_name_by_st(text_input.value).data)
		
initial_name='Jian'       
text_input=TextInput(value=initial_name,title='Type the name here:') 
text_input.on_change('value',callback)

src0=show_overall_stats(initial_name)
src1=show_name_hist(initial_name)
src2=show_name_by_st(initial_name)
s=vis_overall_stats(src0)  
c1=vis_name_hist(src1)
c2=vis_st_map(src2)
grid=gridplot([column(text_input,s,c1),c2],ncols=2)


curdoc().add_root(grid)
	







