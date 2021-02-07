import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px
import pandas as pd
from dash_table import DataTable, FormatTemplate
from dash_table.Format import Format, Symbol
from dash_daq.BooleanSwitch import BooleanSwitch
from utils import banner, DataFetcher
import json
import plotly.express as px
import plotly.graph_objects as go
import time

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
percentage = FormatTemplate.percentage(2)

fond_list = ['天弘互联网A', '天弘互联网C']
get_fond_abbr = lambda fond_select: 'a' if fond_select == fond_list[0] else 'b'
data_fetcher = DataFetcher()

server = app.server
app.config.suppress_callback_exceptions = True

markdown_text = '''
###### 基金的A类份额和C类份额有何不同?

A类和C类只是基金费用的收取方式不同，在投资运作上没有区别，A类和C类单独估值，净值上可能会略有不同。
- A类是在认购/申购时收取一次性收取认购/申购费用；而C类是在认购/申购时不收取认购/申购费用，而是设置每年的销售服务费，每天会从基金净值中计提。
- 根据持有天数不同，A类、C类的赎回费率也有不同。C类较A类略低一些。总体来说，持有时间越长，费率越少。A类一般持有一年到两年以上，赎回费率为零；C类一般持有30天以上赎回费为零。

建议您根据认购/申购金额，计划投资期限等因素综合判断，选择合适自己的基金份额类别。
'''


# fig = px.bar(df, x="City", y="Amount", color="City", barmode="group")

def generate_title():
    """
    :return: A Div containing dashboard title & descriptions.
    """
    return html.Div(
        id="description-card",
        children=[
            html.H5("Ant Fond Fee Analytics"),
            html.H3("Welcome to the Fond Trading Fee Dashboard"),
            html.Div(
                id="intro",
                children=dcc.Markdown(markdown_text),
            ),
        ],
    )


def generate_control_card():
    """
    :return: A Div containing controls for graphs.
    """
    return html.Div(
        id='control-card',
        children=[
            html.P("Select example:", className='control-title'),
            dcc.Dropdown(
                id="fond-select",
                options=[{"label": i, "value": i} for i in fond_list],
                value=fond_list[0],
            ),
            html.Br(),

            html.P(id='control-detail'),
            html.P("Buy Amount:", className='control-title'),
            dcc.Input(
                id="amount",
                type="number"
            ),
            html.P("Buy Days:", className='control-title'),
            dcc.Input(
                id="days",
                type="number"
            ),

            html.Div(id='fee-table',
                     children=[
                         # buy section
                         html.Br(),
                         html.Div(
                             className='flex-container',
                             children=[
                                 html.P('一、买入费率（前段申购）', className='flex-left'),
                                 BooleanSwitch(
                                     className='flex-right',
                                     color='#1257ab9c',
                                     label={'label': '万元', 'style': {'margin-top': 0}},
                                     labelPosition='right',
                                     id='unit-switch',
                                     on=False
                                 ),
                             ]
                         ),
                         html.Div(id='buy-table'),
                         html.P("申购费用：", id='buy-fee'),
                         html.Br(),
                         # operation section
                         html.P('二、运作费率（每年）'),
                         html.Div(id='operation-table'),
                         html.P("运作费用：", id='operation-fee'),
                         html.Br(),
                         # sell section
                         html.P('三、卖出费率'),
                         html.Div(id='sell-table'),
                         html.P("赎回费用：", id='sell-fee')
                     ])
        ]
    )


def generate_fee_table(fond_name, fee_type, unit=1):
    """

    :param fond_name:
    :param fee_type: buy, sell and operation
    :param unit: money unit bigger than 1 is ten thousand -> 万
    :return:
    """
    # money = FormatTemplate.money(2)
    # percentage = FormatTemplate.percentage(2)

    # columns = [
    #     dict(id='account', name='Account'),
    #     dict(id='balance', name='Balance', type='numeric', format=money),
    #     dict(id='rate', name='Rate', type='numeric', format=percentage)
    # ]

    # data = [
    #     dict(account='A', balance=522.31, rate=0.139),
    #     dict(account='B', balance=1607.9, rate=0.1044),
    #     dict(account='C', balance=-228.41, rate=0.199),
    # ]
    data = data_fetcher.get_data(fond_name, fee_type).copy()
    if fee_type == 'sell':
        columns = [
            dict(id='最低天数', name='最低天数'),
            dict(id='最高天数', name='最高天数'),
            dict(id='费率', name='费率', type='numeric', format=percentage)
        ]
        trans_data = data.to_dict('records')
    elif fee_type == 'operation':
        columns = [
            dict(id='管理费', name='管理费', type='numeric', format=percentage),
            dict(id='托管费', name='托管费', type='numeric', format=percentage),
            dict(id='销售服务费', name='销售服务费', type='numeric', format=percentage)
        ]
        trans_data = data.to_dict('records')
    else:
        if unit > 1:
            data['最低金额'] = data['最低金额'] / 10000
            data['最高金额'] = data['最高金额'] / 10000
        columns = [
            dict(id='最低金额', name='最低金额', type='numeric',
                 format=Format(symbol=Symbol.yes, symbol_suffix=' 万元' if unit > 1 else ' 元')),
            dict(id='最高金额', name='最高金额', type='numeric',
                 format=Format(symbol=Symbol.yes, symbol_suffix=' 万元' if unit > 1 else ' 元')),
            dict(id='费率', name='费率', type='numeric', format=percentage)
        ]
        trans_data = data.to_dict('records')

    return DataTable(
        columns=columns,
        data=trans_data
    )


def calculate_fee(fond_name, fee_type, amount, days):
    data = data_fetcher.get_data(fond_name, fee_type)
    days = 0 if days is None else days
    amount = 0 if amount is None else amount

    if fee_type == 'buy' or fee_type == 'sell':
        start = '最低金额' if fee_type == 'buy' else '最低天数'
        end = '最高金额' if fee_type == 'buy' else '最高天数'
        arg = amount if fee_type == 'buy' else days

        target = data[(data[start] <= arg) & (arg < data[end])]
        exception = data[(data[end].isnull()) & (arg >= data[start])]
        if len(target) == 0 and len(exception) == 0:
            return 0
        elif len(target) == 0 and len(exception) != 0:
            return exception.iloc[0]['费率']
        return target.iloc[0]['费率'] * amount
    elif fee_type == 'operation':
        total_rate = data.sum(axis=1).iloc[0]
        return (total_rate / 365) * days * amount


def calculate_total_fee(fond_name, amount, days):
    return calculate_fee(fond_name, 'buy', amount, days) + \
           calculate_fee(fond_name, 'operation', amount, days) + \
           calculate_fee(fond_name, 'sell', amount, days)


# Main App
app.layout = html.Div(
    id='app-container',
    children=[
        # banner
        banner(app),
        # left column
        html.Div(
            id='left-column',
            className='four columns',
            children=[
                generate_title(),
                generate_control_card()
            ]
        ),
        # right column
        html.Div(
            id='right-column',
            className='eight columns',
            children=[
                html.H3("累计费用图表"),
                html.Hr(),
                dcc.Loading(
                    id="loading-2",
                    children=[dcc.Graph(id="fee_dashboard")],
                    type="circle",
                )
            ]
        ),
    ]
)


@app.callback(
    dash.dependencies.Output('fee_dashboard', 'figure'),
    dash.dependencies.Input('amount', 'value'))
def update_graph(amount):
    x = list(range(1, 1000, 7))
    y_a = [calculate_total_fee('a', amount, day) for day in x]
    y_b = [calculate_total_fee('b', amount, day) for day in x]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y_a, name=fond_list[0]))
    fig.add_trace(go.Scatter(x=x, y=y_b, name=fond_list[1]))
    fig.update_traces(mode='lines')
    fig.update_yaxes(rangemode='tozero')

    return fig


@app.callback(
    dash.dependencies.Output('control-detail', 'children'),
    dash.dependencies.Output('buy-table', 'children'),
    dash.dependencies.Output('operation-table', 'children'),
    dash.dependencies.Output('sell-table', 'children'),
    dash.dependencies.Input('unit-switch', 'on'),
    dash.dependencies.Input('fond-select', 'value'))
def update_table(unit_wan, fond_select):
    category_name = get_fond_abbr(fond_select)
    buy_table = generate_fee_table(category_name, 'buy', 10000 if unit_wan else 1)
    operation_table = generate_fee_table(category_name, 'operation')
    sell_table = generate_fee_table(category_name, 'sell')

    description = html.P('在此列举所选 "{}" 中的费率，包括买入费用、运作费用和卖出费。请填入买入金额，以计算各部分及总费用：'.format(fond_select))
    return description, buy_table, operation_table, sell_table


@app.callback(
    dash.dependencies.Output('buy-fee', 'children'),
    dash.dependencies.Input('fond-select', 'value'),
    dash.dependencies.Input('amount', 'value'))
def update_buy_value(fond_select, amount):
    category_name = get_fond_abbr(fond_select)
    return f"申购费用：{calculate_fee(category_name, 'buy', amount, None)}"


@app.callback(
    dash.dependencies.Output('operation-fee', 'children'),
    dash.dependencies.Output('sell-fee', 'children'),
    dash.dependencies.Input('fond-select', 'value'),
    dash.dependencies.Input('amount', 'value'),
    dash.dependencies.Input('days', 'value'))
def update_buy_value(fond_select, amount, days):
    category_name = get_fond_abbr(fond_select)
    operation_fee = f"运作费用：{calculate_fee(category_name, 'operation', amount, days)}"
    sell_fee = f"赎回费用：{calculate_fee(category_name, 'sell', amount, days)}"
    return operation_fee, sell_fee


if __name__ == '__main__':
    app.run_server(debug=True)
