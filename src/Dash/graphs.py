import plotly.graph_objects as go
from plotly.subplots import make_subplots
from os import path
import xgboost
from cptec import get_prediction, get_polygon
from urllib.request import urlopen
import json
from shapely.geometry import Polygon
import pandas as pd

# Color palette

BACKGRUOND = '#191A1A'

TEAL = '#38b2a3'
DARKER_TEAL = '#58C8A3'

BLUE = '#3282b8'
DARKER_BLUE = '#2D75A5'

RED  = '#f05454'
DARKER_RED = '#D84B4B'

GREEN = '#6BDD67'
DARKER_GREEN = '#55B052'

ORANGE = '#f6830f'
DARKER_ORANGE = ''

# CPTEC pred
PREP_ACC = RED
PREP = TEAL
TEMP = BLUE
SENST = ORANGE
UMIDADE = GREEN
PRESSAO = DARKER_BLUE

plot_layout_kwargs = dict(template='plotly_dark',
                          paper_bgcolor = BACKGRUOND,
                          plot_bgcolor  = BACKGRUOND)

path = 'https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-35-mun.json'
token = 'pk.eyJ1IjoiZmlwcG9saXRvIiwiYSI6ImNqeXE4eGp5bjFudmozY3A3M2RwbzYxeHoifQ.OdNEEm5MYvc2AS4iO_X3Pw'

xgb_path = 'src/Dash/model/Identificacao_0H.json'

with urlopen(path) as response:
    counties = json.load(response)
SA = [ i for i in counties['features'] if i['properties']['name'] == 'Santo André' ][0]
SA_polygon = Polygon(SA['geometry']['coordinates'][0])
SA_layer = dict(sourcetype = 'geojson',
             source = SA ,
             below='',
             type = 'fill',
             opacity=0.25,
             color = 'white')


value_dict = {
              'Sem Aviso': 0,
              'Aviso de Observação':1,
              'Aviso de Atenção': 2,
              'Aviso Especial': 3,
              'Aviso Extraordinário de Risco Iminente':4,
              'Aviso Cessado': 5
              }
inv_value_dict = {
              0:'Sem Aviso',
              1:'Aviso de Observação',
              2:'Aviso de Atenção',
              3:'Aviso Especial',
              4:'Aviso Extraordinário de Risco Iminente',
              5:'Aviso Cessado',
              }

x_pred, y_pred = {}, {}

x_pred['bam'], y_pred['bam'] = get_prediction('bam')
x_pred['wrf'], y_pred['wrf'] = get_prediction('wrf')

polygon_dict = get_polygon()

color_dict = {'Aviso de Observação':'#FAFF06',
              'Aviso de Atenção': '#F2C004',
              'Aviso Especial': '#E92C00',
              'Aviso Extraordinário de Risco Iminente': '#000000',
              'Aviso Cessado': '#C3C3C3'
              }


# XGBoost

def get_xgb_predictions(model):

  x_data_t = x_pred[model]
  y_data = y_pred[model]

  df = pd.DataFrame(columns=['Mes', 'Dia', 'Local', 'Precipitacao', 'Data_Hora'])

  df['Data_Hora'] = x_data_t['precipitacao']
  df['Data_Hora'] = pd.to_datetime(df['Data_Hora'], yearfirst = True)
  df['Precipitacao'] = y_data['precipitacao']

  df['Dia'] = df['Data_Hora'].dt.day
  df['Mes'] = df['Data_Hora'].dt.month
  df['Local'] = 1

  df = df.drop(columns = 'Data_Hora')

  sum_precipitacao = df.groupby(['Dia', 'Mes']).sum().reset_index().drop(columns = ['Local'])
  sum_precipitacao = sum_precipitacao.rename(columns = {'Precipitacao': 'PrecSum'} )

  X = df.merge(sum_precipitacao, on = ['Dia','Mes'], how = 'inner')

  return X
def predict(model, xgb_path):
  X = get_xgb_predictions(model)

  model = xgboost.Booster()
  model.load_model(xgb_path)

  data = xgboost.DMatrix(data=X)
  return model.predict(data)

y_xgb = {}
y_xgb['bam'] = predict('bam', xgb_path)
y_xgb['wrf'] = predict('wrf', xgb_path)


def get_geojson_polygon(lons, lats, color='blue'):
    if len(lons) != len(lats):
        raise ValueError('the legth of longitude list  must coincide with that of latitude')
    geojd = {"type": "FeatureCollection"}
    geojd['features'] = []
    coords = []
    for lon, lat in zip(lons, lats):
        coords.append((lon, lat))
    coords.append((lons[0], lats[0]))  #close the polygon
    geojd['features'].append({ "type": "Feature",
                               "geometry": {"type": "Polygon",
                                            "coordinates": [coords] }})
    layer=dict(sourcetype = 'geojson',
             source =geojd,
             below='',
             type = 'fill',
             opacity=0.25,
             color = color)
    return layer

# Graphs

def make_data_repair_plots(merged, error, repaired, col, est, year, month):
  year, month = int(year), int(month)
  repaired_plot = repaired.loc[ (repaired['Data_Hora'].dt.year == year) &
                                (repaired['Data_Hora'].dt.month == month),
                                 ['Data_Hora', f'{col}_{est}'] ]

  merged_plot = merged.loc[ (merged['Data_Hora'].dt.year == year) &
                            (merged['Data_Hora'].dt.month == month),
                            ['Data_Hora', f'{col}_{est}'] ]

  error_plot = error.loc[(error['Data_Hora'].dt.year == year ) &
                         (error['Data_Hora'].dt.month == month),
                         ['Data_Hora', f'{col}_{est}_error'] ]



  plots = make_subplots(2,1, shared_xaxes=True,
                             subplot_titles=('Dados Originais',
                                             'Dados Reparados'))
  plots.add_trace(go.Scatter(
              x = merged_plot['Data_Hora'],
              y = merged_plot[f'{col}_{est}'],
              line = dict( color = BLUE)
              ), col = 1, row = 1)
  plots.add_trace(go.Scatter(
              x = merged_plot['Data_Hora'].where(error_plot[f'{col}_{est}_error']),
              y = merged_plot[f'{col}_{est}'].fillna(0).where(error_plot[f'{col}_{est}_error']),
              line = dict(color = RED)
              ), col = 1, row = 1)
  plots.add_trace(go.Scatter(
              x = repaired_plot['Data_Hora'],
              y = repaired_plot[f'{col}_{est}'],
              line = dict( color = GREEN)
              ), col = 1, row = 2)
  plots.update_layout(showlegend = False,
                      transition_duration=500,
                      **plot_layout_kwargs )

  ymax, ymin = max(repaired_plot[f'{col}_{est}']), min(repaired_plot[f'{col}_{est}'])

  if col == 'PressaoAtmosferica':
    plots.update_yaxes(range=[ymin, ymax], col = 1, row = 1)

  return plots

def make_mapa_plot(label_copy, est):

  mapa = go.Figure()

  mapa.add_trace(go.Scattermapbox(
      lat=est['lat'],
      lon=est['lng'],
      mode='markers',
      marker=go.scattermapbox.Marker(
          size=14,
          color = 'white',
          symbol = 'marker'
      ),
    text=est['Estacao'],
              ))

  mapa.add_trace(go.Densitymapbox(
                      lat=label_copy['lat'],
                      lon=label_copy['lng'],
                      z=[1] * label_copy.shape[0],
                      radius=5,
                      colorscale = 'Tealgrn',
                      reversescale=True,
                      opacity = 0.75,
      showscale=False
                  ))

  mapa.update_layout(
      hovermode='closest',
      mapbox=dict(
          accesstoken=token,
          bearing=0,
          center=go.layout.mapbox.Center(
            lat=-23.652598,
            lon=-46.527872,
        ),
        style='dark',
        pitch=0,
        zoom=11
      ),
      width = 500,
      height = 550,
      showlegend = False,
      **plot_layout_kwargs
                  )

  return mapa

def make_rain_ordem_servico_plot(gb_label_plot, rain_sum_plot):

  ordem_servico_figure = make_subplots(2,1, shared_xaxes=True,
                                       vertical_spacing = 0.1,
                                       subplot_titles=('Ordens de Serviço',
                                                       'Precipitação'))
  ordem_servico_figure.add_trace(go.Bar(
                                    x = gb_label_plot['Data'] ,
                                    y = gb_label_plot['count']),
                                  row = 1, col = 1
                                )
  ordem_servico_figure.add_trace(go.Bar(
                    x = rain_sum_plot['Data'],
                    y = rain_sum_plot['Precipitacao_2'] ,),
              row = 2, col = 1,
             )
  ordem_servico_figure.update_layout(showlegend = False,
                                     bargap = 0,
                                     **plot_layout_kwargs)

  ordem_servico_figure.update_traces(marker_color= TEAL,
                                     marker_line_color=DARKER_TEAL,
                                     marker_line_width=1,
                                     opacity=1,
                                     col = 1, row = 1)
  ordem_servico_figure.update_traces(marker_color = BLUE,
                                     marker_line_color=DARKER_BLUE,
                                     marker_line_width=1,
                                     opacity=1,
                                     col = 1, row = 2)

  return ordem_servico_figure

def make_cptec_prediction(model):

  x, y = x_pred[model], y_pred[model]

  # Cptec Prediction -----------------------------------

  subplot_titles=("Precipitação",
                  "Temperatura",
                  "Umidade Relativa",
                  "Pressão Atmosférica")

  cptec_fig = make_subplots(2,2, shared_xaxes = True,
                                 subplot_titles = subplot_titles)

  # Precipitação
  cptec_fig.add_trace(go.Scatter(
                        x = x['precipitacao_acc'],
                        y = y['precipitacao_acc'],
                        name = 'Precipitação',
                        line = dict(color = PREP_ACC)
                                ),
                                row = 1, col = 1
                    )
  cptec_fig.add_trace(go.Bar(
                        x = x['precipitacao'],
                        y = y['precipitacao'],
                        name = 'Precipitação Acumulada',
                        marker = dict(color = PREP)
                                ),
                                row = 1, col = 1
                    )

  # Temperatura
  cptec_fig.add_trace(go.Scatter(
                        x = x['temperatura'],
                        y = y['temperatura'],
                        name = 'Temperatura',
                        line = dict(color = TEMP)
                                ),
                                row = 1, col = 2
                    )
  cptec_fig.add_trace(go.Scatter(
                        x = x['temperatura_aparente'],
                        y = y['temperatura_aparente'],
                        name = 'Sensação térmica',
                        line = dict(color = SENST)
                                ),
                                row = 1, col = 2
                    )

  # Umidade Relativa
  cptec_fig.add_trace(go.Scatter(
                        x = x['umidade_relativa'],
                        y = y['umidade_relativa'],
                        name = 'Umidade Relativa',
                        line = dict(color = UMIDADE)
                                ),
                                row = 2, col = 1
                    )

  # Pressao
  cptec_fig.add_trace(go.Scatter(
                        x = x['pressao'],
                        y = y['pressao'],
                        name = 'Pressão Atmosférica',
                        line = dict ( color = PRESSAO)
                                ),
                                row = 2, col = 2
                    )

  cptec_fig.update_layout(legend=dict(
                                  orientation="h",
                                  yanchor="bottom",
                                  y=-0.3,
                                  xanchor="center",
                                  x=0.5
                              ),**plot_layout_kwargs )

  return cptec_fig

def make_cptec_polygon(time):

  geom = polygon_dict[time]['geom']
  title = polygon_dict[time]['title']

  mylayers = []

  value = 0

  for t, g in zip(title,geom):

    warning_poly = Polygon(geom[0])
    if warning_poly.intersects(SA_polygon):
      if value_dict[t] > value:
        value = value_dict[t]

    lat = [p[1] for p in g]
    lon = [p[0] for p in g]

    try:
      warning_color = color_dict[t]
    except KeyError:
      warning_color = 'blue'

    mylayers.append(get_geojson_polygon(lon, lat, warning_color))

  mylayers.append(SA_layer)

  fig = go.Figure()
  fig.add_trace(go.Scattermapbox(
                lat=[-23.7052598],
                lon=[-46.4497872],
              mode='markers',
              marker=go.scattermapbox.Marker(
                  size=1
                      ),
                  ))

  fig.update_layout(
      hovermode='closest',
      mapbox=dict(
          accesstoken=token,
          bearing=0,
          center=go.layout.mapbox.Center(
              lat=-23.7052598,
              lon=-46.4497872,
          ),
          style='dark',
          pitch=0,
          zoom=9
      ),
      width = 750,
      height = 750,
      showlegend = False,
                  )

  fig.layout.update(mapbox_layers=mylayers)

  return fig, inv_value_dict[value]

def make_prob_graph(model):

  y = y_xgb[model]

  m = max(y_pred[model]['precipitacao'])
  y_max = 5*m
  if y_max > 50:
      y_max = m

  fig = make_subplots(specs=[[{"secondary_y": True}]])

  fig.add_trace(go.Bar(
      y= y * 100,
      x= x_pred[model]['precipitacao'],
      name='Chance de alagamento',
      marker=dict(
          color = y,
          cmin = 0,
          cmax = 1,
          colorscale=[
              [0, GREEN],
              [1, RED]]
                          ),
                      ), secondary_y=False,
              )

  fig.add_trace(go.Scatter(
      y = y_pred[model]['precipitacao'] ,
      x = x_pred[model]['precipitacao'],
      name='Chuva [mm]',
      line = dict(color = BLUE, width = 3),
                      ), secondary_y=True,
              )
  fig.update_yaxes(range=[0, 100],
                   title = 'Probabilidade de alagamento [%]',
                   secondary_y=False,
                   titlefont=dict(color=GREEN),
                   tickfont=dict(color=GREEN),)
  fig.update_yaxes(range=[0, y_max],
                   title = 'Precipitacao [mm]',
                   secondary_y=True,
                   titlefont=dict(color=BLUE),
                   tickfont=dict(color=BLUE),)
  fig.update_layout( showlegend = False,
                    **plot_layout_kwargs )

  return fig