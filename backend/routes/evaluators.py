"""
Evaluators routes - manages evaluator access and assignments.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from ..auth import get_current_user, require_role
from ..middleware.rate_limiting import read_rate_limit, write_rate_limit
from ..firestore_client import db
from datetime import datetime, timezone
import logging
import secrets
import string

router = APIRouter()


class EvaluatorCreate(BaseModel):
    name: str
    email: Optional[str] = None


class EvaluatorResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    access_code: str
    event_id: str
    created_at: str
    is_active: bool = True


def generate_access_code(length: int = 8) -> str:
    """Generate a random access code for evaluators."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@router.get("/leagues/{league_id}/events/{event_id}/evaluators", dependencies=[Depends(read_rate_limit)])
async def list_evaluators(league_id: str, event_id: str, user=Depends(get_current_user)):
    """List all evaluators for an event."""
    try:
        evaluators = db.collection('evaluators').where('event_id', '==', event_id).stream()
        
        result = []
        for doc in evaluators:
            data = doc.to_dict()
            result.append(EvaluatorResponse(
                id=doc.id,
                name=data.get('name', ''),
                email=data.get('email'),
                access_code=data.get('access_code', ''),
                event_id=data.get('event_id', ''),
                created_at=data.get('created_at', ''),
                is_active=data.get('is_active', True)
            ))
        
        return result
    except Exception as e:
        logging.error(f"Error listing evaluators: {e}")
        raise HTTPException(status_code=500, detail="Failed to list evaluators")


@router.post("/leagues/{league_id}/events/{event_id}/evaluators", dependencies=[Depends(write_rate_limit)])
async def create_evaluator(
    league_id: str,
    event_id: str,
    evaluator: EvaluatorCreate,
    user=Depends(get_current_user)
):
    """Create a new evaluator for an event."""
    try:
        access_code = generate_access_code()
        now = datetime.now(timezone.utc).isoformat()
        
        evaluator_data = {
            'name': evaluator.name,
            'email': evaluator.email,
            'access_code': access_code,
            'event_id': event_id,
            'league_id': league_id,
            'created_at': now,
            'created_by': user['uid'],
            'is_active': True
        }
        
        doc_ref = db.collection('evaluators').add(evaluator_data)
        evaluator_id = doc_ref[1].id
        
        return EvaluatorResponse(
            id=evaluator_id,
            name=evaluator.name,
            email=evaluator.email,
            access_code=access_code,
            event_id=event_id,
            created_at=now,
            is_active=True
        )
    except Exception as e:
        logging.error(f"Error creating evaluator: {e}")
        raise HTTPException(status_code=500, detail="Failed to create evaluator")


@router.delete("/leagues/{league_id}/events/{event_id}/evaluators/{evaluator_id}", dependencies=[Depends(write_rate_limit)])
async def delete_evaluator(
    league_id: str,
    event_id: str,
    evaluator_id: str,
    user=Depends(get_current_user)
):
    """Delete an evaluator."""
    try:
        doc_ref = db.collection('evaluators').document(evaluator_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Evaluator not found")
        
        doc_ref.delete()
        return {"message": "Evaluator deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting evaluator: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete evaluator")


@router.post("/evaluators/verify")
async def verify_evaluator(access_code: str):
    """Verify an evaluator access code and return event details."""
    try:
        evaluators = db.collection('evaluators').where('access_code', '==', access_code.upper()).where('is_active', '==', True).limit(1).stream()
        evaluator_doc = next(evaluators, None)
        
        if not evaluator_doc:
            raise HTTPException(status_code=404, detail="Invalid or expired access code")
        
        data = evaluator_doc.to_dict()
        event_id = data.get('event_id')
        
        # Get event details
        event_doc = db.collection('events').document(event_id).get()
        if not event_doc.exists:
            raise HTTPException(status_code=404, detail="Event not found")
        
        event_data = event_doc.to_dict()
        
        return {
            "evaluator_id": evaluator_doc.id,
            "evaluator_name": data.get('name'),
            "event_id": event_id,
            "event_name": event_data.get('name'),
            "event_date": event_data.get('date')
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error verifying evaluator: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify evaluator")
