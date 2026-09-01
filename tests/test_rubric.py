import os
import pytest
from src.database import init_db, save_hymns
from src.services import create_service_from_preset, get_service_details, update_service_items, validate_service_rubric

def test_validate_service_rubric_standard(tmp_path):
    db_path = str(tmp_path / "rubric_test_standard.db")
    init_db(db_path)
    
    # Create standard DS2 service
    srv_id = create_service_from_preset("Standard DS2 Service", "2026-08-30", "DS2", db_path=db_path)
    
    status = validate_service_rubric(srv_id, db_path=db_path)
    assert status['is_conformant'] is True
    assert len(status['issues']) == 0
    assert status['setting'] == 'DS2'

def test_validate_service_rubric_missing_canticle(tmp_path):
    db_path = str(tmp_path / "rubric_test_missing.db")
    init_db(db_path)
    
    srv_id = create_service_from_preset("Modified Service", "2026-08-30", "DS2", db_path=db_path)
    details = get_service_details(srv_id, db_path=db_path)
    items = details['items']
    
    # Remove the Sanctus canticle (item with slot_name 'Sanctus')
    modified_items = [item for item in items if item['slot_name'] != 'Sanctus']
    update_service_items(srv_id, modified_items, db_path=db_path)
    
    status = validate_service_rubric(srv_id, db_path=db_path)
    assert status['is_conformant'] is False
    assert any("Sanctus" in issue for issue in status['issues'])
