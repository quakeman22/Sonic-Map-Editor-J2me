"""
Sonic J2ME Map & Object Editor
Requer: pip install Pillow
Uso: python sonic_editor.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, struct, json, copy
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw

# ============================================================
# I18N — Textos em PT e EN
# ============================================================
LANG = {
    'pt': {
        'title':           'Sonic J2ME Editor',
        'tab_map':         'Editor de Mapa',
        'tab_obj':         'Editor de Objetos',
        'open_folder':     'Abrir Pasta do Jogo',
        'export_bmd':      'Exportar .bmd',
        'export_act':      'Exportar .act',
        'export_all':      'Exportar Tudo',
        'undo':            'Desfazer',
        'redo':            'Refazer',
        'zone':            'Zona',
        'act':             'Act',
        'zoom':            'Zoom',
        'fit':             'Ajustar',
        'grid_tiles':      'Grade tiles',
        'grid_blocks':     'Grade blocos',
        'show_sprites':    'Sprites',
        'show_hitbox':     'Hitbox',
        'tileset':         'Tileset',
        'block_editor':    'Editor de Bloco',
        'obj_palette':     'Paleta de Objetos',
        'properties':      'Propriedades',
        'obj_list':        'Lista de Objetos',
        'tool_paint':      'Pintar',
        'tool_erase':      'Apagar',
        'tool_pick':       'Pegar',
        'tool_fill':       'Preencher',
        'tool_move':       'Mover',
        'tool_place':      'Colocar',
        'tool_select':     'Selecionar',
        'tool_delete':     'Deletar',
        'no_folder':       'Nenhuma pasta carregada.',
        'select_folder':   'Selecione a pasta res/ do jogo.',
        'loading':         'Carregando...',
        'loaded':          'Carregado: {n} arquivos',
        'status_cursor':   'Cursor: {x},{y}px  Bloco: {bx},{by}',
        'status_objects':  'Objetos: {n}',
        'status_zoom':     'Zoom: {z}x',
        'prop_x':         'X (pixel)',
        'prop_y':         'Y (pixel)',
        'prop_type':      'Tipo',
        'prop_param':     'Param',
        'prop_count':     'Count',
        'delete_obj':     'Deletar Objeto',
        'no_selection':   'Nenhum objeto selecionado.',
        'click_block':    'Clique num bloco no mapa.',
        'language':       'Idioma',
        'backup':         'Backup automático',
        'missing_files':  'Arquivos não encontrados:\n{files}',
        'export_ok':      'Exportado com sucesso:\n{path}',
        'zone_names': [
            'Zone 1 – Green Hill',
            'Zone 2 – Aqua Lake',
            'Zone 3 – Turquoise Hill',
            'Zone 4 – Gigalopolis',
            'Zone 5 – Scrambled Egg',
            'Zone 6 – Crystal Egg',
        ],
        'obj_categories': {
            'rings':      'Anéis',
            'enemies':    'Inimigos',
            'platforms':  'Plataformas',
            'hazards':    'Armadilhas',
            'items':      'Itens',
            'misc':       'Outros',
        },
        'filter_all': 'Todos',
    },
    'en': {
        'title':           'Sonic J2ME Editor',
        'tab_map':         'Map Editor',
        'tab_obj':         'Object Editor',
        'open_folder':     'Open Game Folder',
        'export_bmd':      'Export .bmd',
        'export_act':      'Export .act',
        'export_all':      'Export All',
        'undo':            'Undo',
        'redo':            'Redo',
        'zone':            'Zone',
        'act':             'Act',
        'zoom':            'Zoom',
        'fit':             'Fit',
        'grid_tiles':      'Tile grid',
        'grid_blocks':     'Block grid',
        'show_sprites':    'Sprites',
        'show_hitbox':     'Hitbox',
        'tileset':         'Tileset',
        'block_editor':    'Block Editor',
        'obj_palette':     'Object Palette',
        'properties':      'Properties',
        'obj_list':        'Object List',
        'tool_paint':      'Paint',
        'tool_erase':      'Erase',
        'tool_pick':       'Pick',
        'tool_fill':       'Fill',
        'tool_move':       'Move',
        'tool_place':      'Place',
        'tool_select':     'Select',
        'tool_delete':     'Delete',
        'no_folder':       'No folder loaded.',
        'select_folder':   'Select the game res/ folder.',
        'loading':         'Loading...',
        'loaded':          'Loaded: {n} files',
        'status_cursor':   'Cursor: {x},{y}px  Block: {bx},{by}',
        'status_objects':  'Objects: {n}',
        'status_zoom':     'Zoom: {z}x',
        'prop_x':         'X (pixel)',
        'prop_y':         'Y (pixel)',
        'prop_type':      'Type',
        'prop_param':     'Param',
        'prop_count':     'Count',
        'delete_obj':     'Delete Object',
        'no_selection':   'No object selected.',
        'click_block':    'Click a block on the map.',
        'language':       'Language',
        'backup':         'Auto backup',
        'missing_files':  'Files not found:\n{files}',
        'export_ok':      'Exported successfully:\n{path}',
        'zone_names': [
            'Zone 1 – Green Hill',
            'Zone 2 – Aqua Lake',
            'Zone 3 – Turquoise Hill',
            'Zone 4 – Gigalopolis',
            'Zone 5 – Scrambled Egg',
            'Zone 6 – Crystal Egg',
        ],
        'obj_categories': {
            'rings':      'Rings',
            'enemies':    'Enemies',
            'platforms':  'Platforms',
            'hazards':    'Hazards',
            'items':      'Items',
            'misc':       'Misc',
        },
        'filter_all': 'All',
    },
}

# ============================================================
# WORLD MAP DATA (extraído do MainCanvas.java)
# ============================================================
WORLD_MAP_DATA = [
    # Zone 0 - Green Hill
    [
        [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,56,1,1,1,36,0,0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,56,36,0,0,33,38,17,17,31,15,0,0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,0,45,49,36,20,56,4,35,37,45,53,38,17,31,30,32,15,0,0,0,0,0,0,0,0,0,0,0],
         [45,45,3,49,36,16,2,7,4,5,43,14,30,17,37,26,38,17,8,9,10,23,30,30,32,17,31,15,0,16,5,43,22,2,3,55,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,30,30,32,37,7,34,12,13,21,25,17,37,45,45,45]],
        [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [14,43,22,28,5,43,22,2,55,0,0,0,0,0,0,0,0,0,0,0,0,33,3,0,0,0,0,33,49,36,0,0,0],
         [12,13,6,12,30,13,21,17,37,50,43,11,45,53,45,7,36,18,56,36,45,38,8,5,43,11,33,38,31,15,0,0,0],
         [30,30,30,30,10,23,30,30,12,12,13,25,17,8,23,30,30,30,30,30,30,30,30,24,13,8,35,17,32,37,45,45,45],
         [30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,30,0,0,0,0,0,30,30,10,23,30,17,8,29,9,30,30,0],
         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,30,30,30,30,30,30,30,30,30,0]],
        [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,45,55,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,0,19,56,24,15,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [0,0,0,19,56,36,20,0,19,56,39,2,26,38,31,15,0,0,20,33,45,0,0,0,19,51,51,16,36,44,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [45,55,22,27,35,37,26,3,6,38,31,30,30,30,32,37,53,49,27,35,17,51,51,2,26,52,52,25,37,6,49,39,0,22,2,7,2,55,45,45,45,60,60,45,45],
         [30,15,21,30,30,30,30,30,30,30,32,31,30,30,30,30,30,30,12,17,9,52,52,17,30,30,30,30,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,30,30,32,17,8,9,10,29,9,30,30,30,30,30,30,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],
    ],
    # Zone 1 - Aqua Lake
    [
        [[25,42,39,41,26,23,14,33,23,0,0,0,39,29,36,13,14,14,14,14,14,14,33,23,23,23,23,0,0,0,0,0],
         [14,14,14,14,14,37,12,34,14,20,0,0,14,14,14,2,10,9,10,9,21,12,34,31,1,14,14,14,0,0,0,0],
         [0,0,0,0,14,14,14,14,14,12,45,14,14,14,14,11,58,14,60,25,29,29,29,30,14,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,14,14,24,9,45,14,17,15,59,14,61,17,27,14,14,14,14,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,14,14,14,46,12,15,17,15,14,62,15,16,14,0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,14,14,14,14,25,26,12,11,11,15,14,0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,14,14,14,14,14,14,14,14,0,0,0,0,0,0,0,0,0,0],
         [14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14]],
        [[23,11,23,13,14,14,14,14,14,14,14,14,0,0,0,0,0,0,0],
         [1,1,1,2,3,11,14,17,0,11,23,14,0,0,0,0,0,0,0],
         [14,14,14,11,76,5,20,46,45,14,19,14,14,0,0,0,0,0,0],
         [33,23,12,46,14,14,14,45,46,14,15,14,14,63,28,0,0,0,0],
         [47,21,12,23,34,9,10,46,15,14,19,14,14,64,14,1,14,14,14],
         [14,14,14,14,14,14,14,14,17,11,15,11,12,65,14,0,0,0,0],
         [0,0,0,0,0,0,0,14,21,12,11,15,14,14,14,0,0,0,0],
         [0,0,0,0,0,0,0,14,14,14,14,14,14,0,0,0,0,0,0]],
        [[0,0,0,0,0,14,14,33,77,14,14,14,14,14,0,0,0,14,14,14,14,14,14,14,14,14,14,16,14,14,0,0,0,0,0],
         [14,14,14,14,14,14,32,75,14,17,11,11,11,14,14,14,0,14,17,33,0,13,14,14,14,14,23,15,14,14,49,1,14,14,14],
         [11,11,13,14,12,17,75,14,17,0,46,39,66,68,39,14,0,14,70,71,14,2,3,18,14,14,16,14,14,14,49,14,0,0,0],
         [14,14,2,3,18,8,20,35,36,11,23,40,67,69,34,14,14,14,20,45,23,12,23,4,18,33,15,14,0,14,49,14,0,0,0],
         [0,14,14,14,4,74,12,37,14,17,22,14,36,12,34,9,10,36,12,45,45,11,22,14,72,0,14,14,14,14,49,14,0,0,0],
         [0,0,0,14,14,4,18,36,23,15,14,14,14,14,14,14,14,14,14,43,43,44,14,14,16,14,14,14,23,23,15,14,0,0,0],
         [0,0,0,0,14,14,4,18,43,34,38,10,9,10,9,41,29,41,42,29,41,42,0,11,37,14,35,14,16,14,14,14,0,0,0],
         [0,0,0,0,0,14,14,4,18,14,14,14,14,14,14,14,14,14,14,14,14,14,46,15,14,14,15,33,15,14,14,14,0,0,0]],
    ],
    # Zone 2 - Turquoise Hill
    [
        [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,6,11,8,9,0,0,0,0,0,0,0,32,0,0,0,0,0,0,0,0,0],
         [1,52,2,2,3,5,18,18,10,8,11,7,7,7,9,12,32,12,11,8,3,8,11,16,16,16],
         [0,0,0,0,0,0,0,0,0,51,15,15,14,14,73,13,24,22,32,32,18,18,18,18,18,0],
         [0,0,0,0,0,0,0,0,0,51,39,40,32,32,31,49,25,32,18,18,18,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,32,17,33,20,20,20,69,22,32,0,0,0,0,0,0,0,0]],
        [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,32,32,0,0,0,0,6,8,53,16,9,0,0,32,32,32,32,32,32,0,0,0],
         [52,8,53,7,9,32,32,16,9,11,2,5,18,18,32,10,8,9,32,32,32,32,32,12,53,53,53],
         [18,51,32,43,73,17,21,18,46,30,29,42,42,42,42,32,18,46,40,32,32,42,25,22,32,32,0],
         [0,18,26,44,20,23,22,42,42,31,49,48,47,47,45,32,68,30,22,32,25,22,32,32,32,0,0],
         [0,18,41,27,27,27,30,17,38,36,36,36,23,17,22,32,44,20,20,23,22,32,32,0,0,0,0]],
        [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [1,8,53,16,53,9,0,0,32,32,32,32,32,32,32,32,32,32,32,0,0,0,0,0,0,0,0,0],
         [32,32,32,32,70,73,8,12,32,32,32,32,32,32,32,32,32,32,32,12,11,3,71,11,72,74,53,53],
         [26,33,25,17,22,32,26,22,32,32,32,32,32,32,26,69,25,25,0,22,32,32,18,32,0,0,0,0],
         [21,14,15,30,36,36,22,18,32,32,32,32,32,32,39,42,0,0,0,0,42,32,32,32,0,0,0,0],
         [28,34,69,22,32,37,29,14,30,37,49,31,49,49,49,22,47,47,47,22,39,42,32,0,0,0,0,0],
         [32,35,30,20,20,36,13,32,26,22,32,32,32,42,42,14,14,40,43,40,29,25,32,0,0,0,0,0],
         [32,32,32,32,32,32,32,32,39,30,38,20,20,23,22,32,32,33,44,44,17,22,32,0,0,0,0,0]],
    ],
    # Zone 3 - Gigalopolis
    [
        [[0,0,0,0,0,0,0,0,0,0,0,0,0,1,8,10,0,0,0,0,1,24,5,1,8,0,0,0,0,51,0,0,0,0],
         [0,0,0,1,10,51,51,51,51,0,0,0,15,51,6,7,24,0,0,0,0,0,0,0,6,7,42,15,24,51,0,0,0,0],
         [1,1,38,51,12,5,8,63,47,5,24,3,12,4,1,51,51,1,1,14,24,4,18,5,8,51,47,3,12,18,4,18,18,18],
         [51,51,29,51,0,0,6,7,46,51,51,4,3,1,1,51,51,51,35,20,51,35,20,32,6,7,46,51,32,24,0,0,0,0],
         [0,51,51,51,0,0,51,51,11,51,51,0,51,51,0,1,40,3,12,19,1,24,19,31,3,12,18,24,31,18,0,0,0,0],
         [0,0,0,0,0,0,0,51,41,8,51,0,3,12,3,12,5,40,5,0,51,0,4,0,0,0,51,51,0,4,0,0,0,0],
         [0,0,0,0,0,0,0,51,51,6,7,1,42,40,0,3,0,12,5,24,3,0,0,0,4,3,4,5,24,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,51,0,0,0,0,0,0,0,0,0,0,0,0,0]],
        [[0,0,20,1,8,0,0,0,0,0,0,0,0,0,1,40,5,40,5,40,5,40,4,51,51,0,51,0,1,51,0,0,0,0],
         [21,21,19,51,6,7,52,0,0,0,20,1,38,3,51,20,21,5,42,42,1,24,5,15,51,0,3,0,51,51,0,0,0,0],
         [0,0,0,51,51,51,41,42,40,36,37,8,21,3,12,19,0,1,40,3,0,1,4,3,12,0,51,0,5,32,1,1,1,1],
         [0,0,0,0,0,51,51,51,0,0,0,6,7,52,51,0,0,51,0,51,0,51,0,51,0,0,15,0,15,39,24,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,51,51,11,0,18,40,21,5,52,51,51,20,51,0,4,29,15,29,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,51,51,41,24,51,51,51,51,41,8,24,19,0,4,0,15,29,29,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,0,51,51,51,51,0,0,0,51,6,7,42,24,21,0,29,29,29,0,0,0,0,0]],
        [[0,0,0,0,0,1,24,5,9,5,1,24,5,20,52,51,51,0,0,14,8,0,51,29,14,24,5,8,0,51,0,0,0,0,0],
         [21,21,25,23,0,18,0,0,6,7,52,51,47,19,41,52,51,35,18,10,6,7,52,29,14,10,51,6,7,52,0,0,0,0,0],
         [0,0,51,26,22,0,4,14,32,51,41,1,46,51,51,41,42,40,21,10,51,51,41,24,10,4,5,10,51,41,20,1,1,1,1],
         [0,0,51,2,27,0,0,0,31,5,20,51,41,40,13,22,0,0,3,12,5,14,24,5,20,38,3,12,35,18,19,51,0,0,0],
         [0,0,0,51,28,0,20,14,24,18,19,0,0,0,2,27,0,0,51,0,14,0,3,12,19,3,12,18,24,3,12,51,0,0,0],
         [0,0,0,51,30,21,19,10,51,51,14,0,0,15,63,28,20,33,51,1,10,21,51,1,0,0,0,1,20,51,0,0,0,0,0],
         [0,0,0,51,0,0,4,3,12,3,10,0,0,29,10,30,19,10,0,20,14,0,5,24,3,12,4,4,19,51,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,51,10,0,0,29,21,4,3,12,4,19,10,0,0,51,51,0,0,0,0,0,0,0,0,0,0]],
    ],
    # Zone 4 - Scrambled Egg
    [
        [[36,47,36,66,12,36,56,71,1,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,2,36,2,71,1,36,0],
         [36,36,36,66,10,73,1,71,1,1,43,36,36,4,14,19,30,55,25,28,6,36,2,4,36,36,28,73,36,36,1,36,1,71,1,36,0],
         [36,36,36,8,9,45,1,14,15,17,1,36,36,1,1,20,22,23,23,29,1,36,1,1,71,74,29,43,43,2,1,2,11,2,2,2,2],
         [6,2,7,1,1,1,1,1,16,18,5,33,2,15,17,1,1,1,1,1,1,2,34,37,70,57,67,1,1,1,1,1,1,1,1,1,0],
         [1,1,1,1,1,1,1,1,1,1,1,1,1,16,18,21,27,21,24,21,27,21,35,38,1,1,1,1,1,1,1,1,1,1,1,1,0]],
        [[36,36,38,36,36,40,47,47,36,36,56,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [2,2,44,36,36,36,36,36,36,36,1,71,1,36,49,3,50,48,36,36,36,36,36,2,6,36,36,1,36,36,36,36,36,0,0,0,0,0,0,0,0,0,0],
         [1,1,1,36,36,36,28,73,36,56,1,71,1,56,40,1,52,51,50,48,36,36,28,15,17,4,13,4,36,36,25,36,36,36,36,38,36,36,1,36,0,0,0],
         [1,1,1,36,2,26,29,43,43,1,1,71,1,1,1,1,1,1,52,31,36,4,29,16,18,21,41,5,33,26,23,14,6,73,32,44,36,36,1,36,36,36,0],
         [1,1,1,36,46,17,1,1,1,1,1,71,1,1,1,1,1,1,1,1,56,1,1,1,1,1,1,1,1,1,1,1,40,45,1,1,36,36,58,32,33,2,2],
         [1,1,1,45,16,18,21,27,21,24,5,70,57,67,57,68,68,68,68,68,69,1,1,0,0,0,0,0,0,0,0,0,0,1,1,1,53,2,54,32,33,2,2]],
        [[56,36,36,36,36,36,36,0,0,0,0,1,36,36,25,36,2,36,36,36,36,6,6,44,36,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [1,49,3,50,48,36,36,36,36,36,36,1,36,36,23,4,1,36,36,36,4,71,68,1,36,1,1,1,1,36,36,36,36,36,36,71,1,0,0,0,0,0,0,0,0,0,0,0,0],
         [0,1,1,52,51,50,48,36,36,2,6,1,36,6,42,21,5,33,73,36,54,71,1,1,36,1,1,1,1,36,36,56,36,36,36,71,1,1,36,36,47,47,40,0,0,0,0,0,0],
         [0,0,0,1,1,52,31,36,2,15,17,1,4,71,1,1,1,1,43,43,1,70,40,1,36,40,1,1,1,36,36,1,43,43,43,71,1,12,36,36,36,36,11,36,36,0,0,0,0],
         [0,0,0,0,0,1,1,36,1,16,18,27,5,71,1,1,1,1,1,1,1,1,1,1,36,46,17,1,1,4,13,1,1,1,1,71,1,10,36,56,36,36,36,36,36,36,36,36,0],
         [0,0,0,0,0,0,1,4,1,1,1,1,1,4,57,67,11,1,1,1,1,1,1,1,36,16,18,24,39,39,41,24,21,27,5,72,8,9,36,1,36,36,36,4,36,64,4,4,4],
         [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,45,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,36,36,36,1,36,66,1,1,0]],
    ],
    # Zone 5 - Crystal Egg
    [
        [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,0,0,22,1,14,16,16,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9,0,34,2,34,0,17,16,12,3,16,16,16,0,0,16,16,16,0],
         [0,0,0,0,0,0,0,0,0,22,34,0,0,0,0,46,45,16,0,16,44,16,13,3,16,16,5,16,16,16,30,15,0,0,0,0],
         [0,0,0,0,0,6,0,18,19,17,16,0,0,9,45,29,0,15,0,16,12,7,8,5,16,16,4,75,47,26,42,43,24,20,18,18],
         [1,9,22,22,34,2,1,7,3,16,16,0,0,15,0,0,0,22,22,1,14,16,16,4,75,31,47,33,33,26,42,43,16,16,16,0],
         [16,16,17,17,16,12,3,16,5,16,16,27,24,20,18,45,0,17,17,16,12,7,9,33,33,28,16,0,46,0,32,43,16,16,16,0],
         [16,16,17,17,16,16,5,16,4,75,47,28,16,16,16,17,16,16,30,33,1,21,21,9,34,18,18,45,29,0,0,0,0,0,0,0],
         [0,0,0,0,0,16,4,75,7,21,21,21,9,75,47,75,47,34,25,17,16,16,16,16,16,16,16,0,0,0,0,0,0,0,0,0]],
        [[16,16,16,16,30,30,30,44,11,1,47,33,33,33,33,33,75,50,36,50,9,10,16,30,16,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [11,1,36,47,34,0,0,10,11,75,31,47,34,49,48,48,15,30,16,0,33,26,42,43,16,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [44,16,16,16,16,16,16,13,8,16,28,30,16,9,1,23,24,20,18,19,17,26,42,43,16,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
         [11,1,36,36,47,33,33,10,16,30,15,41,75,36,50,36,47,10,16,16,16,26,42,43,16,16,16,16,16,16,16,16,0,0,0,0,0,0,0,0],
         [16,16,16,15,15,33,33,34,18,19,40,40,16,16,16,13,7,8,11,1,47,26,42,43,15,15,15,15,30,30,30,16,16,0,0,0,0,0,0,0],
         [16,15,0,41,41,17,17,16,11,75,47,75,36,36,9,10,16,16,44,16,11,34,32,43,24,20,37,38,1,9,1,68,69,70,68,68,71,72,73,74],
         [16,0,0,40,22,1,9,10,11,1,9,0,0,1,36,50,36,47,10,16,44,16,16,16,16,16,16,16,16,16,16,16,0,0,0,0,0,0,0,0],
         [18,19,39,40,17,16,16,44,16,16,16,0,0,16,16,15,15,15,16,16,12,14,16,16,16,16,16,16,16,16,16,16,16,0,0,0,0,0,0,0]],
        [],
    ],
]

# ============================================================
# OBJECT TYPE DEFINITIONS
# type -> (name_pt, name_en, png, color, w, h, category)
# ============================================================
OBJ_TYPES = {
    0:  ('Ring H',        'Ring H',        'ring.png',    '#FFD700', 16,  16,  'rings'),
    1:  ('Ring V',        'Ring V',        'ring.png',    '#FFD700', 16,  16,  'rings'),
    2:  ('Mola',          'Spring',        'sjump2.png',  '#FF4444', 32,  32,  'hazards'),
    3:  ('Balanço',       'Swing',         'buranko.png', '#8B4513', 48,  48,  'platforms'),
    4:  ('Ponte',         'Bridge',        'thashi.png',  '#A0522D', 64,  32,  'platforms'),
    5:  ('Ponte 2',       'Bridge 2',      'hashi.png',   '#A0522D', 64,  32,  'platforms'),
    6:  ('Bloco Quebr.',  'Break Block',   'break.png',   '#888888', 32,  32,  'misc'),
    7:  ('Plataforma',    'Platform',      'yuka.png',    '#888888', 64,  16,  'platforms'),
    8:  ('Pendulo',       'Hanging',       'turi.png',    '#888888', 32,  64,  'platforms'),
    9:  ('Espinho',       'Spike',         'toge.png',    '#AAAAAA', 32,  32,  'hazards'),
    10: ('Caixa Item',    'Item Box',      'item.png',    '#4488FF', 32,  32,  'items'),
    11: ('Bloco Cai',     'Falling Block', 'fblock.png',  '#888888', 32,  32,  'platforms'),
    13: ('Pedra Lava',    'Lava Rock',     'yogan2.png',  '#FF6600', 32,  32,  'hazards'),
    14: ('Jato Lava',     'Lava Spout',    'myogan.png',  '#FF4400', 32,  48,  'hazards'),
    15: ('Switch',        'Switch',        'switch.png',  '#FF8800', 24,  40,  'misc'),
    16: ('Plat. Grande',  'Big Platform',  'shima.png',   '#888888', 64,  32,  'platforms'),
    17: ('Plat. XG',      'XL Platform',   'dai2.png',    '#888888', 64,  32,  'platforms'),
    18: ('Parede Quebr.', 'Wall Block',    'brkabe.png',  '#666666', 32,  48,  'misc'),
    19: ('Pedal',         'Pedal',         'pedal.png',   '#FF8800', 48,  32,  'misc'),
    20: ('Bloco Quebr.2', 'Break Block 2', 'break.png',   '#777777', 32,  32,  'misc'),
    21: ('Degrau',        'Step',          'step.png',    '#888888', 32,  32,  'platforms'),
    22: ('Ventilador',    'Fan',           'fun.png',     '#4488FF', 48,  48,  'misc'),
    23: ('Gangorra',      'Seesaw',        'sisoo.png',   '#8B4513', 64,  32,  'platforms'),
    25: ('Pata',          'Pata',          'paka2.png',   '#FF4444', 32,  32,  'enemies'),
    26: ('Jato Fogo',     'Fire Spout',    'fire6.png',   '#FF4400', 32,  48,  'hazards'),
    27: ('Mola Plat.',    'Spring Plat',   'bryuka.png',  '#FF4444', 48,  32,  'platforms'),
    28: ('Girador',       'Spinner',       'mawaru.png',  '#4488FF', 32,  32,  'misc'),
    29: ('Elevador',      'Elevator',      'yukai.png',   '#888888', 48,  48,  'platforms'),
    30: ('Porta',         'Door',          'door.png',    '#8B4513', 32,  48,  'misc'),
    31: ('Plat. Desliz.', 'Slide Plat',    'yukae.png',   '#888888', 64,  16,  'platforms'),
    32: ('Plat. Grande2', 'Big Plat 2',    'dai4.png',    '#888888', 64,  64,  'platforms'),
    33: ('Ele',           'Ele',           'ele.png',     '#FF4444', 32,  24,  'enemies'),
    34: ('Esteira',       'Belt Conv.',    'beltc.png',   '#555555', 64,  32,  'misc'),
    35: ('Noko',          'Noko',          'noko.png',    '#FF4444', 32,  32,  'enemies'),
    36: ('Save Point',    'Save Point',    'save.png',    '#00FF88', 16,  32,  'misc'),
    37: ('Bloco Sombra',  'Shadow Block',  'kageb.png',   '#444444', 32,  32,  'misc'),
    39: ('Kamere',        'Kamere',        'kamere.png',  '#FF4444', 40,  32,  'enemies'),
    40: ('Hachi',         'Hachi',         'hachi.png',   '#FF4444', 32,  24,  'enemies'),
    41: ('Musi',          'Musi',          'musi.png',    '#FF4444', 32,  24,  'enemies'),
    42: ('Caixa Item S',  'Item Box S',    'item.png',    '#4488FF', 32,  32,  'items'),
    43: ('Caixa Item S2', 'Item Box S2',   'item.png',    '#4488FF', 32,  32,  'items'),
    44: ('Meta',          'Goal',          'signal.png',  '#FFD700', 32,  48,  'misc'),
    45: ('Mola Traseira', 'Back Spring',   'sjump.png',   '#FF4444', 32,  32,  'hazards'),
    49: ('Imo',           'Imo',           'imo.png',     '#FF4444', 24,  32,  'enemies'),
    50: ('Brobo',         'Brobo',         'brobo.png',   '#FF4444', 24,  32,  'enemies'),
    51: ('Buta',          'Buta',          'buta.png',    '#FF4444', 24,  32,  'enemies'),
    55: ('Máquina',       'Machine',       'masin.png',   '#888888', 64,  64,  'misc'),
    56: ('Bobin',         'Bobin',         'bobin.png',   '#888888', 32,  40,  'misc'),
    57: ('Kani',          'Kani',          'kani.png',    '#FF4444', 40,  24,  'enemies'),
    58: ('Obstáculo',     'Obstacle',      'jyama.png',   '#666666', 32,  32,  'hazards'),
    60: ('Bola Corrente', 'Ball Chain',    'tekyu.png',   '#888888', 32,  32,  'hazards'),
    61: ('Poste Meta',    'Goal Post',     'signal.png',  '#FFD700', 32,  48,  'misc'),
    63: ('Ring diag↙',   'Ring diag↙',   'ring.png',    '#FFD700', 16,  16,  'rings'),
    64: ('Ring diag↗',   'Ring diag↗',   'ring.png',    '#FFD700', 16,  16,  'rings'),
    65: ('Ring diag 2',   'Ring diag 2',   'ring.png',    '#FFD700', 16,  16,  'rings'),
    66: ('Ring H2',       'Ring H2',       'ring.png',    '#FFD700', 16,  16,  'rings'),
    67: ('Ring H3',       'Ring H3',       'ring.png',    '#FFD700', 16,  16,  'rings'),
    68: ('Ring V2',       'Ring V2',       'ring.png',    '#FFD700', 16,  16,  'rings'),
    69: ('Ring V3',       'Ring V3',       'ring.png',    '#FFD700', 16,  16,  'rings'),
    70: ('Aruma',         'Aruma',         'aruma.png',   '#FF4444', 32,  32,  'enemies'),
    71: ('Yado',          'Yado',          'yado.png',    '#FF4444', 32,  32,  'enemies'),
    72: ('Elevador 80',   'Elevator 80',   'elev.png',    '#888888', 64,  64,  'platforms'),
    73: ('Elevador 2',    'Elevator 2',    'elev.png',    '#888888', 64,  64,  'platforms'),
    74: ('Uni',           'Uni',           'uni.png',     '#FF4444', 24,  24,  'enemies'),
    75: ('Mfire',         'Mfire',         'mfire.png',   '#FF6600', 32,  32,  'hazards'),
    78: ('Morcego',       'Bat',           'bat.png',     '#FF4444', 32,  24,  'enemies'),
    79: ('Obj Cai',       'Fall Obj',      'ochi.png',    '#888888', 32,  24,  'misc'),
    80: ('Lança',         'Spear',         'yari.png',    '#AAAAAA', 32,  64,  'hazards'),
    81: ('Mogura',        'Mogura',        'mogura.png',  '#FF4444', 32,  40,  'enemies'),
    86: ('Peixe',         'Fish',          'fish2.png',   '#FF4444', 32,  24,  'enemies'),
    87: ('Peixe 2',       'Fish 2',        'fish2.png',   '#FF4444', 32,  24,  'enemies'),
    88: ('Kassya',        'Kassya',        'kassya.png',  '#888888', 32,  32,  'misc'),
    91: ('Poste',         'Pole',          'bou.png',     '#888888', 32,  48,  'misc'),
    255:('(fim)',         '(end)',          None,          '#333333', 8,   8,   'misc'),
}

# ============================================================
# COLORS
# ============================================================
C = {
    'bg':       '#2b2b2b',
    'bg2':      '#333333',
    'bg3':      '#3c3c3c',
    'fg':       '#dddddd',
    'fg2':      '#999999',
    'accent':   '#4a9eff',
    'accent2':  '#2d6abf',
    'danger':   '#e05050',
    'success':  '#50c050',
    'border':   '#444444',
    'sel':      '#1a3a5a',
    'hover':    '#3a3a3a',
}

TILE_PX   = 16
BLOCK_PX  = 256  # 16 tiles * 16px

# ============================================================
# APP
# ============================================================
class SonicEditor:
    def __init__(self, root):
        self.root = root
        self.lang = 'pt'
        self.T = LANG[self.lang]

        # Data
        self.res_folder  = None
        self.tilesets    = {}   # zone -> PIL Image
        self.bmd_data    = {}   # zone -> bytearray
        self.act_data    = {}   # zone -> [bytearray x3]
        self.sprites     = {}   # filename -> PIL Image
        self.sprite_tk   = {}   # filename -> ImageTk (cache)

        # State
        self.zone = 0
        self.act  = 0
        self.map_grid    = []   # deep copy of WORLD_MAP_DATA[zone][act]
        self.objects     = []   # list of dicts

        # Map editor state
        self.map_zoom        = 2.0
        self.map_offset      = [0, 0]   # scroll offset in canvas pixels
        self.map_tool        = 'paint'
        self.selected_tile   = 1
        self.selected_block  = 1
        self.editing_block   = None     # block idx open in block editor
        self.map_drag_start  = None
        self.map_undo        = []
        self.map_redo        = []
        self.show_tile_grid  = tk.BooleanVar(value=True)
        self.show_block_grid = tk.BooleanVar(value=False)

        # Object editor state
        self.obj_zoom        = 2.0
        self.obj_offset      = [0, 0]
        self.obj_tool        = 'place'
        self.selected_obj_type = 0
        self.selected_obj_idx  = -1
        self.obj_drag_start  = None
        self.obj_drag_origin = None
        self.obj_undo        = []
        self.obj_redo        = []
        self.show_sprites    = tk.BooleanVar(value=True)
        self.show_hitbox     = tk.BooleanVar(value=False)
        self.obj_filter_cat  = 'all'
        self.sprite_icons    = {}  # type -> ImageTk small icon

        # Collision data
        self.col_data    = None    # bytearray 8192 bytes (blkcol.bct)
        self.show_collision = tk.BooleanVar(value=False)

        # Brush mode: 'block' ou 'tile'
        self.brush_mode  = tk.StringVar(value='block')

        # Map render cache
        self._map_img     = None   # PIL Image of full map
        self._map_tk      = None   # ImageTk
        self._map_dirty   = True
        self._block_tk_cache = {}  # (bi, zoom) -> ImageTk para update incremental

        self._build_ui()
        self._update_title()

    # --------------------------------------------------------
    # UI CONSTRUCTION
    # --------------------------------------------------------
    def _build_ui(self):
        self.root.configure(bg=C['bg'])
        self.root.geometry('1280x800')
        self.root.minsize(900, 600)

        # Top toolbar
        self._build_toolbar()

        # Notebook (tabs)
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook',        background=C['bg'],  borderwidth=0)
        style.configure('TNotebook.Tab',    background=C['bg2'], foreground=C['fg2'],
                         padding=[12,5],    font=('Segoe UI', 9))
        style.map('TNotebook.Tab',
                  background=[('selected', C['bg3'])],
                  foreground=[('selected', C['accent'])])
        style.configure('TFrame',           background=C['bg'])
        style.configure('TPanedwindow',     background=C['bg'])
        style.configure('TSeparator',       background=C['border'])
        style.configure('Vertical.TScrollbar',  background=C['bg3'], troughcolor=C['bg2'], arrowcolor=C['fg2'])
        style.configure('Horizontal.TScrollbar',background=C['bg3'], troughcolor=C['bg2'], arrowcolor=C['fg2'])

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill='both', expand=True, padx=0, pady=0)

        self.tab_map = ttk.Frame(self.nb)
        self.tab_obj = ttk.Frame(self.nb)
        self.nb.add(self.tab_map, text=f'  {self.T["tab_map"]}  ')
        self.nb.add(self.tab_obj, text=f'  {self.T["tab_obj"]}  ')

        self._build_map_tab()
        self._build_obj_tab()

        # Status bar
        self._build_statusbar()

        # Keyboard shortcuts
        self.root.bind('<Control-z>', lambda e: self._undo())
        self.root.bind('<Control-y>', lambda e: self._redo())
        self.root.bind('<Control-Z>', lambda e: self._undo())

    # ── TOOLBAR ─────────────────────────────────────────────
    def _build_toolbar(self):
        tb = tk.Frame(self.root, bg=C['bg2'], height=38)
        tb.pack(fill='x', side='top')
        tb.pack_propagate(False)

        def tbtn(text, cmd, **kw):
            b = tk.Button(tb, text=text, command=cmd,
                          bg=C['bg3'], fg=C['fg'], relief='flat',
                          activebackground=C['accent2'], activeforeground='#fff',
                          font=('Segoe UI', 9), padx=8, pady=3, cursor='hand2', **kw)
            b.pack(side='left', padx=2, pady=4)
            return b

        def tsep():
            tk.Frame(tb, bg=C['border'], width=1).pack(side='left', fill='y', padx=4, pady=6)

        tbtn(self.T['open_folder'], self._open_folder)
        tsep()
        tbtn(self.T['export_bmd'],  self._export_bmd)
        tbtn(self.T['export_act'],  self._export_act)
        tbtn(self.T['export_all'],  self._export_all)
        tsep()
        tbtn(self.T['undo'], self._undo)
        tbtn(self.T['redo'], self._redo)
        tsep()

        # Zone selector
        tk.Label(tb, text=self.T['zone']+':', bg=C['bg2'], fg=C['fg2'],
                 font=('Segoe UI', 9)).pack(side='left', padx=(4,2))
        self.zone_var = tk.StringVar(value='0')
        zc = ttk.Combobox(tb, textvariable=self.zone_var, width=18,
                          values=[f'{i}: {n}' for i,n in enumerate(self.T['zone_names'])],
                          state='readonly', font=('Segoe UI', 9))
        zc.pack(side='left', padx=2, pady=4)
        zc.bind('<<ComboboxSelected>>', self._on_zone_change)

        tk.Label(tb, text=self.T['act']+':', bg=C['bg2'], fg=C['fg2'],
                 font=('Segoe UI', 9)).pack(side='left', padx=(8,2))
        self.act_var = tk.StringVar(value='0')
        ac = ttk.Combobox(tb, textvariable=self.act_var, width=6,
                          values=['0','1','2'],
                          state='readonly', font=('Segoe UI', 9))
        ac.pack(side='left', padx=2, pady=4)
        ac.bind('<<ComboboxSelected>>', self._on_act_change)

        # Style comboboxes
        style = ttk.Style()
        style.configure('TCombobox', fieldbackground=C['bg3'], background=C['bg3'],
                         foreground=C['fg'], arrowcolor=C['fg2'])

        tsep()
        # Language
        tk.Label(tb, text=self.T['language']+':', bg=C['bg2'], fg=C['fg2'],
                 font=('Segoe UI', 9)).pack(side='left', padx=(4,2))
        self.lang_var = tk.StringVar(value='PT')
        for lbl, val in [('PT','pt'),('EN','en')]:
            tk.Radiobutton(tb, text=lbl, variable=self.lang_var, value=val,
                           command=self._change_lang,
                           bg=C['bg2'], fg=C['fg'], selectcolor=C['bg3'],
                           activebackground=C['bg2'], activeforeground=C['accent'],
                           font=('Segoe UI', 9)).pack(side='left', padx=1)

    # ── MAP TAB ─────────────────────────────────────────────
    def _build_map_tab(self):
        tab = self.tab_map
        pw = tk.PanedWindow(tab, orient='horizontal', bg=C['bg'],
                            sashwidth=4, sashrelief='flat', sashpad=0)
        pw.pack(fill='both', expand=True)

        # Left: tileset + tools
        left = tk.Frame(pw, bg=C['bg'], width=180)
        self._build_map_left(left)
        pw.add(left, minsize=150)

        # Center: map canvas
        center = tk.Frame(pw, bg=C['bg'])
        self._build_map_center(center)
        pw.add(center, minsize=400)

        # Right: block editor
        right = tk.Frame(pw, bg=C['bg'], width=200)
        self._build_map_right(right)
        pw.add(right, minsize=180)

    def _build_map_left(self, parent):
        # ── Ferramentas (ícone + nome em coluna)
        tk.Label(parent, text='Ferramentas', bg=C['bg'], fg=C['accent'],
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=(6,2))

        self.map_tool_btns = {}
        tools = [
            ('paint',  '✏',  'Pintar'),
            ('erase',  '🧹', 'Apagar'),
            ('pick',   '💧', 'Pegar'),
            ('fill',   '🪣', 'Preencher'),
            ('move',   '↔',  'Mover bloco'),
        ]
        tf = tk.Frame(parent, bg=C['bg'])
        tf.pack(fill='x', padx=4, pady=0)
        for key, icon, label in tools:
            b = tk.Button(tf, text=f'{icon}  {label}', anchor='w',
                          bg=C['bg3'], fg=C['fg'], relief='flat',
                          font=('Segoe UI', 9), cursor='hand2', padx=6, pady=3,
                          command=lambda k=key: self._set_map_tool(k))
            b.pack(fill='x', pady=1)
            self.map_tool_btns[key] = b

        # ── Modo de pincel
        tk.Label(parent, text='Modo pincel', bg=C['bg'], fg=C['accent'],
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=(8,2))
        bf = tk.Frame(parent, bg=C['bg'])
        bf.pack(fill='x', padx=6)
        for lbl, val in [('Bloco (256px)', 'block'), ('Tile (16px)', 'tile')]:
            tk.Radiobutton(bf, text=lbl, variable=self.brush_mode, value=val,
                           bg=C['bg'], fg=C['fg'], selectcolor=C['bg3'],
                           activebackground=C['bg'], activeforeground=C['accent'],
                           font=('Segoe UI', 8)).pack(anchor='w')

        # ── Checkboxes
        tk.Label(parent, text='Visualização', bg=C['bg'], fg=C['accent'],
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=(8,2))
        cf = tk.Frame(parent, bg=C['bg'])
        cf.pack(fill='x', padx=4, pady=2)
        tk.Checkbutton(cf, text=self.T['grid_tiles'], variable=self.show_tile_grid,
                       command=self._refresh_map_canvas,
                       bg=C['bg'], fg=C['fg2'], selectcolor=C['bg3'],
                       activebackground=C['bg'], font=('Segoe UI', 8)).pack(anchor='w')
        tk.Checkbutton(cf, text=self.T['grid_blocks'], variable=self.show_block_grid,
                       command=self._refresh_map_canvas,
                       bg=C['bg'], fg=C['fg2'], selectcolor=C['bg3'],
                       activebackground=C['bg'], font=('Segoe UI', 8)).pack(anchor='w')
        tk.Checkbutton(cf, text='Colisão', variable=self.show_collision,
                       command=self._refresh_map_canvas,
                       bg=C['bg'], fg=C['fg2'], selectcolor=C['bg3'],
                       activebackground=C['bg'], font=('Segoe UI', 8)).pack(anchor='w')

        # Tileset label
        tk.Label(parent, text=self.T['tileset'], bg=C['bg'], fg=C['accent'],
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=(6,0))

        # Tileset label
        tk.Label(parent, text=self.T['tileset'], bg=C['bg'], fg=C['accent'],
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=(6,0))

        # Tileset canvas with scrollbar
        ts_frame = tk.Frame(parent, bg=C['bg'])
        ts_frame.pack(fill='both', expand=True, padx=4, pady=2)
        ts_sb = tk.Scrollbar(ts_frame, orient='vertical', bg=C['bg3'])
        ts_sb.pack(side='right', fill='y')
        self.tileset_canvas = tk.Canvas(ts_frame, bg='#000', highlightthickness=0,
                                         yscrollcommand=ts_sb.set, cursor='crosshair')
        self.tileset_canvas.pack(side='left', fill='both', expand=True)
        ts_sb.config(command=self.tileset_canvas.yview)
        self.tileset_canvas.bind('<Button-1>', self._on_tileset_click)
        self.tileset_canvas.bind('<MouseWheel>', lambda e: self.tileset_canvas.yview_scroll(-1*(e.delta//120),'units'))
        self.tileset_canvas.bind('<Button-4>', lambda e: self.tileset_canvas.yview_scroll(-1,'units'))
        self.tileset_canvas.bind('<Button-5>', lambda e: self.tileset_canvas.yview_scroll(1,'units'))

    def _build_map_center(self, parent):
        # Zoom bar
        zb = tk.Frame(parent, bg=C['bg2'])
        zb.pack(fill='x', pady=0)
        tk.Label(zb, text=self.T['zoom']+':', bg=C['bg2'], fg=C['fg2'],
                 font=('Segoe UI', 8)).pack(side='left', padx=4)
        for z in [0.5, 1, 2, 4]:
            tk.Button(zb, text=f'{z}×', bg=C['bg3'], fg=C['fg'], relief='flat',
                      font=('Segoe UI', 8), padx=4, pady=1, cursor='hand2',
                      command=lambda v=z: self._set_map_zoom(v)).pack(side='left', padx=1, pady=2)
        tk.Button(zb, text=self.T['fit'], bg=C['bg3'], fg=C['fg'], relief='flat',
                  font=('Segoe UI', 8), padx=4, pady=1, cursor='hand2',
                  command=self._fit_map_zoom).pack(side='left', padx=2, pady=2)
        self.map_zoom_lbl = tk.Label(zb, text='2×', bg=C['bg2'], fg=C['accent'],
                                      font=('Segoe UI', 8))
        self.map_zoom_lbl.pack(side='left', padx=6)

        # Canvas + scrollbars
        cf = tk.Frame(parent, bg=C['bg'])
        cf.pack(fill='both', expand=True)
        h_sb = tk.Scrollbar(cf, orient='horizontal', bg=C['bg3'])
        h_sb.pack(side='bottom', fill='x')
        v_sb = tk.Scrollbar(cf, orient='vertical', bg=C['bg3'])
        v_sb.pack(side='right', fill='y')
        self.map_canvas = tk.Canvas(cf, bg='#111', highlightthickness=0,
                                     xscrollcommand=h_sb.set, yscrollcommand=v_sb.set,
                                     cursor='crosshair')
        self.map_canvas.pack(side='left', fill='both', expand=True)
        h_sb.config(command=self.map_canvas.xview)
        v_sb.config(command=self.map_canvas.yview)

        self.map_canvas.bind('<Button-1>',    self._on_map_click)
        self.map_canvas.bind('<B1-Motion>',   self._on_map_drag)
        self.map_canvas.bind('<ButtonRelease-1>', self._on_map_release)
        self.map_canvas.bind('<Button-3>',    self._on_map_rclick)
        self.map_canvas.bind('<Motion>',      self._on_map_motion)
        self.map_canvas.bind('<MouseWheel>',  self._on_map_wheel)
        self.map_canvas.bind('<Button-4>',    lambda e: self._scroll_map(0, -3))
        self.map_canvas.bind('<Button-5>',    lambda e: self._scroll_map(0,  3))
        self.map_canvas.bind('<Control-MouseWheel>', self._on_map_ctrl_wheel)

    def _build_map_right(self, parent):
        tk.Label(parent, text=self.T['block_editor'], bg=C['bg'], fg=C['accent'],
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=(6,2))
        self.block_info_lbl = tk.Label(parent, text=self.T['click_block'],
                                        bg=C['bg'], fg=C['fg2'], font=('Segoe UI', 8),
                                        wraplength=180, justify='left')
        self.block_info_lbl.pack(anchor='w', padx=6)

        self.block_canvas = tk.Canvas(parent, bg='#000', highlightthickness=1,
                                       highlightbackground=C['border'],
                                       width=256, height=256, cursor='crosshair')
        self.block_canvas.pack(padx=4, pady=4)
        self.block_canvas.bind('<Button-1>',  self._on_block_edit_click)
        self.block_canvas.bind('<Button-3>',  self._on_block_edit_rclick)

    # ── OBJECT TAB ──────────────────────────────────────────
    def _build_obj_tab(self):
        tab = self.tab_obj
        pw = tk.PanedWindow(tab, orient='horizontal', bg=C['bg'],
                            sashwidth=4, sashrelief='flat')
        pw.pack(fill='both', expand=True)

        left  = tk.Frame(pw, bg=C['bg'], width=190)
        self._build_obj_left(left)
        pw.add(left, minsize=160)

        center = tk.Frame(pw, bg=C['bg'])
        self._build_obj_center(center)
        pw.add(center, minsize=400)

        right = tk.Frame(pw, bg=C['bg'], width=210)
        self._build_obj_right(right)
        pw.add(right, minsize=180)

    def _build_obj_left(self, parent):
        tk.Label(parent, text=self.T['obj_palette'], bg=C['bg'], fg=C['accent'],
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=(6,2))

        # Category filter
        ff = tk.Frame(parent, bg=C['bg'])
        ff.pack(fill='x', padx=4, pady=2)
        self.cat_var = tk.StringVar(value='all')
        cats = [('all', self.T['filter_all'])] + list(self.T['obj_categories'].items())
        self.cat_combo = ttk.Combobox(ff, textvariable=self.cat_var, state='readonly',
                                       values=[v for _,v in cats],
                                       font=('Segoe UI', 8), width=16)
        self.cat_combo.pack(fill='x', padx=0)
        self.cat_combo.bind('<<ComboboxSelected>>', self._filter_palette)
        self._cat_keys = [k for k,_ in cats]

        # Palette listbox + scrollbar
        lf = tk.Frame(parent, bg=C['bg'])
        lf.pack(fill='both', expand=True, padx=4, pady=2)
        sb = tk.Scrollbar(lf, bg=C['bg3'])
        sb.pack(side='right', fill='y')
        self.obj_listbox = tk.Listbox(lf, bg=C['bg3'], fg=C['fg'],
                                       selectbackground=C['sel'], selectforeground=C['accent'],
                                       activestyle='none', highlightthickness=0,
                                       font=('Segoe UI', 9), relief='flat',
                                       yscrollcommand=sb.set)
        self.obj_listbox.pack(side='left', fill='both', expand=True)
        sb.config(command=self.obj_listbox.yview)
        self.obj_listbox.bind('<<ListboxSelect>>', self._on_palette_select)
        self.obj_listbox.bind('<MouseWheel>', lambda e: self.obj_listbox.yview_scroll(-1*(e.delta//120),'units'))
        self._palette_types = []  # list of type ints matching listbox rows
        self._populate_palette()

    def _build_obj_center(self, parent):
        # Toolbar
        tb = tk.Frame(parent, bg=C['bg2'])
        tb.pack(fill='x')

        self.obj_tool_btns = {}
        tools = [('place','✚ '+self.T['tool_place']),
                 ('select','↖ '+self.T['tool_select']),
                 ('delete','✕ '+self.T['tool_delete'])]
        for key, lbl in tools:
            b = tk.Button(tb, text=lbl, bg=C['bg3'], fg=C['fg'], relief='flat',
                          font=('Segoe UI', 8), padx=6, pady=2, cursor='hand2',
                          command=lambda k=key: self._set_obj_tool(k))
            b.pack(side='left', padx=2, pady=3)
            self.obj_tool_btns[key] = b

        tk.Frame(tb, bg=C['border'], width=1).pack(side='left', fill='y', padx=4, pady=4)
        tk.Checkbutton(tb, text=self.T['show_sprites'], variable=self.show_sprites,
                       command=self._redraw_objects,
                       bg=C['bg2'], fg=C['fg2'], selectcolor=C['bg3'],
                       activebackground=C['bg2'], font=('Segoe UI', 8)).pack(side='left', padx=2)
        tk.Checkbutton(tb, text=self.T['show_hitbox'], variable=self.show_hitbox,
                       command=self._redraw_objects,
                       bg=C['bg2'], fg=C['fg2'], selectcolor=C['bg3'],
                       activebackground=C['bg2'], font=('Segoe UI', 8)).pack(side='left', padx=2)

        tk.Frame(tb, bg=C['border'], width=1).pack(side='left', fill='y', padx=4, pady=4)
        for z in [1, 2, 4]:
            tk.Button(tb, text=f'{z}×', bg=C['bg3'], fg=C['fg'], relief='flat',
                      font=('Segoe UI', 8), padx=4, pady=1, cursor='hand2',
                      command=lambda v=z: self._set_obj_zoom(v)).pack(side='left', padx=1, pady=2)
        tk.Button(tb, text=self.T['fit'], bg=C['bg3'], fg=C['fg'], relief='flat',
                  font=('Segoe UI', 8), padx=4, pady=1, cursor='hand2',
                  command=self._fit_obj_zoom).pack(side='left', padx=2, pady=2)

        # Canvas
        cf = tk.Frame(parent, bg=C['bg'])
        cf.pack(fill='both', expand=True)
        h_sb = tk.Scrollbar(cf, orient='horizontal', bg=C['bg3'])
        h_sb.pack(side='bottom', fill='x')
        v_sb = tk.Scrollbar(cf, orient='vertical', bg=C['bg3'])
        v_sb.pack(side='right', fill='y')
        self.obj_canvas = tk.Canvas(cf, bg='#111', highlightthickness=0,
                                     xscrollcommand=h_sb.set, yscrollcommand=v_sb.set,
                                     cursor='crosshair')
        self.obj_canvas.pack(side='left', fill='both', expand=True)
        h_sb.config(command=self.obj_canvas.xview)
        v_sb.config(command=self.obj_canvas.yview)

        self.obj_canvas.bind('<Button-1>',    self._on_obj_click)
        self.obj_canvas.bind('<B1-Motion>',   self._on_obj_drag)
        self.obj_canvas.bind('<ButtonRelease-1>', self._on_obj_release)
        self.obj_canvas.bind('<Button-3>',    self._on_obj_rclick)
        self.obj_canvas.bind('<Motion>',      self._on_obj_motion)
        self.obj_canvas.bind('<MouseWheel>',  self._on_obj_wheel)
        self.obj_canvas.bind('<Button-4>',    lambda e: self._scroll_obj(0,-3))
        self.obj_canvas.bind('<Button-5>',    lambda e: self._scroll_obj(0, 3))
        self.obj_canvas.bind('<Control-MouseWheel>', self._on_obj_ctrl_wheel)
        self.obj_canvas.bind('<Delete>',      lambda e: self._delete_selected_obj())
        self.obj_canvas.bind('<BackSpace>',   lambda e: self._delete_selected_obj())

    def _build_obj_right(self, parent):
        tk.Label(parent, text=self.T['properties'], bg=C['bg'], fg=C['accent'],
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=(6,2))

        pf = tk.Frame(parent, bg=C['bg'])
        pf.pack(fill='x', padx=6)

        self.prop_vars = {}
        fields = [('prop_x','x'), ('prop_y','y'), ('prop_type','type'),
                  ('prop_param','param'), ('prop_count','count')]
        for lbl_key, field in fields:
            tk.Label(pf, text=self.T[lbl_key]+':', bg=C['bg'], fg=C['fg2'],
                     font=('Segoe UI', 8)).pack(anchor='w', pady=(3,0))
            var = tk.StringVar()
            e = tk.Entry(pf, textvariable=var, bg=C['bg3'], fg=C['fg'],
                         insertbackground=C['fg'], relief='flat',
                         font=('Consolas', 9), highlightthickness=1,
                         highlightbackground=C['border'],
                         highlightcolor=C['accent'])
            e.pack(fill='x', pady=(0,2))
            var.trace_add('write', lambda *a, f=field, v=var: self._on_prop_change(f, v))
            self.prop_vars[field] = var

        self.delete_obj_btn = tk.Button(pf, text='🗑 '+self.T['delete_obj'],
                                         bg=C['danger'], fg='#fff', relief='flat',
                                         font=('Segoe UI', 8), padx=6, pady=3,
                                         cursor='hand2',
                                         command=self._delete_selected_obj)
        self.delete_obj_btn.pack(fill='x', pady=6)

        tk.Label(parent, text=self.T['obj_list'], bg=C['bg'], fg=C['accent'],
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=6, pady=(4,2))

        lf = tk.Frame(parent, bg=C['bg'])
        lf.pack(fill='both', expand=True, padx=4, pady=(0,4))
        sb = tk.Scrollbar(lf, bg=C['bg3'])
        sb.pack(side='right', fill='y')
        self.obj_list_lb = tk.Listbox(lf, bg=C['bg3'], fg=C['fg'],
                                       selectbackground=C['sel'], selectforeground=C['accent'],
                                       activestyle='none', highlightthickness=0,
                                       font=('Consolas', 8), relief='flat',
                                       yscrollcommand=sb.set)
        self.obj_list_lb.pack(side='left', fill='both', expand=True)
        sb.config(command=self.obj_list_lb.yview)
        self.obj_list_lb.bind('<<ListboxSelect>>', self._on_obj_list_select)

    # ── STATUS BAR ──────────────────────────────────────────
    def _build_statusbar(self):
        sb = tk.Frame(self.root, bg=C['bg2'], height=22)
        sb.pack(fill='x', side='bottom')
        sb.pack_propagate(False)
        self.status_lbl = tk.Label(sb, text=self.T['no_folder'],
                                    bg=C['bg2'], fg=C['fg2'], font=('Segoe UI', 8),
                                    anchor='w')
        self.status_lbl.pack(side='left', padx=8)
        self.status_right = tk.Label(sb, text='', bg=C['bg2'], fg=C['fg2'],
                                      font=('Segoe UI', 8), anchor='e')
        self.status_right.pack(side='right', padx=8)

    # --------------------------------------------------------
    # LOAD FOLDER
    # --------------------------------------------------------
    def _open_folder(self):
        folder = filedialog.askdirectory(title=self.T['open_folder'])
        if not folder:
            return
        self.res_folder = folder
        self._set_status(self.T['loading'])
        self.root.update()
        self._load_all_resources()

    def _load_all_resources(self):
        folder = self.res_folder
        loaded = 0
        missing = []

        # Tilesets
        for z in range(6):
            p = os.path.join(folder, f'zone{z+1}.png')
            if os.path.exists(p):
                self.tilesets[z] = Image.open(p).convert('RGBA')
                loaded += 1
            else:
                missing.append(f'zone{z+1}.png')

        # BMD
        for z in range(6):
            p = os.path.join(folder, f'zone{z+1}.bmd')
            if os.path.exists(p):
                with open(p,'rb') as f:
                    self.bmd_data[z] = bytearray(f.read())
                loaded += 1
            else:
                missing.append(f'zone{z+1}.bmd')

        # ACT
        for z in range(6):
            p = os.path.join(folder, f'ZONE{z+1}ACT.act')
            if not os.path.exists(p):
                p = os.path.join(folder, f'zone{z+1}act.act')
            if os.path.exists(p):
                with open(p,'rb') as f:
                    buf = f.read()
                sizes = [struct.unpack_from('>H', buf, i*2)[0] for i in range(4)]
                pos = 8
                acts = []
                for sz in sizes:
                    acts.append(bytearray(buf[pos:pos+sz]))
                    pos += sz
                self.act_data[z] = acts
                loaded += 1
            else:
                missing.append(f'ZONE{z+1}ACT.act')

        # Collision table (blkcol.bct)
        col_path = os.path.join(folder, 'blkcol.bct')
        if os.path.exists(col_path):
            with open(col_path, 'rb') as f:
                self.col_data = bytearray(f.read())
            loaded += 1

        # Sprites (all PNG files)
        for fname in os.listdir(folder):
            if fname.lower().endswith('.png'):
                key = fname.lower()
                if key not in ('zone1.png','zone2.png','zone3.png',
                               'zone4.png','zone5.png','zone6.png'):
                    try:
                        self.sprites[key] = Image.open(
                            os.path.join(folder, fname)).convert('RGBA')
                        loaded += 1
                    except:
                        pass

        self._set_status(self.T['loaded'].format(n=loaded))
        if missing:
            # Show warning but continue
            print('Missing:', missing)

        self._map_dirty = True
        self._load_zone_act()

    def _load_zone_act(self):
        z = self.zone
        a = self.act
        zd = WORLD_MAP_DATA[z]
        if a < len(zd) and zd[a]:
            self.map_grid = [list(row) for row in zd[a]]
        else:
            self.map_grid = []
        self.objects = self._parse_act(z, a)
        self.map_undo.clear(); self.map_redo.clear()
        self.obj_undo.clear();  self.obj_redo.clear()
        self.selected_obj_idx = -1
        self.editing_block = None
        self._map_dirty = True
        self._rebuild_tileset_canvas()
        self._rebuild_map_canvas()
        self._rebuild_obj_canvas()
        self._refresh_obj_list()
        self._update_props_panel()
        self._update_block_editor()
        self._update_title()

    # --------------------------------------------------------
    # ACT PARSING / SERIALIZATION
    # --------------------------------------------------------
    def _parse_act(self, zone, act):
        acts = self.act_data.get(zone)
        if not acts or act >= len(acts) or len(acts[act]) < 7:
            return []
        buf = acts[act]
        n = len(buf) // 7
        objs = []
        for i in range(n):
            b = i * 7
            x     = ((buf[b]   & 0xFF) << 8) | (buf[b+1] & 0xFF)
            y     = ((buf[b+2] & 0xFF) << 8) | (buf[b+3] & 0xFF)
            param = buf[b+4] & 0xFF
            typ   = buf[b+5] & 0xFF
            count = buf[b+6] & 0xFF
            objs.append({'x':x,'y':y,'param':param,'type':typ,'count':count})
        return objs

    def _serialize_act(self, objs):
        # Sort by X as the game expects
        sorted_objs = sorted(objs, key=lambda o: o['x'])
        buf = bytearray()
        for o in sorted_objs:
            x = o['x'] & 0xFFFF
            y = o['y'] & 0xFFFF
            buf += bytes([(x>>8)&0xFF, x&0xFF,
                           (y>>8)&0xFF, y&0xFF,
                           o['param']&0xFF,
                           o['type'] &0xFF,
                           o['count']&0xFF])
        return buf

    # --------------------------------------------------------
    # RENDER MAP
    # --------------------------------------------------------
    def _get_map_dims(self):
        if not self.map_grid:
            return 0, 0
        h = len(self.map_grid)
        w = max((len(r) for r in self.map_grid), default=0)
        return w, h

    def _render_map_image(self):
        """Render full map as PIL image (cached)."""
        ts  = self.tilesets.get(self.zone)
        bmd = self.bmd_data.get(self.zone)
        w, h = self._get_map_dims()
        if not w or not h:
            return None

        img = Image.new('RGBA', (w * BLOCK_PX, h * BLOCK_PX), (0, 0, 0, 255))

        if ts and bmd:
            tpr = ts.width // TILE_PX
            for row in range(h):
                for col in range(len(self.map_grid[row])):
                    bi = self.map_grid[row][col]
                    if not bi:
                        continue
                    for ty in range(16):
                        for tx in range(16):
                            off = bi * 512 + (tx + ty * 16) * 2
                            if off + 1 >= len(bmd):
                                continue
                            ctrl = bmd[off]
                            tid  = bmd[off + 1]
                            if not tid:
                                continue
                            io = 1 if (ctrl & 1) else (2 if (ctrl & 3) == 2 else 0)
                            at = tid + io * 256
                            sx = (at % tpr) * TILE_PX
                            sy = (at // tpr) * TILE_PX
                            if sy + TILE_PX > ts.height:
                                continue
                            tile = ts.crop((sx, sy, sx + TILE_PX, sy + TILE_PX))
                            rot  = (ctrl >> 3) & 3
                            if rot == 1:
                                tile = tile.transpose(Image.Transpose.ROTATE_90)
                            elif rot == 2:
                                tile = tile.transpose(Image.Transpose.ROTATE_180)
                            elif rot == 3:
                                tile = tile.transpose(Image.Transpose.ROTATE_270)
                            dx = col * BLOCK_PX + tx * TILE_PX
                            dy = row * BLOCK_PX + ty * TILE_PX
                            if tile.mode == 'RGBA':
                                img.paste(tile, (dx, dy), mask=tile.split()[3])
                            else:
                                img.paste(tile.convert('RGB'), (dx, dy))

        # Overlay de colisão
        if self.show_collision.get() and self.col_data:
            for row2 in range(h):
                for col2 in range(len(self.map_grid[row2])):
                    bi2 = self.map_grid[row2][col2]
                    if bi2:
                        self._draw_collision_overlay_block(img, col2, row2, bi2)

        # Grids
        draw = ImageDraw.Draw(img)
        if self.show_tile_grid.get():
            for x in range(0, w * BLOCK_PX + 1, TILE_PX):
                draw.line([(x,0),(x, h*BLOCK_PX)], fill='#1a3050', width=1)
            for y in range(0, h * BLOCK_PX + 1, TILE_PX):
                draw.line([(0,y),(w*BLOCK_PX, y)], fill='#1a3050', width=1)
        if self.show_block_grid.get():
            for x in range(0, w * BLOCK_PX + 1, BLOCK_PX):
                draw.line([(x,0),(x, h*BLOCK_PX)], fill='#503030', width=1)
            for y in range(0, h * BLOCK_PX + 1, BLOCK_PX):
                draw.line([(0,y),(w*BLOCK_PX, y)], fill='#503030', width=1)

        self._map_img = img
        self._map_dirty = False
        return img

    def _rebuild_tileset_canvas(self):
        ts = self.tilesets.get(self.zone)
        c  = self.tileset_canvas
        c.delete('all')
        if not ts:
            return
        scale = 2
        tw = ts.width * scale
        th = ts.height * scale
        # Compor RGBA sobre fundo preto — evita artefato rosa
        ts_rgb = Image.new('RGB', (ts.width, ts.height), (0, 0, 0))
        if ts.mode == 'RGBA':
            ts_rgb.paste(ts, mask=ts.split()[3])
        else:
            ts_rgb.paste(ts.convert('RGB'))
        scaled = ts_rgb.resize((tw, th), Image.NEAREST)
        # Grade
        draw = ImageDraw.Draw(scaled)
        for x in range(0, tw+1, TILE_PX*scale):
            draw.line([(x,0),(x,th)], fill='#3a3a3a')
        for y in range(0, th+1, TILE_PX*scale):
            draw.line([(0,y),(tw,y)], fill='#3a3a3a')
        self._ts_tk = ImageTk.PhotoImage(scaled)
        self._ts_scale = scale
        c.config(width=tw, scrollregion=(0,0,tw,th))
        c.create_image(0, 0, anchor='nw', image=self._ts_tk)
        self._draw_tile_selection()

    def _draw_collision_overlay_block(self, img, bx, by, bi):
        """Pinta overlay de colisão (vermelho semi-transparente) sobre o bloco bi."""
        col = self.col_data
        if not col or bi * 32 + 32 > len(col):
            return
        base = bi * 32
        draw = ImageDraw.Draw(img, 'RGBA')
        for ty in range(16):
            for tx in range(16):
                # Fórmula do blockColChk (rotação 0):
                # blockColTable[base + tx*2 + (ty>>3)] >> (7-(ty&7)) & 1
                byte_idx = base + tx * 2 + (ty >> 3)
                if byte_idx >= len(col):
                    continue
                solid = (col[byte_idx] >> (7 - (ty & 7))) & 1
                if solid:
                    px = bx * BLOCK_PX + tx * TILE_PX
                    py = by * BLOCK_PX + ty * TILE_PX
                    draw.rectangle([px, py, px+TILE_PX-1, py+TILE_PX-1],
                                   fill=(255, 60, 60, 90))
        ts = self.tilesets.get(self.zone)
        c  = self.tileset_canvas
        c.delete('all')
        if not ts:
            return
        scale = 2
        tw = ts.width * scale
        th = ts.height * scale
        # Compor RGBA sobre fundo preto — evita artefato rosa
        ts_rgb = Image.new('RGB', (ts.width, ts.height), (0, 0, 0))
        if ts.mode == 'RGBA':
            ts_rgb.paste(ts, mask=ts.split()[3])
        else:
            ts_rgb.paste(ts.convert('RGB'))
        scaled = ts_rgb.resize((tw, th), Image.NEAREST)
        # grid lines
        draw = ImageDraw.Draw(scaled)
        for x in range(0, tw+1, TILE_PX*scale):
            draw.line([(x,0),(x,th)], fill='#3a3a3a')
        for y in range(0, th+1, TILE_PX*scale):
            draw.line([(0,y),(tw,y)], fill='#3a3a3a')
        self._ts_tk = ImageTk.PhotoImage(scaled)
        self._ts_scale = scale
        c.config(width=tw, scrollregion=(0,0,tw,th))
        c.create_image(0, 0, anchor='nw', image=self._ts_tk)
        # Highlight selected tile
        self._draw_tile_selection()

    def _draw_tile_selection(self):
        ts = self.tilesets.get(self.zone)
        if not ts:
            return
        scale = getattr(self, '_ts_scale', 2)
        tpr = ts.width // TILE_PX
        tx = (self.selected_tile % tpr) * TILE_PX * scale
        ty = (self.selected_tile // tpr) * TILE_PX * scale
        sz = TILE_PX * scale
        self.tileset_canvas.delete('tile_sel')
        self.tileset_canvas.create_rectangle(tx+1, ty+1, tx+sz-1, ty+sz-1,
                                              outline=C['accent'], width=2, tags='tile_sel')

    def _rebuild_map_canvas(self):
        self._render_map_image()
        self._block_tk_cache.clear()
        self._refresh_map_canvas()

    def _patch_block_on_canvas(self, bx, by):
        """Redesenha apenas o bloco (bx,by) no canvas sem reprocessar tudo."""
        if self._map_img is None:
            self._rebuild_map_canvas()
            return
        img  = self._map_img
        z    = self.map_zoom
        bi   = self.map_grid[by][bx] if by < len(self.map_grid) and bx < len(self.map_grid[by]) else 0
        ts   = self.tilesets.get(self.zone)
        bmd  = self.bmd_data.get(self.zone)

        # Renderizar o bloco numa imagem temporária
        blk_img = Image.new('RGBA', (BLOCK_PX, BLOCK_PX), (0, 0, 0, 255))
        if bi and ts and bmd:
            tpr = ts.width // TILE_PX
            for ty in range(16):
                for tx in range(16):
                    off = bi * 512 + (tx + ty * 16) * 2
                    if off + 1 >= len(bmd): continue
                    ctrl = bmd[off]; tid = bmd[off+1]
                    if not tid: continue
                    io = 1 if (ctrl&1) else (2 if (ctrl&3)==2 else 0)
                    at = tid + io*256
                    sx = (at%tpr)*TILE_PX; sy2 = (at//tpr)*TILE_PX
                    if sy2+TILE_PX > ts.height: continue
                    tile = ts.crop((sx, sy2, sx+TILE_PX, sy2+TILE_PX))
                    rot  = (ctrl>>3)&3
                    if rot==1: tile=tile.transpose(Image.Transpose.ROTATE_90)
                    elif rot==2: tile=tile.transpose(Image.Transpose.ROTATE_180)
                    elif rot==3: tile=tile.transpose(Image.Transpose.ROTATE_270)
                    dx2 = tx*TILE_PX; dy2 = ty*TILE_PX
                    if tile.mode=='RGBA':
                        blk_img.paste(tile, (dx2,dy2), mask=tile.split()[3])
                    else:
                        blk_img.paste(tile.convert('RGB'), (dx2,dy2))

        # Sobrescrever a região no _map_img
        img.paste(blk_img, (bx*BLOCK_PX, by*BLOCK_PX))

        # Overlay de colisão se ativo
        if self.show_collision.get() and self.col_data:
            self._draw_collision_overlay_block(img, bx, by, bi)

        # Overlay de grade
        draw = ImageDraw.Draw(img)
        if self.show_tile_grid.get():
            for tx in range(17):
                x = bx*BLOCK_PX + tx*TILE_PX
                draw.line([(x, by*BLOCK_PX),(x,(by+1)*BLOCK_PX)], fill='#1a3050')
            for ty2 in range(17):
                y = by*BLOCK_PX + ty2*TILE_PX
                draw.line([(bx*BLOCK_PX,y),((bx+1)*BLOCK_PX,y)], fill='#1a3050')
        if self.show_block_grid.get():
            x = bx*BLOCK_PX; y = by*BLOCK_PX
            draw.rectangle([x,y,x+BLOCK_PX-1,y+BLOCK_PX-1], outline='#503030')

        # Atualizar o canvas na região correta — escalar só o bloco
        bsz = int(BLOCK_PX * z)
        patch = img.crop((bx*BLOCK_PX, by*BLOCK_PX,
                          (bx+1)*BLOCK_PX, (by+1)*BLOCK_PX))
        patch_rgb = patch.convert('RGB') if patch.mode == 'RGBA' else patch
        patch_scaled = patch_rgb.resize((bsz, bsz), Image.NEAREST)
        tk_patch = ImageTk.PhotoImage(patch_scaled)
        # Guardar referência
        self._block_tk_cache[(bx,by)] = tk_patch
        cx = int(bx * BLOCK_PX * z)
        cy = int(by * BLOCK_PX * z)
        self.map_canvas.create_image(cx, cy, anchor='nw', image=tk_patch)

    def _refresh_map_canvas(self):
        if self._map_dirty:
            self._render_map_image()
        c   = self.map_canvas
        img = self._map_img
        if img is None:
            c.delete('all')
            c.config(scrollregion=(0,0,100,100))
            return
        z   = self.map_zoom
        iw  = int(img.width  * z)
        ih  = int(img.height * z)
        # Converter RGBA -> RGB para exibição (fundo preto já está no img)
        disp = img.convert('RGB') if img.mode == 'RGBA' else img
        scaled = disp.resize((iw, ih), Image.NEAREST)
        self._map_tk = ImageTk.PhotoImage(scaled)
        self._block_tk_cache.clear()
        c.delete('all')
        c.config(scrollregion=(0, 0, iw, ih))
        c.create_image(0, 0, anchor='nw', image=self._map_tk)
        self.map_zoom_lbl.config(text=f'{z}×')

    # ── BLOCK EDITOR ────────────────────────────────────────
    def _update_block_editor(self):
        c = self.block_canvas
        c.delete('all')
        bi = self.editing_block
        if bi is None:
            c.create_text(128, 128, text=self.T['click_block'],
                          fill=C['fg2'], font=('Segoe UI', 9))
            self.block_info_lbl.config(text=self.T['click_block'])
            return
        self.block_info_lbl.config(text=f'Block #{bi}')
        ts  = self.tilesets.get(self.zone)
        bmd = self.bmd_data.get(self.zone)
        sz  = 16  # 256/16
        if ts and bmd:
            tpr = ts.width // TILE_PX
            for ty in range(16):
                for tx in range(16):
                    off = bi * 512 + (tx + ty * 16) * 2
                    if off + 1 >= len(bmd): continue
                    ctrl = bmd[off]; tid = bmd[off+1]
                    if not tid: continue
                    io = 1 if (ctrl&1) else (2 if (ctrl&3)==2 else 0)
                    at = tid + io*256
                    sx = (at%tpr)*TILE_PX; sy=(at//tpr)*TILE_PX
                    if sy+TILE_PX > ts.height: continue
                    tile = ts.crop((sx,sy,sx+TILE_PX,sy+TILE_PX))
                    # Compor RGBA sobre fundo preto
                    tile_rgb = Image.new('RGB', (TILE_PX, TILE_PX), (0, 0, 0))
                    if tile.mode == 'RGBA':
                        tile_rgb.paste(tile, mask=tile.split()[3])
                    else:
                        tile_rgb.paste(tile.convert('RGB'))
                    tile_scaled = tile_rgb.resize((sz, sz), Image.NEAREST)
                    tk_img = ImageTk.PhotoImage(tile_scaled)
                    # Keep reference
                    if not hasattr(self,'_block_tiles'): self._block_tiles=[]
                    self._block_tiles.append(tk_img)
                    c.create_image(tx*sz, ty*sz, anchor='nw', image=tk_img)
        # Grid
        for i in range(17):
            c.create_line(i*sz, 0, i*sz, 256, fill='#3a3050')
            c.create_line(0, i*sz, 256, i*sz, fill='#3a3050')

    # ── OBJECT CANVAS ───────────────────────────────────────
    def _rebuild_obj_canvas(self):
        """Draw map background + objects on obj_canvas."""
        self._render_map_image()
        img = self._map_img
        c   = self.obj_canvas
        c.delete('all')
        if img is None:
            c.config(scrollregion=(0,0,100,100))
            return
        z  = self.obj_zoom
        iw = int(img.width  * z)
        ih = int(img.height * z)
        disp = img.convert('RGB') if img.mode == 'RGBA' else img
        scaled = disp.resize((iw,ih), Image.NEAREST)
        self._obj_bg_tk = ImageTk.PhotoImage(scaled)
        c.config(scrollregion=(0,0,iw,ih))
        c.create_image(0,0, anchor='nw', image=self._obj_bg_tk, tags='bg')
        self._redraw_objects()

    def _redraw_objects(self):
        c = self.obj_canvas
        c.delete('obj')
        z = self.obj_zoom
        show_spr = self.show_sprites.get()
        show_hbx = self.show_hitbox.get()
        for i, obj in enumerate(self.objects):
            if obj['type'] == 255:
                continue
            info = OBJ_TYPES.get(obj['type'])
            if not info:
                name_disp = f"#{obj['type']}"
                color = '#888'; hw = 16; hh = 16
            else:
                name_disp = info[0] if self.lang == 'pt' else info[1]
                color = info[4-1] if False else info[3]  # color at index 3
                hw = min(info[4], 64) // 2
                hh = min(info[5], 64) // 2
                color = info[3]
                hw = min(info[4], 64) // 2
                hh = min(info[5], 64) // 2

            px = int(obj['x'] * z)
            py = int(obj['y'] * z)
            hw_z = int(hw * z)
            hh_z = int(hh * z)
            is_sel = (i == self.selected_obj_idx)

            # Draw sprite or fallback box
            drawn_spr = False
            if show_spr and info and info[2]:
                spr = self.sprites.get(info[2].lower())
                if spr:
                    sw = min(spr.width,  hw*2)
                    sh = min(spr.height, hh*2)
                    crop = spr.crop((0, 0, sw, sh))
                    # Compor sobre fundo transparente (ImageTk suporta RGBA)
                    thumb = crop.resize((hw_z*2, hh_z*2), Image.NEAREST)
                    if thumb.mode != 'RGBA':
                        thumb = thumb.convert('RGBA')
                    tk_i = ImageTk.PhotoImage(thumb)
                    if not hasattr(self,'_obj_tk_cache'): self._obj_tk_cache=[]
                    self._obj_tk_cache.append(tk_i)
                    c.create_image(px-hw_z, py-hh_z, anchor='nw', image=tk_i, tags='obj')
                    drawn_spr = True

            if not drawn_spr or show_hbx:
                outline = C['accent'] if is_sel else color
                lw = 2 if is_sel else 1
                c.create_rectangle(px-hw_z, py-hh_z, px+hw_z, py+hh_z,
                                   outline=outline, width=lw, fill=color+'33', tags='obj')

            if is_sel:
                c.create_rectangle(px-hw_z-3, py-hh_z-3, px+hw_z+3, py+hh_z+3,
                                   outline=C['accent'], width=2, dash=(4,2), tags='obj')

            # Label
            c.create_text(px, py-hh_z-4, text=name_disp, fill='#ddd',
                          font=('Segoe UI', max(7, int(8*z))), tags='obj', anchor='s')

    # ── PALETTE ─────────────────────────────────────────────
    def _populate_palette(self, cat_filter='all'):
        lb = self.obj_listbox
        lb.delete(0,'end')
        self._palette_types = []
        for typ, info in sorted(OBJ_TYPES.items()):
            if typ == 255:
                continue
            cat = info[6]
            if cat_filter != 'all' and cat != cat_filter:
                continue
            name = info[0] if self.lang == 'pt' else info[1]
            lb.insert('end', f'  [{typ:3d}] {name}')
            self._palette_types.append(typ)
        # Select current
        if self.selected_obj_type in self._palette_types:
            idx = self._palette_types.index(self.selected_obj_type)
            lb.selection_set(idx)
            lb.see(idx)

    def _filter_palette(self, event=None):
        idx = self.cat_combo.current()
        cat = self._cat_keys[idx] if idx >= 0 else 'all'
        self._populate_palette(cat)

    def _refresh_obj_list(self):
        lb = self.obj_list_lb
        lb.delete(0,'end')
        for i, obj in enumerate(self.objects):
            if obj['type'] == 255:
                continue
            info = OBJ_TYPES.get(obj['type'])
            name = (info[0] if self.lang=='pt' else info[1]) if info else f"#{obj['type']}"
            lb.insert('end', f'{i:3d} {name:16s} {obj["x"]},{obj["y"]}')
        if 0 <= self.selected_obj_idx < lb.size():
            lb.selection_set(self.selected_obj_idx)
            lb.see(self.selected_obj_idx)

    # --------------------------------------------------------
    # EVENT HANDLERS — MAP
    # --------------------------------------------------------
    def _canvas_to_world(self, canvas, event, zoom):
        cx = canvas.canvasx(event.x)
        cy = canvas.canvasy(event.y)
        return int(cx / zoom), int(cy / zoom)

    def _world_to_block(self, wx, wy):
        return wx // BLOCK_PX, wy // BLOCK_PX

    def _on_tileset_click(self, event):
        ts = self.tilesets.get(self.zone)
        if not ts: return
        scale = getattr(self,'_ts_scale',2)
        tx = int(self.tileset_canvas.canvasx(event.x) / (TILE_PX*scale))
        ty = int(self.tileset_canvas.canvasy(event.y) / (TILE_PX*scale))
        tpr = ts.width // TILE_PX
        self.selected_tile = ty * tpr + tx
        self._draw_tile_selection()

    def _on_map_click(self, event):
        if not self.map_grid: return
        wx, wy = self._canvas_to_world(self.map_canvas, event, self.map_zoom)
        self.map_drag_start = (wx, wy)
        self._last_painted_tile = None  # evitar repintar o mesmo tile no drag
        self._save_map_undo()
        self._apply_map_tool(wx, wy, erase=False)

    def _on_map_drag(self, event):
        if not self.map_grid: return
        wx, wy = self._canvas_to_world(self.map_canvas, event, self.map_zoom)
        if self.map_tool not in ('move',):
            self._apply_map_tool(wx, wy, erase=False)

    def _on_map_release(self, event):
        if self.map_tool == 'move' and self.map_drag_start:
            wx, wy = self._canvas_to_world(self.map_canvas, event, self.map_zoom)
            bx0, by0 = self.map_drag_start[0] // BLOCK_PX, self.map_drag_start[1] // BLOCK_PX
            bx1, by1 = wx // BLOCK_PX, wy // BLOCK_PX
            if (bx0, by0) != (bx1, by1):
                self._save_map_undo()
                self._swap_blocks(bx0, by0, bx1, by1)
        self.map_drag_start = None
        self._last_painted_tile = None

    def _on_map_rclick(self, event):
        if not self.map_grid: return
        wx, wy = self._canvas_to_world(self.map_canvas, event, self.map_zoom)
        self._save_map_undo()
        self._apply_map_tool(wx, wy, erase=True)

    def _apply_map_tool(self, wx, wy, erase):
        """wx, wy em pixels do mundo (antes do zoom)."""
        bx = wx // BLOCK_PX
        by = wy // BLOCK_PX
        if not (0 <= by < len(self.map_grid)): return
        row = self.map_grid[by]
        if not (0 <= bx < len(row)): return

        mode = self.brush_mode.get()  # 'block' ou 'tile'

        if self.map_tool == 'pick':
            self.selected_block = row[bx]
            return

        if self.map_tool == 'fill':
            self._flood_fill(by, bx, row[bx], self.selected_block)
            self._map_dirty = True
            self._refresh_map_canvas()
            return

        if self.map_tool == 'move':
            self.editing_block = row[bx]
            self._update_block_editor()
            return

        # paint e erase — modo bloco ou tile
        if mode == 'block':
            new_val = 0 if (erase or self.map_tool == 'erase') else self.selected_block
            if row[bx] == new_val: return
            row[bx] = new_val
            self._map_dirty = True
            self._patch_block_on_canvas(bx, by)

        else:  # modo tile
            tx = (wx % BLOCK_PX) // TILE_PX
            ty = (wy % BLOCK_PX) // TILE_PX
            tile_key = (bx, by, tx, ty)
            if tile_key == getattr(self, '_last_painted_tile', None):
                return
            self._last_painted_tile = tile_key

            bi = row[bx]
            if bi == 0 and not erase: return
            bmd = self.bmd_data.get(self.zone)
            if not bmd: return
            off = bi * 512 + (tx + ty * 16) * 2
            if off + 1 >= len(bmd): return

            if erase or self.map_tool == 'erase':
                bmd[off] = 0; bmd[off+1] = 0
            else:
                bmd[off] = 0; bmd[off+1] = self.selected_tile & 0xFF

            self._map_dirty = True
            self._patch_block_on_canvas(bx, by)

            self._map_dirty = True
            self._patch_block_on_canvas(bx, by)

    def _on_map_motion(self, event):
        if not self.map_grid: return
        wx, wy = self._canvas_to_world(self.map_canvas, event, self.map_zoom)
        bx = wx // BLOCK_PX; by = wy // BLOCK_PX
        tx = (wx % BLOCK_PX) // TILE_PX; ty = (wy % BLOCK_PX) // TILE_PX
        self._set_status(self.T['status_cursor'].format(x=wx,y=wy,bx=bx,by=by)
                         + f'  Tile: {tx},{ty}')

    def _on_map_wheel(self, event):
        delta = -1 if event.delta < 0 else 1
        self.map_canvas.yview_scroll(-delta, 'units')

    def _on_map_ctrl_wheel(self, event):
        delta = 0.5 if event.delta > 0 else -0.5
        self._set_map_zoom(self.map_zoom + delta)

    def _scroll_map(self, dx, dy):
        if dx: self.map_canvas.xview_scroll(dx, 'units')
        if dy: self.map_canvas.yview_scroll(dy, 'units')

    def _swap_blocks(self, sx, sy, dx, dy):
        if not (0 <= sy < len(self.map_grid) and 0 <= dy < len(self.map_grid)):
            return
        rv = self.map_grid[sy]
        rw = self.map_grid[dy]
        if not (0 <= sx < len(rv) and 0 <= dx < len(rw)):
            return
        rv[sx], rw[dx] = rw[dx], rv[sx]
        self._map_dirty = True
        self._refresh_map_canvas()

    def _flood_fill(self, row, col, target, fill):
        if target == fill: return
        stack = [(row, col)]
        while stack:
            r, c = stack.pop()
            if r < 0 or r >= len(self.map_grid): continue
            if c < 0 or c >= len(self.map_grid[r]): continue
            if self.map_grid[r][c] != target: continue
            self.map_grid[r][c] = fill
            stack += [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]

    def _on_block_edit_click(self, event):
        self._block_edit_at(event, erase=False)

    def _on_block_edit_rclick(self, event):
        self._block_edit_at(event, erase=True)

    def _block_edit_at(self, event, erase):
        bi = self.editing_block
        if bi is None: return
        bmd = self.bmd_data.get(self.zone)
        if not bmd: return
        sz = 16  # 256/16
        tx = event.x // sz
        ty = event.y // sz
        if not (0 <= tx < 16 and 0 <= ty < 16): return
        self._save_map_undo()
        off = bi * 512 + (tx + ty * 16) * 2
        if off + 1 >= len(bmd): return
        if erase:
            bmd[off] = 0; bmd[off+1] = 0
        else:
            bmd[off] = 0; bmd[off+1] = self.selected_tile & 0xFF
        self._map_dirty = True
        self._update_block_editor()
        self._rebuild_map_canvas()

    # --------------------------------------------------------
    # EVENT HANDLERS — OBJECTS
    # --------------------------------------------------------
    def _on_palette_select(self, event):
        sel = self.obj_listbox.curselection()
        if sel:
            self.selected_obj_type = self._palette_types[sel[0]]

    def _on_obj_click(self, event):
        wx, wy = self._canvas_to_world(self.obj_canvas, event, self.obj_zoom)
        if self.obj_tool == 'place':
            self._save_obj_undo()
            self.objects.append({'x':wx,'y':wy,'type':self.selected_obj_type,
                                  'param':0,'count':0})
            self.selected_obj_idx = len(self.objects) - 1
            self._redraw_objects()
            self._refresh_obj_list()
            self._update_props_panel()
            self._update_status_right()
        elif self.obj_tool == 'delete':
            idx = self._hit_test(wx, wy)
            if idx >= 0:
                self._save_obj_undo()
                self.objects.pop(idx)
                self.selected_obj_idx = -1
                self._redraw_objects()
                self._refresh_obj_list()
                self._update_props_panel()
                self._update_status_right()
        elif self.obj_tool == 'select':
            idx = self._hit_test(wx, wy)
            self._select_obj(idx)
            if idx >= 0:
                obj = self.objects[idx]
                self.obj_drag_start  = (wx, wy)
                self.obj_drag_origin = (obj['x'], obj['y'])

    def _on_obj_drag(self, event):
        if self.obj_tool == 'select' and self.obj_drag_start and self.selected_obj_idx >= 0:
            wx, wy = self._canvas_to_world(self.obj_canvas, event, self.obj_zoom)
            dx = wx - self.obj_drag_start[0]
            dy = wy - self.obj_drag_start[1]
            obj = self.objects[self.selected_obj_idx]
            obj['x'] = self.obj_drag_origin[0] + dx
            obj['y'] = self.obj_drag_origin[1] + dy
            self._redraw_objects()
            self._update_props_panel()

    def _on_obj_release(self, event):
        self.obj_drag_start  = None
        self.obj_drag_origin = None
        if self.selected_obj_idx >= 0:
            self._refresh_obj_list()

    def _on_obj_rclick(self, event):
        wx, wy = self._canvas_to_world(self.obj_canvas, event, self.obj_zoom)
        idx = self._hit_test(wx, wy)
        if idx >= 0:
            self._save_obj_undo()
            self.objects.pop(idx)
            if self.selected_obj_idx == idx:
                self.selected_obj_idx = -1
            elif self.selected_obj_idx > idx:
                self.selected_obj_idx -= 1
            self._redraw_objects()
            self._refresh_obj_list()
            self._update_props_panel()
            self._update_status_right()

    def _on_obj_motion(self, event):
        wx, wy = self._canvas_to_world(self.obj_canvas, event, self.obj_zoom)
        n = len([o for o in self.objects if o['type']!=255])
        self._set_status(
            self.T['status_cursor'].format(x=wx,y=wy,bx=wx//BLOCK_PX,by=wy//BLOCK_PX) +
            '  ' + self.T['status_objects'].format(n=n))

    def _on_obj_wheel(self, event):
        delta = -1 if event.delta < 0 else 1
        self.obj_canvas.yview_scroll(-delta,'units')

    def _on_obj_ctrl_wheel(self, event):
        delta = 0.5 if event.delta > 0 else -0.5
        self._set_obj_zoom(self.obj_zoom + delta)

    def _scroll_obj(self, dx, dy):
        if dx: self.obj_canvas.xview_scroll(dx,'units')
        if dy: self.obj_canvas.yview_scroll(dy,'units')

    def _hit_test(self, wx, wy):
        for i in range(len(self.objects)-1, -1, -1):
            obj = self.objects[i]
            if obj['type'] == 255: continue
            info = OBJ_TYPES.get(obj['type'])
            hw = (min(info[4],64)//2) if info else 16
            hh = (min(info[5],64)//2) if info else 16
            if abs(wx-obj['x'])<=hw and abs(wy-obj['y'])<=hh:
                return i
        return -1

    def _select_obj(self, idx):
        self.selected_obj_idx = idx
        self._redraw_objects()
        self._update_props_panel()
        lb = self.obj_list_lb
        lb.selection_clear(0,'end')
        if 0 <= idx < lb.size():
            lb.selection_set(idx)
            lb.see(idx)
        self.delete_obj_btn.config(state='normal' if idx>=0 else 'disabled')

    def _on_obj_list_select(self, event):
        sel = self.obj_list_lb.curselection()
        if sel:
            self._select_obj(sel[0])

    def _delete_selected_obj(self):
        if self.selected_obj_idx < 0: return
        self._save_obj_undo()
        self.objects.pop(self.selected_obj_idx)
        self.selected_obj_idx = -1
        self._redraw_objects()
        self._refresh_obj_list()
        self._update_props_panel()
        self._update_status_right()

    def _update_props_panel(self):
        idx = self.selected_obj_idx
        if idx < 0 or idx >= len(self.objects):
            for v in self.prop_vars.values():
                v.set('')
            return
        obj = self.objects[idx]
        self._prop_update_lock = True
        for field, var in self.prop_vars.items():
            var.set(str(obj.get(field,0)))
        self._prop_update_lock = False

    def _on_prop_change(self, field, var):
        if getattr(self,'_prop_update_lock',False): return
        if self.selected_obj_idx < 0: return
        try:
            val = int(var.get())
        except ValueError:
            return
        self.objects[self.selected_obj_idx][field] = val
        self._redraw_objects()

    # --------------------------------------------------------
    # TOOLS / ZOOM
    # --------------------------------------------------------
    def _set_map_tool(self, t):
        self.map_tool = t
        for k, b in self.map_tool_btns.items():
            b.config(bg=C['accent2'] if k==t else C['bg3'])

    def _set_obj_tool(self, t):
        self.obj_tool = t
        for k, b in self.obj_tool_btns.items():
            b.config(bg=C['accent2'] if k==t else C['bg3'])
        cur = {'place':'crosshair','select':'fleur','delete':'X'}
        self.obj_canvas.config(cursor=cur.get(t,'crosshair'))

    def _set_map_zoom(self, z):
        self.map_zoom = max(0.25, min(8.0, z))
        self._refresh_map_canvas()

    def _fit_map_zoom(self):
        w, h = self._get_map_dims()
        if not w: return
        cw = self.map_canvas.winfo_width()
        ch = self.map_canvas.winfo_height()
        if cw < 10: cw = 800
        if ch < 10: ch = 500
        zx = cw / (w * BLOCK_PX)
        zy = ch / (h * BLOCK_PX)
        self._set_map_zoom(round(min(zx,zy)*4)/4)

    def _set_obj_zoom(self, z):
        self.obj_zoom = max(0.25, min(8.0, z))
        self._rebuild_obj_canvas()

    def _fit_obj_zoom(self):
        w, h = self._get_map_dims()
        if not w: return
        cw = self.obj_canvas.winfo_width()
        ch = self.obj_canvas.winfo_height()
        if cw < 10: cw = 800
        if ch < 10: ch = 500
        zx = cw / (w * BLOCK_PX)
        zy = ch / (h * BLOCK_PX)
        self._set_obj_zoom(round(min(zx,zy)*4)/4)

    # --------------------------------------------------------
    # UNDO / REDO
    # --------------------------------------------------------
    def _save_map_undo(self):
        state = {
            'grid': [list(r) for r in self.map_grid],
            'bmd':  bytes(self.bmd_data.get(self.zone, b'')),
        }
        self.map_undo.append(state)
        if len(self.map_undo) > 50: self.map_undo.pop(0)
        self.map_redo.clear()

    def _save_obj_undo(self):
        self.obj_undo.append(copy.deepcopy(self.objects))
        if len(self.obj_undo) > 50: self.obj_undo.pop(0)
        self.obj_redo.clear()

    def _undo(self):
        tab = self.nb.index('current')
        if tab == 0:  # map
            if not self.map_undo: return
            self.map_redo.append({
                'grid': [list(r) for r in self.map_grid],
                'bmd':  bytes(self.bmd_data.get(self.zone, b'')),
            })
            state = self.map_undo.pop()
            self.map_grid = state['grid']
            if self.zone in self.bmd_data:
                self.bmd_data[self.zone] = bytearray(state['bmd'])
            self._map_dirty = True
            self._rebuild_map_canvas()
            self._update_block_editor()
        else:  # obj
            if not self.obj_undo: return
            self.obj_redo.append(copy.deepcopy(self.objects))
            self.objects = self.obj_undo.pop()
            self.selected_obj_idx = -1
            self._redraw_objects()
            self._refresh_obj_list()
            self._update_props_panel()

    def _redo(self):
        tab = self.nb.index('current')
        if tab == 0:
            if not self.map_redo: return
            self.map_undo.append({
                'grid': [list(r) for r in self.map_grid],
                'bmd':  bytes(self.bmd_data.get(self.zone, b'')),
            })
            state = self.map_redo.pop()
            self.map_grid = state['grid']
            if self.zone in self.bmd_data:
                self.bmd_data[self.zone] = bytearray(state['bmd'])
            self._map_dirty = True
            self._rebuild_map_canvas()
        else:
            if not self.obj_redo: return
            self.obj_undo.append(copy.deepcopy(self.objects))
            self.objects = self.obj_redo.pop()
            self.selected_obj_idx = -1
            self._redraw_objects()
            self._refresh_obj_list()

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------
    def _export_bmd(self):
        bmd = self.bmd_data.get(self.zone)
        if not bmd:
            messagebox.showwarning('', 'No BMD data loaded.')
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.bmd',
            initialfile=f'zone{self.zone+1}.bmd',
            filetypes=[('BMD files','*.bmd'),('All','*.*')])
        if path:
            with open(path,'wb') as f: f.write(bmd)
            messagebox.showinfo('', self.T['export_ok'].format(path=path))

    def _export_act(self):
        acts = self.act_data.get(self.zone)
        if not acts:
            messagebox.showwarning('', 'No ACT data loaded.')
            return
        acts[self.act] = self._serialize_act(self.objects)
        sizes = [len(a) for a in acts]
        buf = bytearray()
        for s in sizes:
            buf += bytes([(s>>8)&0xFF, s&0xFF])
        for a in acts:
            buf += a
        path = filedialog.asksaveasfilename(
            defaultextension='.act',
            initialfile=f'ZONE{self.zone+1}ACT.act',
            filetypes=[('ACT files','*.act'),('All','*.*')])
        if path:
            with open(path,'wb') as f: f.write(buf)
            messagebox.showinfo('', self.T['export_ok'].format(path=path))

    def _export_all(self):
        folder = filedialog.askdirectory(title='Export to folder')
        if not folder: return
        count = 0
        for z in range(6):
            bmd = self.bmd_data.get(z)
            if bmd:
                p = os.path.join(folder, f'zone{z+1}.bmd')
                with open(p,'wb') as f: f.write(bmd)
                count += 1
            acts = self.act_data.get(z)
            if acts:
                # If current zone, apply changes
                if z == self.zone:
                    acts[self.act] = self._serialize_act(self.objects)
                sizes = [len(a) for a in acts]
                buf = bytearray()
                for s in sizes:
                    buf += bytes([(s>>8)&0xFF, s&0xFF])
                for a in acts:
                    buf += a
                p = os.path.join(folder, f'ZONE{z+1}ACT.act')
                with open(p,'wb') as f: f.write(buf)
                count += 1
        messagebox.showinfo('', self.T['export_ok'].format(path=f'{folder} ({count} files)'))

    # --------------------------------------------------------
    # ZONE / ACT CHANGE
    # --------------------------------------------------------
    def _on_zone_change(self, event=None):
        val = self.zone_var.get()
        self.zone = int(val.split(':')[0])
        self._map_dirty = True
        self._load_zone_act()

    def _on_act_change(self, event=None):
        self.act = int(self.act_var.get())
        self._map_dirty = True
        self._load_zone_act()

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------
    def _change_lang(self):
        self.lang = self.lang_var.get()
        self.T = LANG[self.lang]
        # Rebuild UI text would require full rebuild; for simplicity restart notice
        messagebox.showinfo(
            'Language / Idioma',
            'Reinicie o editor para aplicar o idioma.\nRestart the editor to apply the language.')

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------
    def _set_status(self, msg):
        self.status_lbl.config(text=msg)

    def _update_status_right(self):
        n = len([o for o in self.objects if o['type']!=255])
        self.status_right.config(
            text=self.T['status_objects'].format(n=n) +
                 '  ' + self.T['status_zoom'].format(z=self.obj_zoom))

    def _update_title(self):
        zn = self.T['zone_names'][self.zone]
        self.root.title(f"{self.T['title']}  —  {zn}  Act {self.act}")

    def _update_block_canvas_idle(self):
        self.root.after_idle(self._update_block_editor)

    def _refresh_obj_canvas_idle(self):
        self.root.after_idle(self._rebuild_obj_canvas)


# ============================================================
# ENTRY POINT
# ============================================================
def main():
    root = tk.Tk()
    root.title('Sonic J2ME Editor')

    # Dark title bar (Windows)
    try:
        root.wm_attributes('-alpha', 1)
        import ctypes
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.windll.user32.GetForegroundWindow(),
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(1)),
            ctypes.sizeof(ctypes.c_int))
    except:
        pass

    app = SonicEditor(root)
    root.mainloop()


if __name__ == '__main__':
    main()
