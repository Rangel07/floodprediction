#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys
sys.path.insert(1, '../../Pipeline')

import imp
import utils
imp.reload(utils)
from utils import *
from datetime import timedelta


# In[ ]:


import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ip = pd.read_csv('../../../data/cleandata/Info pluviometricas/Merged Data/merged.csv',
                 sep = ';',
                 dtype = {'Local_0': object, 'Local_1':object,
                          'Local_2':object,  'Local_3':object})
ip.head(2)


# ### Select Precipitacao Columns

# In[ ]:


precipitacao_cols =  [c for c in ip.columns if 'Precipitacao' in c ]
local_cols =  [c for c in ip.columns if 'Local' in c ]
df_p = ip[ ['Data_Hora'] + local_cols + precipitacao_cols].copy()
df_p.loc[:, 'Data_Hora'] = pd.to_datetime(df_p.loc[:,'Data_Hora'], yearfirst=True)


# ### Trying different mothods to find error regions

# In[ ]:


# import plotly as py
# from plotly import graph_objects as go

# py.offline.init_notebook_mode()

# fig = go.Figure()

# ano = 2013

# ip_ano = df_p[df_p['Data_Hora'].dt.year == ano]

# for col in precipitacao_cols:
#     fig.add_trace(go.Scatter(
#         x = ip_ano['Data_Hora'],
#         y = ip_ano[col].fillna(0),
#         name = col,
#         connectgaps=False
#                             )
#                  )
    
# fig.show()


# In[ ]:


# def Euclidean_Dist(df, col1, col2):
#     return np.linalg.norm(df[[col1]].values - df[[col2]].values, axis = 1)

# df_p = df_p.fillna(0)
# precipitacao_cols = set(precipitacao_cols)
# dist = {}
# for  col1 in precipitacao_cols:
#     remaining_cols = precipitacao_cols.copy()
#     remaining_cols.remove(col1)
#     cum = 0
#     for i, col2 in enumerate(remaining_cols):
#         cum += Euclidean_Dist(df_p, col1, col2)
#     df_p[col1+'euclidian_d'] = cum / i


# In[ ]:


# import plotly as py
# from plotly import graph_objects as go
# from plotly.subplots import make_subplots

# py.offline.init_notebook_mode()


# fig = make_subplots(2,1, shared_xaxes=True )

# ano = 2013

# ip_ano = df_p[df_p['Data_Hora'].dt.year == ano].fillna(0)

# for col in precipitacao_cols:
#     fig.add_trace(go.Scatter(
#         x = ip_ano['Data_Hora'],
#         y = ip_ano[col],
#         name = col,
#         connectgaps=False
#                             ),
#                   row = 1, col = 1
#                  )
    
# for col in precipitacao_cols:
#     fig.add_trace(go.Scatter(
#         x = ip_ano['Data_Hora'],
#         y = ip_ano[col+'euclidian_d'],
#         name = col,
#         connectgaps=False
#                             ),
#                   row = 2, col = 1
#                  )
# fig.show()


# In[ ]:


# def std_distance(df, col1, remaining_cols):
#     median =  df[remaining_cols].median(axis = 1)
#     std =  df[remaining_cols].std(axis = 1)
#     mask = df[remaining_cols].std(axis = 1) == 0
#     return np.abs((median - df[col1])/ std)

# df_p = df_p.fillna(0)
# precipitacao_cols = set(precipitacao_cols)
# for  col1 in precipitacao_cols:
#     remaining_cols = precipitacao_cols.copy()
#     remaining_cols.remove(col1)
#     df_p[col1 + '_mad'] = std_distance(df_p, col1, remaining_cols)


# In[ ]:


# import plotly as py
# from plotly import graph_objects as go
# from plotly.subplots import make_subplots

# py.offline.init_notebook_mode()


# fig = make_subplots(2,1, shared_xaxes=True )

# ano = 2019

# ip_ano = df_p[df_p['Data_Hora'].dt.year == ano].fillna(0)
# color = ['#c62828', '#283593', '#00685b', '#f9a825', '#009688']

# for i, col in enumerate(precipitacao_cols):
#     fig.add_trace(go.Scatter(
#         x = ip_ano['Data_Hora'],
#         y = ip_ano[col].fillna(0),
#         name = col,
#         legendgroup=col,
#         line = dict(color=color[i]),
#         connectgaps=False),
#                   row = 1, col = 1
#                  )
    
#     fig.add_trace(go.Scatter(
#         x = ip_ano['Data_Hora'],
#         y = ip_ano[col+'_mad'].fillna(0),
#         legendgroup=col,
#         name = col,
#         line = dict(color=color[i]),
#         showlegend = False,
#         connectgaps=False
#                             ),
#                   row = 2, col = 1
#                  )
# fig.show()


# In[ ]:


# import plotly as py
# from plotly import graph_objects as go
# from plotly.subplots import make_subplots

# py.offline.init_notebook_mode()
# fig = make_subplots(5,1, shared_xaxes=True, shared_yaxes=True )

# ano = 2013
# threshold = 50

# ip_ano = df_p[df_p['Data_Hora'].dt.year == ano].fillna(0)
# color = ['#c62828', '#283593', '#00685b', '#f9a825', '#009688']

# for i, col in enumerate(precipitacao_cols):
#     fig.add_trace(go.Scatter(
#         x = ip_ano['Data_Hora'],
#         y = ip_ano[col].fillna(0),
#         showlegend = False,
#         legendgroup=col,
#         line = dict(color='#616161'),
#         connectgaps=False
#                             ),
#                   row = i + 1, col = 1
#                  )
#     fig.add_trace(go.Scatter(
#         x = ip_ano['Data_Hora'],
#         y = ip_ano[col].fillna(0).where(ip_ano[col+'_mad'] > threshold),
#         name = col,
#         legendgroup=col,
#         showlegend = False,
#         line = dict(color='#c62828', width = 4),
#         connectgaps=False
#                             ),
#                   row = i + 1, col = 1
#                  )
    
# fig.update_layout(height=1200, width=800)
# fig.show()


# ### Using Utils derivative to get error regions

# In[ ]:


start= 280512
stop = 306720

n_days = 15
for col in precipitacao_cols:
    
    # Derivative
    peaks = derivative_threshold(df_p[col], 30, False, start, stop, lw = 2,
                                 figsize = (11, 15))
    # Consecutive Zeros
    zeros = derivative_zero(df_p[col].fillna(0), n_days*24*4, False,
                             plot = False, plt_start = start, plt_stop = stop)
    # Consecutive Constant
    const_not_null = derivative_zero(df_p[col].fillna(0), 8, True,
                             plot = False, plt_start = start, plt_stop = stop)
    # Nans
    is_nan = df_p[col].isna()
    
    error = [zeros[i] or const_not_null[i] or is_nan[i] or peaks[i]
                          for i in range(len(df_p)) ]

    error_reg = list_2_regions(error)
    error_reg = increase_margins(1, error_reg, len(peaks))
    error = regions_2_list(error_reg, len(peaks))
    
    try:
        df_p.insert(df_p.shape[1], col+'_error', error.copy())
    except:
        df_p.drop(columns = [col+'_error'], inplace = True)
        df_p.insert(df_p.shape[1], col+'_error', error.copy())


# ### Plot error regions

# In[ ]:


import plotly as py
from plotly import graph_objects as go
from plotly.subplots import make_subplots

py.offline.init_notebook_mode()
fig = make_subplots(5,1, shared_xaxes=True, shared_yaxes=True )

ano = 2019

ip_ano = df_p[df_p['Data_Hora'].dt.year == ano].fillna(0)
color = ['#c62828', '#283593', '#00685b', '#f9a825', '#009688']

for i, col in enumerate(precipitacao_cols):
    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0),
        showlegend = False,
        legendgroup=col,
        line = dict(color='#616161'),
        connectgaps=False
                            ),
                  row = i + 1, col = 1
                 )
    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0).where(ip_ano[col+'_error']),
        name = col,
        legendgroup=col,
        showlegend = False,
        line = dict(color='#c62828', width = 4),
        connectgaps=False
                            ),
                  row = i + 1, col = 1
                 )
    
fig.update_layout(height=1200, width=800)
fig.show()


# [Comparison of Spatial Interpolation Schemes for Rainfall ](https://www.mdpi.com/2073-4441/9/5/342/pdf)
# 
# [Tutorial](https://gisgeography.com/inverse-distance-weighting-idw-interpolation/)
# 
# $$Z(S_0) = \sum_{i=1}^{N} \lambda_i Z(S_i) $$
# 
# $$\lambda_i = \frac{d_{i0}^{-p}}{\sum_{i=1}^{N} d_{i0}^{-p'}}, \sum_{i=1}^{N} \lambda_i = 1$$

# ### Read Estacao Lat and Lng

# In[ ]:


est = pd.read_csv('../../../data/cleandata/Estacoes/lat_lng_estacoes.csv', sep = ';')
est = est.iloc[:-1, :]
est = est.set_index('Estacao')


# In[ ]:


# Calculate distance between 2 points in km
def Calculate_Dist(lat1, lon1, lat2, lon2):
    r = 6371
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi / 2)**2 + np.cos(phi1) *        np.cos(phi2) * np.sin(delta_lambda / 2)**2
    res = r * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))
    return np.round(res, 2)

# Interpolate based on distance
def interpolate_rain( row ,num ,distances):
   
    rest = [i for i in range(5) if i != num]
    row = row.fillna(0)
    
    aux_num, aux_den = 0,0
    for r in rest:
        
        p = row[f'Precipitacao_{r}']
        local_a = row[f'Local_{num}']
        local_b = row[f'Local_{r}']
        
        d = distances[local_a][local_b]
        
        aux_num += p/d * (not row[f'Precipitacao_{r}_error'])
        aux_den += 1/d * (not row[f'Precipitacao_{r}_error'])
      
    if aux_den == 0:
        return np.nan
    
    return aux_num/aux_den


# ### Calculate distance between every station

# In[ ]:


estacoes = list(est.index)

distances = {k: {} for k in estacoes}  

for estacao in estacoes:
    
    rest = [c for c in est.index if c != estacao]
    for r in rest:
        distances[estacao][r] = Calculate_Dist(*est.loc[estacao,:].to_list(),                                               *est.loc[r,:].to_list())


# ### Apply Interpolate distance - Inverse Distance Weighting

# In[ ]:


for i in range(5):
    print(i+1,'/5 - ',df_p[f'Precipitacao_{i}_error'].sum())
    df_p.loc[df_p[f'Precipitacao_{i}_error'], f'Precipitacao_{i}'] =              df_p[df_p[f'Precipitacao_{i}_error']].apply(interpolate_rain,
                                                         args = (i, distances), axis = 1 ).copy()


# ### See how many left

# In[ ]:


df_p.isna().sum()


# ### Plot Interpolated rain

# In[ ]:


py.offline.init_notebook_mode()
fig = make_subplots(5,1, shared_xaxes=True, shared_yaxes=True )

ano = 2019

ip_ano = df_p[df_p['Data_Hora'].dt.year == ano]
color = ['#c62828', '#283593', '#00685b', '#f9a825', '#009688']

for i, col in enumerate(precipitacao_cols):
    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0),
        showlegend = False,
        legendgroup=col,
        line = dict(color='#616161'),
        connectgaps=False
                            ),
                  row = i + 1, col = 1
                 )
    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0).where(ip_ano[col+'_error']),
        name = col,
        legendgroup=col,
        showlegend = False,
        line = dict(color='#c62828', width = 4),
        connectgaps=False
                            ),
                  row = i + 1, col = 1
                 )
    
fig.update_layout(height=1200, width=800)
fig.show()


# ### Copy rain column to see results after
# 

# In[ ]:


for i in range(5):
    df_p.insert(df_p.shape[1], f'Precipitacao_b4_ow_{i}',
                df_p[f'Precipitacao_{i}'].copy())


# ### Fill remaining based on OpenWeather data

# In[ ]:


def fill_ow( row , num , df_ow):
   
    rounded_hour = row['Data_Hora'].round('H')
    mask = pd.to_datetime(df_ow['Data_Hora']) == rounded_hour
    try:
        return df_ow.loc[mask,'Precipitacao'].item()
    except:
        mask = pd.to_datetime(df_ow['Data_Hora']) == rounded_hour + timedelta(hours=1)
        return df_ow.loc[mask,'Precipitacao'].item()


# ### Import OpenWeather data

# In[ ]:


df_ow = pd.read_csv('../../../data/cleandata/OpenWeather/history_bulk.csv', sep = ';' )
df_ow['Data_Hora'] = pd.to_datetime(df_ow['Data_Hora'], yearfirst = True)
df_ow = df_ow.drop_duplicates(subset = 'Data_Hora' )


# ### Apply fill_ow
# 

# In[ ]:


for i in range(5):
    print(i+1,'/5',)
    df_p.loc[df_p[f'Precipitacao_{i}'].isna(), f'Precipitacao_{i}'] =              df_p[df_p[f'Precipitacao_{i}'].isna()].apply(fill_ow, args = (i, df_ow), axis = 1 )


# ### Check remaining

# In[ ]:


df_p.isna().sum()


# ### Plots Results

# In[ ]:


py.offline.init_notebook_mode()
fig = make_subplots(5,1, shared_xaxes=True, shared_yaxes=True )

ano = 2019

ip_ano = df_p[df_p['Data_Hora'].dt.year == ano]
color = ['#c62828', '#283593', '#00685b', '#f9a825', '#009688']

for i, col in enumerate(precipitacao_cols):
    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0),
        showlegend = False,
        legendgroup=col,
        line = dict(color='#616161'),
        connectgaps=False
                            ),
                  row = i + 1, col = 1
                 )

    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0).where(ip_ano[col+'_error'] &
                                        ~ip_ano[f'Precipitacao_b4_ow_{i}'].isna()),
        name = col,
        legendgroup=col,
        showlegend = False,
        line = dict(color='#c62828', width = 4),
        connectgaps=False
                            ),
                  row = i + 1, col = 1
                 )
    
    fig.add_trace(go.Scatter(
            x = ip_ano['Data_Hora'],
            y = ip_ano[col].where(ip_ano[f'Precipitacao_b4_ow_{i}'].isna()),
            name = col,
            legendgroup=col,
            showlegend = False,
            line = dict(color='#0398fc', width = 4),
            connectgaps=False
                                ),
                      row = i + 1, col = 1
                     )
    
fig.update_layout(height=1200, width=800)
fig.show()


# ## Compare with script

# In[ ]:


repaired = pd.read_csv('../../../data/cleandata/Info pluviometricas/Merged Data/repaired.csv',
                       sep = ';')

regions = pd.read_csv('../../../data/cleandata/Info pluviometricas/Merged Data/error_regions.csv',
                       sep = ';')


# In[ ]:


prep_cols = ['Data_Hora'] + [c for c in regions.columns if  'Precipitacao' in c]
regions = regions.loc[:, prep_cols]
regions['Data_Hora'] = pd.to_datetime(regions['Data_Hora'], yearfirst = True)
regions.head(2)


# In[ ]:


prep_cols = ['Data_Hora'] + [c for c in repaired.columns if  'Precipitacao' in c]
repaired = repaired.loc[:, prep_cols]
repaired['Data_Hora'] = pd.to_datetime(repaired['Data_Hora'], yearfirst = True)
repaired.head(2)


# ## Error Regions

# In[ ]:


py.offline.init_notebook_mode()
fig = make_subplots(5,2, shared_xaxes=True, shared_yaxes=True )

ano = 2013

ip_ano = df_p[df_p['Data_Hora'].dt.year == ano]
rip_ano = regions[regions['Data_Hora'].dt.year == ano]
color = ['#c62828', '#283593', '#00685b', '#f9a825', '#009688']

for i, col in enumerate(precipitacao_cols):
    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0),
        showlegend = False,
        legendgroup=col,
        line = dict(color='#616161'),
        connectgaps=False
                            ),
                  row = i + 1, col = 1
                 )
    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0),
        showlegend = False,
        legendgroup=col,
        line = dict(color='#616161'),
        connectgaps=False
                            ),
                  row = i + 1, col = 2
                 )

    
    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0).where(ip_ano[col+'_error']),
        name = col,
        legendgroup=col,
        showlegend = False,
        line = dict(color='#c62828', width = 4),
        connectgaps=False
                            ),
                  row = i + 1, col = 1
                 )
    fig.add_trace(go.Scatter(
        x = rip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0).where(rip_ano[col+'_error']),
        name = col,
        legendgroup=col,
        showlegend = False,
        line = dict(color='#c62828', width = 4),
        connectgaps = False
                            ),
                  row = i + 1, col = 2
                 )
    
fig.update_layout(height=1200, width=800)
fig.show()


# ## Repaired Data

# In[ ]:


py.offline.init_notebook_mode()
fig = make_subplots(5,2, shared_xaxes=True, shared_yaxes=True )

ano = 2013

ip_ano = df_p[df_p['Data_Hora'].dt.year == ano]
rip_ano = repaired[repaired['Data_Hora'].dt.year == ano]
color = ['#c62828', '#283593', '#00685b', '#f9a825', '#009688']

for i, col in enumerate(precipitacao_cols):
    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0),
        showlegend = False,
        legendgroup=col,
        line = dict(color='#616161'),
        connectgaps=False
                            ),
                  row = i + 1, col = 1
                 )
    fig.add_trace(go.Scatter(
        x = rip_ano['Data_Hora'],
        y = rip_ano[col].fillna(0),
        showlegend = False,
        legendgroup=col,
        line = dict(color='#616161'),
        connectgaps=False
                            ),
                  row = i + 1, col = 2
                 )

    
    fig.add_trace(go.Scatter(
        x = ip_ano['Data_Hora'],
        y = ip_ano[col].fillna(0).where(ip_ano[col+'_error'] &
                                        ~ip_ano[f'Precipitacao_b4_ow_{i}'].isna()),
        name = col,
        legendgroup=col,
        showlegend = False,
        line = dict(color='#c62828', width = 4),
        connectgaps=False
                            ),
                  row = i + 1, col = 1
                 )
    fig.add_trace(go.Scatter(
        x = rip_ano['Data_Hora'],
        y = rip_ano[col].fillna(0).where(rip_ano[col+'_idw']),
        name = col,
        legendgroup=col,
        showlegend = False,
        line = dict(color='#c62828', width = 4),
        connectgaps = False
                            ),
                  row = i + 1, col = 2
                 )
    
    
    fig.add_trace(go.Scatter(
            x = ip_ano['Data_Hora'],
            y = ip_ano[col].where(ip_ano[f'Precipitacao_b4_ow_{i}'].isna()),
            name = col,
            legendgroup=col,
            showlegend = False,
            line = dict(color='#0398fc', width = 4),
            connectgaps=False
                                ),
                      row = i + 1, col = 1
                     )
    fig.add_trace(go.Scatter(
            x = rip_ano['Data_Hora'],
            y = rip_ano[col].where(rip_ano[col + '_fill_ow']),
            name = col,
            legendgroup=col,
            showlegend = False,
            line = dict(color='#0398fc', width = 4),
            connectgaps=False
                                ),
                      row = i + 1, col = 2
                     )
    
fig.update_layout(height=1200, width=800)
fig.show()

