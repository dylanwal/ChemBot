from dash import html, dcc

tab1_layout = html.Div([
    html.H3('Enter data to send to RabbitMQ'),
    dcc.Input(id='message-input', type='text', value=''),
    html.Button('Send', id='send-button', n_clicks=0),
    html.Div(id='send-message-status')
])
