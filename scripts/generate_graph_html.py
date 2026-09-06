#!/usr/bin/env python3
"""
generate_graph_html.py
----------------------
Generates the complete graph/index.html application with:
1. Multi-level hierarchy support (190 collections across 6 levels L0-L6).
2. Level-of-Detail (LOD) depth selector.
3. Interactive Ordnerbaum (Tree View) Modal & Drawer with search and auto-expansion.
4. ARCHE Live File Preview (thumbnails via arche-thumbnails.acdh.oeaw.ac.at with CORS support & InC fallback).
5. Breadcrumb trails and sub-folder navigation in the Node Inspector.
6. Quick-Preview Lightbox Modal for resources in both the Corpus-Katalog and the Graph.
"""

import os
import json

def generate():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    data_dir = os.path.join(project_root, "data")
    
    graph_file = os.path.join(data_dir, "arche_graph.json")
    tree_file = os.path.join(data_dir, "arche_collections_tree.json")
    out_html = os.path.join(project_root, "graph", "index.html")
    
    with open(graph_file, "r", encoding="utf-8") as f:
        graph_data = json.load(f)
        
    with open(tree_file, "r", encoding="utf-8") as f:
        tree_data = json.load(f)
        
    embedded_graph_json = json.dumps(graph_data, ensure_ascii=False)
    embedded_tree_json = json.dumps(tree_data, ensure_ascii=False)

    html_content = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IUENNA – ARCHE Knowledge Graph &amp; Corpus Explorer</title>
    
    <!-- Dublin Core Metatags -->
    <meta name="DC.title" content="IUENNA – ARCHE Knowledge Graph &amp; Corpus Explorer">
    <meta name="DC.creator" content="Dominik Hagmann">
    <meta name="DC.creator" content="Franziska Waldhart">
    <meta name="DC.publisher" content="Go!Digital 3.0 Project IUENNA">
    <meta name="DC.subject" content="IUENNA, ARCHE, Knowledge Graph, Cytoscape, Linked Open Data, Archaeology, Corpus">
    <meta name="DC.description" content="Interaktive Wissensgraph- und Korpus-Visualisierung der archäologischen Bestände von IUENNA im Repositorium ARCHE (ACDH-CH / ÖAW). Umfasst alle 20.788 Einträge, 190 Sammlungen/Ordner und 20.541 Primärressourcen mit Live-Dateivorschau.">
    
    <!-- Google Fonts & Font Awesome -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="../styles.css?v=2.1.8">

    <!-- Cytoscape.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>

    <style>
        :root {{
            --graph-bg: #FAF8F5;
            --panel-bg: rgba(255, 255, 255, 0.96);
            --panel-border: #E6E2DB;
            --color-l0: #A8442E;
            --color-l1: #B88E3E;
            --color-l2: #C29243;
            --color-l3: #3D7068;
            --color-l4: #5A6B7C;
            --color-l5: #7E6B8F;
            --color-l6: #9B59B6;
            --color-resource: #3D7068;
            --color-organization: #202226;
            --color-person: #C85A32;
            --color-place: #4A6B53;
            --color-period: #5A6B7C;
            --color-subject: #7E6B8F;
            --color-license: #437F97;
        }}

        body {{
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
            background-color: var(--graph-bg);
        }}

        /* Header Bar */
        .graph-header-bar {{
            background: #FFFFFF;
            border-bottom: 1px solid var(--panel-border);
            padding: 8px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
            z-index: 100;
        }}

        .graph-title-group h1 {{
            font-size: 1.18rem;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-dark);
        }}
        .graph-title-group h1::after {{ display: none; }}
        .graph-title-group p {{
            font-size: 0.78rem;
            color: var(--text-muted);
            margin: 0;
        }}

        .stats-pills {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            align-items: center;
        }}

        .stat-pill {{
            background: var(--bg-main);
            border: 1px solid var(--panel-border);
            padding: 3px 9px;
            border-radius: 20px;
            font-size: 0.73rem;
            font-weight: 600;
            color: var(--text-dark);
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }}
        .stat-pill i {{ color: var(--primary); }}
        .stat-pill a {{ color: inherit; text-decoration: none; }}
        .stat-pill a:hover {{ color: var(--primary); text-decoration: underline; }}

        /* Toolbar */
        .graph-toolbar {{
            background: #FFFFFF;
            border-bottom: 1px solid var(--panel-border);
            padding: 7px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            flex-wrap: wrap;
            z-index: 90;
        }}

        .toolbar-left, .toolbar-right {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .tool-select {{
            border: 1px solid var(--panel-border);
            background: #FFFFFF;
            font-size: 0.76rem;
            font-weight: 500;
            color: var(--text-dark);
            padding: 4px 8px;
            border-radius: 6px;
            cursor: pointer;
        }}

        .tool-btn {{
            border: 1px solid var(--panel-border);
            background: #FFFFFF;
            color: var(--text-dark);
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 0.76rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }}
        .tool-btn:hover {{
            background: var(--bg-main);
            border-color: var(--text-dark);
        }}
        .tool-btn.primary-btn {{
            background: var(--primary);
            color: #FFFFFF;
            border-color: var(--primary);
        }}
        .tool-btn.primary-btn:hover {{
            background: var(--primary-hover);
        }}
        .tool-btn.secondary-btn {{
            background: #FAF8F5;
            border-color: var(--secondary);
            color: var(--text-dark);
        }}

        /* Search Autocomplete */
        .search-box-wrapper {{
            position: relative;
        }}
        .search-input {{
            border: 1px solid var(--panel-border);
            background: #FFFFFF;
            padding: 5px 10px 5px 28px;
            border-radius: 20px;
            font-size: 0.76rem;
            width: 240px;
            transition: all 0.2s;
            outline: none;
        }}
        .search-input:focus {{
            width: 320px;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(168, 68, 46, 0.12);
        }}
        .search-icon {{
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.75rem;
            color: var(--text-muted);
            pointer-events: none;
        }}
        .search-dropdown {{
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: #FFFFFF;
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            box-shadow: var(--shadow-lg);
            margin-top: 4px;
            max-height: 380px;
            overflow-y: auto;
            display: none;
            z-index: 1000;
            min-width: 340px;
        }}
        .search-section-header {{
            padding: 6px 12px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            color: var(--text-muted);
            background: #F7F5F0;
            border-bottom: 1px solid var(--panel-border);
        }}
        .search-item {{
            padding: 8px 12px;
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            border-bottom: 1px solid #F5F3EF;
            font-size: 0.76rem;
        }}
        .search-item:hover {{
            background: var(--bg-main);
        }}

        /* Filter Chips */
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 5px;
            flex-wrap: wrap;
        }}
        .filter-chip {{
            border: 1px solid var(--panel-border);
            background: #FFFFFF;
            color: var(--text-muted);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.74rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.2s ease;
            user-select: none;
        }}
        .filter-chip:hover {{
            border-color: var(--text-dark);
            color: var(--text-dark);
        }}
        .filter-chip.active {{
            background: var(--text-dark);
            color: #FFFFFF;
            border-color: var(--text-dark);
        }}
        .filter-chip .chip-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }}

        /* Stage & Canvas */
        .stage-container {{
            flex: 1;
            position: relative;
            width: 100%;
            overflow: hidden;
            background: radial-gradient(#E6E2DB 1px, transparent 1px);
            background-size: 24px 24px;
        }}
        #cy {{
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
        }}

        /* Floating Legend */
        .legend-card {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: var(--panel-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--panel-border);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-md);
            padding: 10px 14px;
            max-width: 270px;
            font-size: 0.72rem;
            z-index: 50;
            transition: all 0.25s ease;
        }}
        .legend-header {{
            font-weight: 700;
            color: var(--text-dark);
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
            cursor: pointer;
        }}
        .legend-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin: 0;
            padding: 0;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-muted);
        }}
        .legend-icon {{
            width: 10px;
            height: 10px;
            border-radius: 3px;
            display: inline-block;
            flex-shrink: 0;
        }}

        /* Inspector Drawer */
        .inspector-drawer {{
            position: absolute;
            top: 15px;
            right: 15px;
            bottom: 15px;
            width: 400px;
            background: var(--panel-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--panel-border);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            display: flex;
            flex-direction: column;
            transform: translateX(450px);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 80;
            overflow: hidden;
        }}
        .inspector-drawer.open {{
            transform: translateX(0);
        }}

        .drawer-header {{
            padding: 14px 18px;
            border-bottom: 1px solid var(--panel-border);
            background: #FFFFFF;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .drawer-header-top {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
        }}
        .drawer-breadcrumb {{
            font-size: 0.68rem;
            color: var(--text-muted);
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            align-items: center;
            margin-bottom: 2px;
        }}
        .drawer-breadcrumb-pill {{
            background: #EDE8E0;
            padding: 1px 6px;
            border-radius: 3px;
            cursor: pointer;
            color: var(--text-dark);
            text-decoration: none;
        }}
        .drawer-breadcrumb-pill:hover {{
            background: var(--primary);
            color: #FFFFFF;
        }}
        .drawer-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #FFFFFF;
            align-self: flex-start;
        }}
        .drawer-title {{
            font-family: var(--font-header);
            font-size: 1.1rem;
            color: var(--text-dark);
            line-height: 1.3;
            margin: 2px 0 0 0;
            word-break: break-word;
        }}
        .drawer-title::after {{ display: none; }}
        .drawer-close-btn {{
            background: none;
            border: none;
            font-size: 1.2rem;
            color: var(--text-muted);
            cursor: pointer;
            padding: 4px;
            line-height: 1;
        }}
        .drawer-close-btn:hover {{ color: var(--primary); }}

        .drawer-body {{
            padding: 16px 18px;
            overflow-y: auto;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}

        /* Live Preview Card */
        .drawer-preview-box {{
            background: #FFFFFF;
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            overflow: hidden;
            display: none;
            flex-shrink: 0;
            width: 100%;
        }}
        .drawer-preview-header {{
            padding: 6px 12px;
            background: #F7F5F0;
            border-bottom: 1px solid var(--panel-border);
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .drawer-preview-media {{
            position: relative;
            min-height: 180px;
            max-height: 260px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #1A1A1A;
            overflow: hidden;
        }}
        .drawer-preview-img {{
            max-width: 100%;
            max-height: 260px;
            object-fit: contain;
            transition: opacity 0.3s ease;
        }}
        .drawer-preview-fallback {{
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 24px 16px;
            text-align: center;
            color: #FFFFFF;
        }}
        .drawer-preview-fallback i {{
            font-size: 2rem;
            color: #E0A96D;
            margin-bottom: 8px;
        }}
        .drawer-preview-footer {{
            padding: 6px 12px;
            font-size: 0.72rem;
            color: var(--text-muted);
            border-top: 1px solid var(--panel-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #FAF8F5;
        }}

        .drawer-stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }}
        .drawer-stat-card {{
            background: var(--bg-main);
            border: 1px solid var(--panel-border);
            border-radius: var(--radius-sm);
            padding: 8px;
            text-align: center;
        }}
        .drawer-stat-val {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--primary);
        }}
        .drawer-stat-lbl {{
            font-size: 0.68rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }}

        .drawer-section-title {{
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 5px;
            border-bottom: 1px solid #EDE8E0;
            padding-bottom: 3px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .relations-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 5px;
            margin: 0;
            padding: 0;
        }}
        .relation-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 5px 8px;
            background: #FFFFFF;
            border: 1px solid var(--panel-border);
            border-radius: 5px;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.15s;
        }}
        .relation-item:hover {{
            border-color: var(--primary);
            background: var(--bg-main);
        }}
        .relation-target {{
            font-weight: 600;
            color: var(--text-dark);
            display: flex;
            align-items: center;
            gap: 6px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .relation-label {{
            font-size: 0.68rem;
            color: var(--text-muted);
            font-family: monospace;
            background: var(--bg-main);
            padding: 1px 5px;
            border-radius: 3px;
            flex-shrink: 0;
        }}

        .drawer-footer {{
            padding: 12px 18px;
            border-top: 1px solid var(--panel-border);
            background: #FFFFFF;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        /* Modals Backdrop */
        .modal-backdrop {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(32, 34, 38, 0.6);
            backdrop-filter: blur(4px);
            z-index: 1200;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }}
        .modal-backdrop.open {{
            display: flex;
        }}

        .modal-card {{
            background: #FFFFFF;
            border: 1px solid var(--panel-border);
            border-radius: var(--radius-lg);
            width: 100%;
            max-width: 1100px;
            height: 88vh;
            display: flex;
            flex-direction: column;
            box-shadow: var(--shadow-lg);
            overflow: hidden;
        }}

        .modal-header {{
            padding: 16px 24px;
            border-bottom: 1px solid var(--panel-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #FAF8F5;
        }}
        .modal-header h2 {{
            font-size: 1.25rem;
            margin: 0;
            color: var(--text-dark);
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .modal-header h2::after {{ display: none; }}

        /* Tree View Styles */
        .tree-scroll-area {{
            flex: 1;
            overflow-y: auto;
            padding: 16px 24px;
        }}
        .tree-node-row {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 5px 8px;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.15s ease;
            font-size: 0.82rem;
        }}
        .tree-node-row:hover {{
            background: #EDE8E0;
        }}
        .tree-toggle-btn {{
            width: 18px;
            height: 18px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            color: var(--text-muted);
            cursor: pointer;
            border-radius: 3px;
        }}
        .tree-toggle-btn:hover {{
            background: rgba(0,0,0,0.08);
            color: var(--text-dark);
        }}
        .tree-node-children {{
            margin-left: 22px;
            border-left: 1px dashed #D0C9BF;
            padding-left: 8px;
        }}
        .tree-level-badge {{
            font-size: 0.65rem;
            font-weight: 700;
            padding: 1px 6px;
            border-radius: 4px;
            color: #FFFFFF;
            text-transform: uppercase;
        }}
        .tree-actions {{
            margin-left: auto;
            display: flex;
            gap: 6px;
            opacity: 0.85;
        }}
        .tree-action-btn {{
            border: 1px solid var(--panel-border);
            background: #FFFFFF;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            cursor: pointer;
        }}
        .tree-action-btn:hover {{
            background: var(--primary);
            color: #FFFFFF;
            border-color: var(--primary);
        }}

        /* Corpus Catalog Table */
        .corpus-table-container {{
            flex: 1;
            overflow-y: auto;
            padding: 0;
        }}
        .corpus-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }}
        .corpus-table th {{
            position: sticky;
            top: 0;
            background: #F7F5F0;
            padding: 10px 14px;
            text-align: left;
            font-weight: 700;
            color: var(--text-dark);
            border-bottom: 1px solid var(--panel-border);
            z-index: 10;
        }}
        .corpus-table td {{
            padding: 8px 14px;
            border-bottom: 1px solid #F0ECE4;
            color: var(--text-dark);
            vertical-align: middle;
        }}
        .corpus-table tr:hover {{
            background: #FAF8F5;
        }}

        /* Quick Preview Modal */
        .quick-preview-dialog {{
            background: #FFFFFF;
            border: 1px solid var(--panel-border);
            border-radius: var(--radius-lg);
            width: 100%;
            max-width: 780px;
            overflow: hidden;
            box-shadow: var(--shadow-lg);
            display: flex;
            flex-direction: column;
        }}

        @media (max-width: 900px) {{
            .inspector-drawer {{
                left: 10px;
                right: 10px;
                bottom: 10px;
                top: auto;
                height: 55vh;
                width: auto;
                transform: translateY(110%);
            }}
            .inspector-drawer.open {{
                transform: translateY(0);
            }}
            .legend-card {{ display: none; }}
            .search-input {{ width: 150px; }}
            .search-input:focus {{ width: 200px; }}
        }}
    </style>
</head>
<body>

    <!-- Main Navigation Header -->
    <header class="nav-header">
        <div class="nav-container">
            <a href="../index.html" class="nav-brand">
                <img src="https://raw.githubusercontent.com/IUENNA/IUENNA.github.io/refs/heads/main/media/LOGO_IUENNA.jpg" alt="IUENNA Logo" class="nav-logo">
                <span class="nav-title">IUENNA</span>
            </a>
            <nav>
                <ul class="nav-links">
                    <li><a href="../index.html" class="nav-link">Home</a></li>
                    <li><a href="../wma/wma.html" class="nav-link">Web Mapping</a></li>
                    <li><a href="index.html" class="nav-link active" style="color: var(--primary); font-weight: 600;">ARCHE Graph</a></li>
                    <li><a href="https://iuenna.hypotheses.org/" target="_blank" class="nav-link">Blog</a></li>
                    <li><a href="https://id.acdh.oeaw.ac.at/iuenna" target="_blank" class="nav-link btn btn-secondary" style="color: white; padding: 6px 16px;">ARCHE Data</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <!-- App Bar & Collection Stats -->
    <div class="graph-header-bar">
        <div class="graph-title-group">
            <h1><i class="fa-solid fa-circle-nodes" style="color: var(--primary);"></i> ARCHE Knowledge Graph &amp; Corpus Explorer</h1>
            <p>Vollständiges semantisches Netzwerk &amp; Archiv-Korpus des IUENNA-Repositoriums auf ARCHE (ACDH-CH / ÖAW)</p>
        </div>
        <div class="stats-pills">
            <span class="stat-pill"><i class="fa-solid fa-box-archive"></i> <strong id="pillItems">20.788</strong> ARCHE-Einträge</span>
            <span class="stat-pill"><i class="fa-solid fa-file-lines"></i> <strong id="pillResources">20.541</strong> Primärressourcen</span>
            <span class="stat-pill"><i class="fa-solid fa-folder-tree"></i> <strong id="pillCollections">190</strong> Sammlungen &amp; Ordner</span>
            <span class="stat-pill"><i class="fa-solid fa-hard-drive"></i> <strong id="pillSize">356.68 GB</strong></span>
            <span class="stat-pill"><i class="fa-solid fa-network-wired"></i> <strong id="pillVisibleNodes">215</strong> im Graphen</span>
            <span class="stat-pill" id="pillCorpusStatus" style="background: #EBF3ED; border-color: #B5D5BD; color: #2E6038;">
                <i class="fa-solid fa-circle-check"></i> Korpus bereit
            </span>
            <span class="stat-pill"><i class="fa-solid fa-link"></i> <a href="https://hdl.handle.net/21.11115/0000-0016-7B39-F" target="_blank" title="Persistent Identifier auf ARCHE">PID: 21.11115/0000-0016-7B39-F</a></span>
        </div>
    </div>

    <!-- Controls Toolbar -->
    <div class="graph-toolbar">
        <div class="toolbar-left">
            <!-- Layout Selector -->
            <label for="layoutSelect" style="font-size: 0.76rem; font-weight: 600; color: var(--text-dark);">Layout:</label>
            <select id="layoutSelect" class="tool-select">
                <option value="cose" selected>Force-Directed (Organisch)</option>
                <option value="concentric">Konzentrisch (Hierarchie-Ringe)</option>
                <option value="breadthfirst">Baum-Hierarchie (Tree)</option>
                <option value="circle">Kreis (Zirkulär)</option>
            </select>

            <!-- Depth Filter (LOD) -->
            <label for="depthSelect" style="font-size: 0.76rem; font-weight: 600; color: var(--text-dark); margin-left: 6px;">Tiefe:</label>
            <select id="depthSelect" class="tool-select" title="Hierarchie-Tiefe im Graphen filtern">
                <option value="all" selected>Alle Ebenen (L1–L6, 190 Ordner)</option>
                <option value="1">Ebene 1 (6 Subcollections)</option>
                <option value="2">Ebene 2 (Hauptordner &amp; Archivalien)</option>
                <option value="3">Ebene 3 (Fachordner)</option>
            </select>

            <!-- Ordnerbaum Button -->
            <button id="btnOpenTreeModal" class="tool-btn secondary-btn" title="Vollständigen ARCHE-Archivbaum aller 190 Ordner erkunden">
                <i class="fa-solid fa-folder-tree" style="color: var(--secondary);"></i> Ordnerbaum (190)
            </button>

            <!-- Corpus Catalog Drawer Button -->
            <button id="btnOpenCorpus" class="tool-btn primary-btn" title="Katalog aller 20.541 ARCHE-Ressourcen durchsuchen">
                <i class="fa-solid fa-database"></i> Corpus-Katalog (20.541)
            </button>

            <!-- Search Autocomplete -->
            <div class="search-box-wrapper">
                <i class="fa-solid fa-magnifying-glass search-icon"></i>
                <input type="text" id="searchInput" class="search-input" placeholder="20.788 ARCHE-Einträge durchsuchen (z.B. Mosaik, Drohne, glo10)..." autocomplete="off">
                <div id="searchDropdown" class="search-dropdown"></div>
            </div>

            <!-- Entity Filter Chips -->
            <div class="filter-group">
                <span class="filter-chip active" data-type="all">Alle</span>
                <span class="filter-chip active" data-type="subcollection"><span class="chip-dot" style="background: var(--color-l1);"></span>Subcollections</span>
                <span class="filter-chip active" data-type="folder"><span class="chip-dot" style="background: var(--color-l2);"></span>Ordner</span>
                <span class="filter-chip active" data-type="resource"><span class="chip-dot" style="background: var(--color-resource);"></span>Ressourcen</span>
                <span class="filter-chip active" data-type="place"><span class="chip-dot" style="background: var(--color-place);"></span>Fundorte</span>
                <span class="filter-chip active" data-type="organization"><span class="chip-dot" style="background: var(--color-organization);"></span>Institutionen</span>
                <span class="filter-chip active" data-type="person"><span class="chip-dot" style="background: var(--color-person);"></span>Personen</span>
                <span class="filter-chip active" data-type="period"><span class="chip-dot" style="background: var(--color-period);"></span>Epochen</span>
                <span class="filter-chip active" data-type="subject"><span class="chip-dot" style="background: var(--color-subject);"></span>Schlagworte</span>
                <span class="filter-chip active" data-type="license"><span class="chip-dot" style="background: var(--color-license);"></span>Lizenzen</span>
            </div>
        </div>

        <div class="toolbar-right">
            <button id="btnFit" class="tool-btn" title="Ansicht einpassen"><i class="fa-solid fa-expand"></i> Zentrieren</button>
            <button id="btnZoomIn" class="tool-btn" title="Vergrößern"><i class="fa-solid fa-plus"></i></button>
            <button id="btnZoomOut" class="tool-btn" title="Verkleinern"><i class="fa-solid fa-minus"></i></button>
            <button id="btnExportPng" class="tool-btn" title="Graph als Bild exportieren"><i class="fa-solid fa-camera"></i> PNG</button>
            <button id="btnFullscreen" class="tool-btn" title="Vollbild umschalten"><i class="fa-solid fa-maximize"></i></button>
        </div>
    </div>

    <!-- Main Graph Canvas Stage -->
    <main class="stage-container" id="stageContainer">
        <div id="cy"></div>

        <!-- Floating Legend -->
        <div class="legend-card" id="legendCard">
            <div class="legend-header" id="legendToggle">
                <span><i class="fa-solid fa-layer-group"></i> Hierarchie &amp; Typen</span>
                <i class="fa-solid fa-chevron-up" id="legendChevron"></i>
            </div>
            <ul class="legend-list" id="legendBody">
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-l0);"></span> Top-Collection (L0)</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-l1);"></span> Subcollections (L1)</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-l2);"></span> Hauptkategorien (L2)</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-l3);"></span> Fachordner (L3)</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-l4);"></span> Teilsammlungen (L4)</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-l5);"></span> Befundordner (L5/L6)</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-resource);"></span> ARCHE-Datei (Ressource)</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-place);"></span> Geographischer Fundort</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-organization);"></span> Institution / Partner</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-person);"></span> Forscher:in (PI)</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-period);"></span> Zeitepoche</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-subject);"></span> Fachschlagwort</li>
                <li class="legend-item"><span class="legend-icon" style="background: var(--color-license);"></span> Lizenz (InC / CC BY)</li>
            </ul>
        </div>

        <!-- Hint Overlay -->
        <div class="hint-overlay" style="position: absolute; bottom: 20px; right: 20px; background: rgba(255, 255, 255, 0.9); padding: 5px 12px; border-radius: 20px; font-size: 0.72rem; color: var(--text-muted); pointer-events: none; border: 1px solid var(--panel-border);">
            <i class="fa-solid fa-hand-pointer"></i> Klicken zum Inspizieren &amp; Vorschau • Doppelklick zum Aufklappen von Ressourcen
        </div>

        <!-- Node Inspector Drawer -->
        <aside class="inspector-drawer" id="inspectorDrawer">
            <div class="drawer-header">
                <div class="drawer-header-top">
                    <span class="drawer-badge" id="drawerBadge">KNOTEN</span>
                    <button class="drawer-close-btn" id="drawerCloseBtn">&times;</button>
                </div>
                <nav id="drawerBreadcrumb" class="drawer-breadcrumb"></nav>
                <h2 class="drawer-title" id="drawerTitle">Knoten-Titel</h2>
            </div>

            <div class="drawer-body">
                <!-- Live ARCHE Preview Card -->
                <div id="drawerPreviewBox" class="drawer-preview-box">
                    <div class="drawer-preview-header">
                        <span><i class="fa-solid fa-eye" style="color: var(--primary);"></i> ARCHE Dateivorschau</span>
                        <span id="previewStatusBadge" style="font-size: 0.65rem; padding: 1px 6px; border-radius: 10px; background: #E8F5E9; color: #2E7D32;">Live von ARCHE</span>
                    </div>
                    <div id="drawerPreviewMedia" class="drawer-preview-media">
                        <img id="drawerPreviewImg" class="drawer-preview-img" alt="ARCHE Preview" />
                        <div id="drawerPreviewFallback" class="drawer-preview-fallback">
                            <i class="fa-solid fa-lock"></i>
                            <div style="font-size: 0.8rem; font-weight: 700; margin-bottom: 4px;">ARCHE-Zugriffsschutz (InC)</div>
                            <div style="font-size: 0.72rem; color: #BBB; line-height: 1.35; max-width: 280px; margin-bottom: 10px;">Vollansicht und Download im Repositorium nach Login verfügbar.</div>
                            <a id="drawerPreviewFallbackLink" href="#" target="_blank" class="tool-btn primary-btn" style="font-size: 0.72rem; padding: 4px 10px;">Auf ARCHE öffnen ↗</a>
                        </div>
                    </div>
                    <div class="drawer-preview-footer">
                        <span id="drawerPreviewDimensions"><i class="fa-solid fa-image"></i> Vorschau</span>
                        <button id="btnOpenFullPreview" class="tool-btn" style="font-size: 0.68rem; padding: 2px 7px;"><i class="fa-solid fa-expand"></i> Großansicht</button>
                    </div>
                </div>

                <!-- Description -->
                <div>
                    <div class="drawer-section-title">Beschreibung / Kontext</div>
                    <p class="drawer-desc" id="drawerDesc"></p>
                </div>

                <!-- Metrics Grid -->
                <div class="drawer-stats-grid" id="drawerStatsGrid">
                    <div class="drawer-stat-card">
                        <div class="drawer-stat-val" id="drawerStatItems">0</div>
                        <div class="drawer-stat-lbl">Enthaltene Elemente</div>
                    </div>
                    <div class="drawer-stat-card">
                        <div class="drawer-stat-val" id="drawerStatSize">–</div>
                        <div class="drawer-stat-lbl">Speicher-Volumen</div>
                    </div>
                </div>

                <!-- Sub-Folders Box (if folder has child collections) -->
                <div id="drawerChildFoldersBox" style="display: none;">
                    <div class="drawer-section-title">
                        <span>Unterordner dieser Ebene</span>
                        <span id="drawerChildFolderCount" style="font-size: 0.68rem; padding: 1px 6px; border-radius: 8px; background: #EDE8E0; color: var(--text-dark);">0</span>
                    </div>
                    <ul id="drawerChildFoldersList" class="relations-list" style="max-height: 150px; overflow-y: auto;"></ul>
                </div>

                <!-- Resource Expansion Box -->
                <div id="drawerResourceExpansionBox" style="display: none; background: #FAF8F5; border: 1px solid var(--panel-border); border-radius: 6px; padding: 10px;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-dark); margin-bottom: 4px; display: flex; align-items: center; justify-content: space-between;">
                        <span><i class="fa-solid fa-network-wired" style="color: var(--primary);"></i> Dateien im Graphen</span>
                        <span id="drawerResCountBadge" style="background: var(--primary); color: white; padding: 1px 6px; border-radius: 10px; font-size: 0.68rem;">0</span>
                    </div>
                    <p style="font-size: 0.72rem; color: var(--text-muted); margin: 0 0 8px 0;">Dateien dieses Ordners als Knoten in den Graphen einblenden:</p>
                    <div style="display: flex; gap: 6px;">
                        <button id="btnExpandResources" class="tool-btn primary-btn" style="font-size: 0.72rem; flex: 1;"><i class="fa-solid fa-plus"></i> Ressourcen aufklappen</button>
                        <button id="btnCollapseResources" class="tool-btn" style="font-size: 0.72rem; flex: 1; display: none;"><i class="fa-solid fa-minus"></i> Zuklappen</button>
                    </div>
                </div>

                <!-- Identifiers -->
                <div>
                    <div class="drawer-section-title">ARCHE Identifikatoren</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;">ARCHE ID: <strong id="drawerArcheId" style="color: var(--text-dark); font-family: monospace;">–</strong></div>
                    <div id="drawerPidContainer" style="display: none; font-size: 0.75rem; color: var(--text-muted);">Handle PID: <a id="drawerPidLink" href="#" target="_blank" style="color: var(--primary); word-break: break-all;">–</a></div>
                </div>

                <!-- Connected Relations -->
                <div>
                    <div class="drawer-section-title">
                        <span>Verknüpfte Entitäten</span>
                        <span id="relationCount" style="font-size: 0.68rem; padding: 1px 6px; border-radius: 8px; background: #EDE8E0; color: var(--text-dark);">0</span>
                    </div>
                    <ul class="relations-list" id="relationsList"></ul>
                </div>
            </div>

            <div class="drawer-footer">
                <a href="#" target="_blank" class="tool-btn primary-btn" id="drawerArcheBtn" style="width: 100%; justify-content: center;">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> Im ARCHE-Repositorium öffnen
                </a>
                <button class="tool-btn" id="drawerFocusNeighborsBtn" style="width: 100%; justify-content: center;">
                    <i class="fa-solid fa-crosshairs"></i> Nachbarschaft fokussieren
                </button>
            </div>
        </aside>
    </main>

    <!-- Archiv-Ordnerbaum Modal (190 Sammlungen & Ordner) -->
    <div id="treeModal" class="modal-backdrop">
        <div class="modal-card" style="max-width: 980px;">
            <div class="modal-header">
                <div>
                    <h2><i class="fa-solid fa-folder-tree" style="color: var(--secondary);"></i> ARCHE Archiv-Hierarchie: Alle 190 Sammlungen &amp; Ordner</h2>
                    <p style="font-size: 0.78rem; color: var(--text-muted); margin: 2px 0 0 0;">Vollständiger Verzeichnisbaum von IUENNA im ARCHE-Repositorium (Ebenen 0 bis 6)</p>
                </div>
                <button id="btnTreeClose" class="drawer-close-btn">&times;</button>
            </div>
            <div style="padding: 10px 24px; background: #FAF8F5; border-bottom: 1px solid var(--panel-border); display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                <div style="position: relative; flex: 1; min-width: 250px;">
                    <i class="fa-solid fa-search" style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-size: 0.75rem; color: #888;"></i>
                    <input type="text" id="treeSearchInput" placeholder="Ordner nach Namen filtern (z.B. Fotos, Drohne, Befunde, SE 2001, Keramik)..." style="width: 100%; padding: 6px 10px 6px 28px; font-size: 0.8rem; border-radius: 6px; border: 1px solid var(--panel-border); outline: none;" />
                </div>
                <button id="btnTreeExpandAll" class="tool-btn" style="font-size: 0.74rem;"><i class="fa-solid fa-folder-open"></i> Alle aufklappen</button>
                <button id="btnTreeCollapseAll" class="tool-btn" style="font-size: 0.74rem;"><i class="fa-solid fa-folder"></i> Alle zuklappen</button>
            </div>
            <div id="treeContainer" class="tree-scroll-area">
                <!-- Rendered dynamically -->
            </div>
        </div>
    </div>

    <!-- Corpus Catalog Modal (20.541 Ressourcen) -->
    <div id="corpusModal" class="modal-backdrop">
        <div class="modal-card">
            <div class="modal-header">
                <div>
                    <h2><i class="fa-solid fa-database" style="color: var(--primary);"></i> ARCHE Corpus-Katalog: Alle 20.541 Primärressourcen</h2>
                    <p style="font-size: 0.78rem; color: var(--text-muted); margin: 2px 0 0 0;">Vollständiger Index aller digitalen Dateien und Grabungsfunde mit Live-Dateivorschau</p>
                </div>
                <button id="btnCorpusClose" class="drawer-close-btn">&times;</button>
            </div>

            <div style="padding: 10px 24px; background: #FFFFFF; border-bottom: 1px solid var(--panel-border); display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                <div style="position: relative; flex: 1; min-width: 220px;">
                    <i class="fa-solid fa-magnifying-glass" style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-size: 0.75rem; color: var(--text-muted);"></i>
                    <input type="text" id="corpusSearchInput" class="search-input" style="width: 100%;" placeholder="Titel, PID, Dateiname durchsuchen..." />
                </div>
                <select id="corpusColSelect" class="tool-select">
                    <option value="all">Alle Sammlungen (20.541)</option>
                    <option value="col_ret">Retrodigitalisate (RET: 9.147)</option>
                    <option value="col_jau">Jaunstein (JAU: 4.891)</option>
                    <option value="col_hb">Hemmaberg (HB: 3.657)</option>
                    <option value="col_glo">Globasnitz (GLO: 2.664)</option>
                    <option value="col_tal">Jauntal (TAL: 177)</option>
                    <option value="col_ste">Sankt Stefan (STE: 5)</option>
                </select>
                <select id="corpusTypeSelect" class="tool-select">
                    <option value="all">Alle Medientypen</option>
                    <option value="image">Bilder &amp; Scans (.tif, .jpg)</option>
                    <option value="vector">GIS-Vektordaten (.shp, .gpkg)</option>
                    <option value="3d">3D-Modelle (.ply, .obj)</option>
                    <option value="database">Datenbanken (.accdb, .sqlite)</option>
                    <option value="document">Dokumente &amp; PDFs</option>
                </select>
                <select id="corpusPlaceSelect" class="tool-select">
                    <option value="all">Alle Fundorte</option>
                    <option value="Hemmaberg">Hemmaberg</option>
                    <option value="Jaunstein">Jaunstein</option>
                    <option value="Globasnitz">Globasnitz</option>
                    <option value="Sankt Stefan">Sankt Stefan</option>
                </select>
                <button id="btnResetCorpusFilters" class="tool-btn"><i class="fa-solid fa-rotate-left"></i> Zurücksetzen</button>
            </div>

            <div class="corpus-table-container">
                <table class="corpus-table">
                    <thead>
                        <tr>
                            <th style="width: 60px;">Vorschau</th>
                            <th>Dateiname / Ressource</th>
                            <th>Pfad &amp; Archiv-Ordner</th>
                            <th>Fundort &amp; Datum</th>
                            <th>Schlagworte</th>
                            <th style="width: 140px; text-align: right;">Aktionen</th>
                        </tr>
                    </thead>
                    <tbody id="corpusTableBody">
                        <!-- Populated by JS -->
                    </tbody>
                </table>
            </div>

            <div style="padding: 10px 24px; background: #FAF8F5; border-top: 1px solid var(--panel-border); display: flex; align-items: center; justify-content: space-between; font-size: 0.8rem;">
                <div id="corpusPageInfo">Zeige 1–50 von 20.541 Ressourcen</div>
                <div style="display: flex; gap: 6px; align-items: center;">
                    <button id="btnCorpusPrev" class="tool-btn"><i class="fa-solid fa-chevron-left"></i> Zurück</button>
                    <span id="corpusCurrentPage" style="font-weight: 700; padding: 0 8px;">1 / 411</span>
                    <button id="btnCorpusNext" class="tool-btn">Weiter <i class="fa-solid fa-chevron-right"></i></button>
                </div>
            </div>
        </div>
    </div>

    <!-- Quick Preview Lightbox Modal -->
    <div id="quickPreviewModal" class="modal-backdrop" style="z-index: 1300;">
        <div class="quick-preview-dialog">
            <div class="modal-header" style="padding: 12px 20px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fa-solid fa-image" style="color: var(--primary); font-size: 1.1rem;"></i>
                    <div>
                        <h3 id="quickPreviewTitle" style="font-size: 1.05rem; margin: 0; color: var(--text-dark);">Dateiname</h3>
                        <div id="quickPreviewBreadcrumb" style="font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;"></div>
                    </div>
                </div>
                <button id="btnQuickPreviewClose" class="drawer-close-btn">&times;</button>
            </div>
            <div style="background: #111; display: flex; align-items: center; justify-content: center; min-height: 320px; max-height: 520px; padding: 16px; position: relative;">
                <img id="quickPreviewImg" src="" alt="Live Preview" style="max-width: 100%; max-height: 480px; object-fit: contain; border-radius: 4px; display: none;" />
                <div id="quickPreviewProtectedMsg" style="display: none; color: #FFF; text-align: center; padding: 30px 20px;">
                    <i class="fa-solid fa-lock" style="font-size: 2.2rem; color: #E0A96D; margin-bottom: 12px; display: block;"></i>
                    <h4 style="font-size: 1rem; margin-bottom: 6px;">ARCHE-Zugriffsbeschränkung (InC-Lizenz)</h4>
                    <p style="font-size: 0.8rem; color: #BBB; max-width: 440px; margin: 0 auto 16px auto;">Diese historische Primärressource ist urheberrechtlich geschützt. Die Vollauflösung kann nach Login direkt im ARCHE-Repositorium eingesehen werden.</p>
                    <a id="quickPreviewArcheLink" href="#" target="_blank" class="tool-btn primary-btn" style="font-size: 0.8rem; padding: 7px 16px;"><i class="fa-solid fa-arrow-up-right-from-square"></i> Im ARCHE-Repositorium öffnen</a>
                </div>
            </div>
            <div style="padding: 12px 20px; background: #FAF8F5; border-top: 1px solid var(--panel-border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="font-size: 0.75rem; color: var(--text-muted);" id="quickPreviewMeta"></div>
                <div style="display: flex; gap: 8px;">
                    <button id="btnQuickPreviewInGraph" class="tool-btn secondary-btn" style="font-size: 0.75rem;"><i class="fa-solid fa-circle-nodes"></i> Im Graphen fokussieren</button>
                    <a id="quickPreviewDirectLink" href="#" target="_blank" class="tool-btn primary-btn" style="font-size: 0.75rem;"><i class="fa-solid fa-arrow-up-right-from-square"></i> ARCHE Handle</a>
                </div>
            </div>
        </div>
    </div>

    <!-- Application Script -->
    <script>
        let cy = null;
        let graphData = {embedded_graph_json};
        let treeData = {embedded_tree_json};
        let corpusData = null;
        let corpusResources = [];
        let activeFilters = new Set(["all", "root", "subcollection", "folder", "folder_l2", "folder_l3", "folder_l4", "folder_l5", "folder_l6", "resource", "organization", "person", "place", "period", "subject", "license"]);
        let selectedNode = null;
        let currentActivePreviewRes = null;
        let expandedNodesMap = new Map();

        // Corpus Catalog State
        let filteredCorpusItems = [];
        let corpusCurrentPageIdx = 1;
        const CORPUS_PAGE_SIZE = 50;

        const typeColors = {{
            root: "#A8442E",
            subcollection: "#B88E3E",
            folder: "#C29243",
            folder_l2: "#C29243",
            folder_l3: "#3D7068",
            folder_l4: "#5A6B7C",
            folder_l5: "#7E6B8F",
            folder_l6: "#9B59B6",
            resource: "#3D7068",
            organization: "#202226",
            person: "#C85A32",
            place: "#4A6B53",
            period: "#5A6B7C",
            subject: "#7E6B8F",
            license: "#437F97"
        }};

        const ftypeIcons = {{
            image: "fa-image",
            vector: "fa-draw-polygon",
            "3d": "fa-cube",
            database: "fa-database",
            document: "fa-file-pdf",
            other: "fa-file"
        }};

        const ftypeColors = {{
            image: "#4A6B53",
            vector: "#B88E3E",
            "3d": "#7E6B8F",
            database: "#202226",
            document: "#437F97",
            other: "#888888"
        }};

        const layoutConfigs = {{
            cose: {{
                name: "cose",
                animate: false,
                fit: true,
                padding: 40,
                randomize: false,
                nodeRepulsion: function(node) {{ return 800000; }},
                idealEdgeLength: function(edge) {{ return 110; }},
                edgeElasticity: function(edge) {{ return 100; }},
                nestingFactor: 5,
                gravity: 80,
                numIter: 1000
            }},
            concentric: {{
                name: "concentric",
                fit: true,
                padding: 50,
                animate: true,
                animationDuration: 600,
                startAngle: 3/2 * Math.PI,
                clockwise: true,
                equidistant: false,
                minNodeSpacing: 35,
                concentric: function(node) {{
                    const t = node.data("type");
                    const lvl = node.data("level");
                    if (t === "root" || lvl === 0) return 10;
                    if (t === "subcollection" || lvl === 1) return 8;
                    if (lvl === 2) return 6;
                    if (lvl === 3) return 4;
                    if (lvl >= 4) return 2;
                    if (t === "organization" || t === "person" || t === "place") return 7;
                    return 1;
                }},
                levelWidth: function(nodes) {{ return 2; }}
            }},
            breadthfirst: {{
                name: "breadthfirst",
                fit: true,
                padding: 40,
                directed: true,
                animate: true,
                animationDuration: 600,
                spacingFactor: 1.3,
                roots: "#iuenna_root"
            }},
            circle: {{
                name: "circle",
                fit: true,
                padding: 40,
                animate: true,
                animationDuration: 600
            }}
        }};

        // Initialize Cytoscape with elements
        function initCytoscape(elements) {{
            cy = cytoscape({{
                container: document.getElementById("cy"),
                elements: elements,
                style: [
                    {{
                        selector: "node",
                        style: {{
                            "label": "data(label)",
                            "color": "#202226",
                            "font-family": "Plus Jakarta Sans, sans-serif",
                            "font-size": function(ele) {{
                                const lvl = ele.data("level");
                                if (lvl === 0) return "13px";
                                if (lvl === 1) return "11px";
                                if (lvl === 2) return "9.5px";
                                if (lvl >= 3) return "8.5px";
                                return "10px";
                            }},
                            "font-weight": function(ele) {{
                                return ele.data("level") <= 1 ? 700 : 500;
                            }},
                            "text-valign": "bottom",
                            "text-margin-y": 4,
                            "text-outline-color": "#FAF8F5",
                            "text-outline-width": "2px",
                            "text-outline-opacity": 0.9,
                            "background-color": function(ele) {{
                                return ele.data("color") || typeColors[ele.data("type")] || "#888";
                            }},
                            "width": function(ele) {{
                                const lvl = ele.data("level");
                                if (lvl === 0) return 56;
                                if (lvl === 1) return 42;
                                if (lvl === 2) return 30;
                                if (lvl === 3) return 22;
                                if (lvl === 4) return 18;
                                if (lvl >= 5) return 15;
                                if (ele.data("type") === "resource") return 14;
                                return 24;
                            }},
                            "height": function(ele) {{
                                const lvl = ele.data("level");
                                if (lvl === 0) return 56;
                                if (lvl === 1) return 42;
                                if (lvl === 2) return 30;
                                if (lvl === 3) return 22;
                                if (lvl === 4) return 18;
                                if (lvl >= 5) return 15;
                                if (ele.data("type") === "resource") return 14;
                                return 24;
                            }},
                            "border-width": function(ele) {{
                                return ele.data("level") <= 1 ? 2.5 : 1.5;
                            }},
                            "border-color": "#FFFFFF",
                            "transition-property": "background-color, line-color, target-arrow-color, opacity, width, height",
                            "transition-duration": "0.2s"
                        }}
                    }},
                    {{
                        selector: "edge",
                        style: {{
                            "width": 1.3,
                            "line-color": "#D0C9BF",
                            "target-arrow-color": "#D0C9BF",
                            "target-arrow-shape": "triangle",
                            "curve-style": "bezier",
                            "arrow-scale": 0.75,
                            "opacity": 0.65
                        }}
                    }},
                    {{
                        selector: "edge[label = 'isPartOfResource']",
                        style: {{
                            "width": 1.0,
                            "line-color": "#B5C8BF",
                            "target-arrow-shape": "none",
                            "opacity": 0.5
                        }}
                    }},
                    {{
                        selector: ".dimmed",
                        style: {{
                            "opacity": 0.1
                        }}
                    }},
                    {{
                        selector: "node.highlighted",
                        style: {{
                            "border-width": 3.5,
                            "border-color": "#202226",
                            "opacity": 1
                        }}
                    }},
                    {{
                        selector: "edge.highlighted",
                        style: {{
                            "width": 2.5,
                            "line-color": "#A8442E",
                            "target-arrow-color": "#A8442E",
                            "opacity": 1,
                            "z-index": 999
                        }}
                    }}
                ],
                layout: layoutConfigs.cose
            }});

            cy.$id = function(id) {{
                return cy.getElementById(id);
            }};

            cy.on("tap", "node", function(evt) {{
                const node = evt.target;
                openInspector(node);
                highlightNeighbors(node);
            }});

            cy.on("dbltap", "node", function(evt) {{
                const node = evt.target;
                const t = node.data("type");
                if (t && (t.startsWith("folder") || t === "subcollection")) {{
                    if (expandedNodesMap.has(node.id())) {{
                        collapseResourcesForNode(node.id());
                    }} else {{
                        expandResourcesForNode(node.id());
                    }}
                }}
            }});

            cy.on("tap", function(evt) {{
                if (evt.target === cy) {{
                    resetHighlights();
                    closeInspector();
                }}
            }});

            updateVisibleNodesCount();
            setupSearch();
        }}

        function updateVisibleNodesCount() {{
            if (!cy) return;
            const count = cy.nodes(":visible").length;
            document.getElementById("pillVisibleNodes").textContent = count.toLocaleString();
        }}

        function highlightNeighbors(node) {{
            if (!cy) return;
            cy.elements().removeClass("highlighted dimmed");
            const neighborhood = node.neighborhood().add(node);
            cy.elements().not(neighborhood).addClass("dimmed");
            neighborhood.addClass("highlighted");
        }}

        function resetHighlights() {{
            if (!cy) return;
            cy.elements().removeClass("highlighted dimmed");
        }}

        // Depth Filter (LOD)
        function applyDepthFilter(depth) {{
            if (!cy) return;
            if (depth === "all") {{
                cy.nodes().show();
                cy.edges().show();
            }} else {{
                const maxLevel = parseInt(depth, 10);
                cy.nodes().forEach(n => {{
                    const lvl = n.data("level");
                    if (lvl !== undefined && lvl !== null) {{
                        if (lvl <= maxLevel) n.show();
                        else n.hide();
                    }} else {{
                        // Context nodes (places, orgs, persons, etc.)
                        n.show();
                    }}
                }});
                cy.edges().forEach(e => {{
                    if (e.source().visible() && e.target().visible()) e.show();
                    else e.hide();
                }});
            }}
            updateVisibleNodesCount();
            const currentLayout = document.getElementById("layoutSelect").value;
            cy.layout(layoutConfigs[currentLayout] || layoutConfigs.cose).run();
        }}

        document.getElementById("depthSelect").addEventListener("change", function() {{
            applyDepthFilter(this.value);
        }});

        document.getElementById("layoutSelect").addEventListener("change", function() {{
            if (!cy) return;
            cy.layout(layoutConfigs[this.value] || layoutConfigs.cose).run();
        }});

        // Inspector Drawer Logic
        function openInspector(node) {{
            selectedNode = node;
            const d = node.data();
            const drawer = document.getElementById("inspectorDrawer");

            // Badge
            const badge = document.getElementById("drawerBadge");
            badge.textContent = d.type_label || d.type;
            badge.style.backgroundColor = d.color || typeColors[d.type] || "#888";

            // Breadcrumb
            const breadcrumbNav = document.getElementById("drawerBreadcrumb");
            breadcrumbNav.innerHTML = "";
            const path = d.path || [d.label];
            path.forEach((part, idx) => {{
                if (idx > 0) {{
                    const sep = document.createElement("span");
                    sep.textContent = "›";
                    sep.style.color = "#BBB";
                    breadcrumbNav.appendChild(sep);
                }}
                const pill = document.createElement("span");
                pill.className = "drawer-breadcrumb-pill";
                pill.textContent = part;
                breadcrumbNav.appendChild(pill);
            }});

            // Title & Desc
            document.getElementById("drawerTitle").textContent = d.label;
            document.getElementById("drawerDesc").textContent = d.description || d.desc || "Keine weitere Beschreibung hinterlegt.";

            // Live Preview Card
            const previewBox = document.getElementById("drawerPreviewBox");
            const previewImg = document.getElementById("drawerPreviewImg");
            const previewFallback = document.getElementById("drawerPreviewFallback");
            const previewStatusBadge = document.getElementById("previewStatusBadge");
            const previewDimensions = document.getElementById("drawerPreviewDimensions");

            // Determine if preview can be requested
            let previewPid = d.sample_pid || (d.type === "resource" ? d.pid : null);
            let previewTitle = d.sample_title || d.label;

            // If folder or if previewPid not set, fallback to finding a sample image inside it
            if (!previewPid && corpusResources && corpusResources.length > 0) {{
                const sample = corpusResources.find(r => r.col_id === d.id || r.col === d.id || (r.path && r.path.includes(d.label)) || (d.arche_id && r.col_id === `col_${{d.arche_id}}`));
                if (sample) {{
                    previewPid = sample.pid;
                    previewTitle = `${{sample.title}} (Beispiel aus Ordner)`;
                }}
            }}

            if (previewPid) {{
                previewBox.style.display = "block";
                previewImg.style.display = "none";
                previewFallback.style.display = "none";
                previewStatusBadge.textContent = "Lade von ARCHE...";
                previewStatusBadge.style.background = "#FFF3CD";
                previewStatusBadge.style.color = "#856404";

                const thumbUrl = `https://arche-thumbnails.acdh.oeaw.ac.at/?id=${{encodeURIComponent(previewPid)}}&width=360`;
                previewImg.src = thumbUrl;
                currentActivePreviewRes = {{ pid: previewPid, title: previewTitle, path: d.path, thumbUrl: thumbUrl }};

                previewImg.onload = function() {{
                    previewImg.style.display = "block";
                    previewFallback.style.display = "none";
                    previewStatusBadge.textContent = "Live von ARCHE";
                    previewStatusBadge.style.background = "#E8F5E9";
                    previewStatusBadge.style.color = "#2E7D32";
                    previewDimensions.innerHTML = `<i class="fa-solid fa-check"></i> ${{previewTitle}}`;
                }};

                previewImg.onerror = function() {{
                    previewImg.style.display = "none";
                    previewFallback.style.display = "flex";
                    previewStatusBadge.textContent = "InC-Lizenz";
                    previewStatusBadge.style.background = "#FBE9E7";
                    previewStatusBadge.style.color = "#D84315";
                    document.getElementById("drawerPreviewFallbackLink").href = previewPid;
                    previewDimensions.innerHTML = `<i class="fa-solid fa-lock"></i> Zugriffsschutz`;
                }};
            }} else {{
                previewBox.style.display = "none";
            }}

            // Stats
            const statsGrid = document.getElementById("drawerStatsGrid");
            if (d.items !== undefined && d.items !== null) {{
                statsGrid.style.display = "grid";
                document.getElementById("drawerStatItems").textContent = d.items.toLocaleString();
                document.getElementById("drawerStatSize").textContent = d.formatted_size || "–";
            }} else {{
                statsGrid.style.display = "none";
            }}

            // Sub-Folders Box
            const childBox = document.getElementById("drawerChildFoldersBox");
            const childList = document.getElementById("drawerChildFoldersList");
            childList.innerHTML = "";
            
            // Find child nodes in cytoscape
            const childEdges = cy.edges(`[target = "${{node.id()}}"][label = 'isPartOf']`);
            if (childEdges.length > 0) {{
                childBox.style.display = "block";
                document.getElementById("drawerChildFolderCount").textContent = childEdges.length;
                childEdges.slice(0, 20).forEach(edge => {{
                    const child = edge.source();
                    const li = document.createElement("li");
                    li.className = "relation-item";
                    li.innerHTML = `
                        <span class="relation-target"><i class="fa-solid fa-folder" style="color: ${{child.data("color") || "#888"}};"></i> ${{child.data("label")}}</span>
                        <span class="relation-label">${{child.data("items") ? child.data("items") + " Items" : "Ordner"}}</span>
                    `;
                    li.addEventListener("click", () => {{
                        child.show();
                        cy.center(child);
                        cy.zoom({{ level: 2.0, position: child.position() }});
                        openInspector(child);
                        highlightNeighbors(child);
                    }});
                    childList.appendChild(li);
                }});
            }} else {{
                childBox.style.display = "none";
            }}

            // Resource Expansion Box
            const resBox = document.getElementById("drawerResourceExpansionBox");
            const btnExpand = document.getElementById("btnExpandResources");
            const btnCollapse = document.getElementById("btnCollapseResources");
            const resCountBadge = document.getElementById("drawerResCountBadge");

            const isFolderLike = d.type && (d.type.startsWith("folder") || d.type === "subcollection");
            if (isFolderLike && corpusResources.length > 0) {{
                resBox.style.display = "block";
                resCountBadge.textContent = (d.items || 0).toLocaleString();
                if (expandedNodesMap.has(node.id())) {{
                    btnExpand.style.display = "none";
                    btnCollapse.style.display = "inline-flex";
                }} else {{
                    btnExpand.style.display = "inline-flex";
                    btnCollapse.style.display = "none";
                }}
                btnExpand.onclick = () => expandResourcesForNode(node.id());
                btnCollapse.onclick = () => collapseResourcesForNode(node.id());
            }} else {{
                resBox.style.display = "none";
            }}

            // Identifiers
            document.getElementById("drawerArcheId").textContent = d.arche_id || d.id || "–";
            const pidContainer = document.getElementById("drawerPidContainer");
            const pidLink = document.getElementById("drawerPidLink");
            if (d.pid) {{
                pidContainer.style.display = "block";
                pidLink.textContent = d.pid;
                pidLink.href = d.pid;
            }} else {{
                pidContainer.style.display = "none";
            }}

            // Connected Relations
            const relationsList = document.getElementById("relationsList");
            relationsList.innerHTML = "";
            const connectedEdges = node.connectedEdges();
            document.getElementById("relationCount").textContent = connectedEdges.length;

            connectedEdges.slice(0, 30).forEach(edge => {{
                const targetNode = edge.source().id() === node.id() ? edge.target() : edge.source();
                const isOutgoing = edge.source().id() === node.id();
                const li = document.createElement("li");
                li.className = "relation-item";
                li.innerHTML = `
                    <span class="relation-target" title="${{targetNode.data("label")}}">
                        <i class="fa-solid ${{isOutgoing ? "fa-arrow-right" : "fa-arrow-left"}}" style="color: var(--primary); font-size: 0.68rem;"></i>
                        ${{targetNode.data("label")}}
                    </span>
                    <span class="relation-label">${{edge.data("label") || "rel"}}</span>
                `;
                li.addEventListener("click", () => {{
                    targetNode.show();
                    cy.center(targetNode);
                    cy.zoom({{ level: 1.8, position: targetNode.position() }});
                    openInspector(targetNode);
                    highlightNeighbors(targetNode);
                }});
                relationsList.appendChild(li);
            }});

            // ARCHE Button
            const archeBtn = document.getElementById("drawerArcheBtn");
            if (d.pid) archeBtn.href = d.pid;
            else if (d.arche_url) archeBtn.href = d.arche_url;
            else archeBtn.href = "https://id.acdh.oeaw.ac.at/iuenna";

            drawer.classList.add("open");
        }}

        function closeInspector() {{
            document.getElementById("inspectorDrawer").classList.remove("open");
        }}

        // Dynamic On-Demand Node Expansion for Resources
        function expandResourcesForNode(nodeId, maxLimit = 60) {{
            if (!corpusResources || corpusResources.length === 0) return;
            const parentNode = cy.$id(nodeId);
            if (!parentNode || parentNode.length === 0) return;

            const isCol = parentNode.data("type") === "subcollection";
            const matches = corpusResources.filter(r => isCol ? (r.col === nodeId || r.col_id === nodeId) : (r.col_id === nodeId || r.folder === parentNode.data("label")));

            if (matches.length === 0) {{
                alert("Keine individuellen Ressourcen für diesen Ordner hinterlegt.");
                return;
            }}

            const toAdd = matches.slice(0, maxLimit);
            const parentPos = parentNode.position();
            const radius = 110 + Math.min(100, toAdd.length * 2.5);
            const newElements = [];
            const addedIds = new Set();

            toAdd.forEach((res, i) => {{
                if (cy.$id(res.id).length > 0) return;
                const angle = (2 * Math.PI / toAdd.length) * i;
                const px = parentPos.x + radius * Math.cos(angle) + (Math.random() - 0.5) * 20;
                const py = parentPos.y + radius * Math.sin(angle) + (Math.random() - 0.5) * 20;

                newElements.push({{
                    group: "nodes",
                    data: {{
                        id: res.id,
                        label: res.title,
                        type: "resource",
                        type_label: `ARCHE-Datei (${{res.type}})`,
                        ftype: res.type,
                        pid: res.pid,
                        place: res.place,
                        subjs: res.subjs,
                        path: res.path,
                        date: res.date,
                        col: res.col,
                        description: `ARCHE-Ressource: ${{res.title}} | Fundort: ${{res.place}} | Schlagworte: ${{res.subjs.join(", ")}}`,
                        color: ftypeColors[res.type] || "#3D7068"
                    }},
                    position: {{ x: px, y: py }}
                }});

                newElements.push({{
                    group: "edges",
                    data: {{
                        id: `edge_${{res.id}}_${{nodeId}}`,
                        source: res.id,
                        target: nodeId,
                        label: "isPartOfResource"
                    }}
                }});

                addedIds.add(res.id);
            }});

            if (newElements.length > 0) {{
                cy.add(newElements);
                expandedNodesMap.set(nodeId, addedIds);
                updateVisibleNodesCount();
                openInspector(parentNode);
            }}
        }}

        function collapseResourcesForNode(nodeId) {{
            if (!expandedNodesMap.has(nodeId)) return;
            const addedIds = expandedNodesMap.get(nodeId);
            addedIds.forEach(id => {{
                const n = cy.$id(id);
                if (n.length > 0) cy.remove(n);
            }});
            expandedNodesMap.delete(nodeId);
            updateVisibleNodesCount();
            const parentNode = cy.$id(nodeId);
            if (parentNode.length > 0) openInspector(parentNode);
        }}

        function focusResourceInGraph(resId) {{
            closeCorpusModal();
            let node = cy.$id(resId);
            if (node.length === 0) {{
                const res = corpusResources.find(r => r.id === resId);
                if (!res) return;
                const parentColNode = cy.$id(res.col_id) || cy.$id(res.col) || cy.nodes(`[label = "${{res.col_id}}"]`);
                const parentPos = parentColNode.length > 0 ? parentColNode.position() : {{ x: 0, y: 0 }};

                cy.add([
                    {{
                        group: "nodes",
                        data: {{
                            id: res.id,
                            label: res.title,
                            type: "resource",
                            type_label: `ARCHE-Datei (${{res.type}})`,
                            ftype: res.type,
                            pid: res.pid,
                            place: res.place,
                            subjs: res.subjs,
                            path: res.path,
                            date: res.date,
                            description: `ARCHE-Ressource: ${{res.title}} | Fundort: ${{res.place}}`,
                            color: ftypeColors[res.type] || "#3D7068"
                        }},
                        position: {{ x: parentPos.x + 80, y: parentPos.y + 80 }}
                    }},
                    {{
                        group: "edges",
                        data: {{
                            id: `edge_${{res.id}}_foc`,
                            source: res.id,
                            target: parentColNode.length > 0 ? parentColNode.id() : "iuenna_root",
                            label: "isPartOfResource"
                        }}
                    }}
                ]);
                node = cy.$id(res.id);
            }}
            node.show();
            cy.center(node);
            cy.zoom({{ level: 2.2, position: node.position() }});
            openInspector(node);
            highlightNeighbors(node);
        }}

        // Quick Preview Lightbox Modal Logic
        function openQuickPreview(res) {{
            if (!res) return;
            const modal = document.getElementById("quickPreviewModal");
            const titleEl = document.getElementById("quickPreviewTitle");
            const breadcrumbEl = document.getElementById("quickPreviewBreadcrumb");
            const imgEl = document.getElementById("quickPreviewImg");
            const protectedMsg = document.getElementById("quickPreviewProtectedMsg");
            const metaEl = document.getElementById("quickPreviewMeta");
            const archeLink = document.getElementById("quickPreviewArcheLink");
            const directLink = document.getElementById("quickPreviewDirectLink");
            const inGraphBtn = document.getElementById("btnQuickPreviewInGraph");

            titleEl.textContent = res.title;
            breadcrumbEl.textContent = (res.path || ["IUENNA", res.col]).join(" › ");
            metaEl.innerHTML = `<strong>Fundort:</strong> ${{res.place || "–"}} &bull; <strong>Typ:</strong> ${{res.type}} &bull; <strong>PID:</strong> ${{res.pid}}`;

            archeLink.href = res.pid;
            directLink.href = res.pid;

            inGraphBtn.onclick = () => {{
                modal.classList.remove("open");
                focusResourceInGraph(res.id);
            }};

            imgEl.style.display = "none";
            protectedMsg.style.display = "none";

            const thumbUrl = `https://arche-thumbnails.acdh.oeaw.ac.at/?id=${{encodeURIComponent(res.pid)}}&width=720`;
            imgEl.src = thumbUrl;

            imgEl.onload = function() {{
                imgEl.style.display = "block";
                protectedMsg.style.display = "none";
            }};
            imgEl.onerror = function() {{
                imgEl.style.display = "none";
                protectedMsg.style.display = "block";
            }};

            modal.classList.add("open");
        }}

        document.getElementById("btnQuickPreviewClose").addEventListener("click", () => {{
            document.getElementById("quickPreviewModal").classList.remove("open");
        }});
        document.getElementById("btnOpenFullPreview").addEventListener("click", () => {{
            if (currentActivePreviewRes) {{
                openQuickPreview(currentActivePreviewRes);
            }}
        }});

        // Ordnerbaum (Archiv-Hierarchie Modal) Logic
        const treeModal = document.getElementById("treeModal");
        const btnOpenTreeModal = document.getElementById("btnOpenTreeModal");
        const btnTreeClose = document.getElementById("btnTreeClose");
        const treeContainer = document.getElementById("treeContainer");
        const treeSearchInput = document.getElementById("treeSearchInput");

        function openTreeModal() {{
            treeModal.classList.add("open");
            renderTree();
        }}
        function closeTreeModal() {{
            treeModal.classList.remove("open");
        }}
        btnOpenTreeModal.addEventListener("click", openTreeModal);
        btnTreeClose.addEventListener("click", closeTreeModal);
        treeModal.addEventListener("click", (e) => {{
            if (e.target === treeModal) closeTreeModal();
        }});

        function renderTree() {{
            if (!treeData || !treeData.collections) return;
            const filter = treeSearchInput.value.trim().toLowerCase();
            treeContainer.innerHTML = "";

            const rootCol = treeData.collections["1792170"] || Object.values(treeData.collections).find(c => c.level === 0);
            if (rootCol) {{
                const treeDom = buildTreeNodeDom(rootCol, filter);
                if (treeDom) treeContainer.appendChild(treeDom);
                else treeContainer.innerHTML = '<div style="padding: 24px; text-align: center; color: var(--text-muted);">Kein Ordner entspricht diesem Suchfilter.</div>';
            }}
        }}

        function buildTreeNodeDom(node, filter = "") {{
            const children = Object.values(treeData.collections).filter(c => String(c.parent_id) === String(node.arche_id) && String(c.arche_id) !== String(node.arche_id));
            const hasChildren = children.length > 0;

            const matchesSelf = !filter || node.title.toLowerCase().includes(filter) || String(node.arche_id).includes(filter);
            const matchingChildrenDoms = children.map(c => buildTreeNodeDom(c, filter)).filter(Boolean);

            if (filter && !matchesSelf && matchingChildrenDoms.length === 0) return null;

            const nodeDiv = document.createElement("div");
            nodeDiv.className = "tree-node";

            const row = document.createElement("div");
            row.className = "tree-node-row";

            const toggleBtn = document.createElement("span");
            toggleBtn.className = "tree-toggle-btn";
            toggleBtn.innerHTML = hasChildren ? '<i class="fa-solid fa-chevron-down"></i>' : '<i class="fa-solid fa-minus" style="opacity: 0.3;"></i>';

            const lvl = node.level || 0;
            const lvlBadge = document.createElement("span");
            lvlBadge.className = "tree-level-badge";
            lvlBadge.textContent = `L${{lvl}}`;
            lvlBadge.style.backgroundColor = typeColors[`folder_l${{lvl}}`] || typeColors[lvl === 1 ? "subcollection" : (lvl === 0 ? "root" : "folder")];

            const titleSpan = document.createElement("span");
            titleSpan.style.fontWeight = lvl <= 1 ? "700" : "500";
            titleSpan.innerHTML = `<i class="fa-solid ${{hasChildren ? "fa-folder" : "fa-folder-closed"}}" style="color: ${{lvlBadge.style.backgroundColor}}; margin-right: 4px;"></i> ${{node.title}}`;

            const statsSpan = document.createElement("span");
            statsSpan.style.cssText = "font-size: 0.7rem; color: var(--text-muted); margin-left: 6px;";
            statsSpan.textContent = `(${{node.items ? node.items.toLocaleString() + " Items" : "–"}} ${{node.formatted_size ? "• " + node.formatted_size : ""}})`;

            const actionsDiv = document.createElement("div");
            actionsDiv.className = "tree-actions";

            const btnFocus = document.createElement("button");
            btnFocus.className = "tree-action-btn";
            btnFocus.innerHTML = '<i class="fa-solid fa-crosshairs"></i> Im Graph';
            btnFocus.title = "Diesen Ordner im Graphen fokussieren";
            btnFocus.onclick = (e) => {{
                e.stopPropagation();
                treeModal.classList.remove("open");
                focusCollectionNodeInGraph(node.arche_id);
            }};

            const btnCorpus = document.createElement("button");
            btnCorpus.className = "tree-action-btn";
            btnCorpus.innerHTML = '<i class="fa-solid fa-database"></i> Korpus';
            btnCorpus.title = "Dateien dieses Ordners im Korpus anzeigen";
            btnCorpus.onclick = (e) => {{
                e.stopPropagation();
                treeModal.classList.remove("open");
                openCorpusModal();
                document.getElementById("corpusSearchInput").value = node.title;
                filterCorpus();
            }};

            actionsDiv.appendChild(btnFocus);
            actionsDiv.appendChild(btnCorpus);

            row.appendChild(toggleBtn);
            row.appendChild(lvlBadge);
            row.appendChild(titleSpan);
            row.appendChild(statsSpan);
            row.appendChild(actionsDiv);
            nodeDiv.appendChild(row);

            const childrenContainer = document.createElement("div");
            childrenContainer.className = "tree-node-children";

            matchingChildrenDoms.forEach(cDom => childrenContainer.appendChild(cDom));
            nodeDiv.appendChild(childrenContainer);

            let isExpanded = true;
            toggleBtn.onclick = (e) => {{
                e.stopPropagation();
                isExpanded = !isExpanded;
                childrenContainer.style.display = isExpanded ? "block" : "none";
                toggleBtn.innerHTML = isExpanded ? '<i class="fa-solid fa-chevron-down"></i>' : '<i class="fa-solid fa-chevron-right"></i>';
            }};

            row.onclick = () => {{
                if (hasChildren) {{
                    isExpanded = !isExpanded;
                    childrenContainer.style.display = isExpanded ? "block" : "none";
                    toggleBtn.innerHTML = isExpanded ? '<i class="fa-solid fa-chevron-down"></i>' : '<i class="fa-solid fa-chevron-right"></i>';
                }}
            }};

            return nodeDiv;
        }}

        function focusCollectionNodeInGraph(archeId) {{
            if (!cy) return;
            const targetId = `col_${{archeId}}`;
            let node = cy.$id(targetId) || cy.$id(archeId) || (archeId === "1792170" ? cy.$id("iuenna_root") : null);

            if (!node || node.length === 0) {{
                // If deep level is filtered out, switch depth to all
                document.getElementById("depthSelect").value = "all";
                applyDepthFilter("all");
                node = cy.$id(targetId) || cy.$id(archeId);
            }}

            if (node && node.length > 0) {{
                node.show();
                cy.center(node);
                cy.zoom({{ level: 2.0, position: node.position() }});
                openInspector(node);
                highlightNeighbors(node);
            }} else {{
                alert(`Ordner [${{archeId}}] im Graphen nicht gefunden.`);
            }}
        }}

        treeSearchInput.addEventListener("input", () => {{
            clearTimeout(window._treeSearchTimer);
            window._treeSearchTimer = setTimeout(renderTree, 150);
        }});

        document.getElementById("btnTreeExpandAll").addEventListener("click", () => {{
            document.querySelectorAll(".tree-node-children").forEach(el => el.style.display = "block");
            document.querySelectorAll(".tree-toggle-btn").forEach(btn => {{
                if (!btn.innerHTML.includes("fa-minus")) btn.innerHTML = '<i class="fa-solid fa-chevron-down"></i>';
            }});
        }});

        document.getElementById("btnTreeCollapseAll").addEventListener("click", () => {{
            document.querySelectorAll(".tree-node-children").forEach((el, idx) => {{
                if (idx > 0) el.style.display = "none";
            }});
            document.querySelectorAll(".tree-toggle-btn").forEach((btn, idx) => {{
                if (idx > 0 && !btn.innerHTML.includes("fa-minus")) btn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
            }});
        }});

        // Corpus Modal Logic
        const corpusModal = document.getElementById("corpusModal");
        const btnOpenCorpus = document.getElementById("btnOpenCorpus");
        const btnCorpusClose = document.getElementById("btnCorpusClose");
        const corpusTableBody = document.getElementById("corpusTableBody");
        const corpusSearchInput = document.getElementById("corpusSearchInput");
        const corpusColSelect = document.getElementById("corpusColSelect");
        const corpusTypeSelect = document.getElementById("corpusTypeSelect");
        const corpusPlaceSelect = document.getElementById("corpusPlaceSelect");

        btnOpenCorpus.addEventListener("click", openCorpusModal);
        btnCorpusClose.addEventListener("click", closeCorpusModal);
        corpusModal.addEventListener("click", (e) => {{
            if (e.target === corpusModal) closeCorpusModal();
        }});

        function openCorpusModal() {{
            corpusModal.classList.add("open");
            filterCorpus();
        }}
        function closeCorpusModal() {{
            corpusModal.classList.remove("open");
        }}

        function filterCorpus() {{
            if (!corpusResources || corpusResources.length === 0) return;
            const q = corpusSearchInput.value.trim().toLowerCase();
            const col = corpusColSelect.value;
            const type = corpusTypeSelect.value;
            const place = corpusPlaceSelect.value;

            filteredCorpusItems = corpusResources.filter(r => {{
                if (col !== "all" && r.col !== col && r.col_id !== col) return false;
                if (type !== "all" && r.type !== type) return false;
                if (place !== "all" && !r.place.toLowerCase().includes(place.toLowerCase())) return false;
                if (q) {{
                    const match = r.title.toLowerCase().includes(q) ||
                                  r.pid.toLowerCase().includes(q) ||
                                  r.place.toLowerCase().includes(q) ||
                                  (r.path && r.path.some(p => p.toLowerCase().includes(q))) ||
                                  r.subjs.some(s => s.toLowerCase().includes(q));
                    if (!match) return false;
                }}
                return true;
            }});

            corpusCurrentPageIdx = 1;
            renderCorpusPage();
        }}

        function renderCorpusPage() {{
            const total = filteredCorpusItems.length;
            const totalPages = Math.max(1, Math.ceil(total / CORPUS_PAGE_SIZE));
            const startIdx = (corpusCurrentPageIdx - 1) * CORPUS_PAGE_SIZE;
            const endIdx = Math.min(total, startIdx + CORPUS_PAGE_SIZE);
            const pageItems = filteredCorpusItems.slice(startIdx, endIdx);

            document.getElementById("corpusPageInfo").textContent = `Zeige ${{total === 0 ? 0 : startIdx + 1}}–${{endIdx}} von ${{total.toLocaleString()}} Ressourcen`;
            document.getElementById("corpusCurrentPage").textContent = `${{corpusCurrentPageIdx}} / ${{totalPages}}`;

            document.getElementById("btnCorpusPrev").disabled = corpusCurrentPageIdx <= 1;
            document.getElementById("btnCorpusNext").disabled = corpusCurrentPageIdx >= totalPages;

            if (pageItems.length === 0) {{
                corpusTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">Keine Ressourcen für diese Filterkriterien gefunden.</td></tr>`;
                return;
            }}

            corpusTableBody.innerHTML = pageItems.map(r => `
                <tr>
                    <td style="text-align: center; vertical-align: middle;">
                        <div class="corpus-thumb-cell btn-preview-click" data-id="${{r.id}}" title="ARCHE Dateivorschau vergrößern" style="cursor: pointer; display: inline-flex; align-items: center; justify-content: center; width: 42px; height: 42px; border-radius: 6px; background: #F2EFE9; border: 1px solid var(--panel-border); overflow: hidden; position: relative;">
                            <img src="${{r.thumb_url || `https://arche-thumbnails.acdh.oeaw.ac.at/?id=${{encodeURIComponent(r.pid)}}&width=84`}}" loading="lazy" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" alt="Vorschau" />
                            <span style="display: none; width: 100%; height: 100%; align-items: center; justify-content: center; font-size: 0.85rem; color: #8C857B;">
                                <i class="fa-solid ${{r.type === 'image' ? 'fa-image' : (ftypeIcons[r.type] || 'fa-file')}}" style="color: ${{ftypeColors[r.type] || '#3D7068'}};"></i>
                            </span>
                        </div>
                    </td>
                    <td>
                        <strong style="color: var(--primary); cursor: pointer;" class="btn-preview-click" data-id="${{r.id}}">${{r.title}}</strong>
                        <div style="font-size: 0.7rem; color: var(--text-muted); font-family: monospace;">PID: ${{r.pid.split("/").pop()}}</div>
                    </td>
                    <td>
                        <span style="font-weight: 600; font-size: 0.75rem;">${{r.folder}}</span>
                        <div style="font-size: 0.68rem; color: var(--text-muted);">${{(r.path || []).slice(1, -1).join(" › ")}}</div>
                    </td>
                    <td>
                        <strong>${{r.place}}</strong>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">${{r.date}}</div>
                    </td>
                    <td>
                        ${{r.subjs.slice(0, 3).map(s => `<span class="stat-pill" style="font-size: 0.65rem; padding: 1px 5px; margin: 1px;">${{s}}</span>`).join("")}}
                    </td>
                    <td style="text-align: right;">
                        <div style="display: inline-flex; gap: 4px;">
                            <button class="tool-btn btn-graph-focus" data-id="${{r.id}}" style="font-size: 0.72rem; padding: 3px 8px;" title="Im Graphen fokussieren">
                                <i class="fa-solid fa-circle-nodes"></i>
                            </button>
                            <a href="${{r.pid}}" target="_blank" class="tool-btn" style="font-size: 0.72rem; padding: 3px 8px;" title="Auf ARCHE öffnen">
                                <i class="fa-solid fa-arrow-up-right-from-square"></i>
                            </a>
                        </div>
                    </td>
                </tr>
            `).join("");

            // Attach event listeners
            document.querySelectorAll(".btn-preview-click").forEach(btn => {{
                btn.onclick = function() {{
                    const id = this.getAttribute("data-id");
                    const res = corpusResources.find(x => x.id === id);
                    if (res) openQuickPreview(res);
                }};
            }});
            document.querySelectorAll(".btn-graph-focus").forEach(btn => {{
                btn.onclick = function() {{
                    const id = this.getAttribute("data-id");
                    focusResourceInGraph(id);
                }};
            }});
        }}

        corpusSearchInput.addEventListener("input", () => {{
            clearTimeout(window._corpusDebounce);
            window._corpusDebounce = setTimeout(filterCorpus, 150);
        }});
        corpusColSelect.addEventListener("change", filterCorpus);
        corpusTypeSelect.addEventListener("change", filterCorpus);
        corpusPlaceSelect.addEventListener("change", filterCorpus);
        document.getElementById("btnResetCorpusFilters").addEventListener("click", () => {{
            corpusSearchInput.value = "";
            corpusColSelect.value = "all";
            corpusTypeSelect.value = "all";
            corpusPlaceSelect.value = "all";
            filterCorpus();
        }});

        document.getElementById("btnCorpusPrev").addEventListener("click", () => {{
            if (corpusCurrentPageIdx > 1) {{
                corpusCurrentPageIdx--;
                renderCorpusPage();
            }}
        }});
        document.getElementById("btnCorpusNext").addEventListener("click", () => {{
            const totalPages = Math.ceil(filteredCorpusItems.length / CORPUS_PAGE_SIZE);
            if (corpusCurrentPageIdx < totalPages) {{
                corpusCurrentPageIdx++;
                renderCorpusPage();
            }}
        }});

        // Search & Autocomplete
        const searchInput = document.getElementById("searchInput");
        const searchDropdown = document.getElementById("searchDropdown");

        function setupSearch() {{
            let debounceTimer = null;
            searchInput.addEventListener("input", function() {{
                clearTimeout(debounceTimer);
                const query = this.value.trim().toLowerCase();
                if (!query) {{
                    searchDropdown.style.display = "none";
                    return;
                }}

                debounceTimer = setTimeout(() => {{
                    searchDropdown.innerHTML = "";
                    const macroMatches = cy.nodes().filter(n => {{
                        const label = (n.data("label") || "").toLowerCase();
                        const full = (n.data("full_title") || "").toLowerCase();
                        const archeId = (n.data("arche_id") || "").toLowerCase();
                        return label.includes(query) || full.includes(query) || archeId.includes(query);
                    }});

                    let corpusMatches = [];
                    if (corpusResources && corpusResources.length > 0) {{
                        corpusMatches = corpusResources.filter(r => {{
                            return r.title.toLowerCase().includes(query) ||
                                   r.pid.toLowerCase().includes(query) ||
                                   r.place.toLowerCase().includes(query) ||
                                   r.subjs.some(s => s.toLowerCase().includes(query));
                        }}).slice(0, 15);
                    }}

                    if (macroMatches.length === 0 && corpusMatches.length === 0) {{
                        searchDropdown.innerHTML = '<div style="padding: 8px 12px; font-size: 0.78rem; color: #888;">Kein passender Eintrag unter 20.788 ARCHE-Objekten gefunden</div>';
                        searchDropdown.style.display = "block";
                        return;
                    }}

                    if (macroMatches.length > 0) {{
                        const header = document.createElement("div");
                        header.className = "search-section-header";
                        header.textContent = `Struktur- & Kontext-Knoten (${{macroMatches.length}})`;
                        searchDropdown.appendChild(header);

                        macroMatches.slice(0, 5).forEach(node => {{
                            const item = document.createElement("div");
                            item.className = "search-item";
                            item.innerHTML = `
                                <span style="width: 8px; height: 8px; border-radius: 50%; background: ${{node.data("color") || "#888"}}; display: inline-block;"></span>
                                <div style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                    <strong>${{node.data("label")}}</strong>
                                    <div style="font-size: 0.7rem; color: var(--text-muted);">${{node.data("type_label") || node.data("type")}}</div>
                                </div>
                            `;
                            item.addEventListener("click", () => {{
                                searchDropdown.style.display = "none";
                                searchInput.value = node.data("label");
                                node.show();
                                cy.center(node);
                                cy.zoom({{ level: 2.0, position: node.position() }});
                                openInspector(node);
                                highlightNeighbors(node);
                            }});
                            searchDropdown.appendChild(item);
                        }});
                    }}

                    if (corpusMatches.length > 0) {{
                        const header = document.createElement("div");
                        header.className = "search-section-header";
                        header.textContent = `ARCHE-Ressourcen (Dateien / Funde) • ${{corpusMatches.length}} Treffer`;
                        searchDropdown.appendChild(header);

                        corpusMatches.forEach(res => {{
                            const item = document.createElement("div");
                            item.className = "search-item";
                            item.innerHTML = `
                                <i class="fa-solid ${{ftypeIcons[res.type] || "fa-file"}}" style="color: ${{ftypeColors[res.type] || "#3D7068"}}; font-size: 0.85rem;"></i>
                                <div style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                    <strong style="color: var(--primary);">${{res.title}}</strong>
                                    <div style="font-size: 0.68rem; color: var(--text-muted);">${{res.place}} • PID: ${{res.pid.split("/").pop()}}</div>
                                </div>
                                <span style="font-size: 0.68rem; background: #EDE8E0; padding: 1px 5px; border-radius: 3px;">Im Graph</span>
                            `;
                            item.addEventListener("click", () => {{
                                searchDropdown.style.display = "none";
                                searchInput.value = res.title;
                                focusResourceInGraph(res.id);
                            }});
                            searchDropdown.appendChild(item);
                        }});
                    }}

                    searchDropdown.style.display = "block";
                }}, 180);
            }});

            document.addEventListener("click", (e) => {{
                if (!document.querySelector(".search-box-wrapper").contains(e.target)) {{
                    searchDropdown.style.display = "none";
                }}
            }});
        }}

        // Filter Chips Event Listeners
        document.querySelectorAll(".filter-chip").forEach(chip => {{
            chip.addEventListener("click", function() {{
                const type = this.getAttribute("data-type");
                if (type === "all") {{
                    const makeActive = !this.classList.contains("active");
                    document.querySelectorAll(".filter-chip").forEach(c => {{
                        if (makeActive) c.classList.add("active");
                        else c.classList.remove("active");
                    }});
                    if (makeActive) {{ cy.nodes().show(); cy.edges().show(); }}
                    else {{ cy.nodes().hide(); cy.edges().hide(); }}
                    updateVisibleNodesCount();
                    return;
                }}

                this.classList.toggle("active");
                const isNowActive = this.classList.contains("active");

                const selector = type === "folder" ? "[type ^= 'folder']" : `[type = "${{type}}"]`;
                const matchingNodes = cy.nodes(selector);
                if (isNowActive) matchingNodes.show();
                else matchingNodes.hide();

                cy.edges().forEach(edge => {{
                    if (edge.source().visible() && edge.target().visible()) edge.show();
                    else edge.hide();
                }});

                updateVisibleNodesCount();
            }});
        }});

        // Viewport & Legend Controls
        document.getElementById("btnFit").addEventListener("click", () => cy && cy.fit(null, 40));
        document.getElementById("btnZoomIn").addEventListener("click", () => cy && cy.zoom({{ level: cy.zoom() * 1.25, renderedPosition: {{ x: cy.width() / 2, y: cy.height() / 2 }} }}));
        document.getElementById("btnZoomOut").addEventListener("click", () => cy && cy.zoom({{ level: cy.zoom() * 0.8, renderedPosition: {{ x: cy.width() / 2, y: cy.height() / 2 }} }}));

        document.getElementById("btnFullscreen").addEventListener("click", () => {{
            const container = document.getElementById("stageContainer");
            if (!document.fullscreenElement) container.requestFullscreen();
            else document.exitFullscreen();
        }});

        document.getElementById("btnExportPng").addEventListener("click", () => {{
            if (!cy) return;
            const pngBlob = cy.png({{ output: "blob", bg: "#FAF8F5", full: true, scale: 2 }});
            const url = URL.createObjectURL(pngBlob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `iuenna_arche_graph_${{new Date().toISOString().split("T")[0]}}.png`;
            a.click();
            URL.revokeObjectURL(url);
        }});

        document.getElementById("drawerCloseBtn").addEventListener("click", () => {{
            closeInspector();
            resetHighlights();
        }});
        document.getElementById("drawerFocusNeighborsBtn").addEventListener("click", () => {{
            if (selectedNode) {{
                const neighborhood = selectedNode.neighborhood().add(selectedNode);
                cy.fit(neighborhood, 50);
            }}
        }});

        document.getElementById("legendToggle").addEventListener("click", function() {{
            const body = document.getElementById("legendBody");
            const chevron = document.getElementById("legendChevron");
            if (body.style.display === "none") {{
                body.style.display = "flex";
                chevron.classList.replace("fa-chevron-down", "fa-chevron-up");
            }} else {{
                body.style.display = "none";
                chevron.classList.replace("fa-chevron-up", "fa-chevron-down");
            }}
        }});

        // 1. Initial Synchronous Render (Instant & Offline-Compatible)
        initCytoscape(graphData.elements);

        // Fetch Live Updates if Available
        fetch("../data/arche_graph.json")
            .then(res => res.json())
            .then(data => {{
                graphData = data;
                if (data.metadata) {{
                    if (data.metadata.total_items) document.getElementById("pillItems").textContent = data.metadata.total_items.toLocaleString();
                    if (data.metadata.total_resources) document.getElementById("pillResources").textContent = data.metadata.total_resources.toLocaleString();
                    if (data.metadata.total_collections) document.getElementById("pillCollections").textContent = data.metadata.total_collections.toLocaleString();
                    if (data.metadata.total_size) document.getElementById("pillSize").textContent = data.metadata.total_size;
                }}
            }})
            .catch(err => console.log("Using embedded graph data:", err));

        // 2. Fetch Complete ARCHE Resource Corpus (20,541 items)
        const corpusStatusPill = document.getElementById("pillCorpusStatus");
        corpusStatusPill.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Lade 20.541 Ressourcen...';

        fetch("../data/arche_corpus.json")
            .then(res => {{
                if (!res.ok) throw new Error("Could not fetch arche_corpus.json");
                return res.json();
            }})
            .then(data => {{
                corpusData = data;
                corpusResources = data.resources || [];
                corpusStatusPill.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${{corpusResources.length.toLocaleString()}} Ressourcen aktiv`;
                corpusStatusPill.style.background = "#EBF3ED";
                corpusStatusPill.style.borderColor = "#B5D5BD";
                corpusStatusPill.style.color = "#2E6038";

                // Refresh open inspector with corpus details if a node is selected
                if (selectedNode) openInspector(selectedNode);

                // URL Parameters for Deep Linking (Corpus & Resource specific)
                const urlParams = new URLSearchParams(window.location.search);
                if (urlParams.get("q")) {{
                    document.getElementById("corpusSearchInput").value = urlParams.get("q");
                }}
                if (urlParams.get("open") === "corpus") {{
                    openCorpusModal();
                }} else if (urlParams.get("q")) {{
                    filterCorpus();
                }}
                if (urlParams.get("res")) focusResourceInGraph(urlParams.get("res"));
            }})
            .catch(err => {{
                console.warn("Could not load arche_corpus.json in background:", err);
                corpusStatusPill.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Korpus lokal';
                corpusStatusPill.style.background = "#FFF3CD";
                corpusStatusPill.style.color = "#856404";
            }});

        // Immediate URL Parameter handling for Tree Modal & Collection focus
        (function handleImmediateUrlParams() {{
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get("open") === "tree") {{
                openTreeModal();
            }}
            if (urlParams.get("col")) {{
                focusCollectionNodeInGraph(urlParams.get("col"));
            }}
        }})();
    </script>
</body>
</html>
'''

    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"[✓] Successfully generated complete {out_html} ({os.path.getsize(out_html) / 1024:.1f} KB)")

if __name__ == "__main__":
    generate()
