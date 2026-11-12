"""Genera las páginas de las iglesias hijas de Camino al Cielo.

Lee _sedes/sedes.json y escribe:
  - /<slug>/index.html de cada iglesia (desde _sedes/plantilla.html)
  - la lista «Nuestras iglesias» de index.html (entre <!-- iglesias:inicio --> y <!-- iglesias:fin -->)

Uso (desde cualquier carpeta):  python _sedes/hacer_sedes.py
No toca nada más del sitio. Después: revisar en la vista previa, commit y push (con el OK de Luis).
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent.parent
SEDES = RAIZ / '_sedes'
DOMINIO = 'https://caminoalcielo714.org'
DURACION_MIN = 120  # duración de cada culto (para "en culto ahora" y el horario de Google)

DIAS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']
DIAS_EN = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
CONTEO = {1: 'Un culto', 2: 'Dos cultos', 3: 'Tres cultos', 4: 'Cuatro cultos', 5: 'Cinco cultos',
          6: 'Seis cultos', 7: 'Siete cultos', 8: 'Ocho cultos'}

e = html.escape  # escapa & < > " '


def hora(c):
    return f"{c['h'] % 12 or 12}:{c['m']:02d} {'a. m.' if c['h'] < 12 else 'p. m.'}"


def y_lista(cosas):
    cosas = list(cosas)
    return cosas[0] if len(cosas) == 1 else ', '.join(cosas[:-1]) + ' y ' + cosas[-1]


def resumen(cultos, sep=' · '):
    """'Domingo 9:30 a. m. · martes, jueves y viernes 7:00 p. m.' (días agrupados por hora, en orden)."""
    grupos = {}
    for c in cultos:
        grupos.setdefault(hora(c), [])
        if DIAS[c['dia']] not in grupos[hora(c)]:
            grupos[hora(c)].append(DIAS[c['dia']])
    partes = [f'{y_lista(dias)} {h}' for h, dias in grupos.items()]
    texto = sep.join(partes)
    return texto[0].upper() + texto[1:]


def whatsapp_pantalla(num):
    local = num[2:] if num.startswith('57') and len(num) == 12 else num
    return f'{local[:3]} {local[3:6]} {local[6:]}' if len(local) == 10 else local


def wa(num, texto):
    return f'https://wa.me/{num}?text={quote(texto)}'


def json_en_script(obj):
    # dentro de <script> no puede aparecer "</": se escapa para que el bloque no se corte
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def pagina(s, plantilla):
    url = f"{DOMINIO}/{s['slug']}/"
    barrio, ciudad = s['barrio'], s['ciudad']
    cultos = s['cultos']
    pastores = s.get('pastores', [])
    pastores_frase = y_lista(f"{'el' if p['titulo'] == 'pastor' else 'la'} {p['titulo']} {p['nombre']}" for p in pastores)
    pastores_frase = pastores_frase[0].upper() + pastores_frase[1:] if pastores_frase else 'Los pastores'
    pastores_corto = 'Pastores ' + y_lista(p['nombre'] for p in pastores) if pastores else ''
    mensajes = {
        'general': f'Hola, vi la página de la iglesia Camino al Cielo del barrio {barrio} y quiero más información.',
        'visita': f'Hola, quiero visitar la iglesia Camino al Cielo del barrio {barrio}. ¿Me ayudan a llegar?',
        'oracion': 'Hola, quiero pedir oración por ',
        'pastores': 'Hola, quiero hablar con los pastores.',
    }
    lat, lon = (x.strip() for x in s['coord'].split(','))
    mapa = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"

    filas = []
    for c in cultos:
        filas.append(f'          <div class="fila" role="listitem"><span class="dia">{e(DIAS[c["dia"]].capitalize())}</span>'
                     f'<span class="nombre">{e(c["nombre"])}</span><span class="hora">{e(hora(c))}</span></div>')

    def cierre(c):
        t = c['h'] * 60 + c['m'] + DURACION_MIN
        return f'{t // 60 % 24:02d}:{t % 60:02d}'

    jsonld = {
        '@context': 'https://schema.org',
        '@type': 'Church',
        '@id': f'{url}#iglesia',
        'name': f'Iglesia Cristiana Camino al Cielo · Barrio {barrio}',
        'url': url,
        'logo': f'{DOMINIO}/img/sello.svg',
        'telephone': '+' + s['whatsapp'],
        'address': {'@type': 'PostalAddress', 'streetAddress': f"{s['direccion']}, barrio {barrio}",
                    'addressLocality': ciudad, 'addressRegion': s['departamento'], 'addressCountry': 'CO'},
        'geo': {'@type': 'GeoCoordinates', 'latitude': float(lat), 'longitude': float(lon)},
        'openingHoursSpecification': [
            {'@type': 'OpeningHoursSpecification', 'dayOfWeek': DIAS_EN[c['dia']],
             'opens': f"{c['h']:02d}:{c['m']:02d}", 'closes': cierre(c)} for c in cultos],
        'parentOrganization': {'@id': f'{DOMINIO}/#iglesia'},
    }
    if pastores:
        jsonld['employee'] = [{'@type': 'Person', 'name': p['nombre'], 'jobTitle': p['titulo'].capitalize()} for p in pastores]
    if s.get('facebook'):
        jsonld['sameAs'] = [s['facebook']['url']]

    datos = {'whatsapp': s['whatsapp'], 'mensajes': mensajes, 'coord': f'{lat},{lon}', 'mapa': mapa,
             'cultos': cultos, 'duracionMin': DURACION_MIN}

    fb = s.get('facebook')
    facebook_boton = (f'<a class="btn btn-line" href="{e(fb["url"])}" target="_blank" rel="noopener">Facebook del {e(fb["texto"][0].lower() + fb["texto"][1:])}</a>'
                      if fb else '')
    facebook_dato = (f'<dt>Facebook</dt><dd><a href="{e(fb["url"])}" target="_blank" rel="noopener">{e(fb["texto"])}</a></dd>'
                     if fb else '')
    mapa_nota = (f'<p class="nota">El punto del mapa es aproximado: la iglesia queda {e(s["referencia"])}. '
                 f'Si te pierdes, escríbenos por WhatsApp.</p>' if s.get('coord_aproximada') else '')

    descripcion = (f"Iglesia Cristiana Camino al Cielo en el barrio {barrio}, {ciudad}. "
                   f"{pastores_corto + '. ' if pastores_corto else ''}Cultos: {resumen(cultos, '; ').rstrip('.')}. {s['direccion']}.")
    valores = {
        'titulo': f'Camino al Cielo · Barrio {barrio}, {ciudad} | Cultos y horarios',
        'descripcion': descripcion,
        'url': url,
        'og_titulo': f'Iglesia Cristiana Camino al Cielo · Barrio {barrio}',
        'og_descripcion': f"Te esperamos: {resumen(cultos, '; ').rstrip('.')}. {s['direccion']}, barrio {barrio}, {ciudad}.",
        'barrio': barrio, 'ciudad': ciudad, 'departamento': s['departamento'], 'direccion': s['direccion'],
        'resumen': resumen(cultos),
        'conteo': CONTEO.get(len(cultos), f'{len(cultos)} cultos'),
        'pastores_frase': pastores_frase,
        'whatsapp_pantalla': whatsapp_pantalla(s['whatsapp']),
        'mapa': mapa,
        'wa_general': wa(s['whatsapp'], mensajes['general']),
        'wa_visita': wa(s['whatsapp'], mensajes['visita']),
        'wa_oracion': wa(s['whatsapp'], mensajes['oracion']),
        'wa_pastores': wa(s['whatsapp'], mensajes['pastores']),
    }
    # todo lo de texto va escapado; los bloques ya armados (HTML/JSON) entran tal cual
    salida = plantilla
    for k, v in valores.items():
        salida = salida.replace('{{' + k + '}}', e(v))
    crudos = {
        'filas': '\n'.join(filas),
        'facebook_boton': facebook_boton,
        'facebook_dato': facebook_dato,
        'mapa_nota': mapa_nota,
        'jsonld': json_en_script(jsonld),
        'datos': json_en_script(datos),
    }
    for k, v in crudos.items():
        salida = salida.replace('{{' + k + '}}', v)
    sobrantes = re.findall(r'\{\{\w+\}\}', salida)
    if sobrantes:
        sys.exit(f'Faltan valores en la plantilla: {sorted(set(sobrantes))}')
    return salida


def tarjeta(s):
    pastores = s.get('pastores', [])
    spans = f'<span class="nowrap">{e(s["direccion"])}</span>'
    if pastores:
        spans += f'<span>{e("Pastores " + y_lista(p["nombre"] for p in pastores))}</span>'
    spans += f'<span>{e(resumen(s["cultos"]))}</span>'
    return (f'        <li><a href="/{e(s["slug"])}/"><small>{e(s["ciudad"])}</small><b>Barrio {e(s["barrio"])}</b>'
            f'{spans}<em>Horarios y cómo llegar →</em></a></li>')


def main():
    datos = json.loads((SEDES / 'sedes.json').read_text(encoding='utf-8'))
    sedes = datos['sedes']
    plantilla = (SEDES / 'plantilla.html').read_text(encoding='utf-8')
    slugs = set()
    for s in sedes:
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', s['slug']) or s['slug'] in slugs or s['slug'] in {'img', '_sedes'}:
            sys.exit(f"Slug inválido o repetido: {s['slug']!r} (solo minúsculas, números y guiones)")
        if not re.fullmatch(r'57\d{10}', s['whatsapp']):
            sys.exit(f"WhatsApp de {s['slug']} debe ser 57 + 10 dígitos, sin espacios: {s['whatsapp']!r}")
        slugs.add(s['slug'])
        destino = RAIZ / s['slug'] / 'index.html'
        destino.parent.mkdir(exist_ok=True)
        destino.write_text(pagina(s, plantilla), encoding='utf-8', newline='\n')
        print(f'ok  /{s["slug"]}/')

    indice = RAIZ / 'index.html'
    texto = indice.read_text(encoding='utf-8')
    patron = re.compile(r'(<!-- iglesias:inicio -->).*?(<!-- iglesias:fin -->)', re.S)
    if not patron.search(texto):
        sys.exit('index.html no tiene las marcas <!-- iglesias:inicio --> / <!-- iglesias:fin -->')
    lista = '\n'.join(tarjeta(s) for s in sedes)
    texto = patron.sub(lambda m: m.group(1) + '\n' + lista + '\n' + m.group(2), texto, count=1)
    indice.write_text(texto, encoding='utf-8', newline='\n')
    print(f'ok  index.html: {len(sedes)} iglesia(s) en "Nuestras iglesias"')

    # aviso de carpetas generadas antes que ya no están en la lista (no se borran solas)
    for d in RAIZ.iterdir():
        f = d / 'index.html'
        if d.is_dir() and d.name not in slugs and f.exists() and 'hacer_sedes.py' in f.read_text(encoding='utf-8')[:600]:
            print(f'OJO /{d.name}/ ya no está en sedes.json: bórrala si la iglesia salió de la lista')


if __name__ == '__main__':
    main()
