import dash_html_components as html
import pandas as pd


def banner(app):
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.H5("Fondpedia"),
            html.Img(src=app.get_asset_url("plotly_logo.png")),
        ],
    )


class DataFetcher:
    def __init__(self):
        self.warehouse = dict()

    def get_data(self, fond_name: str, fee_type: str):
        key = fond_name + fee_type
        if key in self.warehouse:
            return self.warehouse[key]
        else:
            tmp = self.__fetch_data(fond_name, fee_type)
            self.warehouse[key] = tmp
            return tmp

    def __fetch_data(self, fond_name, fee_type):

        df_data = pd.read_csv(f'example/{fee_type}.csv')
        df_data = df_data[df_data.fond == fond_name]
        data = df_data.drop('fond', 1)
        return data
