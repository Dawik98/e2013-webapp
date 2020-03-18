import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc 
import dash_html_components as html 

#import standard layout
from layout import header


main_body = html.Main(role='main', className='container', children=
    html.Div(className='row', children=
    html.Article(className = "media content-section", children =
    html.Div(className="media-body", children=[
        dcc.Input(id='input', value='Enter something', type='text'),
        html.Div(id='output'),
    ])#div
    )#article
    )#div
    )#main

layout = html.Div(children = [
    header,
    main_body
])

def callbacks(app):
    @app.callback(
        Output(component_id='output', component_property='children'),
        [Input(component_id='input', component_property='value')]
    )
    def update_value(input_data):
        try:
            return str(float(input_data)**2)
        except:
            return "Some error"

        
#if __name__ == "__main__":
#    app.run_server(debug=True)