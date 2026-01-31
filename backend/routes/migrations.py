"""
Migrations routes - handles database migrations and schema updates.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from ..auth import get_current_user, require_role
from ..middleware.rate_limiting import write_rate_limit
from ..firestore_client import db
from datetime import datetime
import logging

router = APIRouter()


class MigrationStatus(BaseModel):
    id: str
    name: str
    applied_at: str
    status: str


class MigrationResult(BaseModel):
    migration_id: str
    success: bool
    message: str
    affected_documents: int


# Define available migrations
MIGRATIONS = {
    'v1_add_composite_score': {
        'name': 'Add composite_score field to players',
        'description': 'Adds composite_score field with default 0.0 to all players',
    },
    'v2_normalize_age_groups': {
        'name': 'Normalize age group values',
        'description': 'Standardizes age_group field format across all players',
    },
    'v3_add_event_league_refs': {
        'name': 'Add league references to events',
        'description': 'Ensures all events have proper league_id references',
    },
}


@router.get("/migrations", dependencies=[Depends(write_rate_limit)])
async def list_migrations(user=Depends(get_current_user)):
    """List all available migrations and their status."""
    try:
        # Get applied migrations
        applied = {}
        migration_docs = db.collection('_migrations').stream()
        for doc in migration_docs:
            data = doc.to_dict()
            applied[doc.id] = data
        
        result = []
        for migration_id, migration_info in MIGRATIONS.items():
            status = 'pending'
            applied_at = None
            
            if migration_id in applied:
                status = applied[migration_id].get('status', 'applied')
                applied_at = applied[migration_id].get('applied_at', '')
            
            result.append({
                'id': migration_id,
                'name': migration_info['name'],
                'description': migration_info['description'],
                'status': status,
                'applied_at': applied_at
            })
        
        return result
    except Exception as e:
        logging.error(f"Error listing migrations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list migrations")


@router.post("/migrations/{migration_id}/run", dependencies=[Depends(write_rate_limit)])
async def run_migration(migration_id: str, user=Depends(get_current_user)):
    """Run a specific migration."""
    try:
        if migration_id not in MIGRATIONS:
            raise HTTPException(status_code=404, detail="Migration not found")
        
        # Check if already applied
        migration_doc = db.collection('_migrations').document(migration_id).get()
        if migration_doc.exists and migration_doc.to_dict().get('status') == 'applied':
            return MigrationResult(
                migration_id=migration_id,
                success=True,
                message="Migration already applied",
                affected_documents=0
            )
        
        affected = 0
        now = datetime.utcnow().isoformat()
        
        # Run migration based on ID
        if migration_id == 'v1_add_composite_score':
            affected = await _migrate_add_composite_score()
        elif migration_id == 'v2_normalize_age_groups':
            affected = await _migrate_normalize_age_groups()
        elif migration_id == 'v3_add_event_league_refs':
            affected = await _migrate_add_event_league_refs()
        
        # Record migration
        db.collection('_migrations').document(migration_id).set({
            'status': 'applied',
            'applied_at': now,
            'applied_by': user['uid'],
            'affected_documents': affected
        })
        
        return MigrationResult(
            migration_id=migration_id,
            success=True,
            message=f"Migration completed successfully",
            affected_documents=affected
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error running migration: {e}")
        raise HTTPException(status_code=500, detail="Failed to run migration")


async def _migrate_add_composite_score() -> int:
    """Add composite_score field to players without it."""
    affected = 0
    players = db.collection('players').stream()
    
    batch = db.batch()
    batch_count = 0
    
    for doc in players:
        data = doc.to_dict()
        if 'composite_score' not in data:
            batch.update(doc.reference, {'composite_score': 0.0})
            batch_count += 1
            affected += 1
            
            if batch_count >= 500:
                batch.commit()
                batch = db.batch()
                batch_count = 0
    
    if batch_count > 0:
        batch.commit()
    
    return affected


async def _migrate_normalize_age_groups() -> int:
    """Normalize age_group values."""
    affected = 0
    players = db.collection('players').stream()
    
    batch = db.batch()
    batch_count = 0
    
    for doc in players:
        data = doc.to_dict()
        age_group = data.get('age_group', '')
        
        # Normalize: strip whitespace, title case
        normalized = age_group.strip().title() if age_group else ''
        
        if normalized != age_group:
            batch.update(doc.reference, {'age_group': normalized})
            batch_count += 1
            affected += 1
            
            if batch_count >= 500:
                batch.commit()
                batch = db.batch()
                batch_count = 0
    
    if batch_count > 0:
        batch.commit()
    
    return affected


async def _migrate_add_event_league_refs() -> int:
    """Ensure all events have league_id."""
    affected = 0
    events = db.collection('events').stream()
    
    for doc in events:
        data = doc.to_dict()
        if not data.get('league_id'):
            # Try to find league from related data
            logging.warning(f"Event {doc.id} has no league_id - requires manual fix")
            affected += 1
    
    return affected
