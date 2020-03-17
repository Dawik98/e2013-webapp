import dash
import dash_core_components as dcc 
import dash_html_components as html 


header = html.Header(className='site-heaader',
            children = html.Nav(className="navbar navbar-expand-md navbar-dark bg-steel fixed-top",
            children = html.Div(className='container',
            children = html.Div(className="navbar-nav mr-auto", 
            children = [
                html.A("E2013", className='navbar-brand mr-4', href="/",),
                html.A("Home", className='nav-item nav-link', href="/",),
                html.A("Sensor Data", className='nav-item nav-link', href="/SensorData",),
                html.A("test 1", className='nav-item nav-link', href="/test1/",),
                html.A("test 2", className='nav-item nav-link', href="/test2/",),
            ])#Div
            )#Div
            )#Nav
            )#header