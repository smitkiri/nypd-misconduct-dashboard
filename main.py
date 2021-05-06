from plotly.subplots import make_subplots

import pandas as pd
import os
import utils
import lightgbm as lgb
import numpy as np
import math
from google.cloud import storage

from flask import Flask, render_template, request
app = Flask(__name__)

CLOUD_STORAGE_BUCKET = os.environ['NYPAB_BUCKET']
gcs = storage.Client()
bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)

'''Prediction Files Here'''
model = lgb.Booster(model_file='data/lgb_classifier.txt')
scalar = utils.open_pickle('data/scalar1.pkl')


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


data = pd.read_csv('https://raw.githubusercontent.com/new-york-civil-liberties-union/NYPD-Misconduct-Complaint-Database-Updated/main/CCRB%20Complaint%20Database%20Raw%2004.20.2021.csv')

# Remove extra spaces
data['IncidentRankLong'] = data['IncidentRankLong'].str.replace(' ', '')
data['CCRBDisposition'] = data['CCRBDisposition'].apply(
    lambda text: ' '.join(list(filter(None, text.split(' ')))) if isinstance(text, str) else text)

# Remove unused column
data.drop('AsOfDate', axis = 1, inplace = True)

# Add a full name column
data['id'] = (data['FirstName'] + data['LastName']).str.lower()
data['FirstName'] = data['FirstName'] + ' ' + data['LastName']
data = data.rename(columns = {'FirstName': 'Name'})
data.drop('LastName', axis = 1, inplace = True)


OUTCOME_LABELS = utils.open_pickle('data/outcome_labels.pkl')
OUTCOME_PARENTS = utils.open_pickle('data/outcome_parents.pkl')
SUSTAINED = utils.open_pickle('data/sustained_list.pkl')
UNSUSTAINED = utils.open_pickle('data/unsustained_list.pkl')

template_files = ['map.html', 'FADO_Types.html', 'outcomes.html', 
                  'timeseries.html', 'Top_Allegations.html', 
                  'Top_Ranks.html']
    
def get_individual_plots(cop_data, filename = None):    
    fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"type": "scatter"}, {"type": "pie"}],
           [{"type": "bar"}, {"type": "sunburst"}]], 
    subplot_titles = ("Allegation History", "FADO Types", "Top Allegations", "Outcomes")
    )
    
    scatter_trace = utils.get_timeseries_plot(cop_data[~cop_data['IncidentDate'].isnull()], 'IncidentDate', 'Unique Id', return_trace = True)
    pie_trace = utils.get_pie_counts(cop_data, 'FADOType', 'AllegationID', return_trace = True)
    bar_trace = utils.get_hbar_plot(cop_data, 'Allegation', 'AllegationID', return_trace = True)
    
    cop_outcomes_df = cop_data['CCRBDisposition'].value_counts().reset_index().rename(
        columns = {'index': 'Disposition', 'CCRBDisposition': 'count'})
    
    cop_outcomes_df = utils.add_newlines(cop_outcomes_df)
    
    cop_outcomes = cop_outcomes_df.set_index('Disposition')['count'].to_dict()
    
    cop_outcomes['Allegations'] = len(cop_data)
    
    unknown_cnt = cop_data['CCRBDisposition'].isna().sum()
    if unknown_cnt != 0:
        cop_outcomes['Unknown'] = unknown_cnt
    
    sus_cnt = utils.get_sustained_count(cop_outcomes_df, SUSTAINED)
    if sus_cnt != 0:
        cop_outcomes['Sustained'] = sus_cnt
        
    uns_cnt = utils.get_unsustained_count(cop_outcomes_df, SUSTAINED)
    if uns_cnt != 0:
        cop_outcomes['Unsustained'] = uns_cnt
    
    labels = []
    parents = []
    for idx, l in enumerate(OUTCOME_LABELS):
        if l in cop_outcomes.keys():
            labels.append(l)
            parents.append(OUTCOME_PARENTS[idx])
        
    values = [cop_outcomes[l] for l in labels]
    sunburst_trace = utils.get_suburst_plot(labels, parents, values, return_trace = True)
    
    fig.add_trace(scatter_trace, row = 1, col = 1)
    fig.add_trace(pie_trace, row = 1, col = 2)
    fig.add_trace(bar_trace, row = 2, col = 1)
    fig.add_trace(sunburst_trace, row = 2, col = 2)
    
    fig.update_layout(height = 1000, width = 1000)
    
    if filename is not None:
        filepath = '/tmp/' + filename
        fig.write_html(filepath, include_plotlyjs = 'cdn')
        blob = bucket.blob(filename)
        blob.upload_from_filename(filepath)
        blob.make_public()
        return blob.public_url
    else:
        fig.show()
        
def add_hyperlink(x):
    link = ''.join(x.split(' ')).lower()
    return '<a href="/search/' + link + '">'+ x +'</a>'

@app.route('/')
@app.route('/home')
@app.route('/index.html')
def plots():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
@app.route('/search.html', methods=['GET', 'POST'])
def search():
    if request.method == "GET":
        return render_template('search.html')
    
    if request.method == "POST":
        name = request.form['name']
        name = name.lower()
        
        subset = data[data['Name'].str.lower().str.contains(name, na = False)]
        subset = subset.reset_index(drop = True)
        
        if len(subset) == 0:
            html_snippet = '<p class = "text-danger" style = "font-size = 17px;">'
            html_snippet += 'No results found!</p>'
            return render_template('search.html', data = html_snippet)
        
        subset['Name'] = subset['Name'].apply(add_hyperlink)
        subset = subset.drop('id', axis = 1)
        html_snippet = subset.to_html().replace('&lt;', '<').replace('&gt;', '>')
        return render_template('search.html', data = html_snippet)

@app.route('/search/<cop_id>')
def police_details(cop_id):
    subset = data[data['id'] == cop_id]
    url = get_individual_plots(subset, filename = cop_id+'.html')
    return render_template('police_details.html', name = list(set(subset['Name']))[0], 
                           url = url)


@app.route('/prediction', methods=['GET', 'POST'])
@app.route('/predict', methods=['GET', 'POST'])
def prediction():
    final_prediction = ''
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

@app.route('/about')
def about():
    return render_template('about.html')

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