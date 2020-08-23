import plotly.graph_objs as go
from plotly.subplots import make_subplots

import pandas as pd
from collections import defaultdict
import os
import utils

import flask
import numpy as np
from flask import Flask, request, jsonify, render_template
import lightgbm as lgb
import pickle
import math

from flask import Flask, render_template, request
app = Flask(__name__)


'''Prediction Files Here'''
model = lgb.Booster(model_file='./lgb_classifier.txt')
with open('scalar1.pkl', 'rb') as pickle_file:
    scalar = pickle.load(pickle_file)


ethnicity_mapping = {
    'Black or African American': 0,'Asian': 1,'Hispanic or Latinx': 2,'White': 3,'American Indian': 4,'Refused': 5,'Other Race': 6,'Unknown': 7
}

gender_mapping_complainant = {
    'Male': 0,'Female': 1, 'Not described': 2,'TransWoman': 3, 'TransMan': 4,'Gender Non-Conforming': 5
}

gender_mapping_mos = {
    'M': 0,'F': 1
}

rank_mapping = {'Police Officer': 0,'Sergeant': 1,'Detective': 2,'Lieutenant': 3,'Captain': 4,'Deputy Inspector': 5,'Inspector': 6,'Chiefs and other ranks': 7
                }

fado_mapping = {'Abuse of Authority': 0,'Force': 1,'Discourtesy': 2,'Offensive Language': 3}

'''End Here'''

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
def main_page():
    return render_template('index.html')
@app.route('/home')
@app.route('/index.html')
def plots():
    return render_template('index.html')

#@app.route('/search')
#@app.route('/search.html')
#def search():

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    final_prediction = ''

    '''if request.method == "GET":
        return render_template('form.html')'''
    if request.method == "POST":
        rank_incident = request.form['rank_incident']	
        mos_ethnicity = request.form['mos_ethnicity']
        mos_gender = request.form['mos_gender']
        mos_age_incident = request.form['mos_age_incident']	
        complainant_ethnicity = request.form['complainant_ethnicity']
        complainant_gender = request.form['complainant_gender']
        complainant_age_incident = request.form['complainant_age_incident']
        fado_type = request.form['fado_type']
        precinct = request.form['precinct']


        rank_incident = rank_mapping[str(rank_incident)]
        fado_type = fado_mapping[str(fado_type)]
        mos_gender = gender_mapping_mos[str(mos_gender)]
        mos_ethnicity = ethnicity_mapping[str(mos_ethnicity)]

        complainant_ethnicity = ethnicity_mapping[str(complainant_ethnicity)]
        complainant_gender = gender_mapping_complainant[str(complainant_gender)]

        feature_set = [np.array([rank_incident, mos_ethnicity, mos_gender, mos_age_incident, complainant_ethnicity, complainant_gender, complainant_age_incident, fado_type, precinct])]
        updated_feature_set = scalar.transform(feature_set)
        prediction = np.exp(model.predict(updated_feature_set))

        final_prediction = math.ceil(prediction[0])
        print(final_prediction)

    return render_template('form.html', prediction_value= final_prediction)
    

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