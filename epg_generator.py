import requests
import datetime
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
from xml.dom import minidom

API_BASE = 'https://playnow.pl/api/v2/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/115.0',
    'Origin': 'https://playnow.pl',
    'Referer': 'https://playnow.pl/'
}

def format_xmltv_time(iso_time_str):
    # API zwraca czas np. '2026-09-20 10:00:00'
    # Przerabiamy na format XMLTV: '20260920100000 +0200'
    try:
        dt = datetime.datetime.strptime(iso_time_str, '%Y-%m-%d %H:%M:%S')
        # Dodajemy stałą strefę czasową dla Polski (uproszczenie, +0200 dla okresu letniego, +0100 zimą)
        # Dla pewności odtwarzaczy IPTV najlepiej podać UTC lub stały offset
        return dt.strftime('%Y%m%d%H%M%S +0200')
    except Exception:
        return ""

def main():
    tv = Element('tv', {'generator-info-name': 'PlayNOW EPG GitHub Actions'})
    
    # 1. Pobieranie kanałów
    resp_ch = requests.get(API_BASE + 'products/lives', headers=HEADERS, params={'platform': 'BROWSER', 'tenant': 'TV_POINTS'})
    channels = [c for c in resp_ch.json() if c.get('liveType') == 'LIVE']
    
    print(f"Pobrano {len(channels)} kanałów.")

    # 2. Zakres czasu: -7 do +7 dni
    now = datetime.datetime.now()
    since = (now - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M+0200')
    till = (now + datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M+0200')

    # 3. Przetwarzanie kanałów
    for ch in channels:
        ch_id = str(ch['id'])
        ch_name = ch['title']
        ch_logo = ch.get('logos', {}).get('L1x1_cl', [{}])[0].get('url', '')
        if ch_logo.startswith('//'):
            ch_logo = 'https:' + ch_logo

        # Element XML <channel>
        channel_elem = SubElement(tv, 'channel', {'id': ch_name})
        display_name = SubElement(channel_elem, 'display-name')
        display_name.text = ch_name
        if ch_logo:
            SubElement(channel_elem, 'icon', {'src': ch_logo})

        # Pobieranie EPG dla danego kanału
        params_epg = {
            'liveId[]': ch_id,
            'since': since,
            'till': till,
            'platform': 'BROWSER',
            'tenant': 'TV_POINTS'
        }
        
        try:
            resp_epg = requests.get(API_BASE + 'products/lives/epgs', headers=HEADERS, params=params_epg, timeout=10)
            epg_data = resp_epg.json()
            
            if isinstance(epg_data, list):
                for prog in epg_data:
                    start_time = format_xmltv_time(prog.get('since', ''))
                    stop_time = format_xmltv_time(prog.get('till', ''))
                    
                    if not start_time or not stop_time:
                        continue
                        
                    prog_elem = SubElement(tv, 'programme', {
                        'start': start_time,
                        'stop': stop_time,
                        'channel': ch_name
                    })
                    
                    title = SubElement(prog_elem, 'title')
                    title.text = prog.get('title', 'Brak tytułu')
                    
                    desc_text = prog.get('description', '')
                    if desc_text:
                        desc = SubElement(prog_elem, 'desc')
                        desc.text = desc_text
                        
                    # Dodawanie kategorii/gatunku
                    genres = prog.get('genres', [])
                    if genres:
                        category = SubElement(prog_elem, 'category')
                        category.text = genres[0].get('name', '')
                        
                    # Sezon i odcinek
                    season = prog.get('season')
                    episode = prog.get('episode')
                    if season is not None or episode is not None:
                        ep_num = SubElement(prog_elem, 'episode-num', {'system': 'onscreen'})
                        s_str = f"S{season}" if season is not None else ""
                        e_str = f"E{episode}" if episode is not None else ""
                        ep_num.text = f"{s_str}{e_str}"
                        
        except Exception as e:
            print(f"Błąd dla kanału {ch_name}: {e}")

    # 4. Zapis do pliku
    xml_str = tostring(tv, 'utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")
    
    with open('epg.xml', 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
        
    print("Wygenerowano plik epg.xml")

if __name__ == '__main__':
    main()