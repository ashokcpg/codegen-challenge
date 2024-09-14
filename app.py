from flask import Flask, render_template, send_file
import os
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO

app = Flask(__name__)

def parse_imports(file_path):
    imports = []
    with open(file_path, "r") as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("import "):
                parts = line.split()
                if len(parts) > 1:
                    imports.append(parts[1])
            elif line.startswith("from "):
                parts = line.split()
                if len(parts) > 3 and parts[2] == "import":
                    imports.append(f"{parts[1]}.{parts[3]}")
    return imports

def build_import_graph(codebase_path):
    graph = nx.DiGraph()
    
    for root, _, files in os.walk(codebase_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                imports = parse_imports(file_path)
                for imp in imports:
                    graph.add_edge(file, imp)
    
    return graph

def identify_critical_nodes(graph):
    # Identify nodes with high in-degree (frequently imported)
    in_degrees = graph.in_degree()
    critical_nodes = [node for node, degree in in_degrees if degree > 1]  # Adjust threshold as needed
    return critical_nodes

def identify_circular_dependencies(graph):
    try:
        cycles = list(nx.find_cycle(graph, orientation='original'))
        return cycles
    except nx.NetworkXNoCycle:
        return []

def draw_insights(graph):
    critical_nodes = identify_critical_nodes(graph)
    circular_dependencies = identify_circular_dependencies(graph)
    
    insights = []
    insights.append("Insights about the codebase:")
    insights.append(f"Total number of nodes (files and imports): {len(graph.nodes)}")
    insights.append(f"Total number of edges (dependencies): {len(graph.edges)}")
    insights.append(f"Number of critical nodes (frequently imported): {len(critical_nodes)}")
    insights.append(f"Critical nodes: {', '.join(critical_nodes)}")
    
    if circular_dependencies:
        insights.append(f"Number of circular dependencies: {len(circular_dependencies)}")
        insights.append(f"Circular dependencies: {', '.join([f'{u} -> {v}' for u, v, _ in circular_dependencies])}")
    else:
        insights.append("No circular dependencies found.")
    
    return "\n".join(insights)

def visualize_graph(graph, output_format='png'):
    num_nodes = len(graph.nodes)
    fig_size = max(14, num_nodes / 5)  # Adjust the figure size based on the number of nodes
    
    pos = nx.spring_layout(graph)
    plt.figure(figsize=(fig_size, fig_size))
    
    critical_nodes = identify_critical_nodes(graph)
    circular_dependencies = identify_circular_dependencies(graph)
    
    # Set node sizes based on the number of imports (in-degree)
    node_sizes = [3000 + 100 * graph.in_degree(node) for node in graph.nodes]
    
    # Convert nodes to a list for indexing
    nodes_list = list(graph.nodes)
    
    # Draw all nodes and edges
    nx.draw(graph, pos, with_labels=True, node_size=node_sizes, node_color="skyblue", font_size=10, font_weight="bold", arrows=True)
    
    # Highlight critical nodes
    nx.draw_networkx_nodes(graph, pos, nodelist=critical_nodes, node_color="red", node_size=[node_sizes[nodes_list.index(node)] for node in critical_nodes], label="Critical Nodes")
    
    # Highlight circular dependencies
    if circular_dependencies:
        circular_edges = [(u, v) for u, v, _ in circular_dependencies]
        nx.draw_networkx_edges(graph, pos, edgelist=circular_edges, edge_color='orange', width=2, label="Circular Dependencies")
    
    # Adding legends
    import_nodes = [node for node in graph.nodes if not node.endswith(".py")]
    file_nodes = [node for node in graph.nodes if node.endswith(".py")]
    
    nx.draw_networkx_nodes(graph, pos, nodelist=import_nodes, node_color="lightgreen", label="Imports")
    nx.draw_networkx_nodes(graph, pos, nodelist=file_nodes, node_color="skyblue", label="Files")
    
    plt.legend(scatterpoints=1)
    plt.title("Enhanced Import Graph Visualization")
    
    if output_format == 'pdf':
        pdf = BytesIO()
        with PdfPages(pdf) as pdf_pages:
            pdf_pages.savefig()
        pdf.seek(0)
        return pdf
    else:
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        return img

@app.route('/')
def index():
    codebase_path = "./example-codebase"  # Set the path to your codebase
    import_graph = build_import_graph(codebase_path)
    insights = draw_insights(import_graph)  # Draw insights about the codebase
    return render_template('index.html', insights=insights)

@app.route('/graph')
def graph():
    codebase_path = "./example-codebase"  # Set the path to your codebase
    import_graph = build_import_graph(codebase_path)
    img = visualize_graph(import_graph)
    return send_file(img, mimetype='image/png')

@app.route('/graph/pdf')
def graph_pdf():
    codebase_path = "./example-codebase"  # Set the path to your codebase
    import_graph = build_import_graph(codebase_path)
    pdf = visualize_graph(import_graph, output_format='pdf')
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name='import_graph.pdf')

if __name__ == '__main__':
    app.run(debug=True)
