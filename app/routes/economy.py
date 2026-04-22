import json
import uuid
import os
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.data import list_entities, campaign_dir

economy = Blueprint('economy', __name__, url_prefix='/c/economy')

GROŠ = 225  # CZK per groš

TIERS = {
    'abundant': {'label': 'Hojné',            'multiplier': 0.8,  'css': 'tier-abundant'},
    'plentiful':{'label': 'Běžné',             'multiplier': 1.0,  'css': 'tier-plentiful'},
    'scarce':   {'label': 'Nedostatkové',      'multiplier': 1.5,  'css': 'tier-scarce'},
    'rare':     {'label': 'Vzácné',            'multiplier': 2.5,  'css': 'tier-rare'},
    'extreme':  {'label': 'Extrémně vzácné',   'multiplier': 5.0,  'css': 'tier-extreme'},
}

CATEGORIES = [
    'Potraviny', 'Nápoje', 'Oblečení', 'Nádobí & nástroje',
    'Nábytek', 'Zbraně', 'Zbroj', 'Zvířata', 'Služby',
    'Materiály', 'Spotřební', 'Magie & byliny',
]

DEFAULT_ITEMS = [
    # Potraviny
    {'id':'bread',    'name':'Bochník chleba',     'category':'Potraviny',          'price_gros':0.10,  'unit':'ks'},
    {'id':'cheese',   'name':'Kus sýra',            'category':'Potraviny',          'price_gros':0.20,  'unit':'ks'},
    {'id':'eggs',     'name':'Vejce (10 ks)',        'category':'Potraviny',          'price_gros':0.12,  'unit':'10 ks'},
    {'id':'chicken',  'name':'Slepice',              'category':'Potraviny',          'price_gros':0.50,  'unit':'ks'},
    {'id':'pork_kg',  'name':'Vepřové maso',         'category':'Potraviny',          'price_gros':0.40,  'unit':'kg'},
    {'id':'beef_kg',  'name':'Hovězí maso',          'category':'Potraviny',          'price_gros':0.60,  'unit':'kg'},
    {'id':'fish_kg',  'name':'Ryba',                 'category':'Potraviny',          'price_gros':0.30,  'unit':'kg'},
    {'id':'salt_kg',  'name':'Sůl',                  'category':'Potraviny',          'price_gros':0.80,  'unit':'kg'},
    {'id':'honey_kg', 'name':'Med',                  'category':'Potraviny',          'price_gros':1.00,  'unit':'kg'},
    {'id':'flour_kg', 'name':'Mouka',                'category':'Potraviny',          'price_gros':0.15,  'unit':'kg'},
    {'id':'spices',   'name':'Koření (malé množství)','category':'Potraviny',         'price_gros':2.00,  'unit':'ks'},
    {'id':'lard',     'name':'Sádlo',                'category':'Potraviny',          'price_gros':0.25,  'unit':'kg'},
    # Nápoje
    {'id':'ale',      'name':'Džbán piva',           'category':'Nápoje',             'price_gros':0.08,  'unit':'džbán'},
    {'id':'wine',     'name':'Džbán vína',            'category':'Nápoje',             'price_gros':0.30,  'unit':'džbán'},
    {'id':'mead',     'name':'Medovina',              'category':'Nápoje',             'price_gros':0.25,  'unit':'džbán'},
    {'id':'barrel_ale','name':'Soudek piva',          'category':'Nápoje',             'price_gros':3.00,  'unit':'soudek'},
    # Oblečení
    {'id':'shirt',    'name':'Lněná košile',          'category':'Oblečení',           'price_gros':1.50,  'unit':'ks'},
    {'id':'boots',    'name':'Kožené boty',            'category':'Oblečení',           'price_gros':3.00,  'unit':'pár'},
    {'id':'cloak',    'name':'Plášť',                  'category':'Oblečení',           'price_gros':4.00,  'unit':'ks'},
    {'id':'coat',     'name':'Vlněný kabátec',         'category':'Oblečení',           'price_gros':6.00,  'unit':'ks'},
    {'id':'gloves',   'name':'Rukavice',               'category':'Oblečení',           'price_gros':1.00,  'unit':'pár'},
    {'id':'belt',     'name':'Kožený opasek',          'category':'Oblečení',           'price_gros':0.80,  'unit':'ks'},
    # Nádobí & nástroje
    {'id':'cup_wood', 'name':'Dřevěný hrnek',          'category':'Nádobí & nástroje',  'price_gros':0.10,  'unit':'ks'},
    {'id':'pot_clay', 'name':'Hliněný hrnec',          'category':'Nádobí & nástroje',  'price_gros':0.30,  'unit':'ks'},
    {'id':'knife',    'name':'Železný nůž',            'category':'Nádobí & nástroje',  'price_gros':1.50,  'unit':'ks'},
    {'id':'axe_tool', 'name':'Sekera (pracovní)',      'category':'Nádobí & nástroje',  'price_gros':3.00,  'unit':'ks'},
    {'id':'shovel',   'name':'Lopata',                 'category':'Nádobí & nástroje',  'price_gros':1.50,  'unit':'ks'},
    {'id':'rope',     'name':'Lano (10 m)',            'category':'Nádobí & nástroje',  'price_gros':0.40,  'unit':'10 m'},
    {'id':'candle',   'name':'Svíčka (10 ks)',         'category':'Nádobí & nástroje',  'price_gros':0.20,  'unit':'10 ks'},
    {'id':'lantern',  'name':'Lucerna',                'category':'Nádobí & nástroje',  'price_gros':2.00,  'unit':'ks'},
    # Nábytek
    {'id':'table',    'name':'Stůl',                   'category':'Nábytek',            'price_gros':5.00,  'unit':'ks'},
    {'id':'bench',    'name':'Lavice',                 'category':'Nábytek',            'price_gros':2.00,  'unit':'ks'},
    {'id':'chest',    'name':'Truhla',                 'category':'Nábytek',            'price_gros':4.00,  'unit':'ks'},
    {'id':'barrel',   'name':'Barely',                 'category':'Nábytek',            'price_gros':2.50,  'unit':'ks'},
    {'id':'bag',      'name':'Vak cestovní',           'category':'Nábytek',            'price_gros':0.80,  'unit':'ks'},
    # Zbraně
    {'id':'club',     'name':'Obušek / kyj',           'category':'Zbraně',             'price_gros':0.30,  'unit':'ks'},
    {'id':'dagger',   'name':'Lovecký nůž / dýka',     'category':'Zbraně',             'price_gros':2.00,  'unit':'ks'},
    {'id':'spear',    'name':'Kopí',                   'category':'Zbraně',             'price_gros':4.00,  'unit':'ks'},
    {'id':'sword',    'name':'Meč prostý',             'category':'Zbraně',             'price_gros':20.00, 'unit':'ks'},
    {'id':'sword_kn', 'name':'Meč rytířský',           'category':'Zbraně',             'price_gros':60.00, 'unit':'ks'},
    {'id':'axe_war',  'name':'Bojová sekera',          'category':'Zbraně',             'price_gros':12.00, 'unit':'ks'},
    {'id':'bow',      'name':'Luk',                    'category':'Zbraně',             'price_gros':6.00,  'unit':'ks'},
    {'id':'arrows',   'name':'Toulec šípů (20 ks)',    'category':'Zbraně',             'price_gros':2.00,  'unit':'toulec'},
    # Zbroj
    {'id':'armor_lth','name':'Kožená zbroj',           'category':'Zbroj',              'price_gros':8.00,  'unit':'ks'},
    {'id':'chain_sh', 'name':'Kroužková košile',       'category':'Zbroj',              'price_gros':40.00, 'unit':'ks'},
    {'id':'chain_full','name':'Plná kroužková zbroj',  'category':'Zbroj',              'price_gros':100.00,'unit':'ks'},
    {'id':'helm',     'name':'Železná přilba',         'category':'Zbroj',              'price_gros':15.00, 'unit':'ks'},
    {'id':'shield_wd','name':'Dřevěný štít',           'category':'Zbroj',              'price_gros':2.00,  'unit':'ks'},
    {'id':'shield_ir','name':'Okovaný štít',           'category':'Zbroj',              'price_gros':8.00,  'unit':'ks'},
    # Zvířata
    {'id':'horse_dr', 'name':'Tažný kůň',             'category':'Zvířata',            'price_gros':80.00, 'unit':'ks'},
    {'id':'horse_rd', 'name':'Jezdecký kůň',          'category':'Zvířata',            'price_gros':150.00,'unit':'ks'},
    {'id':'cow',      'name':'Kráva',                  'category':'Zvířata',            'price_gros':25.00, 'unit':'ks'},
    {'id':'sheep',    'name':'Ovce',                   'category':'Zvířata',            'price_gros':5.00,  'unit':'ks'},
    {'id':'pig',      'name':'Prase',                  'category':'Zvířata',            'price_gros':8.00,  'unit':'ks'},
    {'id':'dog',      'name':'Pes hlídací',            'category':'Zvířata',            'price_gros':3.00,  'unit':'ks'},
    # Služby
    {'id':'inn_barn', 'name':'Nocleh ve stodole',      'category':'Služby',             'price_gros':0.05,  'unit':'noc'},
    {'id':'inn_room', 'name':'Nocleh v hostinci',      'category':'Služby',             'price_gros':0.30,  'unit':'noc'},
    {'id':'bath',     'name':'Koupel',                 'category':'Služby',             'price_gros':0.10,  'unit':'ks'},
    {'id':'laborer',  'name':'Námezdní dělník',        'category':'Služby',             'price_gros':0.20,  'unit':'den'},
    {'id':'messenger','name':'Posel',                  'category':'Služby',             'price_gros':0.50,  'unit':'den'},
    {'id':'healer',   'name':'Léčitel (základní péče)','category':'Služby',             'price_gros':1.00,  'unit':'ošetření'},
    {'id':'blacksmith','name':'Kovář (hodina práce)', 'category':'Služby',              'price_gros':0.50,  'unit':'hod'},

    # Materiály pro výrobu
    {'id':'iron_bog',   'name':'Bahenní železo (surové)', 'category':'Materiály',        'price_gros':0.80,  'unit':'kg'},
    {'id':'iron_bar',   'name':'Železná tyč (zpracovaná)','category':'Materiály',        'price_gros':2.00,  'unit':'kg'},
    {'id':'steel_bar',  'name':'Ocelový ingot',           'category':'Materiály',        'price_gros':15.00, 'unit':'kg'},
    {'id':'wood_log',   'name':'Kláda (dubová)',          'category':'Materiály',        'price_gros':0.20,  'unit':'ks'},
    {'id':'wood_plank', 'name':'Fošna (opracovaná)',      'category':'Materiály',        'price_gros':0.50,  'unit':'ks'},
    {'id':'charcoal',   'name':'Dřevěné uhlí',            'category':'Materiály',        'price_gros':0.30,  'unit':'kg'},
    {'id':'leather_raw','name':'Syrová kůže',             'category':'Materiály',        'price_gros':0.60,  'unit':'ks'},
    {'id':'leather_tnd','name':'Vyčiněná kůže',           'category':'Materiály',        'price_gros':1.50,  'unit':'ks'},
    {'id':'fur_squirl', 'name':'Veverčí kůžka (1 kuna)',  'category':'Materiály',        'price_gros':0.05,  'unit':'ks'},
    {'id':'fur_sorochk','name':'Sorochok (40 kožek)',     'category':'Materiály',        'price_gros':2.00,  'unit':'svazek'},
    {'id':'flax',       'name':'Len (svazek)',             'category':'Materiály',        'price_gros':0.20,  'unit':'svazek'},
    {'id':'linen',      'name':'Lněná látka',              'category':'Materiály',        'price_gros':0.80,  'unit':'loket'},
    {'id':'wool',       'name':'Vlna (střižená)',          'category':'Materiály',        'price_gros':0.40,  'unit':'kg'},
    {'id':'clay',       'name':'Hrnčířská hlína',          'category':'Materiály',        'price_gros':0.05,  'unit':'kg'},
    {'id':'amber_raw',  'name':'Jantar (surový kus)',      'category':'Materiály',        'price_gros':5.00,  'unit':'ks'},
    {'id':'amber_polsh','name':'Jantar (broušený)',        'category':'Materiály',        'price_gros':15.00, 'unit':'ks'},
    {'id':'pitch',      'name':'Smůla / dehet',            'category':'Materiály',        'price_gros':0.15,  'unit':'kg'},
    {'id':'wax',        'name':'Včelí vosk',               'category':'Materiály',        'price_gros':1.20,  'unit':'kg'},
    {'id':'bone',       'name':'Kosti (zpracované)',       'category':'Materiály',        'price_gros':0.10,  'unit':'kg'},

    # Spotřební materiál
    {'id':'torch',      'name':'Pochodeň',                 'category':'Spotřební',        'price_gros':0.03,  'unit':'ks'},
    {'id':'torch_10',   'name':'Pochodně (10 ks)',         'category':'Spotřební',        'price_gros':0.25,  'unit':'10 ks'},
    {'id':'oil_lamp',   'name':'Lampový olej',             'category':'Spotřební',        'price_gros':0.20,  'unit':'džbánek'},
    {'id':'tinder',     'name':'Troud a křesadlo',         'category':'Spotřební',        'price_gros':0.30,  'unit':'sada'},
    {'id':'arrow_iron', 'name':'Šípy železné (10 ks)',     'category':'Spotřební',        'price_gros':1.00,  'unit':'10 ks'},
    {'id':'arrow_bone', 'name':'Šípy kostěné (10 ks)',     'category':'Spotřební',        'price_gros':0.30,  'unit':'10 ks'},
    {'id':'bandage',    'name':'Obvazový hadr',            'category':'Spotřební',        'price_gros':0.05,  'unit':'ks'},
    {'id':'salve',      'name':'Základní mast',            'category':'Spotřební',        'price_gros':0.40,  'unit':'nádobka'},
    {'id':'rations',    'name':'Cestovní zásoby (1 den)',  'category':'Spotřební',        'price_gros':0.15,  'unit':'den/os'},
    {'id':'fodder',     'name':'Krmivo pro koně (1 den)', 'category':'Spotřební',        'price_gros':0.10,  'unit':'den'},
    {'id':'soap',       'name':'Louh / mýdlo',             'category':'Spotřební',        'price_gros':0.08,  'unit':'ks'},
    {'id':'quill',      'name':'Pero a inkoust',           'category':'Spotřební',        'price_gros':0.50,  'unit':'sada'},
    {'id':'parchment',  'name':'Pergamen (list)',          'category':'Spotřební',        'price_gros':1.00,  'unit':'list'},
    {'id':'string_bow', 'name':'Tětivy (5 ks)',            'category':'Spotřební',        'price_gros':0.50,  'unit':'5 ks'},
    {'id':'poison_weak','name':'Jed slabý (omráčení)',    'category':'Spotřební',        'price_gros':8.00,  'unit':'dávka'},

    # Magické propriety
    {'id':'herb_peat',  'name':'Rašelinový dráp',         'category':'Magie & byliny',   'price_gros':3.00,  'unit':'svazek'},
    {'id':'herb_oak',   'name':'Dubové slzy (míza)',       'category':'Magie & byliny',   'price_gros':8.00,  'unit':'nádobka'},
    {'id':'herb_coal',  'name':'Uhelný květ',              'category':'Magie & byliny',   'price_gros':5.00,  'unit':'svazek'},
    {'id':'herb_wrmwd', 'name':'Stříbrný pelyněk',        'category':'Magie & byliny',   'price_gros':4.00,  'unit':'svazek'},
    {'id':'herb_mistl', 'name':'Mohylové jmelí',           'category':'Magie & byliny',   'price_gros':12.00, 'unit':'svazek'},
    {'id':'herb_moss',  'name':'Vrbový jantarián',         'category':'Magie & byliny',   'price_gros':6.00,  'unit':'nádobka'},
    {'id':'skull_anim', 'name':'Zvířecí lebka (rituál)',  'category':'Magie & byliny',   'price_gros':2.00,  'unit':'ks'},
    {'id':'blood_vial', 'name':'Krev (dávka — zvířecí)',  'category':'Magie & byliny',   'price_gros':1.50,  'unit':'vial'},
    {'id':'iron_avar',  'name':'Avarský kov (úlomek)',    'category':'Magie & byliny',   'price_gros':20.00, 'unit':'ks'},
    {'id':'runestone',  'name':'Runový kámen (prostý)',   'category':'Magie & byliny',   'price_gros':10.00, 'unit':'ks'},
    {'id':'charm_bone', 'name':'Kostěný amulet',          'category':'Magie & byliny',   'price_gros':5.00,  'unit':'ks'},
    {'id':'incense',    'name':'Kadidlo (kouř pro rituál)','category':'Magie & byliny',  'price_gros':3.00,  'unit':'ks'},
    {'id':'candle_blk', 'name':'Černá svíčka (rituální)', 'category':'Magie & byliny',   'price_gros':1.50,  'unit':'ks'},
    {'id':'water_dead', 'name':'Voda z Mrtvého pramene',  'category':'Magie & byliny',   'price_gros':25.00, 'unit':'nádobka'},
    {'id':'wolf_tooth', 'name':'Vlčí tesák',              'category':'Magie & byliny',   'price_gros':4.00,  'unit':'ks'},
    {'id':'draugr_frag','name':'Úlomek Draugrovy výzbroje','category':'Magie & byliny',  'price_gros':40.00, 'unit':'ks'},
]


def campaign():
    return session.get('campaign')

def _econ_path(camp):
    return os.path.join(campaign_dir(camp), 'economy.json')

def get_economy(camp):
    path = _econ_path(camp)
    if not os.path.exists(path):
        return {'items': [dict(i) for i in DEFAULT_ITEMS], 'availability': {}}
    data = json.load(open(path, encoding='utf-8'))
    existing_ids = {item['id'] for item in data.get('items', [])}
    for default in DEFAULT_ITEMS:
        if default['id'] not in existing_ids:
            data.setdefault('items', []).append(dict(default))
    return data

def save_economy(camp, data):
    path = _econ_path(camp)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@economy.before_request
def require_campaign():
    if not campaign():
        return redirect(url_for('main.index'))

@economy.route('/')
def index():
    econ = get_economy(campaign())
    all_locs = list_entities(campaign(), 'locations')
    locations = sorted(all_locs, key=lambda l: l['name'])
    # Group items by category preserving order
    grouped = {cat: [] for cat in CATEGORIES}
    for item in econ['items']:
        cat = item.get('category', 'Ostatní')
        grouped.setdefault(cat, []).append(item)
    # Remove empty categories
    grouped = {k: v for k, v in grouped.items() if v}
    return render_template('economy.html',
                           grouped=grouped,
                           availability=econ.get('availability', {}),
                           locations=locations,
                           tiers=TIERS,
                           gros=GROŠ,
                           campaign=campaign())

@economy.route('/item/add', methods=['POST'])
def item_add():
    econ = get_economy(campaign())
    name = request.form.get('name', '').strip()
    if not name:
        return redirect(url_for('economy.index'))
    item = {
        'id':        uuid.uuid4().hex[:8],
        'name':      name,
        'category':  request.form.get('category', 'Ostatní'),
        'price_gros': float(request.form.get('price_gros', 0) or 0),
        'unit':      request.form.get('unit', 'ks'),
    }
    econ['items'].append(item)
    save_economy(campaign(), econ)
    return redirect(url_for('economy.index'))

@economy.route('/item/<item_id>/delete', methods=['POST'])
def item_delete(item_id):
    econ = get_economy(campaign())
    econ['items'] = [i for i in econ['items'] if i['id'] != item_id]
    econ['availability'].pop(item_id, None)
    save_economy(campaign(), econ)
    return redirect(url_for('economy.index'))

@economy.route('/item/<item_id>/price', methods=['POST'])
def item_price(item_id):
    econ = get_economy(campaign())
    for item in econ['items']:
        if item['id'] == item_id:
            item['price_gros'] = float(request.form.get('price_gros', item['price_gros']) or 0)
            break
    save_economy(campaign(), econ)
    return jsonify({'ok': True})

@economy.route('/availability/<item_id>/<loc_slug>', methods=['POST'])
def set_availability(item_id, loc_slug):
    econ = get_economy(campaign())
    tier = request.form.get('tier', '')
    custom_mult = request.form.get('multiplier', '')
    avail = econ.setdefault('availability', {}).setdefault(item_id, {})
    if tier:
        avail[loc_slug] = {
            'tier': tier,
            'multiplier': float(custom_mult) if custom_mult else None,
        }
    else:
        avail.pop(loc_slug, None)
    save_economy(campaign(), econ)
    return jsonify({'ok': True})
