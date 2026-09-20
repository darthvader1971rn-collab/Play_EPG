import requests
import datetime
import time
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

API_BASE = 'https://playnow.pl/api/v2/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/115.0',
    'Origin': 'https://playnow.pl',
    'Referer': 'https://playnow.pl/',
    'Sync-With-Server': 'true'
}

# SŁOWNIK MAPUJĄCY: "Nazwa Play NOW": "ID EPG Onet"
MAPOWANIE_ONET = {
    "TVP1": "TVP 1",
    "TVP2": "TVP 2",
    "HBO2 ": "HBO 2",
    "CANAL+ Premium ": "Canal+ Premium",
    # Dodaj tutaj kolejne kanały zgodnie z ID z Twojej innej listy M3U
}

def format_xmltv_time(iso_time_str):
    try:
        dt = datetime.datetime.strptime(iso_time_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y%m%d%H%M%S +0200')
    except Exception:
        return ""

def main():
    tv = Element('tv', {'generator-info-name': 'PlayNOW EPG GitHub Actions'})
    
    resp_ch = requests.get(API_BASE + 'products/lives', headers=HEADERS, params={'platform': 'BROWSER', 'tenant': 'TV_POINTS'})
    channels = [c for c in resp_ch.json() if c.get('liveType') == 'LIVE']
    print(f"Pobrano {len(channels)} kanałów.")

    now = datetime.datetime.now()
    
    for ch in channels:
        ch_id = str(ch['id'])
        oryginalna_nazwa = ch['title']
        
        # Pobranie nazwy z mapowania (jeśli brak w słowniku, użyje oryginalnej)
        xmltv_id = MAPOWANIE_ONET.get(oryginalna_nazwa, oryginalna_nazwa)
        
        ch_logo = ch.get('logos', {}).get('L1x1_cl', [{}])[0].get('url', '')
        if ch_logo.startswith('//'):
            ch_logo = 'https:' + ch_logo

        # Tworzenie tagu <channel id="ZMAPOWANE_ID">
        channel_elem = SubElement(tv, 'channel', {'id': xmltv_id})
        display_name = SubElement(channel_elem, 'display-name')
        display_name.text = oryginalna_nazwa
        if ch_logo:
            SubElement(channel_elem, 'icon', {'src': ch_logo})
            
        print(f"Pobieranie EPG: {oryginalna_nazwa} (ID: {xmltv_id})...")

        for day_offset in range(-7, 8):
            target_date = now + datetime.timedelta(days=day_offset)
            start_of_day = target_date.replace(hour=0, minute=0, second=0).strftime('%Y-%m-%dT%H:%M+0200')
            end_of_day = target_date.replace(hour=23, minute=59, second=59).strftime('%Y-%m-%dT%H:%M+0200')
            
            params_epg = {
                'liveId[]': ch_id,
                'since': start_of_day,
                'till': end_of_day,
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
                            
                        # Przypisanie zmapowanego ID do audycji
                        prog_elem = SubElement(tv, 'programme', {
                            'start': start_time,
                            'stop': stop_time,
                            'channel': xmltv_id
                        })
                        
                        title = SubElement(prog_elem, 'title')
                        title.text = prog.get('title', 'Brak tytułu')
                        
                        desc_text = prog.get('description', '')
                        if desc_text:
                            desc = SubElement(prog_elem, 'desc')
                            desc.text = desc_text
                            
                        genres = prog.get('genres', [])
                        if genres:
                            category = SubElement(prog_elem, 'category')
                            category.text = genres[0].get('name', '')
                            
                        season = prog.get('season')
                        episode = prog.get('episode')
                        if season is not None or episode is not None:
                            ep_num = SubElement(prog_elem, 'episode-num', {'system': 'onscreen'})
                            s_str = f"S{season}" if season is not None else ""
                            e_str = f"E{episode}" if episode is not None else ""
                            ep_num.text = f"{s_str}{e_str}"
            except Exception:
                pass
            
            time.sleep(0.05)

    xml_str = tostring(tv, 'utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")
    
    with open('epg.xml', 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
        
    print("Wygenerowano pełny plik epg.xml z uniwersalnym mapowaniem.")

if __name__ == '__main__':
    main()