#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, fbeta_score

from hyperopt import hp
import hyperopt.pyll
from hyperopt.pyll import scope
from hyperopt import STATUS_OK
from hyperopt import fmin, tpe, Trials

from datetime import datetime

import sys
sys.path.append('../../Pipeline')

from ml_utils import *


# In[ ]:


original_df = pd.read_csv('../../../data/cleandata/Info pluviometricas/Merged Data/repaired.csv', sep = ';')
original_df['Data_Hora'] = pd.to_datetime(original_df['Data_Hora'])
original_df['Date'] = original_df['Data_Hora'].dt.date


# In[ ]:


interest_cols = list({c.split('_')[0] for c in original_df.columns if '_error' in c})
interest_cols.remove('TemperaturaInterna')
interest_cols.remove('SensacaoTermica')


# # Group Stations - Mean 

# In[ ]:


for c in interest_cols:
    original_df[c] = (original_df[c+'_0'] + original_df[c+'_1'] +
                      original_df[c+'_2'] + original_df[c+'_3'] + original_df[c+'_4'])/5 


# ## Plot data

# In[ ]:


df_plot = original_df[original_df.Data_Hora.dt.year == 2015]

fig = go.Figure(layout=dict(template = 'plotly_dark'))

for col in ['PontoDeOrvalho', 'Precipitacao', 'UmidadeRelativa', 'TemperaturaDoAr']:    
    fig.add_trace(go.Scatter(
        x = df_plot['Data_Hora'],
        y = df_plot[col],
        name = col,
                            )
                 )
fig.show()


# # Feature Engineering

# In[ ]:


interest_cols += ['Diff_Temp_POrvalho']
original_df['Diff_Temp_POrvalho'] = original_df['TemperaturaDoAr'] -  original_df['PontoDeOrvalho']


# In[ ]:


hours = 6
sum = original_df['Precipitacao'].rolling(hours*4).sum()


# ## Has Rain

# In[ ]:



has_rain_treshold = 10
precipitacao_sum = original_df.loc[:, ['Date', 'Precipitacao']].groupby('Date').sum()
precipitacao_sum.loc[:, 'Rain_Today'] = precipitacao_sum['Precipitacao'] > has_rain_treshold
precipitacao_sum.loc[:, 'Rain_Next_Day'] = precipitacao_sum.loc[:, 'Rain_Today'].shift(-1)
precipitacao_sum = precipitacao_sum.dropna()

precipitacao_sum.index = pd.to_datetime(precipitacao_sum.index, yearfirst=True)
precipitacao_sum.head()


# # Create Datewise DataFrame 

# In[ ]:


df = original_df[interest_cols + ['Date' , 'Data_Hora'] ]
df = df.set_index('Data_Hora')


# In[ ]:


unique_dates = df.index.round('D').unique()
df_date = pd.DataFrame(precipitacao_sum.index, columns = ['Date'])


# In[ ]:


df_date = df_date.merge(precipitacao_sum.loc[:, ['Rain_Today','Rain_Next_Day']], on = 'Date')
df_date = df_date.set_index('Date')


# ## Simple Metrics

# In[ ]:



sum_date = df[interest_cols + ['Date']].groupby('Date').sum()
sum_date.columns = [c + '_sum' for c in sum_date.columns]

median_date = df[interest_cols + ['Date']].groupby('Date').median()
median_date.columns = [c + '_median' for c in median_date.columns]

mean_date = df[interest_cols + ['Date']].groupby('Date').mean()
mean_date.columns = [c + '_mean' for c in mean_date.columns]

min_date = df[interest_cols + ['Date']].groupby('Date').min()
min_date.columns = [c + '_min' for c in min_date.columns]

max_date = df[interest_cols + ['Date']].groupby('Date').max()
max_date.columns = [c + '_max' for c in max_date.columns]


# In[ ]:


df_date = pd.concat([df_date, sum_date, mean_date, median_date, min_date, max_date], axis = 1)
df_date.head(2)


# ## Time Metrics

# In[ ]:


hours = [3, 9, 15, 21 ]
for selected_hour in hours:

    selected_df = df.loc[(df.index.hour == selected_hour ) & (df.index.minute == 0 ), interest_cols ]
    selected_df.index = selected_df.index.round('D')
    selected_df.columns = [f'{c}_{selected_hour}H' for c in selected_df.columns]
    df_date = pd.concat([df_date, selected_df], axis = 1)

df_date = df_date.dropna(axis = 0)


# In[ ]:


df_date['Rain_Next_Day'] = df_date['Rain_Next_Day'].astype(int)
df_date['Rain_Today'] = df_date['Rain_Today'].astype(int)


# In[ ]:


df_date.head()


# ## Seasonal Metrics

# In[ ]:



def get_season(Row):
    
    doy = Row.name.timetuple().tm_yday
    
    fall_start = datetime.strptime('2020-03-20', '%Y-%m-%d' ).timetuple().tm_yday
    summer_start = datetime.strptime('2020-06-20', '%Y-%m-%d' ).timetuple().tm_yday
    spring_start = datetime.strptime('2020-09-22', '%Y-%m-%d' ).timetuple().tm_yday
    spring_end = datetime.strptime('2020-12-21', '%Y-%m-%d' ).timetuple().tm_yday
    
    fall = range(fall_start, summer_start)
    summer = range(summer_start, spring_start)
    spring = range(spring_start, spring_end)
    
    if doy in fall:
        season = 1#'fall'
    elif doy in summer:
        season = 2#'winter'
    elif doy in spring:
        season = 3#'spring'
    else:
        season = 0#'summer' 
    
    return season

df_date['season'] =  df_date.apply(get_season, axis = 1)


# In[ ]:


seasonal_means = ['Precipitacao_mean']#, 'RadiacaoSolar_mean', 'TemperaturaDoAr_mean']

for s in seasonal_means:
    map_ = dict(df_date.groupby('season').mean()['Precipitacao_mean'])
    df_date[f'seasonalMean_{s}'] =  df_date['season'].map(map_)

df_date = df_date.drop(columns = ['season'])


# In[ ]:


df_date.head(2)


# # Feature Reduction

# ## Autoencoders

# In[ ]:


from tensorflow import keras
from tensorflow.keras.layers import *
from tensorflow.keras import Model

from sklearn.preprocessing import StandardScaler
sc = StandardScaler()


# In[ ]:



X, y = df_date.drop(columns = ['Rain_Next_Day']), df_date.Rain_Next_Day.values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

X_train, X_test = sc.fit_transform(X_train), sc.fit_transform(X_test)


# In[ ]:


unique, counts = np.unique(y_test, return_counts=True)
print(np.asarray((unique, counts)).T)


# In[ ]:



encoding_dim = 20

input_data = Input(shape=(X.shape[1],))

encoded = Dense(encoding_dim, activation='linear')(input_data)
decoded = Dense(X.shape[1], activation=None)(encoded)
autoencoder = Model(input_data, decoded)

encoder = Model(input_data, encoded)

encoded_input = Input(shape=(encoding_dim,))
decoder_layer = autoencoder.layers[-1]

decoder = Model(encoded_input, decoder_layer(encoded_input))


# In[ ]:


autoencoder.compile(optimizer='adadelta', loss='mean_squared_error')
autoencoder.fit(X_train, X_train,
                epochs=500,
                batch_size=16,
                shuffle=True,
                verbose = 1)


# In[ ]:


encoded_data_train = encoder.predict(X_train)
encoded_data_test = encoder.predict(X_test)

decoded_data_train = decoder.predict(encoded_data_train)
decoded_data_test = decoder.predict(encoded_data_test)

error_train = X_train - decoded_data_train
error_test = X_test - decoded_data_test


# In[ ]:


plt.figure(figsize=(13,8))
plt.subplot(2,1,1)
plt.bar(x = list(range(error_train.shape[1] )), height =  error_train.mean(axis = 0))
plt.subplot(2,1,2)
plt.bar(x = list(range(error_test.shape[1] )), height =  error_test.mean(axis = 0))
plt.show()


# In[ ]:


import seaborn as sns
df_encoded = pd.DataFrame(encoded_data_train, columns = list(range(encoded_data_train.shape[1] )) )
figure = plt.figure(figsize=(13.5,12))
corrMatrix = df_encoded.corr()
sns.heatmap(corrMatrix, annot=True, cbar = False, cmap="viridis")
plt.show()


# ## Test Features

# In[ ]:


params= {'colsample_bytree': 0.8937399605148961,
         'early_stopping_rounds': 12,
         'max_depth': 5,
         'min_child_weight': 5,
         'n_estimators': 729,
         'reg_alpha': 19.86313897722475,
         'reg_lambda': 188.1727458353706}

fit_params={}
fit_params['early_stopping_rounds'] = params.pop('early_stopping_rounds')


# In[ ]:


import xgboost as xgb

clf = xgb.XGBClassifier(tree_method = 'gpu_hist', **params)

eval_set = [(encoded_data_train, y_train), (encoded_data_test, y_test)]

clf.fit(encoded_data_train, y_train,  eval_metric=["logloss","error", "auc", "map"], 
        eval_set=eval_set, verbose=False, **fit_params);

keys = clf.evals_result()['validation_0'].keys()

fig, ax = plt.subplots( 1, len(keys) ,figsize = (7*len(keys),7))
ax = ax.ravel()
for i, key in enumerate(keys):
    ax[i].set_title(key)
    ax[i].plot(clf.evals_result()['validation_0'][key], lw = 3)
    ax[i].plot(clf.evals_result()['validation_1'][key], lw = 3)
plt.show()

y_pred = clf.predict(encoded_data_test)
plot_confusion_matrix(y_test, y_pred, ['0', '1'])


# In[ ]:


unique, counts = np.unique(y_test, return_counts=True)
print(np.asarray((unique, counts)).T)

