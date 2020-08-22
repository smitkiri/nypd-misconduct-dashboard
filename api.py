import flask
import numpy as np
from flask import Flask, request, jsonify, render_template
import lightgbm as lgb
import pickle

app = flask.Flask(__name__)
app.config["DEBUG"] = True

model = lgb.Booster(model_file='./lgb_classifier.txt')
scalar = pickle.load('scalar.pkl')


ethnicity_mapping = {
    'Black': 0,'Asian': 1,'Hispanic': 2,'White': 3,'American Indian': 4,'Refused': 5,'Other Race': 6,'Unknown': 7
}

gender_mapping_complainant = {
    'Male': 0,'Female': 1, 'Not described': 2,'Transwoman (MTF)': 3, 'Transman (FTM)': 4,'Gender non-conforming': 5
}

gender_mapping_mos = {
    'M': 0,'F': 1
}

rank_mapping = {'Police Officer': 0,'Sergeant': 1,'Detective': 2,'Lieutenant': 3,'Captain': 4,'Deputy Inspector': 5,'Inspector': 6,'Chiefs and other ranks': 7
                }

fado_mapping = {'Abuse of Authority': 0,'Force': 1,'Discourtesy': 2,'Offensive Language': 3}

@app.route('/', methods = ['GET', 'POST'])
def m():
    return '<h1>Hi</h1>'

@app.route('/prediction', methods=['POST'])
def prediction():

    rank_incident = request.form['rank_incident']	
    mos_ethnicity = request.form['mos_ethnicity']
    mos_gender = request.form['mos_gender']
    mos_age_incident = request.form['mos_age_incident']	
    complainant_ethnicity = request.form['complainant_ethnicity']
    complainant_gender = request.form['complainant_gender']
    complainant_age_incident = request.form['complainant_age_incident']
    fado_type = request.form['fado_type']
    precinct = request.form['precinct']

    rank_incident = rank_incident.map(rank_mapping)
    fado_type = fado_type.map(fado_mapping)
    mos_gender = mos_gender.map(gender_mapping_mos)
    mos_ethnicity = mos_ethnicity.map(ethnicity_mapping)

    complainant_ethnicity = complainant_ethnicity.map(ethnicity_mapping)
    complainant_gender = complainant_gender.map(gender_mapping_complainant)

    feature_set = np.array([rank_incident, mos_ethnicity, mos_gender, mos_age_incident, complainant_ethnicity, complainant_gender, complainant_age_incident, fado_type, precinct])
    updated_feature_set = scalar.transform(feature_set)

    prediction = np.exp(model.predict(updated_feature_set))




if __name__ == '__main__':
    app.run()