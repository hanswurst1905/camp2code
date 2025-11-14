from dash import Dash, html, dcc, Input, Output     # dcc = dash core components
import base_car as bc
import dash_bootstrap_components as dbc # Grundprinzip Einteilung der Website in Zeilen und Spalten (12 Spalten, damit lässt sich seite gut halbiern, drittln, vierteln oder sechsteln)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])    # interner name der Website/Dashboard

#app.layout = html.Div(  # HTML Gerüst für gesamte Webseite [nur ein Element deshalb mehrere Elemente als Liste übergeben]
#     [                 
#     html.H1("Hallo Projektphase 1", id="h-1"),    # Header (Überschrift) / ID- muss eindeutig sein (nicht mehrfach verwenden)
#     dcc.Slider(min=0,max=10, id="slider-1",step=0.5),           # aktiv etwas machen (input erzeugen) dann dcc Modul [Ausnahme Button der ist html]
#     dcc.Dropdown(options=["hallo","tschüss"], value="initialwert", id="dd-1"),    # Eventhandler steckt in Input
#     dcc.Dropdown(options=["Peter","Oliver","Selman","Matthias"], value="irgendwas", id="dd-2")
#     ]
# )
app.layout = html.Div([dbc.Row([html.H1("Hallo Projektphase 1", id="h-1")]),
                       dbc.Row([dcc.Slider(min=0,max=10, id="slider-1",step=0.5),
                                dcc.Dropdown(options=["hallo","tschüss"], value="initialwert", id="dd-1"),
                                dcc.Dropdown(options=["Peter","Oliver","Selman","Matthias"], value="irgendwas", id="dd-2")
                            ])
                       ])

@app.callback(                     # jede Funktionalität benötigt Input und Output - (Dekorator der die Funktion Callback registriert) - müssen hier nicht als Liste übergeben werden
    Output("h-1", "children"),     # das was verändert werden soll 
    Input("dd-1", "value"),        # z.B. Dropdown
    Input("slider-1","value")     
)
def change_greeting(in1,in2):     # Reihenfolge und Anzahl der oben definierten Inputs beachten
    return f"{in1} du!"           # Anzahl der oben definierten Outpus beachten

@app.callback(                      # weitere Funktionalitäten
    Output("h-1", "children", allow_duplicate=True),      # Output von oben übernommen, weil er doppelt verwendet werden soll "allow_duplicate"
    Input("dd-2", "value"),
    prevent_initial_call=True        # weil beim start der App jede Funktionalität getestet wird und ein doppelt verwendeter Output nur einmal getestet werden kann wird der Test hier mit übersprungen
    )
def change_name(in1):    
    return f"{in1} du!" 

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8051,debug=True) # host IP-Adresse (vergleichbar mit einem Haus) port (vergleichbar mit Zimmernummer)
