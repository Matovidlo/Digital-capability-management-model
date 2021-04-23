# Dashboard using dash and plotly
# Callbacks are registered trough view

import itertools
import dash
import dash_core_components as dcc
import dash_html_components as html
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go


def setup_layout(app):
    app.layout = html.Div([
        html.P("Graph types:"),
        dcc.Dropdown(
                id='graph_type',
                value='pie',
                options=[{'value': x, 'label': x}
                         for x in ['pie', 'bar', 'bubble']],
                clearable=False
        ),
        html.P("Values:"),
        dcc.Dropdown(
                id='values',
                value='Count_labels',
                options=[{'value': x, 'label': x}
                         for x in ['Count_labels', 'Committer']],
                clearable=False
        ),
        dcc.Graph(id="pie-chart"),
        # Create milestones treemap
        dcc.Graph(id='milestones-graph'),
        # Create layout for network graph
        dcc.Graph(id='network-graph')
    ])
    return app


def create_edges(graph, connections):
    edges = []
    for key, connection in connections.items():
        for value in connection['titles']:
            edges.append((key, value))
    graph.add_edges_from(edges)
    edge_x = []
    edge_y = []
    # Add two nodes positions of edge start x0, y0 and edge end x1, y1
    for edge in graph.edges():
        x0, y0 = graph.nodes[edge[0]]['pos']
        x1, y1 = graph.nodes[edge[1]]['pos']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
    edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.7, color='#888'),
            hoverinfo='none',
            mode='lines')
    return graph, edge_trace


def get_random_layout(G, dim=2, low=0.0, high=1.0):
    import numpy as np

    shape = (len(G), dim)
    pos = []
    single_tuple = []
    for single in range(shape[0]):
        for dimension in range(dim):
            single_tuple.append(np.random.uniform(low, high))
        pos.append(single_tuple)
        single_tuple = []
    pos = dict(zip(G, pos))

    return pos


def create_nodes(graph, connections):
    graph.add_nodes_from(list(connections.keys()))
    nodes = [connection['titles'] for connection in connections.values()]
    nodes = list(itertools.chain(*nodes))
    graph.add_nodes_from(nodes)
    # Add positions of the graph nodes
    pos = get_random_layout(graph, low=12, high=125.0)
    nodes_x = []
    nodes_y = []
    # Add coordinates of single node x, y position in graph
    for x, y in pos.items():
        graph.nodes[x]['pos'] = y
        nodes_x.append(y[0])
        nodes_y.append(y[1])
    node_trace = go.Scatter(
            x=nodes_x, y=nodes_y,
            mode='markers',
            hoverinfo='text',
            marker=dict(
                    showscale=True,
                    # colorscale options
                    # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
                    # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
                    # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
                    colorscale='YlGnBu',
                    reversescale=True,
                    color=[],
                    size=8,
                    colorbar=dict(
                            thickness=25,
                            title='Node Connections',
                            xanchor='left',
                            titleside='right'
                    ),
                    line_width=2))
    return graph, node_trace


def compute_adjacency(graph, node_trace):
    node_adjacency = []
    node_text = []
    for node, adjacencies in enumerate(graph.adjacency()):
        node_adjacency.append(len(adjacencies[1]))
        node_text.append(adjacencies[0] + ' number of connections: ' + str(len(adjacencies[1])))
    # Color node traces
    node_trace.marker.color = node_adjacency
    node_trace.text = node_text
    return graph, node_trace


pie_chart_colors = ['rgb(56, 75, 126)', 'rgb(0, 102, 0)', 'rgb(18, 36, 37)',
                    'rgb(128, 0, 0)', 'rgb(6, 4, 4)']
bar_colors = ['rgb(128, 0, 0)', 'rgb(56, 75, 126)', 'rgb(18, 36, 37)',
              'rgb(0, 102, 0)']


def register_callbacks(app, dataframe, connections, milestones):
    @app.callback(
            dash.dependencies.Output("pie-chart", "figure"),
            [dash.dependencies.Input("values", "value"),
             dash.dependencies.Input("graph_type", "value")])
    def generate_chart(values, graph_type):
        filtered = dataframe[dataframe['Graph_type'].eq(graph_type)]
        if graph_type == 'pie':
            fig = go.Figure(data=[go.Pie(labels=filtered['Labels'],
                                         values=filtered[values],
                                         textinfo='label+percent',
                                         name='piechart',
                                         marker_colors=pie_chart_colors)])
        elif graph_type == 'bar':
            fig = px.bar(filtered, y=values, x='Labels', text=values,
                         hover_data=[values], color=bar_colors)
            # Update layout of the bar chart
            fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
            fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        else:
            fig = go.Figure(data=[go.Scatter(
                    x=filtered[values], y=filtered['Labels'],
                    mode='markers',
                    marker=dict(
                            color=['rgb(255, 65, 54)', 'rgb(44, 160, 101)',
                                   'rgb(93, 164, 214)', 'rgb(255, 144, 14)'],
                            size=filtered[values],
                            sizeref=2. * max(filtered[values]) / (40. ** 2),
                            sizemode='area',
                            sizemin=4
                    )
            )])
        return fig

    @app.callback(dash.dependencies.Output('milestones-graph', 'figure'),
                  dash.dependencies.Input('milestones-graph', 'value'))
    def milestones_graph(value):
        tags = list(milestones.keys())
        labels = list(milestones.keys())
        parents = [''] * len(tags)
        # fixme: add colors?
        color = []
        counter = 0
        for index, milestone in enumerate(milestones.values()):
            for title in milestone['title']:
                # Add tag as parent for each issue
                parents.append(tags[index])
                # When title is present in tags, set new id
                labels.append(title)
                if title in tags:
                    # Add issue to treemap but change it's identifier
                    idx = tags.index(title)
                    tags.append(title + '_' + str(counter))
                    counter += 1
                else:
                    # Add issue to treemap
                    tags.append(title)

        fig = go.Figure(go.Treemap(
                labels=labels,
                parents=parents,
                ids=tags
        ))
        return fig

    @app.callback(dash.dependencies.Output('network-graph', 'figure'),
                  dash.dependencies.Input('network-graph', 'value'))
    def update_graph_elements(value):
        G = nx.Graph()
        G, node_trace = create_nodes(G, connections)
        G, edge_trace = create_edges(G, connections)
        G, node_trace = compute_adjacency(G, node_trace)
        fig = go.Figure(
                data=[edge_trace, node_trace],
                layout=go.Layout(
                        title='Network graph representing DCMM relationships of issues',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=30),
                        annotations=[dict(
                                text='Generated by plotly',
                                showarrow=False,
                                xref="paper", yref="paper",
                                x=5, y=-2)],
                        xaxis=dict(showgrid=False, zeroline=False,
                                   showticklabels=True),
                        yaxis=dict(showgrid=False, zeroline=False,
                                   showticklabels=False),
                        height=900,
                        width=1250)
        )
        return fig

    return app
