"""
Imports routes - handles CSV/bulk player imports.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..auth import get_current_user
from ..middleware.rate_limiting import write_rate_limit, bulk_rate_limit
from ..firestore_client import db
from ..utils.identity import generate_player_id
from datetime import datetime, timezone
import logging
import csv
import io

router = APIRouter()


class ImportResult(BaseModel):
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]]
    player_ids: List[str]


class ImportPreview(BaseModel):
    headers: List[str]
    sample_rows: List[Dict[str, str]]
    row_count: int
    suggested_mapping: Dict[str, str]


# Standard field mappings for CSV imports
STANDARD_FIELDS = {
    'name': ['name', 'player_name', 'player', 'full_name', 'fullname', 'athlete'],
    'age_group': ['age_group', 'agegroup', 'age', 'division', 'grade', 'class'],
    'jersey_number': ['jersey', 'jersey_number', 'number', 'num', '#'],
    'position': ['position', 'pos'],
    'team': ['team', 'team_name', 'squad'],
}


def guess_field_mapping(headers: List[str]) -> Dict[str, str]:
    """Attempt to auto-map CSV headers to standard fields."""
    mapping = {}
    headers_lower = [h.lower().strip() for h in headers]
    
    for field, aliases in STANDARD_FIELDS.items():
        for alias in aliases:
            if alias in headers_lower:
                idx = headers_lower.index(alias)
                mapping[field] = headers[idx]
                break
    
    return mapping


@router.post("/leagues/{league_id}/events/{event_id}/import/preview", dependencies=[Depends(write_rate_limit)])
async def preview_import(
    league_id: str,
    event_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """Preview a CSV file before importing."""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        content = await file.read()
        text = content.decode('utf-8-sig')  # Handle BOM
        
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames or []
        
        rows = []
        for i, row in enumerate(reader):
            if i >= 5:  # Preview first 5 rows
                break
            rows.append(row)
        
        # Count total rows
        text_reader = csv.reader(io.StringIO(text))
        row_count = sum(1 for _ in text_reader) - 1  # Subtract header
        
        return ImportPreview(
            headers=headers,
            sample_rows=rows,
            row_count=row_count,
            suggested_mapping=guess_field_mapping(headers)
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error previewing import: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview file")


@router.post("/leagues/{league_id}/events/{event_id}/import", dependencies=[Depends(bulk_rate_limit)])
async def import_players(
    league_id: str,
    event_id: str,
    file: UploadFile = File(...),
    field_mapping: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Import players from a CSV file."""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        content = await file.read()
        text = content.decode('utf-8-sig')
        
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames or []
        
        # Parse field mapping if provided
        mapping = {}
        if field_mapping:
            import json
            mapping = json.loads(field_mapping)
        else:
            mapping = guess_field_mapping(headers)
        
        success_count = 0
        error_count = 0
        errors = []
        player_ids = []
        now = datetime.now(timezone.utc).isoformat()
        
        batch = db.batch()
        batch_count = 0
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1-indexed + header)
            try:
                # Extract mapped fields
                name = row.get(mapping.get('name', ''), '').strip()
                if not name:
                    errors.append({'row': row_num, 'error': 'Missing player name'})
                    error_count += 1
                    continue
                
                player_data = {
                    'name': name,
                    'age_group': row.get(mapping.get('age_group', ''), '').strip(),
                    'jersey_number': row.get(mapping.get('jersey_number', ''), '').strip(),
                    'position': row.get(mapping.get('position', ''), '').strip(),
                    'team': row.get(mapping.get('team', ''), '').strip(),
                    'event_id': event_id,
                    'league_id': league_id,
                    'created_at': now,
                    'created_by': user['uid'],
                    'scores': {},
                    'composite_score': 0.0
                }
                
                # Generate player ID
                player_id = generate_player_id(event_id, name)
                player_data['id'] = player_id
                
                doc_ref = db.collection('players').document(player_id)
                batch.set(doc_ref, player_data)
                batch_count += 1
                player_ids.append(player_id)
                success_count += 1
                
                # Commit batch every 500 documents
                if batch_count >= 500:
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0
                    
            except Exception as e:
                errors.append({'row': row_num, 'error': str(e)})
                error_count += 1
        
        # Commit remaining batch
        if batch_count > 0:
            batch.commit()
        
        return ImportResult(
            success_count=success_count,
            error_count=error_count,
            errors=errors[:10],  # Limit errors returned
            player_ids=player_ids
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error importing players: {e}")
        raise HTTPException(status_code=500, detail="Failed to import players")
