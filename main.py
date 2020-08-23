import plotly.graph_objs as go
from plotly.subplots import make_subplots

import pandas as pd
from collections import defaultdict
import os
import utils

from flask import Flask, render_template, request
app = Flask(__name__)

data = pd.read_excel('NYPD-Misconduct-Complaint-Database/CCRB_database_raw.xlsx')

# Remove extra spaces
data['Rank'] = data['Rank'].str.replace(' ', '')
data['Board Disposition'] = data['Board Disposition'].apply(
    lambda text: ' '.join(list(filter(None, text.split(' ')))) if isinstance(text, str) else text)

# Remove unused column
data.drop('AsOfDate', axis = 1, inplace = True)

OUTCOME_LABELS = utils.open_pickle('data/outcome_labels.pkl')
OUTCOME_PARENTS = utils.open_pickle('data/outcome_parents.pkl')

template_files = ['map.html', 'FADO_Types.html', 'outcomes.html', 
                  'timeseries.html', 'Top_Allegations.html', 
                  'Top_Ranks.html']

# If plots not present, generate them
for t in template_files:
    if t not in os.listdir('templates'):
        import generate_plots
        break
    
def get_individual_plots(fname, lname, filename = None):
    cop_data = data[(data['First Name'] == fname) & (data['Last Name'] == lname)]
    
    fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"type": "scatter"}, {"type": "pie"}],
           [{"type": "bar"}, {"type": "sunburst"}]], 
    subplot_titles = ("Allegation History", "FADO Types", "Top Allegations", "Outcomes")
    )
    
    scatter_trace = utils.get_timeseries_plot(cop_data, 'Incident Date', 'Unique Id', return_trace = True)
    pie_trace = utils.get_pie_counts(cop_data, 'FADO Type', 'Unique Id', return_trace = True)
    bar_trace = utils.get_hbar_plot(cop_data, 'Allegation', 'Unique Id', return_trace = True)
    
    cop_outcomes_df = cop_data['Board Disposition'].value_counts().reset_index().rename(
        columns = {'index': 'Disposition', 'Board Disposition': 'count'})
    
    cop_outcomes_df = utils.add_newlines(cop_outcomes_df)
    
    cop_outcomes = cop_outcomes_df.set_index('Disposition')['count'].to_dict()
    cop_outcomes = defaultdict(int, cop_outcomes)
    
    cop_outcomes['Allegations'] = len(cop_data)
    cop_outcomes['Unknown'] = cop_data['Board Disposition'].isna().sum()
    cop_outcomes['Sustained'] = utils.get_sustained_count(cop_outcomes_df)
    cop_outcomes['Unsustained'] = utils.get_unsustained_count(cop_outcomes_df)
    
    values = [cop_outcomes[l] for l in OUTCOME_LABELS]
    sunburst_trace = utils.get_suburst_plot(OUTCOME_LABELS, OUTCOME_PARENTS, values, return_trace = True)
    
    fig.add_trace(scatter_trace, row = 1, col = 1)
    fig.add_trace(pie_trace, row = 1, col = 2)
    fig.add_trace(bar_trace, row = 2, col = 1)
    fig.add_trace(sunburst_trace, row = 2, col = 2)
    
    fig.update_layout(height = 1000, width = 1000)
    
    if filename is not None:
        fig.write(filename)
    else:
        fig.show()

@app.route('/')
@app.route('/home')
@app.route('/index.html')
def plots():
    return render_template('index.html')

#@app.route('/search')
#@app.route('/search.html')
#def search():
    

@app.route('/map.html')
@app.route('/map')
def nymap():
    return render_template('map.html')

@app.route('/outcomes')
@app.route('/outcomes.html')
def outcomes():
    return render_template('outcomes.html')

@app.route('/timeseries')
@app.route('/timeseries.html')
def timeseries():
    return render_template('timeseries.html')

@app.route('/Top_Allegations')
@app.route('/top_allegations')
@app.route('/top_allegations.html')
@app.route('/Top_Allegations.html')
def top_allegations():
    return render_template('Top_Allegations.html')

@app.route('/Top_Ranks')
@app.route('/top_ranks')
@app.route('/top_ranks.html')
@app.route('/Top_Ranks.html')
def top_ranks():
    return render_template('Top_Ranks.html')

@app.route('/FADO_Types')
@app.route('/fado_types')
@app.route('/fado_types.html')
@app.route('/FADO_Types.html')
def fado_types():
    return render_template('FADO_Types.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug = True)