############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Graphs
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import numpy  as np
import plotly.io as pio
import plotly.graph_objects as go

############################################################################

# Function: Build Coordinates
def build_coordinates(distance_matrix):  
    a           = distance_matrix[0,:].reshape(distance_matrix.shape[0], 1)
    b           = distance_matrix[:,0].reshape(1, distance_matrix.shape[0])
    m           = (1/2)*(a**2 + b**2 - distance_matrix**2)
    w, u        = np.linalg.eig(np.matmul(m.T, m))
    s           = (np.diag(np.sort(w)[::-1]))**(1/2) 
    coordinates = np.matmul(u, s**(1/2))
    coordinates = coordinates.real[:,0:2]
    return coordinates

############################################################################

# Function: Solution Plot 
def plot_tour(coordinates, city_tour = [], view = 'browser', size = 10):
    if (coordinates.shape[0] == coordinates.shape[1]):
      coordinates = build_coordinates(coordinates)
    if (view == 'browser' ):
        pio.renderers.default = 'browser'
    if (len(city_tour) > 0):
        xy = np.zeros((len(city_tour), 2))
        for i in range(0, len(city_tour)):
            if (i < len(city_tour)):
                xy[i, 0] = coordinates[city_tour[i]-1, 0]
                xy[i, 1] = coordinates[city_tour[i]-1, 1]
            else:
                xy[i, 0] = coordinates[city_tour[0]-1, 0]
                xy[i, 1] = coordinates[city_tour[0]-1, 1]
    else:
        xy = np.zeros((coordinates.shape[0], 2))
        for i in range(0, coordinates.shape[0]):
            xy[i, 0] = coordinates[i, 0]
            xy[i, 1] = coordinates[i, 1]
    data = []
    Xe   = []
    Ye   = []
    ids  = [ 'id: '+ str(i+1)+'<br>'+'x: '+str(round(coordinates[i,0], 2))+'<br>'+'y: '+str(round(coordinates[i,1], 2))  for i in range(0, coordinates.shape[0])] 
    if (len(city_tour) > 0):
        id0  = 'id: '+str(city_tour[0])+'<br>'+'x: '+str(round(xy[0,0], 2)) +'<br>'+'y: '+str(round(xy[0,1], 2))
    else:
        id0 = 'id: '+str(1)+'<br>'+'x: '+str(round(xy[0,0], 2)) +'<br>'+'y: '+str(round(xy[0,1], 2))
    if (len(city_tour) > 0):
        for i in range(0, xy.shape[0]-1):
            Xe.append(xy[i,0])
            Xe.append(xy[i+1,0])
            Xe.append(None)
            Ye.append(xy[i,1])
            Ye.append(xy[i+1,1])
            Ye.append(None)
        e_trace = go.Scatter(x         = Xe[2:],
                             y         = Ye[2:],
                             mode      = 'lines',
                             line      = dict(color = 'rgba(0, 0, 0, 1)', width = 0.50, dash = 'solid'),
                             hoverinfo = 'none',
                             name      = ''
                             )
        data.append(e_trace)
    n_trace = go.Scatter(x         = coordinates[0:, -2],
                         y         = coordinates[0:, -1],
                         opacity   = 1,
                         mode      = 'markers+text',
                         marker    = dict(symbol = 'circle-dot', size = size, color = 'rgba(46, 138, 199, 1)'),
                         hoverinfo = 'text',
                         hovertext = ids[0:],
                         name      = ''
                         )
    data.append(n_trace)
    m_trace = go.Scatter(x         = xy[0:1, -2],
                         y         = xy[0:1, -1],
                         opacity   = 1,
                         mode      = 'markers+text',
                         marker    = dict(symbol = 'square-dot', size = size, color = 'rgba(247, 138, 54, 1)'),
                         hoverinfo = 'text',
                         hovertext = id0,
                         name      = ''
                         )
    data.append(m_trace)
    layout  = go.Layout(showlegend   = False,
                        hovermode    = 'closest',
                        margin       = dict(b = 10, l = 5, r = 5, t = 10),
                        plot_bgcolor = 'rgb(235, 235, 235)',
                        xaxis        = dict(  showgrid       = True, 
                                              zeroline       = True, 
                                              showticklabels = True, 
                                              tickmode       = 'array', 
                                           ),
                        yaxis        = dict(  showgrid       = True, 
                                              zeroline       = True, 
                                              showticklabels = True,
                                              tickmode       = 'array', 
                                            )
                        )
    fig = go.Figure(data = data, layout = layout)
    if (len(city_tour) > 0):
        fig.add_annotation(
                           x          = Xe[1]*1.00,  # to x
                           y          = Ye[1]*1.00,  # to y
                           ax         = Xe[0]*1.00,  # from x
                           ay         = Ye[0]*1.00,  # from y
                           xref       = 'x',
                           yref       = 'y',
                           axref      = 'x',
                           ayref      = 'y',
                           text       = '',
                           showarrow  = True,
                           arrowhead  = 3,
                           arrowsize  = 1.5,
                           arrowwidth = 2,
                           arrowcolor = 'red',
                           opacity    = 1
                       )
    fig.update_traces(textfont_size = 10, textfont_color = 'rgb(255, 255, 255)') 
    fig.show() 
    return

############################################################################