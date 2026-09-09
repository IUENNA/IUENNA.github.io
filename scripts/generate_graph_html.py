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
    search_file = os.path.join(data_dir, "arche_search_index.json")
    pubs_file = os.path.join(data_dir, "arche_publications.json")
    out_html = os.path.join(project_root, "graph", "index.html")
    
    with open(graph_file, "r", encoding="utf-8") as f:
        graph_data = json.load(f)
        
    with open(tree_file, "r", encoding="utf-8") as f:
        tree_data = json.load(f)

    with open(search_file, "r", encoding="utf-8") as f:
        search_data = json.load(f)

    with open(pubs_file, "r", encoding="utf-8") as f:
        pubs_data = json.load(f)
        
    embedded_graph_json = json.dumps(graph_data, ensure_ascii=False)
    embedded_tree_json = json.dumps(tree_data, ensure_ascii=False)
    embedded_search_json = json.dumps(search_data, ensure_ascii=False)
    embedded_pubs_json = json.dumps(pubs_data, ensure_ascii=False)

    html_content = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IUENNA – Knowledge Graph &amp; Corpus Explorer</title>
    
    <!-- Dublin Core Metatags -->
    <meta name="DC.title" content="IUENNA – Knowledge Graph &amp; Corpus Explorer">
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

    <!-- Leaflet.js for Geographical Place Maps -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

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
        .tool-btn.btn-active {{
            background: #FAF0EC;
            border-color: var(--primary);
            color: var(--primary);
        }}

        /* Hierarchie-Ebenen Schieberegler (LOD Slider) */
        .lod-slider-wrapper {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #FAF8F5;
            border: 1px solid var(--panel-border);
            padding: 3px 10px;
            border-radius: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }}
        .lod-slider-header {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .lod-slider-label {{
            font-size: 0.76rem;
            font-weight: 600;
            color: var(--text-dark);
            display: inline-flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
            margin: 0;
            white-space: nowrap;
        }}
        .lod-slider-badge {{
            font-size: 0.70rem;
            font-weight: 700;
            color: var(--primary);
            background: rgba(168, 68, 46, 0.08);
            border: 1px solid rgba(168, 68, 46, 0.2);
            padding: 2px 8px;
            border-radius: 10px;
            white-space: nowrap;
            min-width: 120px;
            text-align: center;
        }}
        .lod-slider-track-wrap {{
            display: inline-flex;
            align-items: center;
            width: 110px;
        }}
        .lod-range-slider {{
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: 6px;
            background: #E5DFD5;
            border-radius: 4px;
            outline: none;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .lod-range-slider:hover {{
            background: #D9D2C6;
        }}
        .lod-range-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--primary);
            border: 2px solid #FFFFFF;
            box-shadow: 0 2px 5px rgba(0,0,0,0.25);
            cursor: pointer;
            transition: transform 0.15s ease, background 0.15s ease;
        }}
        .lod-range-slider::-webkit-slider-thumb:hover {{
            transform: scale(1.2);
            background: var(--primary-hover);
        }}
        .lod-range-slider::-moz-range-thumb {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--primary);
            border: 2px solid #FFFFFF;
            box-shadow: 0 2px 5px rgba(0,0,0,0.25);
            cursor: pointer;
            transition: transform 0.15s ease;
        }}
        .lod-range-slider::-moz-range-thumb:hover {{
            transform: scale(1.2);
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
            top: calc(100% + 5px);
            left: 0;
            width: 480px;
            max-width: 90vw;
            background: #FFFFFF;
            border: 1px solid var(--panel-border);
            border-radius: 10px;
            box-shadow: 0 14px 36px rgba(0,0,0,0.18), 0 4px 12px rgba(0,0,0,0.08);
            max-height: 450px;
            overflow-y: auto;
            display: none;
            z-index: 1200;
        }}
        .search-category-header {{
            padding: 7px 12px 5px 12px;
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--text-muted);
            background: #F8F6F2;
            border-bottom: 1px solid #EAE6DF;
            border-top: 1px solid #EAE6DF;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .search-category-header:first-child {{
            border-top: none;
        }}
        .search-item {{
            padding: 8px 12px;
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            border-bottom: 1px solid #F5F3EF;
            font-size: 0.78rem;
            transition: background 0.1s ease;
        }}
        .search-item:last-child {{
            border-bottom: none;
        }}
        .search-item.selected, .search-item:hover {{
            background: #F4EFEA;
        }}
        .search-item-icon {{
            width: 26px;
            height: 26px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.76rem;
            flex-shrink: 0;
            color: #FFFFFF;
        }}
        .search-item-body {{
            flex: 1;
            min-width: 0;
        }}
        .search-item-title {{
            font-weight: 600;
            color: var(--text-dark);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .search-item-title mark {{
            background: #FFE8A3;
            color: inherit;
            padding: 0 1px;
            border-radius: 2px;
        }}
        .search-item-sub {{
            font-size: 0.7rem;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-top: 1px;
        }}
        .search-item-badge {{
            font-size: 0.64rem;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            background: #EDE8E0;
            color: var(--text-dark);
            flex-shrink: 0;
            white-space: nowrap;
        }}
        .search-no-results {{
            padding: 20px;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.8rem;
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

        /* Graph Loading Overlay */
        .graph-loading-overlay {{
            position: absolute;
            inset: 0;
            background: rgba(250, 248, 245, 0.94);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 1;
            transition: opacity 0.35s cubic-bezier(0.16, 1, 0.3, 1), visibility 0.35s ease;
        }}
        .graph-loading-overlay.hidden {{
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
        }}
        .graph-loading-card {{
            background: #FFFFFF;
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            box-shadow: 0 20px 48px rgba(32, 34, 38, 0.12), 0 4px 12px rgba(32, 34, 38, 0.06);
            padding: 34px 40px;
            text-align: center;
            max-width: 440px;
            width: 90%;
            display: flex;
            flex-direction: column;
            align-items: center;
            animation: cardFloat 0.45s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        @keyframes cardFloat {{
            from {{ opacity: 0; transform: translateY(16px) scale(0.97); }}
            to {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        .graph-loading-spinner-wrap {{
            position: relative;
            width: 68px;
            height: 68px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .graph-loading-ring {{
            position: absolute;
            inset: 0;
            border: 3.5px solid #EDE8E1;
            border-top-color: var(--primary);
            border-right-color: var(--secondary);
            border-radius: 50%;
            animation: ringSpin 1.1s linear infinite;
        }}
        @keyframes ringSpin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .graph-loading-icon {{
            font-size: 1.65rem;
            color: var(--primary);
            animation: iconPulse 2s ease-in-out infinite;
        }}
        @keyframes iconPulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.85; }}
            50% {{ transform: scale(1.12); opacity: 1; }}
        }}
        .graph-loading-title {{
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-dark);
            margin: 0 0 8px 0;
            font-family: "Plus Jakarta Sans", sans-serif;
            letter-spacing: -0.2px;
        }}
        .graph-loading-sub {{
            font-size: 0.80rem;
            color: var(--text-muted);
            line-height: 1.5;
            margin: 0 0 20px 0;
        }}
        .graph-loading-progress-track {{
            width: 100%;
            height: 6px;
            background: #EDE8E1;
            border-radius: 6px;
            overflow: hidden;
            position: relative;
        }}
        .graph-loading-progress-bar {{
            height: 100%;
            width: 50%;
            background: linear-gradient(90deg, var(--primary) 0%, #D46B4E 50%, var(--secondary) 100%);
            border-radius: 6px;
            transition: width 0.3s ease;
        }}
        .graph-loading-meta {{
            margin-top: 14px;
            font-size: 0.72rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .graph-loading-meta span {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
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

        .entity-profile-box, .provenance-box, .temporal-box {{
            background: #FDFBF7;
            border: 1px solid #EBE4D8;
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 12px;
        }}
        .entity-profile-details {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-top: 6px;
        }}
        .entity-prop-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.75rem;
            gap: 8px;
        }}
        .entity-prop-lbl {{
            color: var(--text-muted);
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }}
        .entity-prop-val {{
            color: var(--text-dark);
            font-weight: 600;
            text-align: right;
        }}
        .external-id-link {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 0.70rem;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.15s;
        }}
        .orcid-link {{
            background: #EEF7EE;
            color: #2E7D32;
            border: 1px solid #C8E6C9;
        }}
        .orcid-link:hover {{
            background: #E0F2E0;
            color: #1B5E20;
        }}
        .wikidata-link {{
            background: #F3F4F6;
            color: #374151;
            border: 1px solid #D1D5DB;
        }}
        .wikidata-link:hover {{
            background: #E5E7EB;
        }}
        .provenance-chips-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        .provenance-chip {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 9px;
            border-radius: 14px;
            font-size: 0.72rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease;
            border: 1px solid #DFD7CC;
            background: #FFFFFF;
            color: var(--text-dark);
        }}
        .provenance-chip:hover {{
            background: #F5EFE6;
            border-color: var(--primary);
            color: var(--primary);
            transform: translateY(-1px);
        }}
        .provenance-chip.person-chip i {{
            color: var(--color-person);
        }}
        .provenance-chip.org-chip i {{
            color: var(--color-organization);
        }}
        .temporal-pill-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .temporal-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: #EBF3ED;
            border: 1px solid #B5D5BD;
            color: #2E6038;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.72rem;
            font-weight: 600;
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

        /* Quick Preview Modal & Zoom Controls */
        .quick-preview-dialog {{
            background: #FFFFFF;
            border: 1px solid var(--panel-border);
            border-radius: var(--radius-lg);
            width: 100%;
            max-width: 900px;
            overflow: hidden;
            box-shadow: var(--shadow-lg);
            display: flex;
            flex-direction: column;
            transition: max-width 0.2s ease, max-height 0.2s ease;
        }}
        .quick-preview-dialog.is-fullscreen {{
            position: fixed;
            inset: 16px;
            max-width: calc(100vw - 32px);
            max-height: calc(100vh - 32px);
            height: calc(100vh - 32px);
            border-radius: 12px;
            z-index: 1350;
        }}
        .quick-preview-stage {{
            background: #141517;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 380px;
            height: 520px;
            user-select: none;
        }}
        .quick-preview-dialog.is-fullscreen .quick-preview-stage {{
            flex: 1;
            height: auto;
            min-height: auto;
        }}
        .preview-zoom-toolbar {{
            position: absolute;
            top: 14px;
            right: 14px;
            display: flex;
            align-items: center;
            gap: 4px;
            background: rgba(26, 28, 32, 0.88);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 8px;
            padding: 3px 8px;
            z-index: 20;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
        }}
        .zoom-tool-btn {{
            background: transparent;
            border: none;
            color: #FAF8F5;
            font-size: 0.80rem;
            padding: 5px 8px;
            border-radius: 4px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: background 0.15s, color 0.15s;
        }}
        .zoom-tool-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
            color: #FFFFFF;
        }}
        .zoom-level-badge {{
            color: #E6E2DB;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0 4px;
            min-width: 44px;
            text-align: center;
            font-variant-numeric: tabular-nums;
        }}
        .preview-canvas-wrapper {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
            cursor: grab;
        }}
        .preview-canvas-wrapper.is-dragging {{
            cursor: grabbing;
        }}
        .zoomable-preview-img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            transform-origin: center center;
            transition: transform 0.05s ease-out;
            will-change: transform;
            pointer-events: auto;
        }}
        .preview-hover-overlay {{
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.2s;
            border-radius: 6px;
        }}
        .drawer-preview-media:hover .preview-hover-overlay {{
            opacity: 1;
        }}
        .preview-hover-badge {{
            background: rgba(255, 255, 255, 0.94);
            color: var(--text-dark);
            font-size: 0.72rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
            display: inline-flex;
            align-items: center;
            gap: 6px;
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

        /* Toast Notification System */
        .toast-container {{
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 99999;
            display: flex;
            flex-direction: column;
            gap: 8px;
            pointer-events: none;
        }}
        .toast-message {{
            background: #1C2726;
            color: #FFFFFF;
            padding: 10px 18px;
            border-radius: var(--radius-md);
            font-size: 0.82rem;
            font-weight: 500;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            gap: 10px;
            pointer-events: auto;
            animation: fadeInToast 0.25s ease-out;
            border: 1px solid rgba(255,255,255,0.15);
            max-width: 90vw;
        }}
        .toast-message.warning {{
            border-left: 4px solid #C46238;
        }}
        .toast-message.info {{
            border-left: 4px solid #436980;
        }}
        .toast-message.success {{
            border-left: 4px solid #2B6955;
        }}
        @keyframes fadeInToast {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
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
                    <li><a href="index.html" class="nav-link active" style="color: var(--primary); font-weight: 600;">Knowledge Graph</a></li>
                    <li><a href="https://iuenna.hypotheses.org/" target="_blank" class="nav-link">Blog</a></li>
                    <li><a href="https://id.acdh.oeaw.ac.at/iuenna" target="_blank" class="nav-link btn btn-secondary" style="color: white; padding: 6px 16px;">ARCHE Data</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <!-- App Bar & Collection Stats -->
    <div class="graph-header-bar">
        <div class="graph-title-group">
            <h1><i class="fa-solid fa-circle-nodes" style="color: var(--primary);"></i> IUENNA Knowledge Graph &amp; Corpus Explorer</h1>
            <p>Vollständiges semantisches Netzwerk &amp; Archiv-Korpus des IUENNA-Repositoriums auf ARCHE (ACDH-CH / ÖAW)</p>
        </div>
        <div class="stats-pills">
            <span class="stat-pill"><i class="fa-solid fa-box-archive"></i> <strong id="pillItems">21.080</strong> ARCHE-Einträge</span>
            <span class="stat-pill"><i class="fa-solid fa-file-lines"></i> <strong id="pillResources">20.355</strong> Primärressourcen</span>
            <span class="stat-pill"><i class="fa-solid fa-folder-tree"></i> <strong id="pillCollections">434</strong> Sammlungen &amp; Ordner</span>
            <span class="stat-pill"><i class="fa-solid fa-user-group"></i> <strong id="pillResearchers">21</strong> Forscher:innen</span>
            <span class="stat-pill"><i class="fa-solid fa-book-open"></i> <strong id="pillPubs">23</strong> Publikationen</span>
            <span class="stat-pill"><i class="fa-solid fa-map-pin"></i> <strong id="pillPlaces">219</strong> Fundorte</span>
            <span class="stat-pill"><i class="fa-solid fa-building-columns"></i> <strong id="pillOrgs">9</strong> Institutionen</span>
            <span class="stat-pill"><i class="fa-solid fa-hard-drive"></i> <strong id="pillSize">356.68 GB</strong></span>
            <span class="stat-pill"><i class="fa-solid fa-network-wired"></i> <strong id="pillVisibleNodes">21.080</strong> im Graphen</span>
            <span class="stat-pill" id="pillCorpusStatus" style="background: #EBF3ED; border-color: #B5D5BD; color: #2E6038;">
                <i class="fa-solid fa-database"></i> <strong id="corpusStatusCount">20.355</strong> Korpus-Ressourcen
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
                <option value="preset" selected>Vorberechnetes Cluster-Layout (Schnell)</option>
                <option value="cose">Force-Directed (Organisch)</option>
                <option value="concentric">Konzentrisch (Hierarchie-Ringe)</option>
                <option value="breadthfirst">Baum-Hierarchie (Tree)</option>
                <option value="circle">Kreis (Zirkulär)</option>
            </select>

            <!-- Hierarchie-Ebenen Schieberegler (LOD Slider) -->
            <div class="lod-slider-wrapper" title="Hierarchie-Tiefe (Level of Detail) schrittweise anpassen">
                <div class="lod-slider-header">
                    <label for="lodSlider" class="lod-slider-label">
                        <i class="fa-solid fa-layer-group" style="color: var(--secondary);"></i> <span>Ebene:</span>
                    </label>
                    <span class="lod-slider-badge" id="lodLevelBadge">L1–L6 (Alle 434 Ordner)</span>
                </div>
                <div class="lod-slider-track-wrap">
                    <input type="range" id="lodSlider" min="1" max="6" value="6" step="1" class="lod-range-slider" list="lodTickmarks" aria-label="Hierarchie-Ebene">
                    <datalist id="lodTickmarks">
                        <option value="1" label="L1"></option>
                        <option value="2" label="L2"></option>
                        <option value="3" label="L3"></option>
                        <option value="4" label="L4"></option>
                        <option value="5" label="L5"></option>
                        <option value="6" label="L6"></option>
                    </datalist>
                </div>
            </div>

            <!-- Selection Bookmark Buttons (Merkliste) -->
            <button id="btnBookmarkCurrent" class="tool-btn" title="Aktuell ausgewählten Eintrag zur temporären Merkliste hinzufügen">
                <i class="fa-regular fa-bookmark" style="color: var(--secondary);"></i> <span>Auswahl merken</span>
            </button>
            <button id="btnOpenBookmarks" class="tool-btn" title="Gespeicherte Merkliste öffnen">
                <i class="fa-solid fa-bookmark" style="color: var(--primary);"></i> Merkliste (<span id="bookmarkCountPill">0</span>)
            </button>

            <!-- Ordnerbaum Button -->
            <button id="btnOpenTreeModal" class="tool-btn secondary-btn" title="Vollständigen ARCHE-Archivbaum aller 434 Ordner erkunden">
                <i class="fa-solid fa-folder-tree" style="color: var(--secondary);"></i> Ordnerbaum (434)
            </button>

            <!-- Corpus Catalog Drawer Button -->
            <button id="btnOpenCorpus" class="tool-btn primary-btn" title="Katalog aller 20.555 ARCHE-Ressourcen durchsuchen">
                <i class="fa-solid fa-database"></i> Corpus-Katalog (20.555)
            </button>

            <!-- Search Autocomplete -->
            <div class="search-box-wrapper">
                <i class="fa-solid fa-magnifying-glass search-icon"></i>
                <input type="text" id="searchInput" class="search-input" placeholder="21.070 ARCHE-Einträge durchsuchen (z.B. Glaser, Bioarchäologie, 2022, Jauntal)..." autocomplete="off">
                <div id="searchDropdown" class="search-dropdown"></div>
            </div>

            <!-- Entity Filter Chips -->
            <div class="filter-group">
                <span class="filter-chip active" data-type="all">Alle</span>
                <span class="filter-chip active" data-type="subcollection"><span class="chip-dot" style="background: var(--color-l1);"></span>Subcollections</span>
                <span class="filter-chip active" data-type="folder"><span class="chip-dot" style="background: var(--color-l2);"></span>Ordner</span>
                <span class="filter-chip active" data-type="dataset"><span class="chip-dot" style="background: #1B4965;"></span>Datensätze</span>
                <span class="filter-chip active" data-type="publication"><span class="chip-dot" style="background: #7B4F36;"></span>Publikationen</span>
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
            <button id="btnToggleEdges" class="tool-btn" title="Alle Kanten im Graphen ein- oder ausblenden">
                <i class="fa-solid fa-bezier-curve"></i> <span id="btnToggleEdgesText">Kanten verbergen</span>
            </button>
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

        <!-- Graph Loading Overlay -->
        <div id="graphLoadingOverlay" class="graph-loading-overlay">
            <div class="graph-loading-card">
                <div class="graph-loading-spinner-wrap">
                    <div class="graph-loading-ring"></div>
                    <i class="fa-solid fa-circle-nodes graph-loading-icon"></i>
                </div>
                <h3 class="graph-loading-title" id="graphLoadingTitle">Lade Knowledge Graph...</h3>
                <p class="graph-loading-sub" id="graphLoadingStatus">21.080 ARCHE-Knoten &amp; 35.597 Relationen werden initialisiert...</p>
                <div class="graph-loading-progress-track">
                    <div class="graph-loading-progress-bar" id="graphLoadingBar" style="width: 55%;"></div>
                </div>
                <div class="graph-loading-meta">
                    <span><i class="fa-solid fa-circle-nodes" style="color: var(--primary);"></i> 21.080 Knoten</span>
                    <span>&bull;</span>
                    <span><i class="fa-solid fa-folder-tree" style="color: var(--secondary);"></i> 434 Sammlungen</span>
                    <span>&bull;</span>
                    <span><i class="fa-solid fa-file-lines" style="color: #2A9D8F;"></i> 20.355 Ressourcen</span>
                </div>
            </div>
        </div>

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
                <li class="legend-item"><span class="legend-icon" style="background: #1B4965;"></span> Forschungsdatensatz / GeoPackage</li>
                <li class="legend-item"><span class="legend-icon" style="background: #7B4F36;"></span> Fachpublikation (Literaturnachweis)</li>
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
                <!-- Person / Organisation Profile Box -->
                <div id="drawerEntityProfileBox" class="entity-profile-box" style="display: none;">
                    <div class="drawer-section-title">
                        <span><i class="fa-solid fa-id-card" style="color: var(--primary);"></i> <span id="drawerEntityProfileHeading">Forscher:innen-Profil</span></span>
                    </div>
                    <div class="entity-profile-details">
                        <div id="drawerEntityAffiliationRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-building-columns"></i> Institution:</span>
                            <span id="drawerEntityAffiliationVal" class="entity-prop-val"></span>
                        </div>
                        <div id="drawerEntityOrcidRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-brands fa-orcid" style="color: #A6CE39;"></i> ORCID:</span>
                            <span class="entity-prop-val"><a id="drawerEntityOrcidLink" href="#" target="_blank" class="external-id-link orcid-link"><i class="fa-brands fa-orcid"></i> <span id="drawerEntityOrcidVal"></span> ↗</a></span>
                        </div>
                        <div id="drawerEntityWikidataRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-barcode"></i> Wikidata:</span>
                            <span class="entity-prop-val"><a id="drawerEntityWikidataLink" href="#" target="_blank" class="external-id-link wikidata-link"><i class="fa-solid fa-arrow-up-right-from-square"></i> <span id="drawerEntityWikidataVal"></span> ↗</a></span>
                        </div>
                    </div>
                </div>

                <!-- Publication Profile Box -->
                <div id="drawerPublicationBox" class="entity-profile-box" style="display: none; border-left: 4px solid #7B4F36;">
                    <div class="drawer-section-title">
                        <span><i class="fa-solid fa-book-open" style="color: #7B4F36;"></i> <span id="drawerPubHeading">Publikationsdetails</span></span>
                    </div>
                    <div class="entity-profile-details">
                        <div id="drawerPubAuthorsRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-user-pen"></i> Autor:innen:</span>
                            <span id="drawerPubAuthorsVal" class="entity-prop-val"></span>
                        </div>
                        <div id="drawerPubYearRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-calendar-day"></i> Erscheinungsjahr:</span>
                            <span id="drawerPubYearVal" class="entity-prop-val"></span>
                        </div>
                        <div id="drawerPubJournalRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-newspaper"></i> Verlag / Zeitschrift:</span>
                            <span id="drawerPubJournalVal" class="entity-prop-val"></span>
                        </div>
                        <div id="drawerPubPagesRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-file-lines"></i> Seiten:</span>
                            <span id="drawerPubPagesVal" class="entity-prop-val"></span>
                        </div>
                        <div id="drawerPubUrlRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-link"></i> Volltext / Link:</span>
                            <span class="entity-prop-val"><a id="drawerPubUrlLink" href="#" target="_blank" class="external-id-link" style="color: #7B4F36;"><i class="fa-solid fa-arrow-up-right-from-square"></i> <span id="drawerPubUrlVal">Online öffnen</span> ↗</a></span>
                        </div>
                    </div>
                </div>

                <!-- Dataset Profile Box (when Forschungsdatensatz / GeoPackage is selected) -->
                <div id="drawerDatasetBox" class="entity-profile-box" style="display: none; border-left: 4px solid #1B4965; background: #F0F4F8;">
                    <div class="drawer-section-title" style="margin-bottom: 8px;">
                        <span><i class="fa-solid fa-database" style="color: #1B4965;"></i> <span id="drawerDatasetHeading">Forschungsdatensatz / GeoPackage</span></span>
                    </div>
                    <div class="entity-profile-details">
                        <div id="drawerDatasetCitationRow" class="entity-prop-row" style="flex-direction: column; align-items: flex-start; gap: 4px;">
                            <span class="entity-prop-lbl" style="color: #1B4965; font-weight: 700;"><i class="fa-solid fa-quote-left"></i> Zitationsempfehlung (APA):</span>
                            <div id="drawerDatasetCitationVal" style="font-size: 0.73rem; line-height: 1.45; color: #1E293B; background: white; padding: 7px 9px; border-radius: 4px; border: 1px solid #CBD5E1; width: 100%; box-sizing: border-box; font-family: Georgia, serif;"></div>
                        </div>
                        <div id="drawerDatasetCreatorsRow" class="entity-prop-row" style="flex-direction: column; align-items: flex-start; gap: 4px; margin-top: 6px;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-user-group"></i> Urheber:innen / Beteiligte:</span>
                            <div id="drawerDatasetCreatorsChips" style="display: flex; flex-wrap: wrap; gap: 4px; width: 100%;"></div>
                        </div>
                        <div id="drawerDatasetParentRow" class="entity-prop-row" style="margin-top: 4px;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-folder-tree"></i> Zugehörige Sammlung:</span>
                            <span class="entity-prop-val"><a id="drawerDatasetParentLink" href="#" style="color: var(--secondary); font-weight: 600; text-decoration: none;">–</a></span>
                        </div>
                        <div id="drawerDatasetPidRow" class="entity-prop-row">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-link"></i> Handle / PID:</span>
                            <span class="entity-prop-val"><a id="drawerDatasetPidLink" href="#" target="_blank" class="external-id-link" style="color: #1B4965;"><span id="drawerDatasetPidVal">–</span> ↗</a></span>
                        </div>
                        <div id="drawerDatasetPlacesRow" class="entity-prop-row" style="flex-direction: column; align-items: flex-start; gap: 4px; margin-top: 6px;">
                            <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                                <span class="entity-prop-lbl"><i class="fa-solid fa-location-dot" style="color: #2D6A4F;"></i> Erfasste Fundorte:</span>
                                <span id="drawerDatasetPlacesCount" style="font-size: 0.68rem; padding: 1px 6px; border-radius: 8px; background: #D9E8DD; color: #2D6A4F; font-weight: 700;">0</span>
                            </div>
                            <ul id="drawerDatasetPlacesList" class="relations-list" style="max-height: 150px; overflow-y: auto; width: 100%;"></ul>
                        </div>
                    </div>
                </div>

                <!-- Place Profile Box (when Fundort / Place is selected) -->
                <div id="drawerPlaceBox" class="entity-profile-box" style="display: none; border-left: 4px solid #2D6A4F; background: #F4F8F5;">
                    <div class="drawer-section-title" style="margin-bottom: 8px;">
                        <span><i class="fa-solid fa-location-dot" style="color: #2D6A4F;"></i> <span id="drawerPlaceHeading">Fundort-Details</span></span>
                    </div>
                    <div class="entity-profile-details">
                        <div id="drawerPlaceCoordsRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-compass"></i> Koordinaten:</span>
                            <span id="drawerPlaceCoordsVal" class="entity-prop-val"></span>
                        </div>
                        <div id="drawerPlaceGeonamesRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-earth-americas"></i> Geonames:</span>
                            <span class="entity-prop-val"><a id="drawerPlaceGeonamesLink" href="#" target="_blank" class="external-id-link" style="color: #2D6A4F;"><i class="fa-solid fa-arrow-up-right-from-square"></i> <span id="drawerPlaceGeonamesVal">Geonames URI</span> ↗</a></span>
                        </div>
                        <div id="drawerPlaceDatasetRow" class="entity-prop-row" style="display: none; margin-top: 6px; padding: 6px 8px; background: white; border-radius: 4px; border: 1px solid #D9E8DD; flex-direction: column; align-items: flex-start; gap: 4px;">
                            <span class="entity-prop-lbl" style="color: #1B4965; font-weight: 600;"><i class="fa-solid fa-database"></i> Erfasst in Forschungsdatensatz:</span>
                            <div id="drawerPlaceDatasetChips" style="display: flex; flex-wrap: wrap; gap: 4px; width: 100%;"></div>
                        </div>
                        <!-- Interactive Place Map Card -->
                        <div id="drawerPlaceMapCard" style="display: none; margin-top: 8px; border: 1px solid #C8DDD0; border-radius: 8px; overflow: hidden; background: #FFFFFF;">
                            <div style="padding: 5px 10px; background: #EBF3ED; border-bottom: 1px solid #D9E8DD; display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 0.72rem; font-weight: 700; color: #2D6A4F; display: flex; align-items: center; gap: 5px;">
                                    <i class="fa-solid fa-map-location-dot"></i> Fundort-Karte
                                </span>
                                <button id="btnEnlargePlaceMap" class="tool-btn" style="font-size: 0.68rem; padding: 2px 7px; background: white;" title="Karte im Großformat vergrößern">
                                    <i class="fa-solid fa-expand"></i> Vergrößern
                                </button>
                            </div>
                            <div id="drawerPlaceMap" style="height: 155px; width: 100%; z-index: 1;"></div>
                            <div style="padding: 4px 10px; background: #FAF8F5; font-size: 0.68rem; color: var(--text-muted); display: flex; justify-content: space-between; align-items: center;">
                                <span id="drawerPlaceMapCoordsText">–</span>
                                <a id="drawerPlaceWmaLink" href="../wma/wma.html" target="_blank" style="color: #2D6A4F; font-weight: 600; text-decoration: none;">
                                    Im Web Mapping ↗
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ARCHE Resource Profile Box (when arche:Resource is selected) -->
                <div id="drawerResourceBox" class="entity-profile-box" style="display: none; border-left: 4px solid var(--primary); background: #FAF8F5;">
                    <div class="drawer-section-title" style="margin-bottom: 8px;">
                        <span><i class="fa-solid fa-file-lines" style="color: var(--primary);"></i> <span>ARCHE-Ressource</span></span>
                    </div>
                    <div class="entity-profile-details">
                        <div id="drawerResTypeRow" class="entity-prop-row">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-shapes"></i> Dateityp:</span>
                            <span id="drawerResTypeVal" class="entity-prop-val"></span>
                        </div>
                        <div id="drawerResSizeRow" class="entity-prop-row">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-weight-hanging"></i> Dateigröße:</span>
                            <span id="drawerResSizeVal" class="entity-prop-val"></span>
                        </div>
                        <div id="drawerResParentRow" class="entity-prop-row">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-folder-tree"></i> Sammlung/Ordner:</span>
                            <span class="entity-prop-val"><a id="drawerResParentLink" href="#" style="color: var(--secondary); font-weight: 600; text-decoration: none;">–</a></span>
                        </div>
                        <div id="drawerResPlaceRow" class="entity-prop-row" style="display: none;">
                            <span class="entity-prop-lbl"><i class="fa-solid fa-location-dot" style="color: #2D6A4F;"></i> Fundort:</span>
                            <span class="entity-prop-val"><a id="drawerResPlaceLink" href="#" style="color: #2D6A4F; font-weight: 600; text-decoration: none;">–</a></span>
                        </div>
                    </div>
                </div>

                <!-- Provenance / Researchers & Contributors Box (for collections/folders) -->
                <div id="drawerProvenanceBox" class="provenance-box" style="display: none;">
                    <div class="drawer-section-title">
                        <span><i class="fa-solid fa-user-group" style="color: var(--primary);"></i> Beteiligte Forscher:innen &amp; Institutionen</span>
                    </div>
                    <div id="drawerCreatorsGroup" style="margin-bottom: 8px;">
                        <div style="font-size: 0.70rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">Urheber:innen (Creators)</div>
                        <div id="drawerCreatorsChips" class="provenance-chips-group"></div>
                    </div>
                    <div id="drawerContributorsGroup" style="display: none;">
                        <div style="font-size: 0.70rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">Mitwirkende (Contributors)</div>
                        <div id="drawerContributorsChips" class="provenance-chips-group"></div>
                    </div>
                </div>

                <!-- Temporal / Excavation Campaign Box -->
                <div id="drawerTemporalBox" class="temporal-box" style="display: none;">
                    <div class="drawer-section-title">
                        <span><i class="fa-solid fa-clock-rotate-left" style="color: var(--secondary);"></i> Zeitliche Einordnung &amp; Kampagnen</span>
                    </div>
                    <div class="temporal-details">
                        <div id="drawerTemporalCampaign" class="temporal-pill-row"></div>
                        <div id="drawerTemporalEpoch" style="font-size: 0.74rem; color: var(--text-muted); margin-top: 4px;"></div>
                    </div>
                </div>

                <!-- Linked Publications Box (for collections/folders documented by publications) -->
                <div id="drawerLinkedPubsBox" style="display: none; background: #FAF5F2; border: 1px solid #E4D5CE; border-radius: 6px; padding: 10px; margin-bottom: 10px;">
                    <div class="drawer-section-title" style="margin-bottom: 6px;">
                        <span><i class="fa-solid fa-book-open" style="color: #7B4F36;"></i> Zugeordnete Fachpublikationen</span>
                        <span id="drawerLinkedPubsCount" style="font-size: 0.68rem; padding: 1px 6px; border-radius: 8px; background: #EBDAD2; color: #7B4F36; font-weight: 700;">0</span>
                    </div>
                    <ul id="drawerLinkedPubsList" class="relations-list" style="max-height: 140px; overflow-y: auto;"></ul>
                </div>

                <!-- Description -->
                <div>
                    <div class="drawer-section-title">Beschreibung / Kontext</div>
                    <p class="drawer-desc" id="drawerDesc"></p>
                </div>

                <!-- Live ARCHE Preview Card (Collapsible, Default: Eingeklappt) -->
                <div id="drawerPreviewBox" class="drawer-preview-box">
                    <div class="drawer-preview-header" id="drawerPreviewToggle" style="cursor: pointer; user-select: none;" title="ARCHE Dateivorschau auf- oder einklappen">
                        <span style="display: flex; align-items: center; gap: 6px;">
                            <i id="previewCollapseIcon" class="fa-solid fa-chevron-down" style="font-size: 0.72rem; color: var(--text-muted); transition: transform 0.2s ease; transform: rotate(-90deg);"></i>
                            <i class="fa-solid fa-eye" style="color: var(--primary);"></i> ARCHE Dateivorschau
                        </span>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span id="previewStatusBadge" style="font-size: 0.65rem; padding: 1px 6px; border-radius: 10px; background: #E8F5E9; color: #2E7D32;">Live von ARCHE</span>
                            <span id="previewToggleText" style="font-size: 0.68rem; color: var(--text-muted); font-weight: 500;">(Ausklappen)</span>
                        </div>
                    </div>
                    <div id="drawerPreviewCollapseBody" style="display: none;">
                        <div id="drawerPreviewMedia" class="drawer-preview-media" style="cursor: pointer; position: relative;" title="Klicken für interaktive Vergrößerung &amp; Zoom">
                            <img id="drawerPreviewImg" class="drawer-preview-img" alt="ARCHE Preview" />
                            <div class="preview-hover-overlay">
                                <span class="preview-hover-badge"><i class="fa-solid fa-magnifying-glass-plus"></i> Vergrößern</span>
                            </div>
                            <div id="drawerPreviewFallback" class="drawer-preview-fallback">
                                <i class="fa-solid fa-lock"></i>
                                <div style="font-size: 0.8rem; font-weight: 700; margin-bottom: 4px;">ARCHE-Zugriffsschutz (InC)</div>
                                <div style="font-size: 0.72rem; color: #BBB; line-height: 1.35; max-width: 280px; margin-bottom: 10px;">Vollansicht und Download im Repositorium nach Login verfügbar.</div>
                                <a id="drawerPreviewFallbackLink" href="#" target="_blank" class="tool-btn primary-btn" style="font-size: 0.72rem; padding: 4px 10px;">Auf ARCHE öffnen ↗</a>
                            </div>
                        </div>
                        <div class="drawer-preview-footer">
                            <span id="drawerPreviewDimensions"><i class="fa-solid fa-image"></i> Vorschau</span>
                            <button id="btnOpenFullPreview" class="tool-btn" style="font-size: 0.68rem; padding: 2px 7px;" title="Bild im Zoom-Viewer vergrößern"><i class="fa-solid fa-magnifying-glass-plus"></i> Vergrößern</button>
                        </div>
                    </div>
                </div>

                <!-- Associated Collections (for Person / Organisation) -->
                <div id="drawerEntityCollectionsBox" style="display: none;">
                    <div class="drawer-section-title">
                        <span><i class="fa-solid fa-folder-tree" style="color: var(--secondary);"></i> <span id="drawerEntityCollectionsHeading">Zugeordnete Sammlungen</span></span>
                        <span id="drawerEntityCollectionsCount" style="font-size: 0.68rem; padding: 1px 6px; border-radius: 8px; background: #EDE8E0; color: var(--text-dark);">0</span>
                    </div>
                    <ul id="drawerEntityCollectionsList" class="relations-list" style="max-height: 180px; overflow-y: auto;"></ul>
                    <button id="btnFocusEntityCollections" class="tool-btn" style="width: 100%; margin-top: 6px; font-size: 0.72rem; justify-content: center; background: white;"><i class="fa-solid fa-crosshairs"></i> Alle zugehörigen Bestände fokussieren</button>
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
                    <button id="btnFocusAllChildren" class="tool-btn" style="width: 100%; margin-top: 6px; font-size: 0.72rem; justify-content: center; background: white;"><i class="fa-solid fa-folder-tree"></i> Alle Unterordner fokussieren</button>
                </div>

                <!-- Resource Expansion Box -->
                <div id="drawerResourceExpansionBox" style="display: none; background: #FAF8F5; border: 1px solid var(--panel-border); border-radius: 6px; padding: 10px;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-dark); margin-bottom: 4px; display: flex; align-items: center; justify-content: space-between;">
                        <span><i class="fa-solid fa-network-wired" style="color: var(--primary);"></i> Dateien im Graphen</span>
                        <span id="drawerResCountBadge" style="background: var(--primary); color: white; padding: 1px 6px; border-radius: 10px; font-size: 0.68rem;">0</span>
                    </div>
                    <p id="drawerResHelpText" style="font-size: 0.72rem; color: var(--text-muted); margin: 0 0 8px 0;">Dateien dieses Ordners als Knoten in den Graphen einblenden:</p>
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

    <!-- Bookmarks (Merkliste) Modal -->
    <div id="bookmarksModal" class="modal-backdrop">
        <div class="modal-card" style="max-width: 680px; max-height: 80vh; display: flex; flex-direction: column;">
            <div class="modal-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-bookmark" style="color: var(--secondary); font-size: 1.15rem;"></i>
                    <div>
                        <h2 style="font-size: 1.1rem; margin: 0;">Gespeicherte Merkliste</h2>
                        <p style="font-size: 0.76rem; color: var(--text-muted); margin: 2px 0 0 0;">Im Browser gemerkte Sammlungen, Forscher:innen, Fundorte &amp; Ressourcen</p>
                    </div>
                </div>
                <button id="btnCloseBookmarksModal" class="drawer-close-btn">&times;</button>
            </div>
            <div style="padding: 10px 20px; background: #FAF8F5; border-bottom: 1px solid var(--panel-border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <span id="bookmarksModalCount" class="stat-pill" style="font-weight: 700; background: #EDE8E0;">0 Einträge</span>
                <div style="display: flex; gap: 6px;">
                    <button id="btnCopyBookmarksLink" class="tool-btn" style="font-size: 0.74rem;"><i class="fa-solid fa-share-nodes"></i> Link kopieren</button>
                    <button id="btnClearBookmarks" class="tool-btn" style="font-size: 0.74rem; color: #C0392B;"><i class="fa-solid fa-trash-can"></i> Alle leeren</button>
                </div>
            </div>
            <div id="bookmarksListContainer" style="padding: 14px 20px; overflow-y: auto; flex: 1;">
                <ul id="bookmarksList" class="relations-list"></ul>
            </div>
        </div>
    </div>

    <!-- Archiv-Ordnerbaum Modal (434 Sammlungen & Ordner) -->
    <div id="treeModal" class="modal-backdrop">
        <div class="modal-card" style="max-width: 980px;">
            <div class="modal-header">
                <div>
                    <h2><i class="fa-solid fa-folder-tree" style="color: var(--secondary);"></i> ARCHE Archiv-Hierarchie: Alle 434 Sammlungen &amp; Ordner</h2>
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

    <!-- Corpus Catalog Modal (20.355 Ressourcen) -->
    <div id="corpusModal" class="modal-backdrop">
        <div class="modal-card">
            <div class="modal-header">
                <div>
                    <h2><i class="fa-solid fa-database" style="color: var(--primary);"></i> ARCHE Corpus-Katalog: Alle 20.355 Primärressourcen</h2>
                    <p style="font-size: 0.78rem; color: var(--text-muted); margin: 2px 0 0 0;">Vollständiger Index aller digitalen Dateien und Grabungsfunde mit Live-Dateivorschau</p>
                </div>
                <button id="btnCorpusClose" class="drawer-close-btn">&times;</button>
            </div>

            <div style="padding: 10px 24px; background: #FFFFFF; border-bottom: 1px solid var(--panel-border); display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                <div style="position: relative; flex: 1; min-width: 220px;">
                    <i class="fa-solid fa-magnifying-glass" style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-size: 0.75rem; color: var(--text-muted);"></i>
                    <input type="text" id="corpusSearchInput" class="search-input" style="width: 100%;" placeholder="Titel, PID, Dateiname, Fundort, Ordner durchsuchen..." />
                </div>
                <select id="corpusColSelect" class="tool-select">
                    <option value="all">Alle Sammlungen &amp; Bestände</option>
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
                    <option value="all">Alle Fundorte (Lade...)</option>
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

    <!-- Quick Preview Lightbox Modal with Zoom & Pan for Maps, Plans and Documents -->
    <div id="quickPreviewModal" class="modal-backdrop" style="z-index: 1300;">
        <div class="quick-preview-dialog" id="quickPreviewDialog">
            <div class="modal-header" style="padding: 10px 18px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fa-solid fa-map-location-dot" id="quickPreviewTypeIcon" style="color: var(--primary); font-size: 1.1rem;"></i>
                    <div>
                        <h3 id="quickPreviewTitle" style="font-size: 1.05rem; margin: 0; color: var(--text-dark);">Dateiname</h3>
                        <div id="quickPreviewBreadcrumb" style="font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;"></div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <button id="btnToggleFullscreenPreview" class="tool-btn" style="font-size: 0.75rem; padding: 4px 8px;" title="Vollbild umschalten (Vergrößern)">
                        <i id="previewFullscreenIcon" class="fa-solid fa-expand"></i> <span id="previewFullscreenText">Vollbild</span>
                    </button>
                    <button id="btnQuickPreviewClose" class="drawer-close-btn">&times;</button>
                </div>
            </div>
            <div class="quick-preview-stage" id="quickPreviewStage">
                <!-- Floating Zoom Controls -->
                <div class="preview-zoom-toolbar">
                    <button id="btnZoomInPreview" class="zoom-tool-btn" title="Vergrößern (oder Mausrad)"><i class="fa-solid fa-plus"></i></button>
                    <button id="btnZoomOutPreview" class="zoom-tool-btn" title="Verkleinern (oder Mausrad)"><i class="fa-solid fa-minus"></i></button>
                    <span id="previewZoomLevel" class="zoom-level-badge">100%</span>
                    <button id="btnZoomResetPreview" class="zoom-tool-btn" title="Ansicht zurücksetzen (1:1)"><i class="fa-solid fa-rotate-left"></i></button>
                </div>

                <!-- Canvas / Image Wrapper with Pan & Drag -->
                <div class="preview-canvas-wrapper" id="previewCanvasWrapper" title="Klicken und Ziehen zum Verschieben, Mausrad zum Zoomen">
                    <img id="quickPreviewImg" src="" alt="Live Preview" class="zoomable-preview-img" style="display: none;" />
                </div>

                <div id="quickPreviewProtectedMsg" style="display: none; color: #FFF; text-align: center; padding: 30px 20px; z-index: 5;">
                    <i class="fa-solid fa-lock" style="font-size: 2.2rem; color: #E0A96D; margin-bottom: 12px; display: block;"></i>
                    <h4 style="font-size: 1rem; margin-bottom: 6px;">ARCHE-Zugriffsbeschränkung (InC-Lizenz)</h4>
                    <p style="font-size: 0.8rem; color: #BBB; max-width: 440px; margin: 0 auto 16px auto;">Diese historische Primärressource ist urheberrechtlich geschützt. Die Vollauflösung kann nach Login direkt im ARCHE-Repositorium eingesehen werden.</p>
                    <a id="quickPreviewArcheLink" href="#" target="_blank" class="tool-btn primary-btn" style="font-size: 0.8rem; padding: 7px 16px;"><i class="fa-solid fa-arrow-up-right-from-square"></i> Im ARCHE-Repositorium öffnen</a>
                </div>
            </div>
            <div style="padding: 10px 18px; background: #FAF8F5; border-top: 1px solid var(--panel-border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="font-size: 0.74rem; color: var(--text-muted);" id="quickPreviewMeta"></div>
                <div style="display: flex; gap: 8px;">
                    <button id="btnQuickPreviewInGraph" class="tool-btn secondary-btn" style="font-size: 0.75rem;"><i class="fa-solid fa-circle-nodes"></i> Im Graphen fokussieren</button>
                    <a id="quickPreviewFullResLink" href="#" target="_blank" class="tool-btn" style="font-size: 0.75rem;" title="ARCHE Bildressource in neuem Tab öffnen"><i class="fa-solid fa-arrow-up-right-from-square"></i> Vollauflösung</a>
                    <a id="quickPreviewDirectLink" href="#" target="_blank" class="tool-btn primary-btn" style="font-size: 0.75rem;"><i class="fa-solid fa-link"></i> ARCHE Handle</a>
                </div>
            </div>
        </div>
    </div>

    <!-- Large Geographical Place Map Modal (Fundort-Karte Großansicht) -->
    <div id="largePlaceMapModal" class="modal-backdrop" style="z-index: 1350;">
        <div class="large-map-dialog" style="background: white; border-radius: 12px; width: 92vw; max-width: 1100px; height: 85vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: var(--shadow-lg);">
            <div class="modal-header" style="padding: 10px 20px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fa-solid fa-map-location-dot" style="color: #2D6A4F; font-size: 1.2rem;"></i>
                    <div>
                        <h3 id="largePlaceMapTitle" style="font-size: 1.1rem; margin: 0; color: var(--text-dark);">Fundort-Karte</h3>
                        <div id="largePlaceMapSub" style="font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;">Archäologische Lokalisierung im Jauntal (Kärnten)</div>
                    </div>
                </div>
                <button id="btnLargePlaceMapClose" class="drawer-close-btn">&times;</button>
            </div>
            <div id="largePlaceMapCanvas" style="flex: 1; width: 100%; z-index: 1; min-height: 400px;"></div>
            <div style="padding: 10px 20px; background: #FAF8F5; border-top: 1px solid var(--panel-border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="font-size: 0.76rem; color: var(--text-muted);" id="largePlaceMapFooterInfo"></div>
                <div style="display: flex; gap: 8px;">
                    <a id="largePlaceMapWmaLink" href="../wma/wma.html" target="_blank" class="tool-btn primary-btn" style="font-size: 0.76rem; background: #2D6A4F; border-color: #2D6A4F;">
                        <i class="fa-solid fa-layer-group"></i> Im Web Mapping Portal (WMA) öffnen ↗
                    </a>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Notification Container -->
    <div id="toastContainer" class="toast-container"></div>

    <!-- Application Script -->
    <script>
        let cy = null;
        let graphData = {embedded_graph_json};
        let treeData = {embedded_tree_json};
        let searchIndex = {embedded_search_json};
        let publicationsData = {embedded_pubs_json};
        let corpusData = null;
        let corpusResources = [];
        let activeFilters = new Set(["all", "root", "subcollection", "folder", "folder_l2", "folder_l3", "folder_l4", "folder_l5", "folder_l6", "dataset", "resource", "organization", "person", "place", "publication", "period", "subject", "license"]);
        let selectedNode = null;
        let currentActivePreviewRes = null;
        let expandedNodesMap = new Map();
        let isPreviewCollapsed = true;
        let currentSelectedPlace = null;
        let drawerMiniMap = null;
        let drawerMiniMarker = null;
        let largePlaceMap = null;
        let largePlaceMarker = null;
        let previewZoom = 1.0;
        let previewPanX = 0;
        let previewPanY = 0;
        let isPreviewPanning = false;
        let previewPanStartX = 0;
        let previewPanStartY = 0;

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
            dataset: "#1B4965",
            resource: "#3D7068",
            organization: "#202226",
            person: "#C85A32",
            publication: "#7B4F36",
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
            preset: {{
                name: "preset",
                fit: true,
                padding: 40
            }},
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
                    if (lvl === 2 || t === "dataset") return 6;
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
            let safeElements = elements;
            if (elements && elements.nodes && elements.edges) {{
                const nodeIds = new Set(elements.nodes.map(n => (n.data ? n.data.id : n.id)));
                safeElements = {{
                    nodes: elements.nodes,
                    edges: elements.edges.filter(e => {{
                        const d = e.data || e;
                        return nodeIds.has(d.source) && nodeIds.has(d.target);
                    }})
                }};
            }}
            cy = cytoscape({{
                container: document.getElementById("cy"),
                elements: safeElements,
                boxSelectionEnabled: false,
                textureOnViewport: true,
                hideEdgesOnViewport: true,
                pixelRatio: 'auto',
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
                                if (ele.data("type") === "dataset") return 30;
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
                                if (ele.data("type") === "dataset") return 30;
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
                        selector: "node[type = 'dataset']",
                        style: {{
                            "shape": "round-diamond",
                            "width": 30,
                            "height": 30,
                            "background-color": "#1B4965",
                            "border-color": "#FFFFFF",
                            "border-width": 2
                        }}
                    }},
                    {{
                        selector: "node[type = 'resource']",
                        style: {{
                            "shape": "ellipse",
                            "width": 11,
                            "height": 11,
                            "border-width": 0.5,
                            "border-color": "#FFFFFF",
                            "min-zoomed-font-size": 13,
                            "background-color": function(ele) {{
                                return ele.data("color") || typeColors[ele.data("ftype")] || typeColors.resource || "#3D7068";
                            }}
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
                        selector: "edge[label = 'isPartOf']",
                        style: {{
                            "width": 0.8,
                            "line-color": "#C2D1C8",
                            "target-arrow-shape": "none",
                            "curve-style": "straight",
                            "opacity": 0.35
                        }}
                    }},
                    {{
                        selector: "edge[label = 'hasSpatialCoverage']",
                        style: {{
                            "width": 1.2,
                            "line-color": "#4A6B53",
                            "target-arrow-color": "#4A6B53",
                            "line-style": "dashed",
                            "opacity": 0.6
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
                        selector: "edge[label = 'hasCreator']",
                        style: {{
                            "width": 1.3,
                            "line-color": "#C85A32",
                            "target-arrow-color": "#C85A32",
                            "line-style": "dashed",
                            "opacity": 0.65
                        }}
                    }},
                    {{
                        selector: "edge[label = 'hasContributor']",
                        style: {{
                            "width": 1.1,
                            "line-color": "#888888",
                            "target-arrow-color": "#888888",
                            "line-style": "dotted",
                            "opacity": 0.55
                        }}
                    }},
                    {{
                        selector: "edge[label = 'isMemberOf']",
                        style: {{
                            "width": 1.2,
                            "line-color": "#5A6B7C",
                            "target-arrow-color": "#5A6B7C",
                            "line-style": "dashed",
                            "opacity": 0.55
                        }}
                    }},
                    {{
                        selector: "edge[label = 'hasPrincipalInvestigator']",
                        style: {{
                            "width": 2.0,
                            "line-color": "#C85A32",
                            "target-arrow-color": "#C85A32",
                            "opacity": 0.85
                        }}
                    }},
                    {{
                        selector: "edge[label = 'hasHostInstitution'], edge[label = 'hasFunder']",
                        style: {{
                            "width": 1.8,
                            "line-color": "#202226",
                            "target-arrow-color": "#202226",
                            "opacity": 0.75
                        }}
                    }},
                    {{
                        selector: "edge[label = 'documents']",
                        style: {{
                            "width": 1.5,
                            "line-color": "#7B4F36",
                            "target-arrow-color": "#7B4F36",
                            "line-style": "dashed",
                            "opacity": 0.75
                        }}
                    }},
                    {{
                        selector: "edge[label = 'hasAuthor']",
                        style: {{
                            "width": 1.4,
                            "line-color": "#C85A32",
                            "target-arrow-color": "#C85A32",
                            "opacity": 0.75
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
                layout: layoutConfigs.preset
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
            updateBookmarksUI();

            // Dismiss Loading Overlay on First Render unless preview requested
            const urlParamsInit = new URLSearchParams(window.location.search);
            if (urlParamsInit.get("loading") !== "1") {{
                cy.one("render", function() {{
                    const bar = document.getElementById("graphLoadingBar");
                    if (bar) bar.style.width = "100%";
                    const status = document.getElementById("graphLoadingStatus");
                    if (status) status.textContent = "Wissensgraph erfolgreich aufgebaut!";
                    setTimeout(hideGraphLoading, 250);
                }});
                setTimeout(hideGraphLoading, 1200);
            }}
        }}

        function showGraphLoading(title, subtext) {{
            const overlay = document.getElementById("graphLoadingOverlay");
            if (!overlay) return;
            if (title) document.getElementById("graphLoadingTitle").textContent = title;
            if (subtext) document.getElementById("graphLoadingStatus").textContent = subtext;
            const bar = document.getElementById("graphLoadingBar");
            if (bar) bar.style.width = "65%";
            overlay.classList.remove("hidden");
        }}

        function hideGraphLoading() {{
            const overlay = document.getElementById("graphLoadingOverlay");
            if (!overlay) return;
            const bar = document.getElementById("graphLoadingBar");
            if (bar) bar.style.width = "100%";
            setTimeout(() => {{
                overlay.classList.add("hidden");
            }}, 200);
        }}

        function getNodeByIdFlexible(id) {{
            if (!cy || !id) return null;
            const strId = String(id).trim();
            const cleanId = strId.replace(/^(col_|per_|person_|org_|pub_|plc_|place_|res_|dts_)/, '');
            const candidates = [
                strId,
                `dts_${{cleanId}}`,
                `plc_${{cleanId}}`,
                `place_${{cleanId}}`,
                `col_${{cleanId}}`,
                `per_${{cleanId}}`,
                `person_${{cleanId}}`,
                `org_${{cleanId}}`,
                `pub_${{cleanId}}`,
                `res_${{cleanId}}`,
                cleanId,
                (cleanId === "1792170" ? "iuenna_root" : null)
            ].filter(Boolean);

            for (const c of candidates) {{
                const found = cy.getElementById(c);
                if (found && found.length > 0) {{
                    return found;
                }}
            }}
            // Fallback: search by arche_id data property
            const byArcheId = cy.nodes().filter(n => String(n.data("arche_id")) === cleanId);
            if (byArcheId && byArcheId.length > 0) return byArcheId.first();

            // Fallback: search by exact label match
            const byLabel = cy.nodes().filter(n => (n.data("label") || "").toLowerCase() === strId.toLowerCase());
            if (byLabel && byLabel.length > 0) return byLabel.first();

            return null;
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

        // Bookmarks / Merkliste Logic
        let bookmarks = [];
        try {{
            const saved = localStorage.getItem("iuenna_graph_bookmarks");
            if (saved) bookmarks = JSON.parse(saved);
            if (!Array.isArray(bookmarks)) bookmarks = [];
        }} catch (e) {{
            bookmarks = [];
        }}

        function saveBookmarks() {{
            try {{
                localStorage.setItem("iuenna_graph_bookmarks", JSON.stringify(bookmarks));
            }} catch (e) {{
                console.warn("Could not persist bookmarks:", e);
            }}
            updateBookmarksUI();
        }}

        function updateBookmarksUI() {{
            const btnOpen = document.getElementById("btnOpenBookmarks");
            if (btnOpen) {{
                btnOpen.innerHTML = '<i class="fa-solid fa-bookmark" style="color: var(--secondary);"></i> Merkliste (' + bookmarks.length + ')';
            }}
            const modalCount = document.getElementById("bookmarksModalCount");
            if (modalCount) {{
                modalCount.textContent = bookmarks.length + (bookmarks.length === 1 ? ' Eintrag' : ' Einträge');
            }}
        }}

        function addBookmark(nodeOrData) {{
            if (!nodeOrData) {{
                if (selectedNode) {{
                    nodeOrData = selectedNode.data();
                }} else {{
                    showNotification("Bitte zuerst einen Eintrag im Graphen oder Korpus auswählen.", "warning");
                    return;
                }}
            }}
            const data = (nodeOrData && nodeOrData.data) ? nodeOrData.data() : nodeOrData;
            const bId = String(data.id || data.arche_id);
            const exists = bookmarks.find(b => String(b.id) === bId || (data.arche_id && String(b.arche_id) === String(data.arche_id)));
            if (exists) {{
                showNotification(`"${{data.label || data.title}}" ist bereits in der Merkliste.`, "info", 2000);
                return;
            }}
            const item = {{
                id: bId,
                arche_id: data.arche_id || bId.replace(/^[a-z]+_/, ''),
                label: data.label || data.title || bId,
                type: data.type || "folder",
                type_label: data.type_label || (data.type === "place" ? "Fundort" : (data.type === "person" ? "Forscher:in" : "Ordner")),
                color: data.color || typeColors[data.type] || "#888",
                pid: data.pid || "",
                timestamp: Date.now()
            }};
            bookmarks.push(item);
            saveBookmarks();
            showNotification(`"${{item.label}}" zur Merkliste hinzugefügt.`, "success", 2500);
        }}

        function removeBookmark(id) {{
            bookmarks = bookmarks.filter(b => b.id !== id);
            saveBookmarks();
            renderBookmarksList();
        }}

        function openBookmarksModal() {{
            renderBookmarksList();
            document.getElementById("bookmarksModal").classList.add("open");
        }}

        function closeBookmarksModal() {{
            document.getElementById("bookmarksModal").classList.remove("open");
        }}

        function renderBookmarksList() {{
            const list = document.getElementById("bookmarksList");
            if (!list) return;
            list.innerHTML = "";
            if (bookmarks.length === 0) {{
                list.innerHTML = `
                    <div style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
                        <i class="fa-regular fa-bookmark" style="font-size: 2.2rem; opacity: 0.4; margin-bottom: 12px; display: block;"></i>
                        <p style="margin: 0; font-size: 0.9rem; font-weight: 500;">Die Merkliste ist aktuell leer.</p>
                        <p style="margin: 4px 0 0 0; font-size: 0.76rem;">Wählen Sie einen Knoten im Graphen oder eine Ressource aus und klicken Sie auf <strong>"Auswahl merken"</strong>.</p>
                    </div>
                `;
                return;
            }}

            bookmarks.forEach(b => {{
                const li = document.createElement("li");
                li.className = "relation-item";
                li.style.justifyContent = "space-between";
                li.style.padding = "8px 12px";

                let iconClass = "fa-folder";
                if (b.type === "person") iconClass = "fa-user";
                else if (b.type === "organization") iconClass = "fa-building-columns";
                else if (b.type === "place") iconClass = "fa-location-dot";
                else if (b.type === "publication") iconClass = "fa-book-open";
                else if (b.type === "resource") iconClass = "fa-file";

                li.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px; min-width: 0; flex: 1;">
                        <span style="width: 26px; height: 26px; border-radius: 50%; background: ${{b.color}}; color: #FFF; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem; flex-shrink: 0;">
                            <i class="fa-solid ${{iconClass}}"></i>
                        </span>
                        <div style="min-width: 0; flex: 1;">
                            <div style="font-weight: 600; font-size: 0.82rem; color: var(--text-dark); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${{b.label}}</div>
                            <div style="font-size: 0.7rem; color: var(--text-muted);">${{b.type_label}} &bull; ARCHE #${{b.arche_id}}</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px; margin-left: 8px;">
                        <button class="tool-btn btn-bm-focus" title="Im Graphen fokussieren" style="font-size: 0.72rem; padding: 3px 8px;">
                            <i class="fa-solid fa-circle-nodes"></i>
                        </button>
                        ${{b.pid ? `<a href="${{b.pid}}" target="_blank" class="tool-btn" title="Auf ARCHE öffnen" style="font-size: 0.72rem; padding: 3px 8px;"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>` : ''}}
                        <button class="tool-btn btn-bm-delete" title="Aus Merkliste entfernen" style="font-size: 0.72rem; padding: 3px 8px; color: #C0392B;">
                            <i class="fa-solid fa-xmark"></i>
                        </button>
                    </div>
                `;

                li.querySelector(".btn-bm-focus").onclick = (e) => {{
                    e.stopPropagation();
                    closeBookmarksModal();
                    if (b.type === "resource") {{
                        focusResourceInGraph(b.id);
                    }} else {{
                        focusCollectionNodeInGraph(b.arche_id || b.id);
                    }}
                }};

                li.querySelector(".btn-bm-delete").onclick = (e) => {{
                    e.stopPropagation();
                    removeBookmark(b.id);
                }};

                li.onclick = () => {{
                    closeBookmarksModal();
                    if (b.type === "resource") {{
                        focusResourceInGraph(b.id);
                    }} else {{
                        focusCollectionNodeInGraph(b.arche_id || b.id);
                    }}
                }};

                list.appendChild(li);
            }});
        }}

        // Bookmarks UI event wiring
        const btnBmCurrent = document.getElementById("btnBookmarkCurrent");
        if (btnBmCurrent) btnBmCurrent.addEventListener("click", () => addBookmark());
        const btnOpenBm = document.getElementById("btnOpenBookmarks");
        if (btnOpenBm) btnOpenBm.addEventListener("click", openBookmarksModal);
        const btnCloseBm = document.getElementById("btnCloseBookmarksModal");
        if (btnCloseBm) btnCloseBm.addEventListener("click", closeBookmarksModal);
        const bmModal = document.getElementById("bookmarksModal");
        if (bmModal) bmModal.addEventListener("click", (e) => {{
            if (e.target === bmModal) closeBookmarksModal();
        }});
        const btnClearBm = document.getElementById("btnClearBookmarks");
        if (btnClearBm) btnClearBm.addEventListener("click", () => {{
            if (bookmarks.length === 0) return;
            if (confirm("Möchten Sie wirklich die gesamte Merkliste leeren?")) {{
                bookmarks = [];
                saveBookmarks();
                renderBookmarksList();
                showNotification("Merkliste geleert.", "info");
            }}
        }});
        const btnCopyBm = document.getElementById("btnCopyBookmarksLink");
        if (btnCopyBm) btnCopyBm.addEventListener("click", () => {{
            if (bookmarks.length === 0) {{
                showNotification("Die Merkliste ist leer.", "warning");
                return;
            }}
            const ids = bookmarks.map(b => b.id).join(",");
            const url = new URL(window.location.href);
            url.searchParams.set("bookmarks", ids);
            navigator.clipboard.writeText(url.toString()).then(() => {{
                showNotification("Link zur Merkliste kopiert!", "success");
            }}).catch(() => {{
                showNotification("Kopieren nicht möglich.", "warning");
            }});
        }});

        // Edge visibility state
        let edgesVisible = true;

        // Hierarchie-Ebenen Mapping für LOD Slider
        const lodLevels = {{
            1: {{ badge: "L1 (6 Subcollections)", maxLevel: 1 }},
            2: {{ badge: "L1–L2 (74 Hauptbestände)", maxLevel: 2 }},
            3: {{ badge: "L1–L3 (274 Fachordner)", maxLevel: 3 }},
            4: {{ badge: "L1–L4 (312 Teilsammlungen)", maxLevel: 4 }},
            5: {{ badge: "L1–L5 (432 Befundordner)", maxLevel: 5 }},
            6: {{ badge: "L1–L6 (Alle 434 Ordner)", maxLevel: 99 }}
        }};

        // Depth Filter (LOD) via Range Slider
        function applyDepthFilter(depth) {{
            if (!cy) return;
            const maxLevel = depth === "all" ? 99 : parseInt(depth, 10);
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
            if (edgesVisible) {{
                cy.edges().forEach(e => {{
                    if (e.source().visible() && e.target().visible()) e.show();
                    else e.hide();
                }});
            }} else {{
                cy.edges().hide();
            }}
            updateVisibleNodesCount();
            const currentLayout = document.getElementById("layoutSelect").value;
            if (currentLayout === "preset") {{
                cy.layout(layoutConfigs.preset).run();
            }} else {{
                const visNodes = cy.nodes(":visible");
                if (visNodes.length > 1500) {{
                    showNotification("Layout auf Makro-Knoten beschränkt (hohe Knotenanzahl)", "info", 3000);
                    visNodes.filter("[type != 'resource']").layout(layoutConfigs[currentLayout] || layoutConfigs.preset).run();
                }} else {{
                    cy.elements(":visible").layout(layoutConfigs[currentLayout] || layoutConfigs.preset).run();
                }}
            }}
        }}

        const lodSlider = document.getElementById("lodSlider");
        if (lodSlider) {{
            lodSlider.addEventListener("input", function() {{
                const val = parseInt(this.value, 10);
                const lvl = lodLevels[val] || lodLevels[6];
                const badge = document.getElementById("lodLevelBadge");
                if (badge) badge.textContent = lvl.badge;
                applyDepthFilter(lvl.maxLevel === 99 ? "all" : String(lvl.maxLevel));
            }});
        }}

        const btnToggleEdges = document.getElementById("btnToggleEdges");
        if (btnToggleEdges) {{
            btnToggleEdges.addEventListener("click", function() {{
                if (!cy) return;
                edgesVisible = !edgesVisible;
                const btnText = document.getElementById("btnToggleEdgesText");
                if (!edgesVisible) {{
                    cy.edges().hide();
                    this.classList.add("btn-active");
                    if (btnText) btnText.textContent = "Kanten einblenden";
                    showNotification("Alle Kanten ausgeblendet", "info", 1800);
                }} else {{
                    cy.edges().forEach(e => {{
                        if (e.source().visible() && e.target().visible()) e.show();
                    }});
                    this.classList.remove("btn-active");
                    if (btnText) btnText.textContent = "Kanten verbergen";
                    showNotification("Kanten wieder eingeblendet", "info", 1800);
                }}
            }});
        }}

        document.getElementById("layoutSelect").addEventListener("change", function() {{
            if (!cy) return;
            const layoutName = this.value;
            if (layoutName === "preset") {{
                showGraphLoading("Cluster-Layout laden...", "Vorberechnetes Koordinatenmodell wird geladen...");
                setTimeout(() => {{
                    cy.layout(layoutConfigs.preset).run();
                    hideGraphLoading();
                }}, 40);
                return;
            }}
            const visNodes = cy.nodes(":visible");
            const layoutLabels = {{
                cose: "Force-Directed (Organisch)",
                concentric: "Konzentrisch",
                breadthfirst: "Baum-Hierarchie",
                circle: "Zirkulär"
            }};
            const labelStr = layoutLabels[layoutName] || layoutName;
            if (visNodes.length > 1500) {{
                showNotification("Layout auf sichtbare Makro-Knoten beschränkt (hohe Knotenanzahl)", "info", 3000);
                showGraphLoading(`Layout: ${{labelStr}}`, `Berechne Anordnung für ${{visNodes.filter("[type != 'resource']").length}} Makro-Knoten...`);
                setTimeout(() => {{
                    visNodes.filter("[type != 'resource']").layout(layoutConfigs[layoutName] || layoutConfigs.preset).run();
                    hideGraphLoading();
                }}, 50);
            }} else {{
                showGraphLoading(`Layout: ${{labelStr}}`, `Berechne Anordnung für ${{visNodes.length}} Knoten...`);
                setTimeout(() => {{
                    cy.elements(":visible").layout(layoutConfigs[layoutName] || layoutConfigs.preset).run();
                    hideGraphLoading();
                }}, 50);
            }}
        }});

        // Toast Notification Helper
        function showNotification(msg, type = "info", duration = 4000) {{
            let container = document.getElementById("toastContainer");
            if (!container) {{
                container = document.createElement("div");
                container.id = "toastContainer";
                container.className = "toast-container";
                document.body.appendChild(container);
            }}
            const toast = document.createElement("div");
            toast.className = `toast-message ${{type}}`;
            const icon = type === "warning" ? "fa-triangle-exclamation" : (type === "success" ? "fa-circle-check" : "fa-circle-info");
            toast.innerHTML = `<i class="fa-solid ${{icon}}"></i> <span>${{msg}}</span>`;
            container.appendChild(toast);
            setTimeout(() => {{
                toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
                toast.style.opacity = "0";
                toast.style.transform = "translateY(8px)";
                setTimeout(() => toast.remove(), 300);
            }}, duration);
        }}

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
            const rawPath = d.path || [d.label];
            const path = rawPath.map(p => p === 'col_ret' ? 'Retrodigitalisat-Collection (RET)' : p);
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
            const previewCollapseBody = document.getElementById("drawerPreviewCollapseBody");
            const previewCollapseIcon = document.getElementById("previewCollapseIcon");
            const previewToggleText = document.getElementById("previewToggleText");

            // Determine if preview can be requested
            let previewPid = (d.type === "dataset" || d.type === "place" || d.type === "person" || d.type === "organization" || d.type === "publication" || d.type === "period" || d.type === "subject" || d.type === "license") ? null : (d.sample_pid || (d.type === "resource" ? d.pid : null));
            let previewTitle = d.sample_title || d.label;

            // If folder or if previewPid not set, fallback to finding a sample image inside it
            if (!previewPid && d.type !== "dataset" && d.type !== "place" && d.type !== "person" && d.type !== "organization" && d.type !== "publication" && corpusResources && corpusResources.length > 0) {{
                const sample = corpusResources.find(r => r.col_id === d.id || r.col === d.id || (r.path && r.path.includes(d.label)) || (d.arche_id && r.col_id === `col_${{d.arche_id}}`));
                if (sample) {{
                    previewPid = sample.pid;
                    previewTitle = `${{sample.title}} (Beispiel aus Ordner)`;
                }}
            }}

            if (previewPid) {{
                previewBox.style.display = "block";
                if (previewCollapseBody) previewCollapseBody.style.display = isPreviewCollapsed ? "none" : "block";
                if (previewCollapseIcon) previewCollapseIcon.style.transform = isPreviewCollapsed ? "rotate(-90deg)" : "rotate(0deg)";
                if (previewToggleText) previewToggleText.textContent = isPreviewCollapsed ? "(Ausklappen)" : "(Einklappen)";

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

            // Entity Profile Box (Person or Organisation)
            const profileBox = document.getElementById("drawerEntityProfileBox");
            const heading = document.getElementById("drawerEntityProfileHeading");
            const affilRow = document.getElementById("drawerEntityAffiliationRow");
            const affilVal = document.getElementById("drawerEntityAffiliationVal");
            const orcidRow = document.getElementById("drawerEntityOrcidRow");
            const orcidVal = document.getElementById("drawerEntityOrcidVal");
            const orcidLink = document.getElementById("drawerEntityOrcidLink");
            const wikiRow = document.getElementById("drawerEntityWikidataRow");
            const wikiVal = document.getElementById("drawerEntityWikidataVal");
            const wikiLink = document.getElementById("drawerEntityWikidataLink");

            if (d.type === "person" || d.type === "organization") {{
                profileBox.style.display = "block";
                heading.textContent = d.type === "person" ? "Forscher:innen-Profil" : "Institutions-Profil";

                if (d.affiliation || d.affiliation_name) {{
                    affilRow.style.display = "flex";
                    affilVal.textContent = d.affiliation || d.affiliation_name;
                    if (d.affiliation_id) {{
                        affilVal.style.cursor = "pointer";
                        affilVal.style.color = "var(--primary)";
                        affilVal.title = "Klicken, um Institution im Graphen zu fokussieren";
                        affilVal.onclick = () => {{
                            const orgNode = cy.$id(`org_${{d.affiliation_id}}`);
                            if (orgNode && orgNode.length > 0) {{
                                orgNode.show();
                                cy.center(orgNode);
                                cy.zoom({{ level: 2.0, position: orgNode.position() }});
                                openInspector(orgNode);
                                highlightNeighbors(orgNode);
                            }}
                        }};
                    }}
                }} else {{
                    affilRow.style.display = "none";
                }}

                if (d.orcid) {{
                    orcidRow.style.display = "flex";
                    orcidVal.textContent = d.orcid;
                    orcidLink.href = `https://orcid.org/${{d.orcid}}`;
                }} else {{
                    orcidRow.style.display = "none";
                }}

                if (d.wikidata) {{
                    wikiRow.style.display = "flex";
                    wikiVal.textContent = d.wikidata;
                    wikiLink.href = `https://www.wikidata.org/wiki/${{d.wikidata}}`;
                }} else {{
                    wikiRow.style.display = "none";
                }}
            }} else {{
                profileBox.style.display = "none";
            }}

            // Dataset Profile Box (when Forschungsdatensatz / GeoPackage is selected)
            const datasetBox = document.getElementById("drawerDatasetBox");
            if (d.type === "dataset") {{
                if (datasetBox) datasetBox.style.display = "block";

                // Citation
                const citVal = document.getElementById("drawerDatasetCitationVal");
                if (citVal) citVal.textContent = d.citation || "Keine Zitation verfügbar.";

                // Creators Chips
                const creatorsChips = document.getElementById("drawerDatasetCreatorsChips");
                if (creatorsChips) {{
                    creatorsChips.innerHTML = "";
                    (d.creators || []).forEach(c => {{
                        const chip = document.createElement("span");
                        chip.className = `provenance-chip ${{c.type === "Person" ? "person-chip" : "org-chip"}}`;
                        chip.innerHTML = `<i class="fa-solid ${{c.type === "Person" ? "fa-user" : "fa-building-columns"}}"></i> ${{c.name}}`;
                        chip.title = `${{c.name}} (${{c.type}}) im Graphen fokussieren`;
                        chip.addEventListener("click", () => {{
                            const target = getNodeByIdFlexible(c.id);
                            if (target && target.length > 0) {{
                                target.show();
                                cy.center(target);
                                cy.zoom({{ level: 1.8, position: target.position() }});
                                openInspector(target);
                                highlightNeighbors(target);
                            }}
                        }});
                        creatorsChips.appendChild(chip);
                    }});
                }}

                // Parent Collection Link
                const parentLink = document.getElementById("drawerDatasetParentLink");
                if (parentLink && d.parent_id) {{
                    const parentNode = getNodeByIdFlexible(d.parent_id);
                    const pTitle = parentNode && parentNode.data("label") ? parentNode.data("label") : `Sammlung ${{d.parent_id}}`;
                    parentLink.textContent = pTitle;
                    parentLink.onclick = (e) => {{
                        e.preventDefault();
                        if (parentNode && parentNode.length > 0) {{
                            parentNode.show();
                            cy.center(parentNode);
                            cy.zoom({{ level: 1.8, position: parentNode.position() }});
                            openInspector(parentNode);
                            highlightNeighbors(parentNode);
                        }}
                    }};
                }}

                // PID Link
                const pidLink = document.getElementById("drawerDatasetPidLink");
                const pidVal = document.getElementById("drawerDatasetPidVal");
                if (pidLink && pidVal) {{
                    const pidUrl = d.pid || `https://arche.acdh.oeaw.ac.at/api/${{d.arche_id}}`;
                    pidLink.href = pidUrl;
                    pidVal.textContent = d.pid ? d.pid.replace("https://hdl.handle.net/", "hdl:") : `ARCHE #${{d.arche_id}}`;
                }}

                // Connected Places list
                const placesCount = document.getElementById("drawerDatasetPlacesCount");
                const placesList = document.getElementById("drawerDatasetPlacesList");
                if (placesList && placesCount) {{
                    const spatEdges = cy.edges(`[source = "${{node.id()}}"][label = 'hasSpatialCoverage']`);
                    placesCount.textContent = spatEdges.length;
                    placesList.innerHTML = "";
                    spatEdges.forEach(edge => {{
                        const plcNode = edge.target();
                        const li = document.createElement("li");
                        li.className = "relation-item";
                        li.innerHTML = `
                            <span class="relation-target"><i class="fa-solid fa-location-dot" style="color: #2D6A4F;"></i> ${{plcNode.data("label")}}</span>
                            <span class="relation-label">Fundort</span>
                        `;
                        li.addEventListener("click", () => {{
                            plcNode.show();
                            cy.center(plcNode);
                            cy.zoom({{ level: 2.0, position: plcNode.position() }});
                            openInspector(plcNode);
                            highlightNeighbors(plcNode);
                        }});
                        placesList.appendChild(li);
                    }});
                }}
            }} else {{
                if (datasetBox) datasetBox.style.display = "none";
            }}

            // Place Profile Box (when Fundort / Place is selected)
            const placeBox = document.getElementById("drawerPlaceBox");
            if (d.type === "place") {{
                currentSelectedPlace = d;
                if (placeBox) placeBox.style.display = "block";
                const coordsRow = document.getElementById("drawerPlaceCoordsRow");
                const coordsVal = document.getElementById("drawerPlaceCoordsVal");
                const placeMapCard = document.getElementById("drawerPlaceMapCard");
                const placeMapCoordsText = document.getElementById("drawerPlaceMapCoordsText");
                const placeWmaLink = document.getElementById("drawerPlaceWmaLink");

                if (d.latitude !== undefined && d.longitude !== undefined && d.latitude !== null && d.longitude !== null) {{
                    coordsRow.style.display = "flex";
                    const latStr = typeof d.latitude === "number" ? d.latitude.toFixed(5) : d.latitude;
                    const lonStr = typeof d.longitude === "number" ? d.longitude.toFixed(5) : d.longitude;
                    coordsVal.textContent = `${{latStr}}°, ${{lonStr}}°`;
                    if (placeMapCard) placeMapCard.style.display = "block";
                    if (placeMapCoordsText) placeMapCoordsText.textContent = `${{latStr}}°, ${{lonStr}}°`;
                    if (placeWmaLink) placeWmaLink.href = `../wma/wma.html?lat=${{d.latitude}}&lng=${{d.longitude}}&zoom=15`;
                    updateDrawerMiniMap(d.latitude, d.longitude, d.label);
                }} else {{
                    coordsRow.style.display = "none";
                    if (placeMapCard) placeMapCard.style.display = "none";
                }}

                const geoRow = document.getElementById("drawerPlaceGeonamesRow");
                const geoVal = document.getElementById("drawerPlaceGeonamesVal");
                const geoLink = document.getElementById("drawerPlaceGeonamesLink");
                if (d.geonames) {{
                    geoRow.style.display = "flex";
                    const gnId = d.geonames.replace("https://sws.geonames.org/", "").replace(/\/$/, "");
                    geoVal.textContent = `Geonames #${{gnId}}`;
                    geoLink.href = d.geonames;
                }} else {{
                    geoRow.style.display = "none";
                }}

                // Show datasets containing this place
                const placeDatasetRow = document.getElementById("drawerPlaceDatasetRow");
                const placeDatasetChips = document.getElementById("drawerPlaceDatasetChips");
                if (placeDatasetRow && placeDatasetChips) {{
                    const incEdges = cy.edges(`[target = "${{node.id()}}"][label = 'hasSpatialCoverage']`);
                    const dtsNodes = incEdges.sources().filter(s => s.data("type") === "dataset");
                    if (dtsNodes.length > 0) {{
                        placeDatasetRow.style.display = "flex";
                        placeDatasetChips.innerHTML = "";
                        dtsNodes.forEach(dts => {{
                            const chip = document.createElement("span");
                            chip.className = "provenance-chip";
                            chip.style.borderColor = "#1B4965";
                            chip.style.color = "#1B4965";
                            chip.style.background = "#F0F4F8";
                            chip.innerHTML = `<i class="fa-solid fa-database" style="color: #1B4965;"></i> ${{dts.data("label")}}`;
                            chip.title = `${{dts.data("label")}} im Graphen anzeigen`;
                            chip.addEventListener("click", () => {{
                                dts.show();
                                cy.center(dts);
                                cy.zoom({{ level: 1.8, position: dts.position() }});
                                openInspector(dts);
                                highlightNeighbors(dts);
                            }});
                            placeDatasetChips.appendChild(chip);
                        }});
                    }} else {{
                        placeDatasetRow.style.display = "none";
                    }}
                }}
            }} else {{
                if (placeBox) placeBox.style.display = "none";
            }}

            // Resource Profile Box (when ARCHE Resource is selected)
            const resDrawerBox = document.getElementById("drawerResourceBox");
            if (d.type === "resource") {{
                if (resDrawerBox) resDrawerBox.style.display = "block";
                const typeVal = document.getElementById("drawerResTypeVal");
                if (typeVal) typeVal.textContent = d.type_label || d.ftype || "ARCHE-Datei";
                const sizeVal = document.getElementById("drawerResSizeVal");
                if (sizeVal) sizeVal.textContent = d.formatted_size || (d.size_bytes ? `${{(d.size_bytes / 1024).toFixed(1)}} KB` : "–");

                const parentLink = document.getElementById("drawerResParentLink");
                if (parentLink && (d.parent_col || d.col_id || d.col)) {{
                    const pColId = d.parent_col || d.col_id || `col_${{d.col}}`;
                    const parentNode = cy.$id(pColId);
                    const pTitle = (parentNode && parentNode.length > 0) ? parentNode.data("label") : `Sammlung ${{pColId}}`;
                    parentLink.textContent = pTitle;
                    parentLink.onclick = (e) => {{
                        e.preventDefault();
                        if (parentNode && parentNode.length > 0) {{
                            parentNode.show();
                            cy.center(parentNode);
                            cy.zoom({{ level: 1.8, position: parentNode.position() }});
                            openInspector(parentNode);
                            highlightNeighbors(parentNode);
                        }}
                    }};
                }}

                const placeRow = document.getElementById("drawerResPlaceRow");
                const placeLink = document.getElementById("drawerResPlaceLink");
                if (d.place && placeRow && placeLink) {{
                    placeRow.style.display = "flex";
                    placeLink.textContent = d.place;
                    placeLink.onclick = (e) => {{
                        e.preventDefault();
                        const plcNode = cy.nodes("[type = 'place']").filter(n => n.data("label") === d.place || (d.spatial_ids && d.spatial_ids.includes(n.data("arche_id"))));
                        if (plcNode.length > 0) {{
                            plcNode.show();
                            cy.center(plcNode);
                            cy.zoom({{ level: 1.8, position: plcNode.position() }});
                            openInspector(plcNode);
                            highlightNeighbors(plcNode);
                        }}
                    }};
                }} else if (placeRow) {{
                    placeRow.style.display = "none";
                }}
            }} else {{
                if (resDrawerBox) resDrawerBox.style.display = "none";
            }}

            // Publication Profile Box
            const pubBox = document.getElementById("drawerPublicationBox");
            if (d.type === "publication") {{
                pubBox.style.display = "block";
                const pubInfo = publicationsData && (publicationsData[d.arche_id] || publicationsData[d.id]);
                const authors = (pubInfo && pubInfo.authors) || d.authors || [];
                const authorsList = Array.isArray(authors) ? authors : (authors ? [authors] : []);
                const year = (pubInfo && pubInfo.date) || d.year;
                const journal = (pubInfo && (pubInfo.journal || pubInfo.publisher)) || d.journal || d.publisher;
                const pages = (pubInfo && pubInfo.pages) || d.pages;
                const url = (pubInfo && pubInfo.url) || d.url || d.pid;

                const authorsRow = document.getElementById("drawerPubAuthorsRow");
                const authorsVal = document.getElementById("drawerPubAuthorsVal");
                if (authorsList && authorsList.length > 0 && authorsList[0]) {{
                    authorsRow.style.display = "flex";
                    authorsVal.textContent = authorsList.join(", ");
                }} else {{
                    authorsRow.style.display = "none";
                }}

                const yearRow = document.getElementById("drawerPubYearRow");
                const yearVal = document.getElementById("drawerPubYearVal");
                if (year) {{
                    yearRow.style.display = "flex";
                    yearVal.textContent = year;
                }} else {{
                    yearRow.style.display = "none";
                }}

                const journalRow = document.getElementById("drawerPubJournalRow");
                const journalVal = document.getElementById("drawerPubJournalVal");
                if (journal) {{
                    journalRow.style.display = "flex";
                    journalVal.textContent = journal;
                }} else {{
                    journalRow.style.display = "none";
                }}

                const pagesRow = document.getElementById("drawerPubPagesRow");
                const pagesVal = document.getElementById("drawerPubPagesVal");
                if (pages) {{
                    pagesRow.style.display = "flex";
                    pagesVal.textContent = pages;
                }} else {{
                    pagesRow.style.display = "none";
                }}

                const urlRow = document.getElementById("drawerPubUrlRow");
                const urlLink = document.getElementById("drawerPubUrlLink");
                const urlVal = document.getElementById("drawerPubUrlVal");
                if (url) {{
                    urlRow.style.display = "flex";
                    urlLink.href = url;
                    urlVal.textContent = url.length > 35 ? url.substring(0, 32) + "..." : url;
                }} else {{
                    urlRow.style.display = "none";
                }}
            }} else {{
                pubBox.style.display = "none";
            }}

            // Linked Publications for Collections/Folders
            const linkedPubsBox = document.getElementById("drawerLinkedPubsBox");
            const linkedPubsList = document.getElementById("drawerLinkedPubsList");
            const linkedPubsCount = document.getElementById("drawerLinkedPubsCount");
            if (d.type && (d.type.startsWith("folder") || d.type === "subcollection" || d.type === "root" || d.type === "collection")) {{
                const incomingPubEdges = cy.edges(`[target = "${{node.id()}}"][label = 'documents']`);
                if (incomingPubEdges.length > 0) {{
                    linkedPubsBox.style.display = "block";
                    linkedPubsCount.textContent = incomingPubEdges.length;
                    linkedPubsList.innerHTML = "";
                    incomingPubEdges.forEach(edge => {{
                        const pubNode = edge.source();
                        const li = document.createElement("li");
                        li.className = "relation-item";
                        li.innerHTML = `
                            <span class="relation-target"><i class="fa-solid fa-book-open" style="color: #7B4F36;"></i> ${{pubNode.data("label")}}</span>
                            <span class="relation-label">${{pubNode.data("year") || "Publikation"}}</span>
                        `;
                        li.addEventListener("click", () => {{
                            pubNode.show();
                            cy.center(pubNode);
                            cy.zoom({{ level: 2.0, position: pubNode.position() }});
                            openInspector(pubNode);
                            highlightNeighbors(pubNode);
                        }});
                        linkedPubsList.appendChild(li);
                    }});
                }} else {{
                    linkedPubsBox.style.display = "none";
                }}
            }} else {{
                linkedPubsBox.style.display = "none";
            }}

            // Temporal / Excavation Campaign Box
            const tempBox = document.getElementById("drawerTemporalBox");
            const tempCamp = document.getElementById("drawerTemporalCampaign");
            const tempEpoch = document.getElementById("drawerTemporalEpoch");
            if (d.temporal || d.epoch) {{
                tempBox.style.display = "block";
                tempCamp.innerHTML = d.temporal ? `<span class="temporal-badge"><i class="fa-solid fa-calendar-check"></i> ${{d.temporal}}</span>` : "";
                tempEpoch.innerHTML = d.epoch ? `<i class="fa-solid fa-hourglass-half" style="color: #7E6B8F;"></i> Epoche: <strong>${{d.epoch}}</strong>` : "";
            }} else {{
                tempBox.style.display = "none";
            }}

            // Provenance Box (Creators & Contributors for collections/folders)
            const provBox = document.getElementById("drawerProvenanceBox");
            const creatorsGroup = document.getElementById("drawerCreatorsGroup");
            const creatorsChips = document.getElementById("drawerCreatorsChips");
            const contribsGroup = document.getElementById("drawerContributorsGroup");
            const contribsChips = document.getElementById("drawerContributorsChips");

            const hasCreators = d.creators && d.creators.length > 0;
            const hasContribs = d.contributors && d.contributors.length > 0;

            if (hasCreators || hasContribs) {{
                provBox.style.display = "block";
                creatorsChips.innerHTML = "";
                if (hasCreators) {{
                    creatorsGroup.style.display = "block";
                    d.creators.forEach(c => {{
                        const chip = document.createElement("span");
                        chip.className = `provenance-chip ${{c.type === "Person" ? "person-chip" : "org-chip"}}`;
                        chip.innerHTML = `<i class="fa-solid ${{c.type === "Person" ? "fa-user" : "fa-building-columns"}}"></i> ${{c.name}}`;
                        chip.title = `${{c.name}} (${{c.type}}) im Graphen fokussieren`;
                        chip.addEventListener("click", () => {{
                            const target = getNodeByIdFlexible(c.id);
                            if (target && target.length > 0) {{
                                target.show();
                                cy.center(target);
                                cy.zoom({{ level: 1.8, position: target.position() }});
                                openInspector(target);
                                highlightNeighbors(target);
                            }}
                        }});
                        creatorsChips.appendChild(chip);
                    }});
                }} else {{
                    creatorsGroup.style.display = "none";
                }}

                contribsChips.innerHTML = "";
                if (hasContribs) {{
                    contribsGroup.style.display = "block";
                    d.contributors.forEach(c => {{
                        const chip = document.createElement("span");
                        chip.className = `provenance-chip ${{c.type === "Person" ? "person-chip" : "org-chip"}}`;
                        chip.innerHTML = `<i class="fa-solid ${{c.type === "Person" ? "fa-user" : "fa-building-columns"}}"></i> ${{c.name}}`;
                        chip.title = `${{c.name}} (${{c.type}}) im Graphen fokussieren`;
                        chip.addEventListener("click", () => {{
                            const target = getNodeByIdFlexible(c.id);
                            if (target && target.length > 0) {{
                                target.show();
                                cy.center(target);
                                cy.zoom({{ level: 1.8, position: target.position() }});
                                openInspector(target);
                                highlightNeighbors(target);
                            }}
                        }});
                        contribsChips.appendChild(chip);
                    }});
                }} else {{
                    contribsGroup.style.display = "none";
                }}
            }} else {{
                provBox.style.display = "none";
            }}

            // Associated Collections Box (when Person, Organisation or Place is selected)
            const entColBox = document.getElementById("drawerEntityCollectionsBox");
            const entColList = document.getElementById("drawerEntityCollectionsList");
            const entColCount = document.getElementById("drawerEntityCollectionsCount");
            const entColHeading = document.getElementById("drawerEntityCollectionsHeading");
            const btnFocusEntCols = document.getElementById("btnFocusEntityCollections");

            if (d.type === "person" || d.type === "organization" || d.type === "place") {{
                entColList.innerHTML = "";
                const incomingEdges = cy.edges(`[target = "${{node.id()}}"]`);
                const colNodes = incomingEdges.sources().filter(s => {{
                    const t = s.data("type");
                    return t && (t.startsWith("folder") || t === "subcollection" || t === "root" || t === "collection" || t === "dataset");
                }});

                if (colNodes.length > 0) {{
                    entColBox.style.display = "block";
                    entColCount.textContent = colNodes.length;
                    if (d.type === "place") {{
                        entColHeading.textContent = "Verortete Sammlungen & Datensätze";
                    }} else {{
                        entColHeading.textContent = d.type === "person" ? "Beteiligte Sammlungen & Ordner" : "Zugeordnete Sammlungen & Bestände";
                    }}
                    colNodes.slice(0, 35).forEach(col => {{
                        const li = document.createElement("li");
                        li.className = "relation-item";
                        const isDts = col.data("type") === "dataset";
                        const colIcon = isDts ? "fa-database" : "fa-folder";
                        const colColor = isDts ? "#1B4965" : (col.data("color") || "#888");
                        const colBadge = isDts ? "GeoPackage" : (col.data("items") ? col.data("items").toLocaleString() + " Items" : "Ordner");
                        li.innerHTML = `
                            <span class="relation-target"><i class="fa-solid ${{colIcon}}" style="color: ${{colColor}};"></i> ${{col.data("label")}}</span>
                            <span class="relation-label">${{colBadge}}</span>
                        `;
                        li.addEventListener("click", () => {{
                            col.show();
                            cy.center(col);
                            cy.zoom({{ level: 2.0, position: col.position() }});
                            openInspector(col);
                            highlightNeighbors(col);
                        }});
                        entColList.appendChild(li);
                    }});

                    if (btnFocusEntCols) {{
                        btnFocusEntCols.onclick = () => {{
                            colNodes.show();
                            cy.fit(colNodes.union(node), 60);
                            highlightNeighbors(node);
                            showNotification(`${{colNodes.length}} Sammlungen von ${{d.label}} im Graphen fokussiert.`, "info", 2500);
                        }};
                    }}
                }} else {{
                    entColBox.style.display = "none";
                }}
            }} else {{
                entColBox.style.display = "none";
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
                childEdges.slice(0, 25).forEach(edge => {{
                    const child = edge.source();
                    const li = document.createElement("li");
                    li.className = "relation-item";
                    const isDts = child.data("type") === "dataset";
                    const childIcon = isDts ? "fa-database" : "fa-folder";
                    const childColor = isDts ? "#1B4965" : (child.data("color") || "#888");
                    const childBadge = isDts ? "GeoPackage" : (child.data("items") ? child.data("items") + " Items" : "Ordner");
                    li.innerHTML = `
                        <span class="relation-target"><i class="fa-solid ${{childIcon}}" style="color: ${{childColor}};"></i> ${{child.data("label")}}</span>
                        <span class="relation-label">${{childBadge}}</span>
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

                const btnFocusAll = document.getElementById("btnFocusAllChildren");
                if (btnFocusAll) {{
                    btnFocusAll.onclick = () => {{
                        const childNodes = childEdges.sources();
                        childNodes.show();
                        cy.fit(childNodes.union(node), 80);
                        highlightNeighbors(node);
                        showNotification(`${{childNodes.length}} Unterordner im Graphen fokussiert.`, "info", 2500);
                    }};
                }}
            }} else {{
                childBox.style.display = "none";
            }}

            // Resource Expansion Box
            const resBox = document.getElementById("drawerResourceExpansionBox");
            const btnExpand = document.getElementById("btnExpandResources");
            const btnCollapse = document.getElementById("btnCollapseResources");
            const resCountBadge = document.getElementById("drawerResCountBadge");
            const resHelpText = document.getElementById("drawerResHelpText");

            const isFolderLike = d.type && (d.type.startsWith("folder") || d.type === "subcollection" || d.type === "collection");
            if (isFolderLike && corpusResources && corpusResources.length > 0) {{
                resBox.style.display = "block";
                const archeId = String(d.arche_id || (d.id ? d.id.replace("col_", "") : ""));
                
                // Count unique local matches
                const localMatches = corpusResources.filter(r => {{
                    if (r.col_id === node.id() || r.col === node.id()) return true;
                    if (archeId && (r.col_id === archeId || r.col_id === `col_${{archeId}}` || r.col === archeId)) return true;
                    if (r.folder && (r.folder === d.label || (d.title && r.folder === d.title))) return true;
                    return false;
                }});

                const seenKeys = new Set();
                const uniqueLocalCount = localMatches.reduce((acc, r) => {{
                    const k = r.pid || r.title;
                    if (!seenKeys.has(k)) {{
                        seenKeys.add(k);
                        return acc + 1;
                    }}
                    return acc;
                }}, 0);

                if (uniqueLocalCount > 0) {{
                    resCountBadge.textContent = uniqueLocalCount.toLocaleString();
                    if (resHelpText) resHelpText.textContent = "Direkte Dateien dieses Ordners als Knoten in den Graphen einblenden:";
                }} else if (childEdges.length > 0) {{
                    resCountBadge.textContent = `${{(d.items || 0).toLocaleString()}} (in Unterordnern)`;
                    if (resHelpText) resHelpText.textContent = "Überordner: Einzeldateien sind in den Unterordnern organisiert.";
                }} else {{
                    resCountBadge.textContent = (d.items || 0).toLocaleString();
                    if (resHelpText) resHelpText.textContent = "Dateien dieses Ordners von ARCHE abrufen und einblenden:";
                }}

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

        // Collapsible Preview Box
        const previewToggle = document.getElementById("drawerPreviewToggle");
        const previewCollapseBody = document.getElementById("drawerPreviewCollapseBody");
        const previewCollapseIcon = document.getElementById("previewCollapseIcon");
        const previewToggleText = document.getElementById("previewToggleText");

        if (previewToggle && previewCollapseBody) {{
            previewToggle.addEventListener("click", () => {{
                isPreviewCollapsed = !isPreviewCollapsed;
                if (isPreviewCollapsed) {{
                    previewCollapseBody.style.display = "none";
                    if (previewCollapseIcon) previewCollapseIcon.style.transform = "rotate(-90deg)";
                    if (previewToggleText) previewToggleText.textContent = "(Ausklappen)";
                }} else {{
                    previewCollapseBody.style.display = "block";
                    if (previewCollapseIcon) previewCollapseIcon.style.transform = "rotate(0deg)";
                    if (previewToggleText) previewToggleText.textContent = "(Einklappen)";
                }}
            }});
        }}

        // Dynamic On-Demand Node Expansion for Resources
        async function expandResourcesForNode(nodeId, maxLimit = 60) {{
            if (!corpusResources) return;
            const parentNode = cy.$id(nodeId);
            if (!parentNode || parentNode.length === 0) return;
            const d = parentNode.data();
            const archeId = String(d.arche_id || (d.id ? d.id.replace("col_", "") : ""));
            const btnExpand = document.getElementById("btnExpandResources");
            const originalBtnHtml = btnExpand ? btnExpand.innerHTML : '<i class="fa-solid fa-plus"></i> Ressourcen aufklappen';

            // 1. Check local matches in corpusResources
            let matches = corpusResources.filter(r => {{
                if (r.col_id === nodeId || r.col === nodeId) return true;
                if (archeId && (r.col_id === archeId || r.col_id === `col_${{archeId}}` || r.col === archeId)) return true;
                if (r.folder && (r.folder === d.label || (d.title && r.folder === d.title))) return true;
                return false;
            }});

            // Deduplicate by PID or title
            const seenPids = new Set();
            const seenTitles = new Set();
            const uniqueMatches = [];
            for (const r of matches) {{
                if (r.pid && seenPids.has(r.pid)) continue;
                if (r.title && seenTitles.has(r.title)) continue;
                if (r.pid) seenPids.add(r.pid);
                if (r.title) seenTitles.add(r.title);
                uniqueMatches.push(r);
            }}
            matches = uniqueMatches;

            // 2. If no local matches, query ARCHE live API
            if (matches.length === 0 && archeId && /^\\d+$/.test(archeId)) {{
                try {{
                    if (btnExpand) {{
                        btnExpand.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Lade von ARCHE...';
                        btnExpand.disabled = true;
                    }}
                    const searchUrl = `https://arche.acdh.oeaw.ac.at/api/search?property%5B0%5D=https%3A%2F%2Fvocabs.acdh.oeaw.ac.at%2Fschema%23isPartOf&value%5B0%5D=https%3A%2F%2Farche.acdh.oeaw.ac.at%2Fapi%2F${{archeId}}`;
                    const resp = await fetch(searchUrl, {{
                        headers: {{ "Accept": "application/json" }}
                    }});
                    if (resp.ok) {{
                        const data = await resp.json();
                        const graph = data["@graph"] || [];
                        const fetched = [];
                        for (const item of graph) {{
                            const typeStr = String(item["@type"] || "");
                            if (typeStr.includes("Resource")) {{
                                const rawId = (item["@id"] || "").split("/").pop().replace("n0:", "");
                                let title = item["n1:hasTitle"] || item["n1:hasFilename"] || rawId;
                                if (Array.isArray(title)) title = title[0];
                                if (typeof title === "object" && title !== null) title = title["@value"] || "";

                                let pid = item["n1:hasPid"] || "";
                                if (typeof pid === "object" && pid !== null) pid = pid["@value"] || pid["@id"] || "";

                                let desc = item["n1:hasDescription"] || "";
                                if (typeof desc === "object" && desc !== null) desc = desc["@value"] || "";

                                let ext = "";
                                if (typeof title === "string" && title.includes(".")) {{
                                    ext = "." + title.split(".").pop().toLowerCase();
                                }}
                                let ftype = "other";
                                if ([".tif", ".tiff", ".jpg", ".jpeg", ".png"].includes(ext)) ftype = "image";
                                else if ([".shp", ".gpkg", ".dxf", ".dwg", ".geojson"].includes(ext)) ftype = "vector";
                                else if ([".ply", ".obj", ".stl"].includes(ext)) ftype = "3d";
                                else if ([".accdb", ".sqlite", ".db", ".xlsx", ".xls", ".csv"].includes(ext)) ftype = "database";
                                else if ([".pdf", ".doc", ".docx", ".txt"].includes(ext)) ftype = "document";

                                const resObj = {{
                                    id: `res_arche_${{rawId}}`,
                                    title: String(title),
                                    col: nodeId,
                                    col_id: nodeId,
                                    folder: d.label,
                                    path: d.path || ["IUENNA", d.label],
                                    place: d.spatial || "Jauntal",
                                    subjs: ["ARCHE"],
                                    pid: String(pid),
                                    thumb_url: pid ? `https://arche-thumbnails.acdh.oeaw.ac.at/?id=${{encodeURIComponent(pid)}}&width=360` : "",
                                    date: "n/a",
                                    type: ftype,
                                    description: desc || `ARCHE-Ressource: ${{title}}`
                                }};
                                fetched.push(resObj);
                                corpusResources.push(resObj);
                            }}
                        }}
                        if (fetched.length > 0) matches = fetched;
                    }}
                }} catch (err) {{
                    console.warn("ARCHE fetch error:", err);
                }} finally {{
                    if (btnExpand) {{
                        btnExpand.innerHTML = originalBtnHtml;
                        btnExpand.disabled = false;
                    }}
                }}
            }}

            // 3. If still no matches:
            if (matches.length === 0) {{
                const childEdges = cy.edges(`[target = "${{nodeId}}"][label = 'isPartOf']`);
                if (childEdges.length > 0) {{
                    showNotification(`Dieser Überordner enthält ${{childEdges.length}} Unterordner. Einzeldateien befinden sich in den jeweiligen Unterordnern.`, "info", 4500);
                }} else {{
                    showNotification("Keine individuellen Ressourcen für diesen Ordner auf ARCHE hinterlegt.", "warning", 3500);
                }}
                return;
            }}

            // 4. Render nodes in Cytoscape
            const toAdd = matches.slice(0, maxLimit);
            const parentPos = parentNode.position();
            const radius = 110 + Math.min(120, toAdd.length * 3);
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
                        description: res.description || `ARCHE-Ressource: ${{res.title}} | Fundort: ${{res.place}}`,
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
                showNotification(`${{addedIds.size}} Ressource(n) im Graphen aufgespannt.`, "success", 3000);
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
            showNotification("Ressourcen eingeklappt.", "info", 2000);
        }}

        function focusResourceInGraph(resId) {{
            closeCorpusModal();
            if (!cy || !resId) return;
            let node = getNodeByIdFlexible(resId) || cy.$id(resId);
            if (!node || node.length === 0) {{
                const cleanId = String(resId).replace(/^res_/, "");
                node = cy.$id(`res_${{cleanId}}`);
            }}
            if (!node || node.length === 0) {{
                const res = corpusResources.find(r => r.id === resId || r.id === `res_${{resId}}` || r.arche_id === resId);
                if (!res) {{
                    showNotification(`Ressource [${{resId}}] nicht im Graphen gefunden.`, "warning", 3000);
                    return;
                }}
                const parentColNode = getNodeByIdFlexible(res.col_id) || getNodeByIdFlexible(res.col) || cy.$id("iuenna_root");
                const parentPos = (parentColNode && parentColNode.length > 0) ? parentColNode.position() : {{ x: 0, y: 0 }};

                cy.add([
                    {{
                        group: "nodes",
                        data: {{
                            id: res.id,
                            arche_id: res.arche_id,
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
                            target: (parentColNode && parentColNode.length > 0) ? parentColNode.id() : "iuenna_root",
                            label: "isPartOf"
                        }}
                    }}
                ]);
                node = cy.$id(res.id);
            }}
            node.show();
            if (edgesVisible) node.connectedEdges().show();

            const chip = document.querySelector('.filter-chip[data-type="resource"]');
            if (chip && !chip.classList.contains('active')) chip.classList.add('active');

            cy.center(node);
            cy.zoom({{ level: 2.2, position: node.position() }});
            openInspector(node);
            highlightNeighbors(node);
        }}

        // Quick Preview Zoom & Pan Helper Functions
        function updatePreviewTransform() {{
            const imgEl = document.getElementById("quickPreviewImg");
            const badge = document.getElementById("previewZoomLevel");
            if (imgEl) {{
                imgEl.style.transform = `translate(${{previewPanX}}px, ${{previewPanY}}px) scale(${{previewZoom}})`;
            }}
            if (badge) {{
                badge.textContent = `${{Math.round(previewZoom * 100)}}%`;
            }}
        }}

        function resetPreviewZoom() {{
            previewZoom = 1.0;
            previewPanX = 0;
            previewPanY = 0;
            updatePreviewTransform();
        }}

        function zoomPreview(delta) {{
            const newZoom = Math.max(0.4, Math.min(8.0, previewZoom + delta));
            previewZoom = Math.round(newZoom * 100) / 100;
            updatePreviewTransform();
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
            const fullResLink = document.getElementById("quickPreviewFullResLink");
            const inGraphBtn = document.getElementById("btnQuickPreviewInGraph");

            resetPreviewZoom();

            titleEl.textContent = res.title;
            const rawPath = res.path || ["IUENNA", res.col];
            breadcrumbEl.textContent = rawPath.map(p => p === 'col_ret' ? 'Retrodigitalisat-Collection (RET)' : p).join(" › ");
            metaEl.innerHTML = `<strong>Fundort:</strong> ${{res.place || "–"}} &bull; <strong>Typ:</strong> ${{res.type || "ARCHE-Resource"}} &bull; <strong>PID:</strong> ${{res.pid}}`;

            archeLink.href = res.pid;
            directLink.href = res.pid;
            if (fullResLink) fullResLink.href = res.pid;

            inGraphBtn.onclick = () => {{
                modal.classList.remove("open");
                focusResourceInGraph(res.id);
            }};

            imgEl.style.display = "none";
            protectedMsg.style.display = "none";

            // Request high-resolution thumbnail (width=1920) for crisp inspection of maps/drawings
            const thumbUrl = `https://arche-thumbnails.acdh.oeaw.ac.at/?id=${{encodeURIComponent(res.pid)}}&width=1920`;
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

        // Quick Preview Zoom & Drag Controls
        const previewCanvasWrapper = document.getElementById("previewCanvasWrapper");
        if (previewCanvasWrapper) {{
            previewCanvasWrapper.addEventListener("wheel", (e) => {{
                e.preventDefault();
                const delta = e.deltaY < 0 ? 0.25 : -0.25;
                zoomPreview(delta);
            }}, {{ passive: false }});

            previewCanvasWrapper.addEventListener("mousedown", (e) => {{
                if (e.button !== 0) return;
                isPreviewPanning = true;
                previewPanStartX = e.clientX - previewPanX;
                previewPanStartY = e.clientY - previewPanY;
                previewCanvasWrapper.classList.add("is-dragging");
            }});

            window.addEventListener("mousemove", (e) => {{
                if (!isPreviewPanning) return;
                previewPanX = e.clientX - previewPanStartX;
                previewPanY = e.clientY - previewPanStartY;
                updatePreviewTransform();
            }});

            window.addEventListener("mouseup", () => {{
                if (isPreviewPanning) {{
                    isPreviewPanning = false;
                    previewCanvasWrapper.classList.remove("is-dragging");
                }}
            }});
        }}

        const btnZoomIn = document.getElementById("btnZoomInPreview");
        if (btnZoomIn) btnZoomIn.addEventListener("click", () => zoomPreview(0.3));
        const btnZoomOut = document.getElementById("btnZoomOutPreview");
        if (btnZoomOut) btnZoomOut.addEventListener("click", () => zoomPreview(-0.3));
        const btnZoomReset = document.getElementById("btnZoomResetPreview");
        if (btnZoomReset) btnZoomReset.addEventListener("click", () => resetPreviewZoom());

        const btnToggleFullscreen = document.getElementById("btnToggleFullscreenPreview");
        const quickPreviewDialog = document.querySelector(".quick-preview-dialog");
        if (btnToggleFullscreen && quickPreviewDialog) {{
            btnToggleFullscreen.addEventListener("click", () => {{
                quickPreviewDialog.classList.toggle("is-fullscreen");
                const isFull = quickPreviewDialog.classList.contains("is-fullscreen");
                btnToggleFullscreen.innerHTML = isFull ? '<i class="fa-solid fa-compress"></i>' : '<i class="fa-solid fa-expand"></i>';
                btnToggleFullscreen.title = isFull ? "Vollbild beenden" : "Vollbildmodus aktivieren";
            }});
        }}

        document.getElementById("btnQuickPreviewClose").addEventListener("click", () => {{
            document.getElementById("quickPreviewModal").classList.remove("open");
            if (quickPreviewDialog) quickPreviewDialog.classList.remove("is-fullscreen");
            if (btnToggleFullscreen) btnToggleFullscreen.innerHTML = '<i class="fa-solid fa-expand"></i>';
        }});

        const drawerPreviewMedia = document.getElementById("drawerPreviewMedia");
        if (drawerPreviewMedia) {{
            drawerPreviewMedia.addEventListener("click", (e) => {{
                if (e.target && e.target.closest("#drawerPreviewFallbackLink")) return;
                if (currentActivePreviewRes) {{
                    openQuickPreview(currentActivePreviewRes);
                }}
            }});
        }}

        document.getElementById("btnOpenFullPreview").addEventListener("click", () => {{
            if (currentActivePreviewRes) {{
                openQuickPreview(currentActivePreviewRes);
            }}
        }});

        // Mini Map in Drawer & Large Map Modal
        function updateDrawerMiniMap(lat, lng, label) {{
            const mapContainer = document.getElementById("drawerPlaceMap");
            if (!mapContainer || typeof L === "undefined") return;
            if (!drawerMiniMap) {{
                drawerMiniMap = L.map('drawerPlaceMap', {{
                    zoomControl: false,
                    attributionControl: false
                }});
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 18
                }}).addTo(drawerMiniMap);
            }}
            if (drawerMiniMarker) {{
                drawerMiniMap.removeLayer(drawerMiniMarker);
            }}
            drawerMiniMap.setView([lat, lng], 13);
            drawerMiniMarker = L.marker([lat, lng]).addTo(drawerMiniMap);
            setTimeout(() => {{
                drawerMiniMap.invalidateSize();
            }}, 200);
        }}

        function openLargePlaceMap(placeData) {{
            if (!placeData || placeData.latitude === undefined || placeData.longitude === undefined || typeof L === "undefined") return;
            currentSelectedPlace = placeData;
            const modal = document.getElementById("largePlaceMapModal");
            const titleEl = document.getElementById("largePlaceMapTitle");
            const subEl = document.getElementById("largePlaceMapSub");
            const footerEl = document.getElementById("largePlaceMapFooterInfo");
            const wmaLink = document.getElementById("largePlaceMapWmaLink");

            titleEl.textContent = `Fundort: ${{placeData.label || 'Fundort'}}`;
            subEl.textContent = placeData.geonames ? `Geonames: ${{placeData.geonames}}` : 'Archäologische Fundstelle im Jauntal';
            const latStr = typeof placeData.latitude === 'number' ? placeData.latitude.toFixed(5) : placeData.latitude;
            const lonStr = typeof placeData.longitude === 'number' ? placeData.longitude.toFixed(5) : placeData.longitude;
            footerEl.innerHTML = `<strong>Koordinaten:</strong> ${{latStr}}°, ${{lonStr}}° &bull; <strong>Typ:</strong> Fundort (Place)`;
            wmaLink.href = `../wma/wma.html?lat=${{placeData.latitude}}&lng=${{placeData.longitude}}&zoom=15`;

            modal.classList.add("open");

            setTimeout(() => {{
                if (!largePlaceMap) {{
                    largePlaceMap = L.map('largePlaceMapCanvas', {{
                        attributionControl: true
                    }});
                    const osmLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        maxZoom: 19,
                        attribution: '&copy; OpenStreetMap contributors'
                    }});
                    const topoLayer = L.tileLayer('https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png', {{
                        maxZoom: 17,
                        attribution: 'Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap'
                    }});
                    osmLayer.addTo(largePlaceMap);
                    L.control.layers({{
                        "OpenStreetMap (Standard)": osmLayer,
                        "OpenTopoMap (Topographie)": topoLayer
                    }}).addTo(largePlaceMap);
                }}
                if (largePlaceMarker) {{
                    largePlaceMap.removeLayer(largePlaceMarker);
                }}
                largePlaceMap.setView([placeData.latitude, placeData.longitude], 14);
                largePlaceMarker = L.marker([placeData.latitude, placeData.longitude]).addTo(largePlaceMap);
                largePlaceMarker.bindPopup(`<b>${{placeData.label || 'Fundort'}}</b><br>${{latStr}}°, ${{lonStr}}°`).openPopup();
                largePlaceMap.invalidateSize();
            }}, 180);
        }}

        const btnEnlargePlaceMap = document.getElementById("btnEnlargePlaceMap");
        if (btnEnlargePlaceMap) {{
            btnEnlargePlaceMap.addEventListener("click", () => {{
                if (currentSelectedPlace) {{
                    openLargePlaceMap(currentSelectedPlace);
                }}
            }});
        }}

        const btnLargePlaceMapClose = document.getElementById("btnLargePlaceMapClose");
        if (btnLargePlaceMapClose) {{
            btnLargePlaceMapClose.addEventListener("click", () => {{
                document.getElementById("largePlaceMapModal").classList.remove("open");
            }});
        }}

        const largePlaceMapModal = document.getElementById("largePlaceMapModal");
        if (largePlaceMapModal) {{
            largePlaceMapModal.addEventListener("click", (e) => {{
                if (e.target === largePlaceMapModal) {{
                    largePlaceMapModal.classList.remove("open");
                }}
            }});
        }}

        window.addEventListener("keydown", (e) => {{
            if (e.key === "Escape") {{
                const previewModal = document.getElementById("quickPreviewModal");
                if (previewModal && previewModal.classList.contains("open")) {{
                    if (quickPreviewDialog && quickPreviewDialog.classList.contains("is-fullscreen")) {{
                        quickPreviewDialog.classList.remove("is-fullscreen");
                        if (btnToggleFullscreen) btnToggleFullscreen.innerHTML = '<i class="fa-solid fa-expand"></i>';
                    }} else {{
                        previewModal.classList.remove("open");
                    }}
                }}
                const placeModal = document.getElementById("largePlaceMapModal");
                if (placeModal && placeModal.classList.contains("open")) {{
                    placeModal.classList.remove("open");
                }}
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
            if (!cy || !archeId) return;
            let node = getNodeByIdFlexible(archeId);

            if (!node || node.length === 0) {{
                // If deep level is filtered out, switch slider to all (level 6)
                const slider = document.getElementById("lodSlider");
                if (slider) slider.value = 6;
                const badge = document.getElementById("lodLevelBadge");
                if (badge) badge.textContent = "L1–L6 (Alle 434 Ordner)";
                applyDepthFilter("all");
                node = getNodeByIdFlexible(archeId);
            }}

            if (node && node.length > 0) {{
                node.show();
                cy.center(node);
                cy.zoom({{ level: 2.0, position: node.position() }});
                openInspector(node);
                highlightNeighbors(node);
            }} else {{
                showNotification(`Eintrag [${{archeId}}] im Graphen nicht gefunden.`, "warning");
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

        function populateCorpusFilters() {{
            if (!corpusResources || corpusResources.length === 0) return;

            // 1. Dynamic Places with counts
            const placeCounts = {{}};
            corpusResources.forEach(r => {{
                const p = (r.place || "").trim();
                if (p && p !== "–") {{
                    placeCounts[p] = (placeCounts[p] || 0) + 1;
                }}
            }});

            const sortedPlaces = Object.keys(placeCounts).sort((a, b) => {{
                if (placeCounts[b] !== placeCounts[a]) return placeCounts[b] - placeCounts[a];
                return a.localeCompare(b);
            }});

            const currentPlace = corpusPlaceSelect.value;
            corpusPlaceSelect.innerHTML = '<option value="all">Alle Fundorte (' + Object.keys(placeCounts).length + ' Orte)</option>';
            sortedPlaces.forEach(p => {{
                const opt = document.createElement("option");
                opt.value = p;
                opt.textContent = `${{p}} (${{placeCounts[p].toLocaleString()}})`;
                corpusPlaceSelect.appendChild(opt);
            }});
            if (sortedPlaces.includes(currentPlace)) {{
                corpusPlaceSelect.value = currentPlace;
            }}

            // 2. Dynamic Collections with counts
            const colCounts = {{}};
            const colTitles = {{}};
            corpusResources.forEach(r => {{
                const cid = r.col_id || r.col || "unassigned";
                colCounts[cid] = (colCounts[cid] || 0) + 1;
                const title = r.folder || (r.path && r.path[r.path.length - 1]) || cid;
                if (!colTitles[cid] || colTitles[cid].length < title.length) {{
                    colTitles[cid] = title;
                }}
            }});

            const sortedCols = Object.keys(colCounts).sort((a, b) => colCounts[b] - colCounts[a]);
            const currentCol = corpusColSelect.value;
            corpusColSelect.innerHTML = '<option value="all">Alle Sammlungen &amp; Bestände (' + Object.keys(colCounts).length + ')</option>';
            sortedCols.forEach(cid => {{
                const opt = document.createElement("option");
                opt.value = cid;
                const name = colTitles[cid] || cid;
                const shortName = name.length > 52 ? name.substring(0, 50) + "..." : name;
                opt.textContent = `${{shortName}} (${{colCounts[cid].toLocaleString()}})`;
                corpusColSelect.appendChild(opt);
            }});
            if (sortedCols.includes(currentCol)) {{
                corpusColSelect.value = currentCol;
            }}
        }}

        function openCorpusModal() {{
            corpusModal.classList.add("open");
            if (corpusPlaceSelect.options.length <= 1) {{
                populateCorpusFilters();
            }}
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
            const tokens = q ? q.split(/\s+/).filter(Boolean) : [];

            filteredCorpusItems = corpusResources.filter(r => {{
                if (col !== "all" && r.col !== col && r.col_id !== col) return false;
                if (type !== "all" && r.type !== type) return false;
                if (place !== "all") {{
                    if (r.place !== place && (!r.place || !r.place.toLowerCase().includes(place.toLowerCase()))) return false;
                }}
                if (tokens.length > 0) {{
                    const match = tokens.every(token => {{
                        return (r.title && r.title.toLowerCase().includes(token)) ||
                               (r.pid && r.pid.toLowerCase().includes(token)) ||
                               (r.place && r.place.toLowerCase().includes(token)) ||
                               (r.folder && r.folder.toLowerCase().includes(token)) ||
                               (r.path && r.path.some(p => p.toLowerCase().includes(token))) ||
                               (r.subjs && r.subjs.some(s => s.toLowerCase().includes(token)));
                    }});
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

        function highlightMatch(text, tokens) {{
            if (!text || !tokens || !tokens.length) return text || "";
            let result = String(text);
            tokens.forEach(tok => {{
                if (!tok || tok.length < 1) return;
                const idx = result.toLowerCase().indexOf(tok.toLowerCase());
                if (idx !== -1) {{
                    const matched = result.substring(idx, idx + tok.length);
                    result = result.substring(0, idx) + "<mark>" + matched + "</mark>" + result.substring(idx + tok.length);
                }}
            }});
            return result;
        }}

        function setupSearch() {{
            let debounceTimer = null;
            let currentFocusIndex = -1;

            function selectItem(itemEl) {{
                if (!itemEl) return;
                const targetType = itemEl.getAttribute("data-target-type");
                const targetId = itemEl.getAttribute("data-target-id");
                const targetArcheId = itemEl.getAttribute("data-target-arche-id") || targetId;
                const targetTitle = itemEl.getAttribute("data-target-title");

                searchDropdown.style.display = "none";
                searchInput.value = targetTitle;
                currentFocusIndex = -1;

                if (targetType === "resource") {{
                    focusResourceInGraph(targetId);
                }} else {{
                    focusCollectionNodeInGraph(targetArcheId || targetId);
                }}
            }}

            function updateVisualSelection() {{
                const allItems = searchDropdown.querySelectorAll(".search-item");
                allItems.forEach((el, idx) => {{
                    if (idx === currentFocusIndex) {{
                        el.classList.add("selected");
                        el.scrollIntoView({{ block: "nearest", behavior: "smooth" }});
                    }} else {{
                        el.classList.remove("selected");
                    }}
                }});
            }}

            searchInput.addEventListener("keydown", function(e) {{
                const allItems = searchDropdown.querySelectorAll(".search-item");
                if (searchDropdown.style.display !== "block" || allItems.length === 0) return;

                if (e.key === "ArrowDown") {{
                    e.preventDefault();
                    currentFocusIndex = (currentFocusIndex + 1) % allItems.length;
                    updateVisualSelection();
                }} else if (e.key === "ArrowUp") {{
                    e.preventDefault();
                    currentFocusIndex = (currentFocusIndex - 1 + allItems.length) % allItems.length;
                    updateVisualSelection();
                }} else if (e.key === "Enter") {{
                    e.preventDefault();
                    if (currentFocusIndex >= 0 && currentFocusIndex < allItems.length) {{
                        selectItem(allItems[currentFocusIndex]);
                    }} else if (allItems.length > 0) {{
                        selectItem(allItems[0]);
                    }}
                }} else if (e.key === "Escape") {{
                    searchDropdown.style.display = "none";
                    currentFocusIndex = -1;
                    this.blur();
                }}
            }});

            searchInput.addEventListener("input", function() {{
                clearTimeout(debounceTimer);
                const query = this.value.trim().toLowerCase();
                if (!query) {{
                    searchDropdown.style.display = "none";
                    currentFocusIndex = -1;
                    return;
                }}

                debounceTimer = setTimeout(() => {{
                    searchDropdown.innerHTML = "";
                    currentFocusIndex = -1;
                    const tokens = query.split(/\s+/).filter(Boolean);

                    // 1. Filter Structured ARCHE Index (706 entities)
                    let matchedEntities = [];
                    if (searchIndex && searchIndex.length > 0) {{
                        matchedEntities = searchIndex.filter(item => {{
                            const textToSearch = [
                                item.label,
                                item.sublabel,
                                item.arche_id,
                                ...(item.tokens || [])
                            ].join(" ").toLowerCase();
                            return tokens.every(tok => textToSearch.includes(tok));
                        }});
                    }}

                    // Group by categories
                    const categoryGroups = {{
                        "Forscher:innen": [],
                        "Sammlungen & Ordner": [],
                        "Publikationen": [],
                        "Institutionen": [],
                        "Fundorte": []
                    }};

                    const seenIds = new Set();

                    matchedEntities.forEach(ent => {{
                        const cat = ent.category || "Sammlungen & Ordner";
                        if (!categoryGroups[cat]) categoryGroups[cat] = [];
                        if (!seenIds.has(ent.arche_id || ent.id)) {{
                            seenIds.add(ent.arche_id || ent.id);
                            categoryGroups[cat].push(ent);
                        }}
                    }});

                    // 2. Search ARCHE Resources (Corpus)
                    let corpusMatches = [];
                    if (corpusResources && corpusResources.length > 0 && query.length >= 2) {{
                        corpusMatches = corpusResources.filter(r => {{
                            const searchStr = `${{r.title}} ${{r.pid}} ${{r.place}} ${{r.folder}} ${{(r.path || []).join(" ")}} ${{(r.subjs || []).join(" ")}}`.toLowerCase();
                            return tokens.every(tok => searchStr.includes(tok));
                        }}).slice(0, 15);
                    }}

                    let totalMatches = Object.values(categoryGroups).reduce((sum, g) => sum + g.length, 0) + corpusMatches.length;

                    if (totalMatches === 0) {{
                        searchDropdown.innerHTML = '<div class="search-no-results"><i class="fa-solid fa-magnifying-glass" style="margin-bottom: 6px; font-size: 1.2rem; display: block; opacity: 0.5;"></i>Keine passenden ARCHE-Einträge gefunden</div>';
                        searchDropdown.style.display = "block";
                        return;
                    }}

                    let globalIndex = 0;

                    const catIcons = {{
                        "Forscher:innen": "fa-user-tie",
                        "Sammlungen & Ordner": "fa-folder-tree",
                        "Publikationen": "fa-book-open",
                        "Institutionen": "fa-building-columns",
                        "Fundorte": "fa-map-pin"
                    }};

                    Object.keys(categoryGroups).forEach(catName => {{
                        const items = categoryGroups[catName];
                        if (!items || items.length === 0) return;

                        const header = document.createElement("div");
                        header.className = "search-category-header";
                        header.innerHTML = `<span><i class="fa-solid ${{catIcons[catName] || "fa-layer-group"}}"></i> ${{catName}}</span> <span>${{items.length}}</span>`;
                        searchDropdown.appendChild(header);

                        items.slice(0, 8).forEach(item => {{
                            const itemEl = document.createElement("div");
                            itemEl.className = "search-item";
                            itemEl.setAttribute("data-index", globalIndex++);
                            itemEl.setAttribute("data-target-type", item.type);
                            itemEl.setAttribute("data-target-id", item.id);
                            itemEl.setAttribute("data-target-arche-id", item.arche_id || item.id);
                            itemEl.setAttribute("data-target-title", item.label);

                            const highlightedTitle = highlightMatch(item.label, tokens);
                            const highlightedSub = highlightMatch(item.sublabel || (item.arche_id ? "ARCHE ID: " + item.arche_id : ""), tokens);

                            itemEl.innerHTML = `
                                <div class="search-item-icon" style="background: ${{item.color || "#888"}};">
                                    <i class="fa-solid ${{item.icon || "fa-cube"}}"></i>
                                </div>
                                <div class="search-item-body">
                                    <div class="search-item-title">${{highlightedTitle}}</div>
                                    <div class="search-item-sub">${{highlightedSub}}</div>
                                </div>
                                <span class="search-item-badge">${{item.arche_id ? "#" + item.arche_id : item.type}}</span>
                            `;

                            itemEl.addEventListener("click", () => selectItem(itemEl));
                            searchDropdown.appendChild(itemEl);
                        }});
                    }});

                    if (corpusMatches.length > 0) {{
                        const header = document.createElement("div");
                        header.className = "search-category-header";
                        header.innerHTML = `<span><i class="fa-solid fa-file-lines"></i> Dateien &amp; Primärressourcen</span> <span>${{corpusMatches.length}}</span>`;
                        searchDropdown.appendChild(header);

                        corpusMatches.forEach(res => {{
                            const itemEl = document.createElement("div");
                            itemEl.className = "search-item";
                            itemEl.setAttribute("data-index", globalIndex++);
                            itemEl.setAttribute("data-target-type", "resource");
                            itemEl.setAttribute("data-target-id", res.id);
                            itemEl.setAttribute("data-target-arche-id", res.id);
                            itemEl.setAttribute("data-target-title", res.title);

                            const highlightedTitle = highlightMatch(res.title, tokens);
                            const highlightedSub = highlightMatch(`${{res.folder}} • ${{res.place}}`, tokens);

                            itemEl.innerHTML = `
                                <div class="search-item-icon" style="background: ${{ftypeColors[res.type] || "#3D7068"}};">
                                    <i class="fa-solid ${{ftypeIcons[res.type] || "fa-file"}}"></i>
                                </div>
                                <div class="search-item-body">
                                    <div class="search-item-title">${{highlightedTitle}}</div>
                                    <div class="search-item-sub">${{highlightedSub}}</div>
                                </div>
                                <span class="search-item-badge">Ressource</span>
                            `;

                            itemEl.addEventListener("click", () => selectItem(itemEl));
                            searchDropdown.appendChild(itemEl);
                        }});
                    }}

                    searchDropdown.style.display = "block";
                }}, 120);
            }});

            document.addEventListener("click", (e) => {{
                if (!document.querySelector(".search-box-wrapper").contains(e.target)) {{
                    searchDropdown.style.display = "none";
                    currentFocusIndex = -1;
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
                    if (makeActive) {{
                        cy.nodes().show();
                        if (edgesVisible) cy.edges().show();
                        else cy.edges().hide();
                    }} else {{
                        cy.nodes().hide();
                        cy.edges().hide();
                    }}
                    updateVisibleNodesCount();
                    return;
                }}

                this.classList.toggle("active");
                const isNowActive = this.classList.contains("active");

                const selector = type === "folder" ? "[type ^= 'folder']" : `[type = "${{type}}"]`;
                const matchingNodes = cy.nodes(selector);
                if (isNowActive) {{
                    matchingNodes.show();
                    if (edgesVisible) {{
                        matchingNodes.connectedEdges().forEach(edge => {{
                            if (edge.source().visible() && edge.target().visible()) edge.show();
                        }});
                    }}
                }} else {{
                    matchingNodes.hide();
                    matchingNodes.connectedEdges().hide();
                }}

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

        // 2. Fetch Complete ARCHE Resource Corpus (20,355 items)
        fetch("../data/arche_corpus.json")
            .then(res => {{
                if (!res.ok) throw new Error("Could not fetch arche_corpus.json");
                return res.json();
            }})
            .then(data => {{
                corpusData = data;
                corpusResources = data.resources || [];
                populateCorpusFilters();
                const countEl = document.getElementById("corpusStatusCount");
                if (countEl) countEl.textContent = corpusResources.length.toLocaleString();

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
                const pill = document.getElementById("pillCorpusStatus");
                if (pill) {{
                    pill.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Korpus lokal';
                    pill.style.background = "#FFF3CD";
                    pill.style.color = "#856404";
                }}
            }});

        // Immediate URL Parameter handling for Tree Modal, Bookmarks & Collection focus
        (function handleImmediateUrlParams() {{
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get("open") === "tree") {{
                openTreeModal();
            }}
            if (urlParams.get("open") === "bookmarks") {{
                openBookmarksModal();
            }}
            const bmParam = urlParams.get("bookmarks");
            if (bmParam) {{
                setTimeout(() => {{
                    const ids = bmParam.split(",").filter(Boolean);
                    ids.forEach(id => {{
                        const n = getNodeByIdFlexible(id);
                        if (n && n.length > 0) addBookmark(n.data());
                    }});
                    openBookmarksModal();
                }}, 300);
            }}
            const colParam = urlParams.get("col");
            if (colParam) {{
                setTimeout(() => {{
                    focusCollectionNodeInGraph(colParam);
                    if (urlParams.get("expand") === "1" || urlParams.get("autoexpand") === "1") {{
                        setTimeout(() => {{
                            const n = getNodeByIdFlexible(colParam);
                            if (n && n.length > 0) expandResourcesForNode(n.id());
                        }}, 400);
                    }}
                }}, 150);
            }}
            const searchParam = urlParams.get("search") || urlParams.get("s");
            if (searchParam) {{
                setTimeout(() => {{
                    const sInput = document.getElementById("searchInput");
                    if (sInput) {{
                        sInput.value = searchParam;
                        sInput.dispatchEvent(new Event("input", {{ bubbles: true }}));
                        sInput.focus();
                    }}
                }}, 300);
            }}
            if (urlParams.get("edges") === "0" || urlParams.get("hide_edges") === "1") {{
                setTimeout(() => {{
                    const btn = document.getElementById("btnToggleEdges");
                    if (btn && edgesVisible) btn.click();
                }}, 100);
            }}
            const lodParam = urlParams.get("lod") || urlParams.get("level");
            if (lodParam) {{
                setTimeout(() => {{
                    const val = Math.min(6, Math.max(1, parseInt(lodParam, 10)));
                    const slider = document.getElementById("lodSlider");
                    if (slider && !isNaN(val)) {{
                        slider.value = val;
                        slider.dispatchEvent(new Event("input"));
                    }}
                }}, 120);
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
