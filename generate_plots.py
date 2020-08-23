import pandas as pd
import plotly.graph_objs as go
import utils

data = pd.read_excel('NYPD-Misconduct-Complaint-Database/CCRB_database_raw.xlsx')

# Remove extra spaces
data['Rank'] = data['Rank'].str.replace(' ', '')
data['Board Disposition'] = data['Board Disposition'].apply(
    lambda text: ' '.join(list(filter(None, text.split(' ')))) if isinstance(text, str) else text)

# Remove unused column
data.drop('AsOfDate', axis = 1, inplace = True)

COMMAND_KEY = utils.get_command_key()
RANK_KEY = utils.get_rank_key()

outcomes = data['Board Disposition'].value_counts().reset_index().rename(
    columns = {'index': 'Disposition', 'Board Disposition': 'count'})

outcomes = outcomes.append({'Disposition': 'Unknown', 'count': data['Board Disposition'].isna().sum()}, 
                            ignore_index = True)

SUSTAINED = utils.get_sustained_list(outcomes)
UNSUSTAINED = utils.get_unsustained_list(outcomes, SUSTAINED)

sustained_count = utils.get_sustained_count(outcomes, SUSTAINED)
unsustained_count = utils.get_unsustained_count(outcomes, SUSTAINED)

outcomes = outcomes.append({'Disposition': 'Allegations', 'count': len(data)}, ignore_index = True)
outcomes = outcomes.append({'Disposition': 'Sustained', 'count': sustained_count}, ignore_index = True)
outcomes = outcomes.append({'Disposition': 'Unsustained', 'count': unsustained_count}, ignore_index = True)

outcomes = outcomes.sort_values('count', ascending = False)
outcomes['Disposition'] = outcomes['Disposition'].apply(lambda x: ' '.join(x.replace('(', '').replace(')', '').split(' ')[1:]) if 'Substantiated' in x else x)

OUTCOME_HIREARCHY = {'Allegations': '', 'Sustained': 'Allegations', 'Unsustained': 'Allegations', 'Unknown': 'Unsustained'}

for s in list(SUSTAINED):
    OUTCOME_HIREARCHY[s] = 'Sustained'
    
for u in list(UNSUSTAINED):
    OUTCOME_HIREARCHY[u] = 'Unsustained'
    
outcomes = utils.add_newlines(outcomes)
OUTCOME_LABELS = list(outcomes['Disposition'])
OUTCOME_PARENTS = [OUTCOME_HIREARCHY[''.join(l.split('<br> '))] for l in OUTCOME_LABELS]
values = list(outcomes['count'])

def generate_map():
    nypd_commands = pd.read_pickle('data/command_locations_df.pkl')
    
    count_by_commands = data.groupby('Command')['Unique Id'].count().reset_index()
    count_by_commands['Command'] = count_by_commands['Command'].apply(lambda x: ''.join(x.split(' ')).lower())
    count_by_commands['Command'] = count_by_commands['Command'].apply(lambda x: utils.get_command(x, COMMAND_KEY))
    count_by_commands = count_by_commands.dropna()
    
    count_by_commands = count_by_commands.rename(columns = {'Unique Id': 'count'})
    count_by_commands = count_by_commands.set_index('Command').join(nypd_commands[['commands', 'lat', 'lng']].set_index('commands'))
    
    total = len(data) 
    sustained_pct = outcomes[outcomes['Disposition'] == 'Sustained']['count'].iloc[0]/len(data)*100
    
    fig = go.Figure(go.Densitymapbox(lat=count_by_commands['lat'], lon=count_by_commands['lng'], colorscale = 'viridis',
                                     z = count_by_commands['count'], radius = 20, showscale = False,
                                     hovertemplate = '%{text}: %{z}<extra></extra>', text = count_by_commands.index))
    
    fig.update_layout(mapbox_style="carto-positron", mapbox_center_lon=-73.77, 
                      mapbox_center_lat = 40.75, mapbox_zoom = 10.6, height = 450,
                      margin = dict(l = 3, r = 3, b = 3, t = 0),
                      annotations = [
                          dict(
                              x = 0.9, 
                              y = 0.661, 
                              showarrow = False, 
                              bordercolor = 'black',
                              text = "NYPD 1986 - 2020",
                              bgcolor = "white", 
                              font = dict(family = "Times New Roman, Helvetica", size = 25),
                              xref = "paper", 
                              yref = "paper", 
                              width = 350, 
                              height = 40), 
                          dict(
                              x = 0.9, 
                              y = 0.5775, 
                              showarrow = False, 
                              text = "{:,d} allegations".format(total), 
                              bordercolor = 'black',
                              bgcolor = "white", 
                              font = dict(family = "Impact, Times New Roman, Helvetica", size = 30), 
                              xref = "paper", 
                              yref = "paper", 
                              width = 350, 
                              height = 40),
                          dict(
                              x = 0.9, 
                              y = 0.489, 
                              showarrow = False, 
                              text = "{:.1f}% disciplined".format(sustained_pct), 
                              bgcolor = "white", 
                              bordercolor = 'black',
                              font = dict(family = "Impact, Times New Roman, Helvetica", size = 30, color = "red"), 
                              xref = "paper", 
                              yref = "paper", 
                              width = 350, 
                              height = 40)]
                     )
    
    config = dict({'scrollZoom': False})
    fig.write_html(file = 'templates/map.html', config = config, include_plotlyjs = 'cdn')

 
utils.save_pickle('data/outcome_labels.pkl', OUTCOME_LABELS)
utils.save_pickle('data/outcome_parents.pkl', OUTCOME_PARENTS)

generate_map()
utils.get_timeseries_plot(data, 'Incident Date', 'Unique Id', 
                          filename = 'templates/timeseries.html')

utils.get_pie_counts(data, 'FADO Type', 'Unique Id', 
                     filename = 'templates/FADO_Types.html')

utils.get_hbar_plot(data, 'Rank', 'Unique Id', RANK_KEY, 
                    filename = 'templates/Top_Ranks.html')

utils.get_hbar_plot(data, 'Allegation', 'Unique Id', top_n = 10, 
                    filename = 'templates/Top_Allegations.html')

utils.get_suburst_plot(OUTCOME_LABELS, OUTCOME_PARENTS, values, 
                       filename = 'templates/outcomes.html')
