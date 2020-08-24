import pandas as pd
import pickle

import plotly.graph_objs as go

def get_command(x, command_key):
    try:
        command = command_key[x]
    except:
        command = float('nan')
    return command

def get_command_key():
    #Get command abbreviations
    command_df = pd.read_excel('NYPD-Misconduct-Complaint-Database/CCRB_filespecs.xlsx', 
                                sheet_name = 'Tab3_Command Key')
    command_df['Command Abrev.'] = command_df['Command Abrev.'].apply(lambda x: ''.join(x.split(' ')).lower())
    
    return command_df.set_index(command_df['Command Abrev.'])['Command'].to_dict()

def get_rank_key():
    # Get rank abbreviations
    return pd.read_excel('data/CCRB Data Layout Table.xlsx', sheet_name = 'Rank Abbrevs').set_index('Abbreviation')['Rank'].to_dict()

def get_sustained_list(outcomes):
    return outcomes[outcomes['Disposition'].str.contains('Substantiated')]['Disposition'].apply(
            lambda x: ' '.join(x.replace('(', '').replace(')', '').split(' ')[1:]))

def get_unsustained_list(outcomes, sustained_list):
    return outcomes[~outcomes['Disposition'].str.contains('|'.join(list(sustained_list)))]['Disposition']

def get_sustained_count(outcomes_df, sustained_list):
    return outcomes_df[outcomes_df['Disposition'].str.contains('|'.join(list(sustained_list)))]['count'].sum()

def get_unsustained_count(outcomes_df, sustained_list):
    return outcomes_df[~outcomes_df['Disposition'].str.contains('|'.join(list(sustained_list)))]['count'].sum()

def add_newlines(outcomes_df):
    outcomes_df['Disposition'] = outcomes_df['Disposition'].apply(
        lambda x: 'Complainant <br> Uncooperative' if x == 'Complainant Uncooperative' else x)

    outcomes_df['Disposition'] = outcomes_df['Disposition'].apply(
        lambda x: 'Complaint <br> Withdrawn' if x == 'Complaint Withdrawn' else x)

    outcomes_df['Disposition'] = outcomes_df['Disposition'].apply(
        lambda x: 'Complainant <br> Unavailable' if x == 'Complainant Unavailable' else x)
    
    return outcomes_df

def open_pickle(file):
    with open(file, 'rb') as f:
        return pickle.load(f)

def save_pickle(file, variable):    
    with open(file, 'wb') as f:
        pickle.dump(variable, f)
        

def get_timeseries_plot(df, date_col, count_col, freq = "M", return_trace = False, filename = None):
    counts = df.set_index(date_col).groupby(pd.Grouper(freq = freq)).count()[count_col]
    counts = counts[counts.index.year > 1985]
    
    total_trace = go.Scatter(x = counts.index, y = counts, hovertemplate = '%{x}: %{y}<extra></extra>', name = "Total allegations")
    
    if return_trace:
        return total_trace
    
    fig = go.Figure(data = total_trace)
    
    for typ in list(set(df['FADO Type'])):
        counts = df[df['FADO Type'] == typ].set_index(date_col).groupby(pd.Grouper(freq = freq)).count()[count_col]
        counts = counts[counts.index.year > 1985]
        trace = go.Scatter(x = counts.index, y = counts, hovertemplate = '%{x}: %{y}<extra></extra>', name = typ)
        fig.add_trace(trace)    
    
    fig.update_layout(template = 'plotly_white', 
                      margin = dict(t = 1, b = 0, r = 0, l = 0))
    
    if filename is not None:
        fig.write_html(filename, include_plotlyjs = 'cdn')
    else:
        fig.show()
    
def get_pie_counts(df, group_col, count_col, hole = None, return_trace = False, filename = None):
    counts = df.groupby(group_col).count()[count_col]
    trace = go.Pie(labels = counts.index, values = counts, hole = hole)
    fig = go.Figure(data = [trace])
    
    if return_trace:
        return trace
    
    if filename is not None:
        fig.write_html(filename, include_plotlyjs = 'cdn')
    else:
        fig.show()
    
def get_hbar_plot(df, group_col, count_col, desc_key = None, top_n = 5, return_trace = False, filename = None):
    counts = df.groupby(group_col).count()[count_col].reset_index()
    
    if desc_key is not None:
        counts[group_col] = counts[group_col].apply(lambda x: desc_key[x] if x in desc_key.keys() else x)
    
    counts = counts.groupby(group_col).sum()[count_col]
    top = counts.sort_values().iloc[-top_n:]
    
    trace = go.Bar(x = top, y = top.index, orientation = 'h', showlegend = False,
                   hovertemplate = '%{x}<extra></extra>', marker_color='rgb(55, 83, 109)')
    fig = go.Figure(trace)
    
    if return_trace:
        return trace
    
    if filename is not None:
        fig.write_html(filename, include_plotlyjs = 'cdn')
    else:  
        fig.show()
    
def get_suburst_plot(labels, parents, values, return_trace = False, filename = None):
    trace = go.Sunburst(labels = labels, parents = parents, values = values, branchvalues = "total", 
                        marker = dict(colorscale='Emrld'))
    if return_trace:
        return trace

    fig = go.Figure(trace)
    fig.update_layout(margin = dict(t = 0, b = 0, r = 0, l = 0))
    
    if filename is not None:
        fig.write_html(filename, include_plotlyjs = 'cdn')
    else:
        fig.show()
    
