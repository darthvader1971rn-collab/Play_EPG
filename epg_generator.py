import os
import requests
import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

API_BASE = 'https://playnow.pl/api/v2/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/115.0',
    'Origin': 'https://playnow.pl',
    'Referer': 'https://playnow.pl/',
    'Sync-With-Server': 'true'
}

# SŁOWNIK MAPUJĄCY KANAŁY
# Klucz to oryginalna nazwa z Play NOW.
# "id" to uniwersalny atrybut kanału.
# "names" to lista wszystkich możliwych wariantów nazw, które wypluje skrypt.
MAPOWANIE = {
    # === KANAŁY OGÓLNE I INFORMACYJNE ===
    "TVP1": {"id": "TVP1HD.pl", "names": ["TVP1", "TVP 1", "TVP 1 HD", "TVP1 HD", "PL: TVP 1", "TVP1HD.pl"]},
    "TVP2": {"id": "TVP2HD.pl", "names": ["TVP2", "TVP 2", "TVP 2 HD", "TVP2 HD", "PL: TVP 2", "TVP2HD.pl"]},
    "TVN": {"id": "TVNHD.pl", "names": ["TVN", "TVN HD", "PL: TVN", "TVNHD.pl"]},
    "TVN 7 HD": {"id": "TVN7HD.pl", "names": ["TVN 7 HD", "TVN 7", "TVN7", "TVN7 HD", "PL: TVN 7", "TVN7HD.pl"]},
    "Polsat": {"id": "PolsatHD.pl", "names": ["Polsat", "Polsat HD", "PL: Polsat", "PolsatHD.pl"]},
    "TV4": {"id": "TV4HD.pl", "names": ["TV4", "TV 4", "TV4 HD", "TV 4 HD", "PL: TV 4", "TV4HD.pl"]},
    "TV Puls": {"id": "TVPulsHD.pl", "names": ["TV Puls", "TV Puls HD", "Puls", "Puls HD", "PL: TV Puls", "TVPulsHD.pl"]},
    "Puls 2": {"id": "Puls2HD.pl", "names": ["Puls 2", "Puls 2 HD", "Puls2", "PL: Puls 2", "Puls2HD.pl"]},
    "TTV HD": {"id": "TTVHD.pl", "names": ["TTV HD", "TTV", "TTV FHD", "PL: TTV", "TTVHD.pl"]},
    "METRO HD": {"id": "MetroHD.pl", "names": ["METRO HD", "Metro", "Metro TV", "Metro HD", "PL: Metro", "MetroHD.pl"]},
    "TV 6": {"id": "TV6HD.pl", "names": ["TV 6", "TV6", "TV6 HD", "TV 6 HD", "PL: TV 6", "TV6HD.pl"]},
    "Fokus TV": {"id": "FokusTVHD.pl", "names": ["Fokus TV", "Fokus TV HD", "PL: Fokus TV", "FokusTVHD.pl"]},
    "Nowa TV": {"id": "NowaTVHD.pl", "names": ["Nowa TV", "Nowa TV HD", "PL: Nowa TV", "NowaTVHD.pl"]},
    "Super POLSAT": {"id": "SuperPolsatHD.pl", "names": ["Super POLSAT", "Super Polsat", "Super Polsat HD", "PL: Super Polsat"]},
    "WP HD": {"id": "WPHD.pl", "names": ["WP HD", "WP", "Telewizja WP", "PL: WP", "WPHD.pl"]},
    "ZOOM": {"id": "ZoomTVHD.pl", "names": ["ZOOM", "Zoom TV", "Zoom TV HD", "PL: Zoom TV", "ZoomTVHD.pl"]},
    "Antena HD": {"id": "AntenaHD.pl", "names": ["Antena HD", "Antena", "PL: Antena", "AntenaHD.pl"]},
    "TV Trwam": {"id": "TVTrwam.pl", "names": ["TV Trwam", "TV Trwam HD", "PL: TV Trwam", "TVTrwam.pl"]},
    "Polonia1": {"id": "Polonia1.pl", "names": ["Polonia1", "Polonia 1", "Polonia 1 HD", "PL: Polonia 1"]},
    "Tele5": {"id": "Tele5HD.pl", "names": ["Tele5", "Tele 5", "Tele 5 HD", "PL: Tele 5", "Tele5HD.pl"]},
    "TVC HD": {"id": "TVCHD.pl", "names": ["TVC HD", "TVC", "PL: TVC", "TVCHD.pl"]},
    "TVC Super": {"id": "TVCSuper.pl", "names": ["TVC Super", "PL: TVC Super", "TVCSuper.pl"]},
    "ViDoc TV HD": {"id": "ViDocTVHD.pl", "names": ["ViDoc TV HD", "ViDoc TV", "PL: ViDoc TV"]},
    "Home TV HD": {"id": "HomeTVHD.pl", "names": ["Home TV HD", "HOME TV HD", "Home TV", "PL: Home TV"]},
    "TV Okazje": {"id": "TVOkazje.pl", "names": ["TV Okazje", "PL: TV Okazje"]},

    "TVN24": {"id": "TVN24HD.pl", "names": ["TVN24", "TVN 24", "TVN 24 HD", "PL: TVN 24", "TVN24HD.pl"]},
    "TVN24 BIS": {"id": "TVN24BisHD.pl", "names": ["TVN24 BIS", "TVN 24 BiS", "TVN 24 BiS HD", "PL: TVN 24 BiS"]},
    "POLSAT News": {"id": "PolsatNewsHD.pl", "names": ["POLSAT News", "Polsat News", "Polsat News HD", "PL: Polsat News"]},
    "POLSAT News 2": {"id": "PolsatNews2.pl", "names": ["POLSAT News 2", "Polsat News 2", "PL: Polsat News 2"]},
    "Wydarzenia24": {"id": "Wydarzenia24HD.pl", "names": ["Wydarzenia24", "Wydarzenia 24", "Wydarzenia 24 HD"]},
    "TVP Info": {"id": "TVPInfoHD.pl", "names": ["TVP Info", "TVP Info HD", "PL: TVP Info", "TVPInfoHD.pl"]},
    "wPolsce24": {"id": "wPolsce24HD.pl", "names": ["wPolsce24", "wPolsce24 HD", "PL: wPolsce24", "wPolsce24HD.pl"]},
    "TV Republika HD": {"id": "TVRepublikaHD.pl", "names": ["TV Republika HD", "TV Republika", "PL: TV Republika"]},
    "Biznes24": {"id": "Biznes24HD.pl", "names": ["Biznes24", "Biznes 24", "PL: Biznes24", "Biznes24HD.pl"]},
    "News24": {"id": "News24.pl", "names": ["News24", "News 24", "PL: News 24"]},
    "Polsat News Polityka": {"id": "PolsatNewsPolityka.pl", "names": ["Polsat News Polityka", "Polsat News Polityka HD"]},
    "TV Biznesowa": {"id": "TVBiznesowa.pl", "names": ["TV Biznesowa"]},

    # === FILMY I SERIALE ===
    "HBO": {"id": "HBOHD.pl", "names": ["HBO", "HBO HD", "PL: HBO", "HBOHD.pl"]},
    "HBO2 ": {"id": "HBO2HD.pl", "names": ["HBO2 ", "HBO 2", "HBO2", "HBO 2 HD", "PL: HBO 2", "HBO2HD.pl"]},
    "HBO3": {"id": "HBO3HD.pl", "names": ["HBO3", "HBO 3", "HBO 3 HD", "PL: HBO 3", "HBO3HD.pl"]},
    "Cinemax HD": {"id": "CinemaxHD.pl", "names": ["Cinemax HD", "Cinemax", "PL: Cinemax", "CinemaxHD.pl"]},
    "Cinemax2 HD": {"id": "Cinemax2HD.pl", "names": ["Cinemax2 HD", "Cinemax 2", "Cinemax 2 HD", "PL: Cinemax 2"]},
    "SkyShowtime 1": {"id": "SkyShowtime1HD.pl", "names": ["SkyShowtime 1", "SkyShowtime 1 HD", "PL: SkyShowtime 1"]},
    "SkyShowtime 2": {"id": "SkyShowtime2HD.pl", "names": ["SkyShowtime 2", "SkyShowtime 2 HD", "PL: SkyShowtime 2"]},
    
    "CANAL+ Premium ": {"id": "CanalPlusPremiumHD.pl", "names": ["CANAL+ Premium ", "Canal+ Premium", "Canal+ Premium HD"]},
    "CANAL+ 1 HD": {"id": "CanalPlus1HD.pl", "names": ["CANAL+ 1 HD", "Canal+ 1", "Canal+ 1 HD", "PL: Canal+ 1"]},
    "CANAL+ Film HD": {"id": "CanalPlusFilmHD.pl", "names": ["CANAL+ Film HD", "Canal+ Film", "Canal+ Film HD"]},
    "CANAL+ Seriale HD": {"id": "CanalPlusSerialeHD.pl", "names": ["CANAL+ Seriale HD", "Canal+ Seriale", "Canal+ Seriale HD"]},
    "CANAL+ 360": {"id": "CanalPlus360HD.pl", "names": ["CANAL+ 360", "Canal+ 360 HD", "PL: Canal+ 360"]},
    "Canal+ 4K Ultra HD": {"id": "CanalPlus4K.pl", "names": ["Canal+ 4K Ultra HD", "Canal+ 4K"]},
    
    "FX HD": {"id": "FoxHD.pl", "names": ["FX HD", "FX", "Fox", "Fox HD", "PL: FX", "PL: Fox"]},
    "FX Comedy HD": {"id": "FoxComedyHD.pl", "names": ["FX Comedy HD", "FX Comedy", "Fox Comedy", "Fox Comedy HD"]},
    "Paramount Network": {"id": "ParamountNetworkHD.pl", "names": ["Paramount Network", "Paramount Channel", "Paramount Channel HD"]},
    "Ale Kino+": {"id": "AleKinoPlusHD.pl", "names": ["Ale Kino+", "Ale Kino", "Ale Kino+ HD", "PL: Ale Kino+"]},
    "Comedy Central": {"id": "ComedyCentralHD.pl", "names": ["Comedy Central", "Comedy Central HD", "PL: Comedy Central"]},
    "Polsat Comedy Central Extra": {"id": "PolsatComedyCentralExtraHD.pl", "names": ["Polsat Comedy Central Extra", "Comedy Central Family"]},
    "AMC": {"id": "AMCHD.pl", "names": ["AMC", "AMC HD", "PL: AMC", "AMCHD.pl"]},
    "Warner TV": {"id": "WarnerTVHD.pl", "names": ["Warner TV", "Warner TV HD", "PL: Warner TV"]},
    "TVN Fabuła HD": {"id": "TVNFabulaHD.pl", "names": ["TVN Fabuła HD", "TVN Fabuła", "PL: TVN Fabuła"]},
    "Viasat Epic Drama": {"id": "EpicDramaHD.pl", "names": ["Viasat Epic Drama", "Epic Drama", "Epic Drama HD"]},
    "Stopklatka TV": {"id": "StopklatkaTVHD.pl", "names": ["Stopklatka TV", "Stopklatka", "Stopklatka TV HD", "PL: Stopklatka"]},
    "AXN": {"id": "AXNHD.pl", "names": ["AXN", "AXN HD", "PL: AXN", "AXNHD.pl"]},
    "AXN Black": {"id": "AXNBlack.pl", "names": ["AXN Black", "AXN Black HD", "PL: AXN Black"]},
    "AXN Spin": {"id": "AXNSpinHD.pl", "names": ["AXN Spin", "AXN Spin HD", "PL: AXN Spin"]},
    "AXN White": {"id": "AXNWhite.pl", "names": ["AXN White", "AXN White HD", "PL: AXN White"]},
    "POLSAT 2": {"id": "Polsat2HD.pl", "names": ["POLSAT 2", "Polsat 2", "Polsat 2 HD"]},
    "POLSAT Film": {"id": "PolsatFilmHD.pl", "names": ["POLSAT Film", "Polsat Film", "Polsat Film HD"]},
    "POLSAT Seriale": {"id": "PolsatSerialeHD.pl", "names": ["POLSAT Seriale", "Polsat Seriale", "Polsat Seriale HD"]},
    "Kino Polska": {"id": "KinoPolskaHD.pl", "names": ["Kino Polska", "Kino Polska HD", "PL: Kino Polska"]},
    "Kino TV HD": {"id": "KinoTVHD.pl", "names": ["Kino TV HD", "Kino TV", "PL: Kino TV"]},
    "Sundance TV": {"id": "SundanceTVHD.pl", "names": ["Sundance TV", "Sundance TV HD", "Sundance Channel"]},
    "BBC First": {"id": "BBCFirstHD.pl", "names": ["BBC First", "BBC First HD", "PL: BBC First"]},
    "13 Ulica": {"id": "13UlicaHD.pl", "names": ["13 Ulica", "13 Ulica HD", "PL: 13 Ulica"]},
    "SciFi": {"id": "SciFiUniversal.pl", "names": ["SciFi", "Sci Fi", "Sci Fi HD", "PL: Sci Fi"]},
    "Romance.TV": {"id": "RomanceTVHD.pl", "names": ["Romance.TV", "Romance TV", "Romance TV HD"]},
    "NOVELAS+": {"id": "NovelasPlusHD.pl", "names": ["NOVELAS+", "Novelas+", "Novelas+ HD", "Novela TV"]},
    "TVP Seriale": {"id": "TVPSerialeHD.pl", "names": ["TVP Seriale", "TVP Seriale HD", "PL: TVP Seriale"]},
    "KINO PLAY": {"id": "KinoPlay.pl", "names": ["KINO PLAY", "Kino Play"]},
    "Polsat Film 2": {"id": "PolsatFilm2.pl", "names": ["Polsat Film 2"]},
    "Filmax": {"id": "FilmaxHD.pl", "names": ["Filmax", "Filmax HD", "PL: Filmax"]},
    "Short TV": {"id": "ShortTV.pl", "names": ["Short TV"]},
    "CTV Dla Ciebie ": {"id": "CTVDlaCiebie.pl", "names": ["CTV Dla Ciebie ", "CTV Dla Ciebie"]},
    "Bollywood": {"id": "BollywoodHD.pl", "names": ["Bollywood", "Bollywood HD"]},
    "Kabaret TV": {"id": "KabaretTV.pl", "names": ["Kabaret TV"]},
    "FilmBox Premium": {"id": "FilmboxPremium.pl", "names": ["FilmBox Premium"]},
    "FilmBox Extra HD": {"id": "FilmboxExtraHD.pl", "names": ["FilmBox Extra HD", "FilmBox Extra"]},
    "FILMBOX+ Action": {"id": "FilmboxAction.pl", "names": ["FILMBOX+ Action", "FilmBox Action"]},
    "FilmBox Family": {"id": "FilmboxFamily.pl", "names": ["FilmBox Family"]},
    "FilmBox ArtHouse": {"id": "FilmboxArthouse.pl", "names": ["FilmBox ArtHouse"]},
    "FilmBox ArtHouse 2": {"id": "FilmboxArthouse2.pl", "names": ["FilmBox ArtHouse 2"]},
    "FILMBOX+ Hits": {"id": "FilmboxHits.pl", "names": ["FILMBOX+ Hits"]},
    "FILMBOX+ Emotion": {"id": "FilmboxEmotion.pl", "names": ["FILMBOX+ Emotion"]},
    "FILMBOX+ Comedy": {"id": "FilmboxComedy.pl", "names": ["FILMBOX+ Comedy"]},
    "FILMBOX+ Festival": {"id": "FilmboxFestival.pl", "names": ["FILMBOX+ Festival"]},
    "FILMBOX+ One": {"id": "FilmboxOne.pl", "names": ["FILMBOX+ One"]},
    "Film Cafe PL": {"id": "FilmCafe.pl", "names": ["Film Cafe PL", "Film Cafe"]},
    "TOP Movies Rakuten": {"id": "TopMoviesRakuten.pl", "names": ["TOP Movies Rakuten"]},

    # === TVN FAST KANAŁY (VOD) ===
    "TVN Milionerzy": {"id": "TVNMilionerzy.pl", "names": ["TVN Milionerzy"]},
    "TVN Kryminalnie": {"id": "TVNKryminalnie.pl", "names": ["TVN Kryminalnie"]},
    "TVN Telenowele": {"id": "TVNTelenowele.pl", "names": ["TVN Telenowele"]},
    "TVN Czas na Ślub": {"id": "TVNCzasNaSlub.pl", "names": ["TVN Czas na Ślub"]},
    "TVN Prawo i Życie": {"id": "TVNPrawoIZycie.pl", "names": ["TVN Prawo i Życie"]},
    "TVN Rajska Miłość": {"id": "TVNRajskaMilosc.pl", "names": ["TVN Rajska Miłość"]},
    "TVN Talk Show": {"id": "TVNTalkShow.pl", "names": ["TVN Talk Show"]},
    "TVN Pora na Show": {"id": "TVNPoraNaShow.pl", "names": ["TVN Pora na Show"]},
    "TVN Momenty Prawdy": {"id": "TVNMomentyPrawdy.pl", "names": ["TVN Momenty Prawdy"]},
    "TVN Życie Jak w Bajce": {"id": "TVNZycieJakWBajce.pl", "names": ["TVN Życie Jak w Bajce"]},
    "TVN Szpitalne Historie": {"id": "TVNSzpitalneHistorie.pl", "names": ["TVN Szpitalne Historie"]},
    "TVN Szkoła Życia": {"id": "TVNSzkolaZycia.pl", "names": ["TVN Szkoła Życia"]},
    "TVN W Domu": {"id": "TVNWDomu.pl", "names": ["TVN W Domu"]},
    "TVN Usterka": {"id": "TVNUsterka.pl", "names": ["TVN Usterka"]},
    "TVN Rewolucje w Kuchni": {"id": "TVNRewolucjeWKuchni.pl", "names": ["TVN Rewolucje w Kuchni"]},
    "TVN Kulinarne Podróże": {"id": "TVNKulinarnePodroze.pl", "names": ["TVN Kulinarne Podróże"]},
    "TVN Kultowe Seriale": {"id": "TVNKultoweSeriale.pl", "names": ["TVN Kultowe Seriale"]},
    "TVN Patrol": {"id": "TVNPatrol.pl", "names": ["TVN Patrol"]},
    "TVN Moto": {"id": "TVNMoto.pl", "names": ["TVN Moto"]},

    # === DOKUMENT, LIFESTYLE I EDUKACJA ===
    "TVN Style HD": {"id": "TVNStyleHD.pl", "names": ["TVN Style HD", "TVN Style", "PL: TVN Style"]},
    "HGTV HD": {"id": "HGTVHD.pl", "names": ["HGTV HD", "HGTV", "PL: HGTV", "HGTVHD.pl"]},
    "POLSAT Cafe": {"id": "PolsatCafeHD.pl", "names": ["POLSAT Cafe", "Polsat Cafe", "Polsat Café HD"]},
    "TLC HD": {"id": "TLCHD.pl", "names": ["TLC HD", "TLC", "PL: TLC", "TLCHD.pl"]},
    "Discovery Life HD": {"id": "DiscoveryLifeHD.pl", "names": ["Discovery Life HD", "Discovery Life", "PL: Discovery Life"]},
    "CANAL+ KUCHNIA": {"id": "CanalPlusKuchniaHD.pl", "names": ["CANAL+ KUCHNIA", "Canal+ Kuchnia HD", "Canal+ Kuchnia"]},
    "CANAL+ DOMO HD": {"id": "CanalPlusDomoHD.pl", "names": ["CANAL+ DOMO HD", "Canal+ Domo HD", "Canal+ Domo"]},
    "CANAL+ Dokument HD": {"id": "CanalPlusDokumentHD.pl", "names": ["CANAL+ Dokument HD", "Canal+ Dokument", "Canal+ Dokument HD"]},
    "BBC Lifestyle": {"id": "BBCLifestyleHD.pl", "names": ["BBC Lifestyle", "BBC Lifestyle HD", "PL: BBC Lifestyle"]},
    "Food Network HD ": {"id": "FoodNetworkHD.pl", "names": ["Food Network HD ", "Food Network HD", "Food Network"]},
    "TVN Turbo HD": {"id": "TVNTurboHD.pl", "names": ["TVN Turbo HD", "TVN Turbo", "PL: TVN Turbo"]},
    "POLSAT Play": {"id": "PolsatPlayHD.pl", "names": ["POLSAT Play", "Polsat Play", "Polsat Play HD"]},
    "BBC Brit": {"id": "BBCBritHD.pl", "names": ["BBC Brit", "BBC Brit HD", "PL: BBC Brit"]},
    "National Geographic": {"id": "NationalGeographicHD.pl", "names": ["National Geographic", "National Geographic Channel"]},
    "Nat Geo Wild": {"id": "NatGeoWildHD.pl", "names": ["Nat Geo Wild", "National Geographic Wild"]},
    "Nat Geo People HD": {"id": "NatGeoPeopleHD.pl", "names": ["Nat Geo People HD", "Nat Geo People"]},
    "Crime+Investigation Polsat": {"id": "CIPolsat.pl", "names": ["Crime+Investigation Polsat", "CI Polsat"]},
    "Discovery Channel HD": {"id": "DiscoveryChannelHD.pl", "names": ["Discovery Channel HD", "Discovery Channel", "Discovery"]},
    "Discovery Science HD": {"id": "DiscoveryScienceHD.pl", "names": ["Discovery Science HD", "Discovery Science"]},
    "DTX HD": {"id": "DTXHD.pl", "names": ["DTX HD", "DTX", "PL: DTX"]},
    "Animal Planet HD": {"id": "AnimalPlanetHD.pl", "names": ["Animal Planet HD", "Animal Planet"]},
    "HISTORY": {"id": "HistoryHD.pl", "names": ["HISTORY", "History", "History HD"]},
    "H2": {"id": "History2HD.pl", "names": ["H2", "History 2", "History 2 HD"]},
    "Polsat Viasat Explore": {"id": "PolsatViasatExploreHD.pl", "names": ["Polsat Viasat Explore", "Polsat Viasat Explore HD"]},
    "Planete+": {"id": "PlanetePlusHD.pl", "names": ["Planete+", "Planete", "Planete+ HD"]},
    "Polsat Viasat History": {"id": "PolsatViasatHistoryHD.pl", "names": ["Polsat Viasat History", "Polsat Viasat History HD"]},
    "Polsat Viasat Nature": {"id": "PolsatViasatNatureHD.pl", "names": ["Polsat Viasat Nature", "Polsat Viasat Nature HD"]},
    "BBC Earth": {"id": "BBCEarthHD.pl", "names": ["BBC Earth", "BBC Earth HD", "PL: BBC Earth"]},
    "Discovery Historia": {"id": "DiscoveryHistoria.pl", "names": ["Discovery Historia", "Discovery Historia HD"]},
    "Travel Channel HD": {"id": "TravelChannelHD.pl", "names": ["Travel Channel HD", "Travel Channel", "PL: Travel Channel"]},
    "Viasat True Crime": {"id": "ViasatTrueCrime.pl", "names": ["Viasat True Crime", "Viasat True Crime HD"]},
    "POLSAT Doku": {"id": "PolsatDokuHD.pl", "names": ["POLSAT Doku", "Polsat Doku HD", "Polsat Doku"]},
    "ID HD": {"id": "InvestigationDiscoveryHD.pl", "names": ["ID HD", "ID", "Investigation Discovery"]},
    "Polsat Reality": {"id": "PolsatReality.pl", "names": ["Polsat Reality", "Polsat Reality HD", "PL: Polsat Reality"]},
    "DocuBox": {"id": "Docubox.pl", "names": ["DocuBox", "Docubox Polska"]},
    "Polsat X": {"id": "PolsatX.pl", "names": ["Polsat X"]},
    "Stargaze TV": {"id": "StargazeTV.pl", "names": ["Stargaze TV"]},
    "E! Entertainment": {"id": "EEntertainment.pl", "names": ["E! Entertainment"]},
    "STUDIOMED TV": {"id": "StudioMedTV.pl", "names": ["STUDIOMED TV", "StudioMed TV HD", "StudioMed TV"]},
    "Active Family": {"id": "ActiveFamily.pl", "names": ["Active Family"]},
    "Adventure": {"id": "AdventureHD.pl", "names": ["Adventure", "Adventure HD"]},
    "Love Nature 4K": {"id": "LoveNature4K.pl", "names": ["Love Nature 4K"]},
    "Travelxp 4K": {"id": "Travelxp4K.pl", "names": ["Travelxp 4K"]},
    "Museum 4K": {"id": "Museum4K.pl", "names": ["Museum 4K"]},
    "Red Carpet TV International": {"id": "RedCarpet.pl", "names": ["Red Carpet TV International"]},
    "FashionBox HD": {"id": "FashionBoxHD.pl", "names": ["FashionBox HD"]},
    "Kapitan Bomba TV": {"id": "KapitanBombaTV.pl", "names": ["Kapitan Bomba TV"]},
    "Porucznik Kabura": {"id": "PorucznikKabura.pl", "names": ["Porucznik Kabura"]},
    "MyZen.TV": {"id": "MyZenTV.pl", "names": ["MyZen.TV"]},
    "Fast FunBox": {"id": "FastFunBox.pl", "names": ["Fast FunBox"]},
    "Fast FunBox 2": {"id": "FastFunBox2.pl", "names": ["Fast FunBox 2"]},
    "InUltra": {"id": "InUltra.pl", "names": ["InUltra"]},
    "Water Planet": {"id": "WaterPlanet.pl", "names": ["Water Planet"]},
    "English Club TV": {"id": "EnglishClubTV.pl", "names": ["English Club TV"]},

    # === SPORT I PPV ===
    "Eurosport 1 HD": {"id": "Eurosport1HD.pl", "names": ["Eurosport 1 HD", "Eurosport", "PL: Eurosport 1"]},
    "Eurosport 2 HD ": {"id": "Eurosport2HD.pl", "names": ["Eurosport 2 HD ", "Eurosport 2", "Eurosport 2 HD"]},
    "Eurosport 3": {"id": "Eurosport3HD.pl", "names": ["Eurosport 3", "Eurosport 3 HD"]},
    "Eurosport 4": {"id": "Eurosport4HD.pl", "names": ["Eurosport 4", "Eurosport 4 HD"]},
    "Polsat Sport 1": {"id": "PolsatSport1HD.pl", "names": ["Polsat Sport 1", "Polsat Sport 1 HD", "PL: Polsat Sport 1"]},
    "Polsat Sport 2": {"id": "PolsatSport2HD.pl", "names": ["Polsat Sport 2", "Polsat Sport 2 HD", "PL: Polsat Sport 2"]},
    "Polsat Sport 3": {"id": "PolsatSport3HD.pl", "names": ["Polsat Sport 3", "Polsat Sport 3 HD", "PL: Polsat Sport 3"]},
    "POLSAT Sport Fight": {"id": "PolsatSportFightHD.pl", "names": ["POLSAT Sport Fight", "Polsat Sport Fight HD", "Polsat Sport Fight"]},
    "CANAL+ Sport HD": {"id": "CanalPlusSportHD.pl", "names": ["CANAL+ Sport HD", "Canal+ Sport HD", "Canal+ Sport"]},
    "CANAL+ Sport 2 HD": {"id": "CanalPlusSport2HD.pl", "names": ["CANAL+ Sport 2 HD", "Canal+ Sport 2 HD", "Canal+ Sport 2"]},
    "CANAL+ Sport 3 HD": {"id": "CanalPlusSport3HD.pl", "names": ["CANAL+ Sport 3 HD", "Canal+ Sport 3 HD", "Canal+ Sport 3"]},
    "CANAL+ Sport 4 HD": {"id": "CanalPlusSport4HD.pl", "names": ["CANAL+ Sport 4 HD", "Canal+ Sport 4 HD", "Canal+ Sport 4"]},
    "CANAL+ Sport 5": {"id": "CanalPlusSport5HD.pl", "names": ["CANAL+ Sport 5", "Canal+ Sport 5 HD"]},
    "CANAL+ NOW": {"id": "CanalPlusNowHD.pl", "names": ["CANAL+ NOW", "Canal+ Now"]},
    "Canal+ Sport CZ": {"id": "CanalPlusSportCZ.pl", "names": ["Canal+ Sport CZ"]},
    "Canal+ Extra 1": {"id": "CanalPlusExtra1.pl", "names": ["Canal+ Extra 1", "Canal+ Extra 1 HD"]},
    "Canal+ Extra 2 HD": {"id": "CanalPlusExtra2HD.pl", "names": ["Canal+ Extra 2 HD"]},
    "Canal+ Extra 3 HD": {"id": "CanalPlusExtra3HD.pl", "names": ["Canal+ Extra 3 HD"]},
    "Canal+ Extra 4 HD": {"id": "CanalPlusExtra4HD.pl", "names": ["Canal+ Extra 4 HD"]},
    "Canal+ Extra 5 HD": {"id": "CanalPlusExtra5HD.pl", "names": ["Canal+ Extra 5 HD"]},
    "Canal+ Extra 6 HD": {"id": "CanalPlusExtra6HD.pl", "names": ["Canal+ Extra 6 HD"]},
    "Canal+ Extra 7 HD": {"id": "CanalPlusExtra7HD.pl", "names": ["Canal+ Extra 7 HD"]},
    "Canal+ Extra 8": {"id": "CanalPlusExtra8.pl", "names": ["Canal+ Extra 8"]},
    "Canal+ Extra 9": {"id": "CanalPlusExtra9.pl", "names": ["Canal+ Extra 9"]},
    "Canal+ Live 2": {"id": "CanalPlusLive2.pl", "names": ["Canal+ Live 2"]},
    "Canal+ Live 3": {"id": "CanalPlusLive3.pl", "names": ["Canal+ Live 3"]},
    "Canal+ Live 4": {"id": "CanalPlusLive4.pl", "names": ["Canal+ Live 4"]},
    "Eleven Sports 1": {"id": "ElevenSports1HD.pl", "names": ["Eleven Sports 1", "Eleven Sports 1 HD"]},
    "Eleven Sports 1 4K": {"id": "ElevenSports14K.pl", "names": ["Eleven Sports 1 4K"]},
    "Eleven Sports 2": {"id": "ElevenSports2HD.pl", "names": ["Eleven Sports 2", "Eleven Sports 2 HD"]},
    "Eleven Sports 3": {"id": "ElevenSports3HD.pl", "names": ["Eleven Sports 3", "Eleven Sports 3 HD"]},
    "Eleven Sports 4": {"id": "ElevenSports4HD.pl", "names": ["Eleven Sports 4", "Eleven Sports 4 HD"]},
    "Polsat Sport Premium 1": {"id": "PolsatSportPremium1HD.pl", "names": ["Polsat Sport Premium 1", "Polsat Sport Premium 1 (v2)"]},
    "Polsat Sport Premium 2": {"id": "PolsatSportPremium2HD.pl", "names": ["Polsat Sport Premium 2", "Polsat Sport Premium 2 (v2)"]},
    "Polsat Sport Extra 1": {"id": "PolsatSportExtra1.pl", "names": ["Polsat Sport Extra 1"]},
    "Polsat Sport Extra 2": {"id": "PolsatSportExtra2.pl", "names": ["Polsat Sport Extra 2"]},
    "Polsat Sport Extra 3": {"id": "PolsatSportExtra3.pl", "names": ["Polsat Sport Extra 3"]},
    "Polsat Sport Extra 4": {"id": "PolsatSportExtra4.pl", "names": ["Polsat Sport Extra 4"]},
    "Viaplay Sports 1": {"id": "ViaplaySports1.pl", "names": ["Viaplay Sports 1"]},
    "Viaplay Sports 2": {"id": "ViaplaySports2.pl", "names": ["Viaplay Sports 2"]},
    "Viaplay Sports 3": {"id": "ViaplaySports3.pl", "names": ["Viaplay Sports 3"]},
    "Viaplay Sports 4": {"id": "ViaplaySports4.pl", "names": ["Viaplay Sports 4"]},
    "Viaplay Sports 5": {"id": "ViaplaySports5.pl", "names": ["Viaplay Sports 5"]},
    "Viaplay Sports 6": {"id": "ViaplaySports6.pl", "names": ["Viaplay Sports 6"]},
    "Viaplay Sports 7": {"id": "ViaplaySports7.pl", "names": ["Viaplay Sports 7"]},
    "Viaplay Sports 8": {"id": "ViaplaySports8.pl", "names": ["Viaplay Sports 8"]},
    "Gametoon": {"id": "GametoonHD.pl", "names": ["Gametoon", "Gametoon HD"]},
    "POLSAT Games": {"id": "PolsatGamesHD.pl", "names": ["POLSAT Games", "Polsat Games HD"]},
    "Motowizja": {"id": "MotowizjaHD.pl", "names": ["Motowizja", "Motowizja HD"]},
    "Extreme Channel": {"id": "ExtremeChannelHD.pl", "names": ["Extreme Channel", "Extreme Sports Channel"]},
    "Golf Zone": {"id": "GolfZone.pl", "names": ["Golf Zone", "Golf Channel"]},
    "FightBox": {"id": "FightBoxHD.pl", "names": ["FightBox", "FightBox HD"]},
    "Prime Fight HD": {"id": "PrimeFightHD.pl", "names": ["Prime Fight HD"]},
    "FightKlub HD": {"id": "FightKlubHD.pl", "names": ["FightKlub HD"]},
    "Fight Sports HD": {"id": "FightSportsHD.pl", "names": ["Fight Sports HD"]},
    "Sport Klub HD": {"id": "SportKlubHD.pl", "names": ["Sport Klub HD"]},
    "Sportowa TV": {"id": "SportowaTV.pl", "names": ["Sportowa TV"]},
    "eSports One HD": {"id": "eSportsOneHD.pl", "names": ["eSports One HD"]},
    "Xtreme TV": {"id": "XtremeTV.pl", "names": ["Xtreme TV"]},
    "PPV 1": {"id": "PPV1.pl", "names": ["PPV 1"]},
    "PPV 2": {"id": "PPV2.pl", "names": ["PPV 2"]},
    "PPV 3": {"id": "PPV3.pl", "names": ["PPV 3"]},
    "PPV 4": {"id": "PPV4.pl", "names": ["PPV 4"]},

    # === DZIECI ===
    "MiniMini+": {"id": "MiniMiniPlusHD.pl", "names": ["MiniMini+", "MiniMini+ HD"]},
    "Disney Junior": {"id": "DisneyJunior.pl", "names": ["Disney Junior"]},
    "Nick Jr.": {"id": "NickJr.pl", "names": ["Nick Jr."]},
    "TeenNick": {"id": "TeenNick.pl", "names": ["TeenNick"]},
    "NickMusic": {"id": "NickMusic.pl", "names": ["NickMusic"]},
    "CBeebies": {"id": "CBeebies.pl", "names": ["CBeebies", "BBC CBeebies"]},
    "Cartoonito": {"id": "BoomerangHD.pl", "names": ["Cartoonito", "Cartoonito HD"]},
    "Baby TV": {"id": "BabyTV.pl", "names": ["Baby TV", "BabyTV"]},
    "Duck TV": {"id": "DuckTV.pl", "names": ["Duck TV", "Duck TV HD"]},
    "Duck TV Plus": {"id": "DuckTVPlus.pl", "names": ["Duck TV Plus"]},
    "POLSAT JimJam": {"id": "JimJam.pl", "names": ["POLSAT JimJam", "Polsat JimJam"]},
    "Cartoon Network": {"id": "CartoonNetworkHD.pl", "names": ["Cartoon Network", "Cartoon Network HD"]},
    "Nickelodeon": {"id": "Nickelodeon.pl", "names": ["Nickelodeon"]},
    "NickToons": {"id": "NicktoonsHD.pl", "names": ["NickToons", "Nicktoons HD"]},
    "Disney Channel": {"id": "DisneyChannelHD.pl", "names": ["Disney Channel", "Disney Channel HD"]},
    "Disney XD": {"id": "DisneyXD.pl", "names": ["Disney XD"]},
    "teleTOON+": {"id": "TeletoonPlusHD.pl", "names": ["teleTOON+", "Teletoon+ HD"]},
    "Da Vinci": {"id": "DaVinciLearning.pl", "names": ["Da Vinci", "Da Vinci Learning"]},
    "TOP KIDS": {"id": "TopKidsHD.pl", "names": ["TOP KIDS", "Top Kids HD"]},
    "ALFA TVP": {"id": "AlfaTVPHD.pl", "names": ["ALFA TVP", "Alfa TVP HD"]},
    "Junior Channel": {"id": "JuniorChannel.pl", "names": ["Junior Channel"]},
    "4FUN Kids": {"id": "4FUNKids.pl", "names": ["4FUN Kids", "4Fun Kids"]},
    "JUNIOR MUSIC HD": {"id": "JuniorMusicHD.pl", "names": ["JUNIOR MUSIC HD", "Junior Music HD"]},
    "2x2 HD": {"id": "2x2HD.pl", "names": ["2x2 HD"]},

    # === MUZYKA ===
    "Eska TV": {"id": "EskaTVHD.pl", "names": ["Eska TV"]},
    "Eska TV Extra": {"id": "EskaTVExtraHD.pl", "names": ["Eska TV Extra"]},
    "Eska Rock TV": {"id": "EskaRockTV.pl", "names": ["Eska Rock TV"]},
    "POLSAT Music": {"id": "PolsatMusicHD.pl", "names": ["POLSAT Music", "Polsat Music HD"]},
    "4FUN Dance": {"id": "4FUNDance.pl", "names": ["4FUN Dance", "4Fun Dance"]},
    "4FUN TV": {"id": "4FUNTV.pl", "names": ["4FUN TV", "4Fun TV"]},
    "Music Box Polska": {"id": "MusicBoxPolska.pl", "names": ["Music Box Polska"]},
    "Clubbing": {"id": "ClubbingTV.pl", "names": ["Clubbing"]},
    "Mixtape TV": {"id": "MixtapeTV.pl", "names": ["Mixtape TV", "Mix tape HD"]},
    "Power TV HD": {"id": "PowerTVHD.pl", "names": ["Power TV HD", "Power TV"]},
    "Nuta. TV HD": {"id": "NutaTVHD.pl", "names": ["Nuta. TV HD", "Nuta TV HD", "Nuta TV"]},
    "Nuta Gold": {"id": "NutaGoldHD.pl", "names": ["Nuta Gold", "Nuta Gold HD"]},
    "Kino Polska Muzyka": {"id": "KinoPolskaMuzyka.pl", "names": ["Kino Polska Muzyka"]},
    "Stars.TV": {"id": "StarsTVHD.pl", "names": ["Stars.TV", "Stars TV"]},
    "Szlagier TV": {"id": "SzlagierTV.pl", "names": ["Szlagier TV"]},
    "Disco Polo Music": {"id": "DiscoPoloMusic.pl", "names": ["Disco Polo Music"]},
    "Polo TV": {"id": "PoloTV.pl", "names": ["Polo TV"]},
    "VOX Music TV": {"id": "VoxMusicTV.pl", "names": ["VOX Music TV"]},
    "Mezzo": {"id": "Mezzo.pl", "names": ["Mezzo"]},
    "Mezzo Live": {"id": "MezzoLiveHD.pl", "names": ["Mezzo Live", "Mezzo Live HD"]},
    "MTV Polska HD": {"id": "MTVPolskaHD.pl", "names": ["MTV Polska HD", "MTV Polska"]},
    "MTV 80s": {"id": "MTV80s.pl", "names": ["MTV 80s"]},
    "MTV 90s": {"id": "MTV90s.pl", "names": ["MTV 90s"]},
    "MTV 00s": {"id": "MTV00s.pl", "names": ["MTV 00s"]},
    "MTV Hits": {"id": "MTVHits.pl", "names": ["MTV Hits"]},
    "MTV Live": {"id": "MTVLiveHD.pl", "names": ["MTV Live"]},
    "MTV Club": {"id": "MTVClub.pl", "names": ["MTV Club"]},
    "360TuneBox": {"id": "360TuneBox.pl", "names": ["360TuneBox"]},
    "Deluxe Dance": {"id": "DeluxeDance.pl", "names": ["Deluxe Dance"]},
    "Deluxe Music": {"id": "DeluxeMusic.pl", "names": ["Deluxe Music"]},
    "Deluxe music 2": {"id": "DeluxeMusic2.pl", "names": ["Deluxe music 2"]},
    "Deluxe RAP": {"id": "DeluxeRap.pl", "names": ["Deluxe RAP"]},
    "First Music Channel HD": {"id": "FirstMusicChannelHD.pl", "names": ["First Music Channel HD"]},
    "Jazz TV HD": {"id": "JazzTVHD.pl", "names": ["Jazz TV HD"]},
    "Stingray CMusic HD": {"id": "StingrayCMusicHD.pl", "names": ["Stingray CMusic HD"]},

    # === KANAŁY TVP I LOKALNE ===
    "TVP3 Warszawa": {"id": "TVP3Warszawa.pl", "names": ["TVP3 Warszawa"]},
    "TVP3 Białystok": {"id": "TVP3Bialystok.pl", "names": ["TVP3 Białystok", "TVP 3 Białystok"]},
    "TVP3 Bydgoszcz": {"id": "TVP3Bydgoszcz.pl", "names": ["TVP3 Bydgoszcz"]},
    "TVP3 Gdańsk": {"id": "TVP3Gdansk.pl", "names": ["TVP3 Gdańsk"]},
    "TVP3 Gorzów Wielkopolski": {"id": "TVP3GorzowWielkopolski.pl", "names": ["TVP3 Gorzów Wielkopolski"]},
    "TVP3 Katowice": {"id": "TVP3Katowice.pl", "names": ["TVP3 Katowice"]},
    "TVP3 Kielce": {"id": "TVP3Kielce.pl", "names": ["TVP3 Kielce"]},
    "TVP3 Kraków": {"id": "TVP3Krakow.pl", "names": ["TVP3 Kraków"]},
    "TVP3 Lublin": {"id": "TVP3Lublin.pl", "names": ["TVP3 Lublin"]},
    "TVP3 Łódź": {"id": "TVP3Lodz.pl", "names": ["TVP3 Łódź"]},
    "TVP3 Olsztyn": {"id": "TVP3Olsztyn.pl", "names": ["TVP3 Olsztyn"]},
    "TVP3 Opole": {"id": "TVP3Opole.pl", "names": ["TVP3 Opole"]},
    "TVP3 Poznań": {"id": "TVP3Poznan.pl", "names": ["TVP3 Poznań"]},
    "TVP3 Rzeszów": {"id": "TVP3Rzeszow.pl", "names": ["TVP3 Rzeszów"]},
    "TVP3 Szczecin": {"id": "TVP3Szczecin.pl", "names": ["TVP3 Szczecin"]},
    "TVP3 Wrocław": {"id": "TVP3Wroclaw.pl", "names": ["TVP3 Wrocław"]},
    "TVP 3 HD": {"id": "TVP3HD.pl", "names": ["TVP 3 HD", "TVP 3"]},
    "TVP HD": {"id": "TVPHD.pl", "names": ["TVP HD"]},
    "TVP Rozrywka": {"id": "TVPRozrywka.pl", "names": ["TVP Rozrywka", "TVP Rozrywka HD"]},
    "TVP Kultura HD": {"id": "TVPKulturaHD.pl", "names": ["TVP Kultura HD"]},
    "TVP Kultura 2 HD": {"id": "TVPKultura2HD.pl", "names": ["TVP Kultura 2 HD"]},
    "TVP Historia": {"id": "TVPHistoria.pl", "names": ["TVP Historia", "TVP Historia HD"]},
    "TVP Historia 2": {"id": "TVPHistoria2.pl", "names": ["TVP Historia 2"]},
    "TVP Dokument HD": {"id": "TVPDokumentHD.pl", "names": ["TVP Dokument HD"]},
    "TVP Nauka HD": {"id": "TVPNaukaHD.pl", "names": ["TVP Nauka HD"]},
    "TVP Kobieta": {"id": "TVPKobieta.pl", "names": ["TVP Kobieta"]},
    "TVP ABC": {"id": "TVPABC.pl", "names": ["TVP ABC", "TVP ABC HD"]},
    "TVP ABC 2 HD": {"id": "TVPABC2HD.pl", "names": ["TVP ABC 2 HD"]},
    "TVP Polonia": {"id": "TVPPolonia.pl", "names": ["TVP Polonia"]},
    "TVP Wilno HD": {"id": "TVPWilnoHD.pl", "names": ["TVP Wilno HD"]},
    "TVP Sport HD": {"id": "TVPSportHD.pl", "names": ["TVP Sport HD"]},
    "TVS": {"id": "TVS.pl", "names": ["TVS"]},
    "WTK": {"id": "WTK.pl", "names": ["WTK"]},
    "TVT": {"id": "TVT.pl", "names": ["TVT"]},
    "ECHO24": {"id": "Echo24.pl", "names": ["ECHO24", "Echo24"]},
    "DlaCiebie. TV": {"id": "DlaCiebieTV.pl", "names": ["DlaCiebie. TV", "Dla Ciebie TV"]},
    "TV Bolesławiec": {"id": "TVBoleslawiec.pl", "names": ["TV Bolesławiec"]},
    "Lubuska TV Horyzont": {"id": "LubuskaTV.pl", "names": ["Lubuska TV Horyzont"]},
    "Toya": {"id": "Toya.pl", "names": ["Toya"]},
    "Kujawy TV": {"id": "KujawyTV.pl", "names": ["Kujawy TV"]},
    "TV Regio": {"id": "TVRegio.pl", "names": ["TV Regio"]},
    "Twoja TV": {"id": "TwojaTV.pl", "names": ["Twoja TV"]},

    # === ZAGRANICZNE I INNE ===
    "CNN": {"id": "CNN.pl", "names": ["CNN"]},
    "BBC News": {"id": "BBCNews.pl", "names": ["BBC News"]},
    "Deutsche Welle ENG": {"id": "DW.pl", "names": ["Deutsche Welle ENG"]},
    "WELT": {"id": "Welt.pl", "names": ["WELT"]},
    "France 24": {"id": "France24.pl", "names": ["France 24"]},
    "Current Time": {"id": "CurrentTime.pl", "names": ["Current Time"]},
    "Bloomberg Television": {"id": "Bloomberg.pl", "names": ["Bloomberg Television"]},
    "Euronews": {"id": "Euronews.pl", "names": ["Euronews"]},
    "Euronews PL": {"id": "EuronewsPL.pl", "names": ["Euronews PL"]},
    "Sky News": {"id": "SkyNews.pl", "names": ["Sky News"]},
    "TVP World": {"id": "TVPWorld.pl", "names": ["TVP World", "TVP World HD"]},
    "Arirang TV": {"id": "ArirangTV.pl", "names": ["Arirang TV"]},
    "1+1 International": {"id": "1Plus1.pl", "names": ["1+1 International"]},
    "Kvartal TV": {"id": "KvartalTV.pl", "names": ["Kvartal TV"]},
    "Film UA Drama": {"id": "FilmUADrama.pl", "names": ["Film UA Drama"]},
    "Dacha TV": {"id": "DachaTV.pl", "names": ["Dacha TV"]},
    "Kus Kus": {"id": "KusKus.pl", "names": ["Kus Kus"]},
    "36,6 TV": {"id": "366TV.pl", "names": ["36,6 TV"]},
    "Star Cinema": {"id": "StarCinema.pl", "names": ["Star Cinema"]},
    "Star Family": {"id": "StarFamily.pl", "names": ["Star Family"]},
    "Freedom": {"id": "Freedom.pl", "names": ["Freedom"]},
    "Rybalka TV": {"id": "RybalkaTV.pl", "names": ["Rybalka TV"]},
    "DIM": {"id": "DIM.pl", "names": ["DIM"]},
    "BBC Player": {"id": "BBCPlayer.pl", "names": ["BBC Player"]},
    "National Geographic Play": {"id": "NatGeoPlay.pl", "names": ["National Geographic Play"]},
    "Newsmax Polska": {"id": "NewsmaxPolska.pl", "names": ["Newsmax Polska"]},
    "Fox News": {"id": "FoxNews.pl", "names": ["Fox News"]},
    "TBN Polska": {"id": "TBNPolska.pl", "names": ["TBN Polska"]},
    "DayStar HD": {"id": "DayStarHD.pl", "names": ["DayStar HD"]},
    "iTVN": {"id": "iTVN.pl", "names": ["iTVN"]},
    "iTVN Extra": {"id": "iTVNExtra.pl", "names": ["iTVN Extra"]},

    # === RADIO ===
    "Radio Nowy Świat": {"id": "RadioNowySwiat.pl", "names": ["Radio Nowy Świat"]},
    "Radio 357": {"id": "Radio357.pl", "names": ["Radio 357"]},
    "Radio Eska": {"id": "RadioEska.pl", "names": ["Radio Eska"]},
    "Radio Eska 2": {"id": "RadioEska2.pl", "names": ["Radio Eska 2"]},
    "Radio EskaROCK": {"id": "RadioEskaRock.pl", "names": ["Radio EskaROCK"]},
    "VOX FM": {"id": "VoxFM.pl", "names": ["VOX FM"]},
    "RMF FM": {"id": "RMFFM.pl", "names": ["RMF FM"]},
    "RMF Classic": {"id": "RMFClassic.pl", "names": ["RMF Classic"]},
    "RMF MAXXX": {"id": "RMFMaxxx.pl", "names": ["RMF MAXXX"]},
    "Chillizet": {"id": "Chillizet.pl", "names": ["Chillizet"]},
    "TOK FM": {"id": "TOKFM.pl", "names": ["TOK FM"]},
    "Radio Złote Przeboje": {"id": "RadioZlotePrzeboje.pl", "names": ["Radio Złote Przeboje"]},
    "Polskie Radio Jedynka": {"id": "PR1.pl", "names": ["Polskie Radio Jedynka"]},
    "Polskie Radio Trójka": {"id": "PR3.pl", "names": ["Polskie Radio Trójka"]},
    "Radio Jasna Góra": {"id": "RadioJasnaGora.pl", "names": ["Radio Jasna Góra"]}
}

def format_xmltv_time(iso_time_str):
    try:
        dt = datetime.datetime.strptime(iso_time_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y%m%d%H%M%S +0200')
    except Exception:
        return ""

def process_channel(ch, now, headers, api_base, mapowanie):
    ch_id = str(ch['id'])
    oryginalna_nazwa = ch['title']
    
    dane_mapowania = mapowanie.get(oryginalna_nazwa, {})
    xmltv_id = dane_mapowania.get("id", oryginalna_nazwa)
    display_names = dane_mapowania.get("names", [oryginalna_nazwa])
    
    ch_logo = ch.get('logos', {}).get('L1x1_cl', [{}])[0].get('url', '')
    if ch_logo.startswith('//'):
        ch_logo = 'https:' + ch_logo

    channel_elem = Element('channel', {'id': xmltv_id})
    for name in display_names:
        disp_elem = SubElement(channel_elem, 'display-name', {'lang': 'pl'})
        disp_elem.text = name
        
    if ch_logo:
        SubElement(channel_elem, 'icon', {'src': ch_logo})
        
    programmes = []
    print(f"Pobieranie EPG (wątek): {oryginalna_nazwa} (ID: {xmltv_id})...")

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
            resp_epg = requests.get(api_base + 'products/lives/epgs', headers=headers, params=params_epg, timeout=10)
            epg_data = resp_epg.json()
            
            if isinstance(epg_data, list):
                for prog in epg_data:
                    start_time = format_xmltv_time(prog.get('since', ''))
                    stop_time = format_xmltv_time(prog.get('till', ''))
                    
                    if not start_time or not stop_time:
                        continue
                        
                    prog_elem = Element('programme', {
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
                        
                    programmes.append(prog_elem)
        except Exception:
            pass
            
    return channel_elem, programmes

def main():
    os.makedirs('releases', exist_ok=True)
    
    xml_header = '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE tv SYSTEM "xmltv.dtd">\n'
    
    tv = Element('tv', {
        'generator-info-name': 'EPG-Hybrid-Grabber',
        'generator-info-url': 'https://epg.ovh'
    })
    
    resp_ch = requests.get(API_BASE + 'products/lives', headers=HEADERS, params={'platform': 'BROWSER', 'tenant': 'TV_POINTS'})
    channels = [c for c in resp_ch.json() if c.get('liveType'] == 'LIVE']
    print(f"Pobrano {len(channels)} kanałów. Uruchamiam wielowątkowe pobieranie EPG...")

    now = datetime.datetime.now()
    
    # Wielowątkowość (ThreadPoolExecutor z 15 wątkami)
    max_threads = 15
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_channel = {
            executor.submit(process_channel, ch, now, HEADERS, API_BASE, MAPOWANIE): ch 
            for ch in channels
        }
        
        for future in as_completed(future_to_channel):
            try:
                channel_elem, programmes = future.result()
                tv.append(channel_elem)
                for prog_elem in programmes:
                    tv.append(prog_elem)
            except Exception as exc:
                ch_info = future_to_channel[future]
                print(f"Kanał {ch_info.get('title')} wygenerował błąd: {exc}")

    xml_str = tostring(tv, 'utf-8')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")
    pretty_xml_without_default_header = pretty_xml.split('?>\n', 1)[-1]
    
    final_output = xml_header + pretty_xml_without_default_header
    
    output_path = os.path.join('releases', 'epg.xml')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_output)
        
    print(f"Sukces! Wygenerowano uniwersalny plik epg.xml w katalogu releases/")

if __name__ == '__main__':
    main()