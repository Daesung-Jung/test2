# -*- coding: utf-8 -*-
from threading import Timer
import os
import webbrowser

import math
import dash 
import pandas as pd
import numpy as np
from dash import Dash, dcc, html, dash_table
import plotly.express as px
import plotly.graph_objs as go
import easygui as g

import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

template_use = "flatly"
load_figure_template(["flatly"])

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])


# CSV 파일 불러오기
def load_data():
    data = pd.read_csv("/home/user_name/mysite/data/file.csv")
    data["Year"] = pd.to_datetime(data["Date"]).dt.year.astype(str)
    columns_rename={
            'Date':'일자',
            'Level':'수준',
            'Athlete_Name':'선수',
            'Pitch_Type':'구종',
            'MPH':'구속',
            'MPH_MAX':'구속최대',
            'Total_Spin':'회전수',
            'Total_Spin_MAX':'회전최대',
            'Vertical_Break_Inches':'상하무브',
            'Horizontal_Break_Inches':'좌우무브',
            'Spin_Efficiency':'회전효율',
            'Gyro_Degree':'자이로디그리',
            'Spin_Direction':'회전축_시간',
            'Release_Angle':'릴_앵글_상하',
            'Horizontal_Angle':'릴_앵글_좌우',
            'Release_Height':'릴_위치_상하',
            'Release_Side':'릴_위치_좌우', 
            'Pitch_Count':'번호',
            'Strike':'스트라이크', 
            'pitch_horizontal_offset':'수평오프셋',
            'pitch_vertical_offset':'수직오프셋', 
            'Year':'연도'
        }
    
    data['Release_Height'] = round(data['Release_Height']*30.48,1)    
    data['Release_Side'] = round(data['Release_Side']*30.48,1)

    Pitch_Type_Change = {
        '4 Seam Fastball':'속구',
        '2 Seam Fastball':'투심',
        'Slider': '슬라',
        'Curveball' : '커브',
        'Changeup' : '첸접',
        'Splitter' :'포크',
        'Knuckleball' :'너클'
        }
    data.rename(columns=columns_rename,
                        inplace = True)    
    
    data['회전축']= data.apply(calculate_tilt, axis=1)
    data['구종'] = data['구종'].map(Pitch_Type_Change)
    data.loc[:,'BU'] = round(data['회전수'] / data['구속'], 1)
    
    return data

def get_pitch_type_color(pitch_type):
    # Pitch Type에 따라 색상 반환
    if pitch_type == "속구":
        return "#C92A47"  # 
    elif pitch_type == "투심":
        return "#F69C00"  # 
    elif pitch_type == "슬라":
        return "#ECE600"  # 
    elif pitch_type == "커브":
        return "#47D2EF"  # 
    elif pitch_type == "첸접":
        return "#42BE2F"  # 
    elif pitch_type == "포크":
      return "#4FACAD"  # 
    else:
        return "white"  # 검정색


#회전축 구하는 공식
def calculate_spin_direction(row):

    horizontal_movement = row['좌우무브']
    vertical_movement = row['상하무브']

    spin_direction = round(-math.degrees(math.atan2(vertical_movement, horizontal_movement)) + 270,0)

    if spin_direction>=360:
        spin_direction= spin_direction-360       

    return spin_direction


def convert_angle_to_time(angle):
    angle = (angle + 180) % 360  # 각도에 180을 더하고 360으로 나누어 0~360 범위로 조정

    hours = int(angle / 30)  # 360도를 12시간으로 나누기
    minutes = int((angle % 30) * 2)  # 30도를 60분으로 나누기
    
    # 시간과 분을 문자열 형태로 변환하여 반환
    time_str = '{:02d}:{:02d}'.format(hours, minutes)
    return time_str

def calculate_tilt(row):
    if row['좌우무브'] or row['상하무브'] is not None:

        horizontal_movement = row['좌우무브']
        vertical_movement = row['상하무브']

        spin_direction = round(-math.degrees(math.atan2(vertical_movement, horizontal_movement)) + 270,0)

        time = convert_angle_to_time(spin_direction)    
    else:
        time="" 

    return time



# 대시보드 앱 초기화
app = Dash(__name__)

data = load_data()
PAGE_SIZE = 5

# 대시보드 레이아웃 구성
app.layout = html.Div(
    style={"width": "400mm", "height": "297mm", "margin": "0 auto", "padding": "0px", "display": "flex", "flex-direction": "column"},
    children=[      
        html.H1("2023 스타워즈 랩소도 리포트", style={"text-align": "center", "fontSize": "80px","margin-bottom": "5px","margin-top": "5px"}),
        html.Div(
            style={"display": "flex", "justify-content": "center", "gap": "100px"},
            children=[
                html.Div(
                    style={"text-align": "center","width": "150px"},
                    children=[
                        html.Label("연도"),
                        dcc.Checklist(
                            id="year-filter",
                            options=[
                                {"label": year, "value": year}
                                for year in sorted(data["연도"].unique())
                            ],
                            value=["2022"],
                            labelStyle={"display": "inline-block", "margin-right": "10px"},
                        ),
                    ],
                ),
                html.Div(
                    style={"text-align": "center", "width": "150px"},
                    children=[
                        html.Label("수준"),
                        dcc.Dropdown(
                            id="level-filter",
                            options=[
                                {"label": level, "value": level}
                                for level in sorted(data["수준"].unique())
                            ],
                            value=data["수준"].unique()[0],
                        ),
                    ],
                ),
                html.Div(
                    style={"text-align": "center","width": "150px"},
                    children=[
                        html.Label("선수"),
                        dcc.Dropdown(
                            id="athlete-filter",
                            options=[],
                            value=data[data["수준"]==data["수준"].unique()[0]]['선수'].unique()[0],
                        ),
                    ],
                ),
            ],
        ),
        html.H1(style={"text-align": "center", "border-bottom": "1px solid #ccc","border-top": "1px solid #ccc","margin-bottom": "5px"}),
      
        html.Hr(),
        html.Div(
        style={"display": "flex", "justify-content": "center","flex-direction": "column","margin-bottom": "5px"},
        children=[
            html.H1("속구 비교", style={"text-align": "left","fontSize": "30px", "margin-left": "8.2%","margin-bottom": "-20px"}),        
            html.Div(
                id="player-avg-table",
                style={"margin": "40px auto", "text-align": "center", "flex": "1","margin-bottom": "-15px"}
            ),
            html.Div(
                style={"display": "flex", "justify-content": "center","flex-direction": "row"},
                children=[
                    html.H4("최상 -", style={"text-align": "center",'color': 'red'}),
                    html.H4("중상 - ", style={"text-align": "center",'color': 'darkred'}),
                    html.H4("보통 -", style={"text-align": "center",'color': 'black'}),
                    html.H4("잠재중상 -", style={"text-align": "center",'color': 'navy'}),
                    html.H4("잠재최상", style={"text-align": "center",'color': 'blue'}),                            
                ]
            ),   
            html.H1("구종별 요약", style={"text-align": "left","fontSize": "30px", "margin-left": "8.2%","margin-bottom": "-20px"}),      
            html.Div(
                id="player-summary-table",
                style={"margin": "40px auto", "text-align": "center", "flex": "1","margin-bottom": "5px","margin-bottom": "0px"},
            ),
        ]
    ),
    
    html.H1("무브먼트(cm) - 릴리즈포인트(cm)", style={"text-align": "left","fontSize": "30px", "margin-left": "8.2%","writing-mode": "horizontal-tb","margin-bottom": "0px"}),  
    html.Div(        
        style={"margin": "auto", "display": "flex"},
        children=[    
            html.Div(
                id="scatter-plot",
                style={"text-align": "left", "flex": "1"}
            ), 
            html.Div(
                id="release-plot",
                style={"text-align": "left", "flex": "1"}
            ),
        ]
    ),
    html.Div(
        style={"margin": "40px auto", "text-align": "center", "flex": "1","margin-top": "-5px"},        
        children=[
            dash_table.DataTable(
                id='table-paging',                
                columns=[
                    {"name": col, "id": col} for col in data[['일자','구종','구속','회전수','BU','회전효율','회전축','상하무브','좌우무브','릴_위치_상하','릴_위치_좌우','릴_앵글_상하','릴_앵글_좌우','스트라이크']]
                        ],
                page_current=0,
                page_size=PAGE_SIZE,
                page_action='custom',
                filter_action='custom',
                filter_query='',
                sort_action='custom',
                sort_mode='multi',
                sort_by=[],
                style_cell={
                    'fontSize': '24px',
                    'fontFamily': 'Arial',
                    'textAlign': 'center',
                    'whiteSpace': 'normal',
                    'height': '50px',
                    'minWidth': '170.0px',
                    'width': '170.0px',
                    'maxWidth': '200px',
                },
                 style_header={
                    'height': '30px',
                    'fontWeight': 'bold',
                    'whiteSpace': 'normal',
                    'backgroundColor': '#000000',  # 검정색 배경
                    'color': '#FFFFFF',  # 흰색 글자
                   },
                style_header_conditional=[
                    {'if': {'header_index': 0},
                    'backgroundColor': '#000000',  # 검정색 배경
                    'color': '#FFFFFF',  # 흰색 글자
                    },
                ],
                style_table={
                    'width': '100%',
                    'maxWidth': '1300px',  # 테이블 전체의 최대 넓이 설정
                    'overflowX': 'auto',  # 가로 스크롤 허용
                },
                ),
             html.Div(id='table-paging-container')
            ]
        ),
    html.Div(
        [
            html.Img(src=app.get_asset_url("sports_science_lab.png"), style={"width": "100px", "vertical-align": "middle", "float": "left", "margin-left": "400px", "display": "block"}),
            html.Img(src=app.get_asset_url("kbsa_bi.png"), style={"width": "100px", "vertical-align": "middle", "float": "none", "margin-right": "0px"}),
            html.Img(src=app.get_asset_url("diegobaseball_bi.png"), style={"width": "100px", "vertical-align": "middle", "float": "right", "margin-right": "400px", "display": "block"})  
        ],
    style={"text-align": "center"}
     ),
    ]
    
)

# Athlete_Name 옵션 업데이트 콜백 함수
@app.callback(
    dash.dependencies.Output("athlete-filter", "options"),
    [dash.dependencies.Input("level-filter", "value")]
)
def update_athlete_options(level):
    athlete_options = [
        {"label": name, "value": name}
        for name in sorted(data[data["수준"] == level]["선수"].unique())
    ]
    return athlete_options


# 속구 PivotTable 콜백 함수
@app.callback(
    dash.dependencies.Output("player-avg-table", "children"),
    [
        dash.dependencies.Input("year-filter", "value"),
        dash.dependencies.Input("level-filter", "value"),
        dash.dependencies.Input("athlete-filter", "value"),
    ],
)
def level_pivot_table(year, level, athlete):
    filtered_data = data[
        (data["연도"].isin(year)) & (data["수준"] == level) & (data['구종'] == "속구")
    ]      

    filtered_player_data = filtered_data[filtered_data['선수'] == athlete]

    pivot_table_ = pd.pivot_table(filtered_data, index="수준",
                                        values=['구속', '회전수', 'BU', '회전효율', '릴_앵글_상하',
                                            '상하무브','좌우무브', '릴_위치_상하'],
                                        aggfunc='mean'
                                        )

    pivot_table_ = pivot_table_.rename_axis("속구")
    
    player_pivot_table = pd.pivot_table(filtered_player_data, index="선수",
                                        values=['구속', '회전수', 'BU', '회전효율', '릴_앵글_상하',
                                           '상하무브','좌우무브', '릴_위치_상하'],
                                        aggfunc='mean'
                                        )
    player_pivot_table.loc[:,'회전축'] = player_pivot_table.apply(calculate_tilt, axis=1)

    player_pivot_table = player_pivot_table.rename_axis("속구")
    pivot_table_ = pivot_table_.append(player_pivot_table)

    pivot_table_.loc[:,'구속'] = round(pivot_table_['구속'], 1)
    pivot_table_.loc[:,'회전수'] = round(pivot_table_['회전수'], 0)
    pivot_table_.loc[:,'회전효율'] = round(pivot_table_['회전효율'], 1)
    pivot_table_.loc[:,'BU'] = round(pivot_table_['BU'], 1)
    pivot_table_.loc[:,'릴_앵글_상하'] = round(pivot_table_['릴_앵글_상하'], 1)
    pivot_table_.loc[:,'릴_위치_상하'] = round(pivot_table_['릴_위치_상하'], 1)
    pivot_table_.loc[:,'상하무브'] = round(pivot_table_['상하무브'], 1)

    columns_=['구속','회전수','BU','회전효율','회전축','상하무브','릴_위치_상하']
    columns__=['구속','회전수','BU','회전효율','상하무브','릴_위치_상하']

    pivot_table_ = pivot_table_[columns_]
    filtered_data_ = filtered_data[columns__]

    style_data_conditional = [
    {'if': {'row_index': 'odd'},
     'backgroundColor': '#F0F0F0',  # 옅은 회색 배경
    },
    {'if': {'row_index': 1, 'column_id': '속구'},
     'backgroundColor': '#C92A47',
     'color': 'white'
    }
] + [
    {
        'if': {
            'filter_query': '{{{}}} > {}'.format(col, value),
            'column_id': col
        },
        'color': 'blue'
    } for col, value in filtered_data_.quantile(0.0).iteritems()
] + [
    {
        'if': {
            'filter_query': '{{{}}} > {}'.format(col, value),
            'column_id': col
        },
        'color': 'navy'
    } for col, value in filtered_data_.quantile(0.2).iteritems()
] + [
    {
        'if': {
            'filter_query': '{{{}}} > {}'.format(col, value),
            'column_id': col
        },
        'color': 'black'
    } for col, value in filtered_data_.quantile(0.4).iteritems()
] + [
    {
        'if': {
            'filter_query': '{{{}}} > {}'.format(col, value),
            'column_id': col
        },
        'color': 'darkred'
    } for col, value in filtered_data_.quantile(0.6).iteritems()
] + [
    {
        'if': {
            'filter_query': '{{{}}} > {}'.format(col, value),
            'column_id': col
        },
        'color': 'red'
    } for col, value in filtered_data_.quantile(0.8).iteritems()
]

    pivot_table_layout = dash_table.DataTable(
        data=pivot_table_.reset_index().to_dict('records'),
        columns=[{'id': col, 'name': col} for col in pivot_table_.reset_index().columns],
        style_cell={
            'fontSize': '24px',  # 글자 크기
            'fontFamily': 'Arial',
            'textAlign': 'center',
            'whiteSpace': 'normal',
            'height': '50px',
            'minWidth': '157.5px',  # 모든 컬럼의 최소 넓이 설정
            'width': '157.5px',  # 모든 컬럼의 기본 넓이 설정
            'maxWidth': '200px',  # 모든 컬럼의 최대 넓이 설정
        },
        style_header={
            'height': '30px',
            'fontWeight': 'bold',
            'whiteSpace': 'normal',
            'backgroundColor': '#000000',  # 검정색 배경
            'color': '#FFFFFF',  # 흰색 글자
        },
        style_header_conditional=[
            {'if': {'header_index': 0},
             'backgroundColor': '#000000',  # 검정색 배경
             'color': '#FFFFFF',  # 흰색 글자
            },
        ],
        style_table={
            'width': '100%',
            'maxWidth': '1300px',  # 테이블 전체의 최대 넓이 설정
            'overflowX': 'auto',  # 가로 스크롤 허용
        },
        style_data_conditional=style_data_conditional
    )

    return pivot_table_layout


# 선수 요약 테이블
@app.callback(
    dash.dependencies.Output("player-summary-table", "children"),
    [
        dash.dependencies.Input("year-filter", "value"),
        dash.dependencies.Input("level-filter", "value"),
        dash.dependencies.Input("athlete-filter", "value"),
    ],
)

def player_summary_pivot_table(year, level, athlete):
    #if athlete is None or len(athlete)==0 :
    #    return print("레벨과 선수 이름은 선택해주세요!")
    if athlete is None or len(athlete) == 0:
        athlete = data[data["수준"] == level]["선수"].unique()[0] 
    
    filtered_data = data[
        (data["연도"].isin(year)) & (data["수준"] == level) & (data["선수"] == athlete)    
    ] 

    pivot_table = pd.pivot_table(filtered_data, index='구종',
                                values=['구속', '회전수', '상하무브', '좌우무브', '회전효율'],
                                aggfunc={'구속': [np.mean, np.max],
                                        '회전수': [np.mean, np.max],
                                        '상하무브': np.mean,
                                        '좌우무브': np.mean,
                                        '회전효율': np.mean}
                                )
    
    pivot_table = pivot_table.round(0)

    #비어 있는 인덱스와 컬럼들 격을 만들고 fillna("")

    pivot_table.columns = pivot_table.columns.map('_'.join)
    
    pitch_type_columns_all = ['속구','투심','슬라', '커브',
            '첸접','포크','너클']
    columns_rename={'구속_amax':'구속',
                    '구속_mean':'구속최대',
                    '상하무브_mean':'상하무브',
                    '좌우무브_mean':'좌우무브',
                    '회전수_amax':'회전최대',
                    '회전수_mean':'회전',
                    '회전효율_mean':'회전효율'}
    
    pivot_table.rename(columns=columns_rename,
                        inplace = True)
    
    pivot_table.loc[:,'회전축'] = pivot_table.apply(calculate_tilt, axis=1)

    pivot_table_append= list(set(pitch_type_columns_all).difference(set(pivot_table.index.to_list())))
    pivot_table = pivot_table.reindex(pivot_table.index.union(pivot_table_append))
        
    pivot_table = pivot_table.reindex(index=['속구','투심','슬라', '커브',
            '첸접','포크','너클'],
                columns= ['구속','구속최대','회전','회전최대', '회전효율','회전축',
                '상하무브','좌우무브'])
    
    pivot_table= pivot_table.rename_axis("구종")
   
    
    pivot_table = pivot_table.loc[['속구', '투심', '슬라', '커브', '첸접', '포크', '너클'],]

    pivot_table_layout = dash_table.DataTable(
    data=pivot_table.reset_index().to_dict('records'),
    columns=[{'id': col, 'name': col} for col in pivot_table.reset_index().columns],
    style_cell={
        'fontSize': '24px',  # 글자 크기
        'fontFamily': 'Arial',
        'textAlign': 'center',
        'whiteSpace': 'normal',
        'height': '50px',
        'minWidth': '140px',  # 모든 컬럼의 최소 넓이 설정
        'width': '140px',  # 모든 컬럼의 기본 넓이 설정
        'maxWidth': '200px',  # 모든 컬럼의 최대 넓이 설정
    },
    style_header={
        'height': '30px',
        'fontWeight': 'bold',
        'whiteSpace': 'normal',
        'backgroundColor': '#000000',  # 검정색 배경
        'color': '#FFFFFF',  # 흰색 글자
    },
    style_header_conditional=[
        {'if': {'header_index': 0},
         'backgroundColor': '#000000',  # 검정색 배경
         'color': '#FFFFFF',  # 흰색 글자
        },
    ],
    style_table={
        'width': '100%',
        'maxWidth': '1300px',  # 테이블 전체의 최대 넓이 설정
        'overflowX': 'auto',  # 가로 스크롤 허용
    },
    
    style_data_conditional=[
        {'if': {'row_index': 'odd'},
         'backgroundColor': '#F0F0F0',  # 옅은 회색 배경
        },
        {'if': {            
                'row_index': 0,
                'column_id': '구종'              
            },
            'backgroundColor': '#C92A47',
            'color': 'white' 
        },
        {'if': {            
                'row_index': 1,
                'column_id': '구종'                               
            },
            'backgroundColor': '#F69C00',
            'color': 'white' 
        },
        {'if': {            
                'row_index': 2,
                'column_id': '구종'
            },
            'backgroundColor': '#ECE600',
            'color': 'black'  
        },
        
        {'if': {            
                'row_index': 3,
                'column_id': '구종'                
            },
            'backgroundColor': '#47D2EF',
            'color': 'white'  
        },
        
        {'if': {            
                'row_index': 4,
                'column_id': '구종'                                
            },
            'backgroundColor': '#42BE2F',
            'color': 'white'
        },

        {'if': {            
                'row_index': 5,
                'column_id': '구종'                
            },
            'backgroundColor': '#4FACAD',
            'color': 'white'
        },

      #커터 : #903E29  
      #스위퍼 : #D9B22B
    ],
    
    editable=True,
    )

    return pivot_table_layout

# ScatterPlot 콜백 함수
@app.callback(
    dash.dependencies.Output("scatter-plot", "children"),
    [
        dash.dependencies.Input("year-filter", "value"),
        dash.dependencies.Input("level-filter", "value"),
        dash.dependencies.Input("athlete-filter", "value"),
    ],
)

def update_scatter_plot(year, level, athlete):
    filtered_data = data[
        (data["연도"].isin(year)) & (data["수준"] == level) & (data["선수"] == athlete)
    ]
    scatter_plot = px.scatter(
        filtered_data,
        x="좌우무브",
        y="상하무브",
        range_x=[-70, 70],
        range_y=[-70, 70],
        color="구종",
        color_discrete_map={pitch_type: get_pitch_type_color(pitch_type) for pitch_type in data["구종"].unique()},
        width=650,  # Set the width of the graph,
        height=650,  # Set the height of the graph,
    )
    scatter_plot.update_traces(marker=dict(size=10))
    scatter_plot.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showticklabels=True, tickfont=dict(size=14)),
        yaxis=dict(showticklabels=True, tickfont=dict(size=14)),
        xaxis_title=None,
        yaxis_title=None
    )
    
    return dcc.Graph(figure=scatter_plot)


# ScatterPlot 콜백 함수
@app.callback(
    dash.dependencies.Output("release-plot", "children"),
    [
        dash.dependencies.Input("year-filter", "value"),
        dash.dependencies.Input("level-filter", "value"),
        dash.dependencies.Input("athlete-filter", "value"),
    ],
)
def update_release_plot(year, level, athlete):
    filtered_data = data[
        (data["연도"].isin(year)) & (data["수준"] == level) & (data["선수"] == athlete)
    ]
    scatter_plot = px.scatter(
        filtered_data,
        x="릴_위치_좌우",
        y="릴_위치_상하",
        range_x=[-100, 100],
        range_y=[00, 200],
        color="구종",
        color_discrete_map={pitch_type: get_pitch_type_color(pitch_type) for pitch_type in data["구종"].unique()},
        width=650,  # Set the width of the graph,
        height=650,  # Set the height of the graph,
   
    )
    scatter_plot.update_traces(marker=dict(size=10))    
    scatter_plot.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showticklabels=True, tickfont=dict(size=14)),
        yaxis=dict(showticklabels=True, tickfont=dict(size=14)),
        xaxis_title=None,
        yaxis_title=None
    )
    return dcc.Graph(figure=scatter_plot)

@app.callback(
    dash.dependencies.Output('table-paging', 'data'),
    dash.dependencies.Output('table-paging-container', 'children'),
    dash.dependencies.Input('table-paging', 'page_current'),
    dash.dependencies.Input('table-paging', 'page_size'),
    dash.dependencies.Input('table-paging', 'filter_query'),
    dash.dependencies.Input('table-paging', 'sort_by'),
    dash.dependencies.Input("year-filter", "value"),
    dash.dependencies.Input("level-filter", "value"),
    dash.dependencies.Input("athlete-filter", "value"),
)
def update_table(page_current, page_size, filter_query, sort_by, year, level, athlete):
    filtering_expressions = filter_query.split(' && ')

    filtered_data = data[
        (data["연도"].isin(year)) & (data["수준"] == level) & (data["선수"] == athlete)
    ]
    
    filtered_data.loc[:,'구속'] = round(filtered_data['구속'], 1)
    filtered_data.loc[:,'회전수'] = round(filtered_data['회전수'], 0)
    filtered_data.loc[:,'회전효율'] = round(filtered_data['회전효율'], 1)
    filtered_data.loc[:,'BU'] = round(filtered_data['BU'], 1)
    filtered_data.loc[:,'릴_앵글_상하'] = round(filtered_data['릴_앵글_상하'], 1)    
    filtered_data.loc[:,'릴_앵글_좌우'] = round(filtered_data['릴_앵글_좌우'], 1)
    filtered_data.loc[:,'릴_위치_상하'] = round(filtered_data['릴_위치_상하'], 1)
    filtered_data.loc[:,'릴_위치_좌우'] = round(filtered_data['릴_위치_좌우'], 1)
    filtered_data.loc[:,'상하무브'] = round(filtered_data['상하무브'], 1)
    filtered_data.loc[:,'좌우무브'] = round(filtered_data['좌우무브'], 1)

    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)
        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            filtered_data = filtered_data.loc[getattr(filtered_data[col_name], operator)(filter_value)]
        elif operator == 'contains':
            filtered_data = filtered_data.loc[filtered_data[col_name].str.contains(filter_value, case=False)]
        elif operator == 'datestartswith':
            filtered_data = filtered_data.loc[filtered_data[col_name].str.startswith(filter_value)]

    if len(sort_by):
        filtered_data = filtered_data.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[col['direction'] == 'asc' for col in sort_by],
            inplace=False
        )

    total_pages = math.ceil(len(filtered_data) / page_size)
    filtered_data_ = filtered_data.iloc[page_current * page_size:(page_current + 1) * page_size].to_dict('records')

    pivot_table_ = filtered_data_, html.Div(
        className='table-paging',
        children=[
            html.Span(
                f'Page {page_current + 1} of {total_pages}',
                className='table-paging-description'
            ),
            dcc.RangeSlider(
                id='table-paging-slider',
                min=0,
                max=total_pages - 1,
                value=[page_current, page_current],
                marks={i: str(i + 1) for i in range(total_pages)},
                allowCross=False,
                className='table-paging-slider'
            )
        ]
    )

    return pivot_table_

@app.callback(
    dash.dependencies.Output('table-paging', 'page_current'),
    dash.dependencies.Input('table-paging-slider', 'value')
)
def update_table_page_current(slider_value):
    return slider_value[1]

def split_filter_part(filter_part):
    operators = [['ge ', '>='],
                 ['le ', '<='],
                 ['lt ', '<'],
                 ['gt ', '>'],
                 ['ne ', '!='],
                 ['eq ', '='],
                 ['contains '],
                 ['datestartswith ']]
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                return name, operator_type[0].strip(), value

    return [None] * 3



def open_browser():
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new("")


if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run_server(debug=True)

"""
columns=[
                {"name": i, "id": i} for i in sorted(data[['일자',
                                                            '구종',
                                                            '구속',
                                                            '회전수',
                                                            'BU',
                                                            '회전효율',
                                                            '회전축',
                                                            '상하무브',
                                                            '좌우무브']])

                                    """
