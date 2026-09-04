import os
import pytest
from src.scanner import parse_hymn_file, scan_hymns_directory

def test_parse_hymn_file_advent():
    sample_path = r'c:\dev\IdeaProjects\hymnody-manager\music\1-01 331 - The advent of our King.m4a'
    assert os.path.exists(sample_path)
    
    meta = parse_hymn_file(sample_path)
    assert meta['hymn_number'] == 331
    assert "The advent of our King" in meta['title']
    assert meta['disc_number'] == 1
    assert meta['track_number'] == 1
    assert meta['album'] == "The Concordia Organist"
    assert meta['artist'] == "Concordia Publishing House"
    assert meta['year'] == 2009
    assert meta['liturgical_season'] == "Advent"

def test_parse_hymn_file_liturgical():
    sample_path = r'c:\dev\IdeaProjects\hymnody-manager\music\30-30 DS2 - Kyrie_ Intonation.m4a'
    assert os.path.exists(sample_path)
    
    meta = parse_hymn_file(sample_path)
    assert meta['disc_number'] == 30
    assert meta['track_number'] == 30
    assert "DS2 - Kyrie" in meta['title']

def test_scan_hymns_directory():
    music_dir = r'c:\dev\IdeaProjects\hymnody-manager\music'
    results = scan_hymns_directory(music_dir)
    assert len(results) > 300

def test_parse_hymn_file_office_settings_and_sacramental_ranges():
    base_dir = r'c:\dev\IdeaProjects\hymnody-manager\music'
    
    # Test LSB Sacramental & Seasonal ranges
    meta_bap = parse_hymn_file(os.path.join(base_dir, '13-23 601 - All who believe and are baptized.m4a'))
    assert meta_bap['liturgical_season'] == "Baptism"
    
    meta_conf = parse_hymn_file(os.path.join(base_dir, '14-04 606 - I lay my sins on Jesus.m4a'))
    assert meta_conf['liturgical_season'] == "Confession"
    
    meta_comm = parse_hymn_file(os.path.join(base_dir, '14-15 617 - O Lord, we praise Thee.m4a'))
    assert meta_comm['liturgical_season'] == "Communion"
    
    meta_trust = parse_hymn_file(os.path.join(base_dir, '21-25 780 - O Lord, hear my prayer.m4a'))
    assert meta_trust['liturgical_season'] == "Trust & Comfort"
    
    meta_praise = parse_hymn_file(os.path.join(base_dir, '22-21 801 - How Great Thou Art.m4a'))
    assert meta_praise['liturgical_season'] == "Praise"
    
    # Test Discs 30/31 Office Settings
    meta_ds1 = parse_hymn_file(os.path.join(base_dir, '30-01 DS1 - Kyrie_ Intonation.m4a'))
    assert meta_ds1['liturgical_season'] == "DS1"
    
    meta_ma = parse_hymn_file(os.path.join(base_dir, '31-01 MA - Versicles_ Intonation.m4a'))
    assert meta_ma['liturgical_season'] == "Matins"
    
    meta_ve = parse_hymn_file(os.path.join(base_dir, '31-19 VE - Versicles_ Intonation.m4a'))
    assert meta_ve['liturgical_season'] == "Vespers"
    
    meta_mp = parse_hymn_file(os.path.join(base_dir, '31-35 MP - Versicle_ Intonation.m4a'))
    assert meta_mp['liturgical_season'] == "Morning Prayer"
    
    meta_ep = parse_hymn_file(os.path.join(base_dir, '31-46 EP - Versicles_ Intonation.m4a'))
    assert meta_ep['liturgical_season'] == "Evening Prayer"
    
    meta_co = parse_hymn_file(os.path.join(base_dir, '31-60 CO - Versicles_ Intonation.m4a'))
    assert meta_co['liturgical_season'] == "Compline"
    
    meta_pt = parse_hymn_file(os.path.join(base_dir, '31-76 PT - Tone A.m4a'))
    assert meta_pt['liturgical_season'] == "Psalm Tones"

