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
