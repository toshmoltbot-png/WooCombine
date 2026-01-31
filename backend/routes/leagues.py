"""
Leagues routes - manages league creation, joining, and membership.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..auth import get_current_user
from ..middleware.rate_limiting import read_rate_limit, write_rate_limit
from ..firestore_client import db
from datetime import datetime, timezone
import logging
import secrets
import string

router = APIRouter()


class LeagueCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sport: str = "football"


class LeagueResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    sport: str
    join_code: str
    created_at: str
    owner_id: str


def generate_join_code(length: int = 6) -> str:
    """Generate a random alphanumeric join code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@router.get("/leagues", response_model=List[LeagueResponse], dependencies=[Depends(read_rate_limit)])
async def list_leagues(user=Depends(get_current_user)):
    """List all leagues the current user is a member of."""
    try:
        # Get user's league memberships
        memberships = db.collection('league_members').where('user_id', '==', user['uid']).stream()
        league_ids = [m.to_dict().get('league_id') for m in memberships]
        
        if not league_ids:
            return []
        
        # Fetch league details
        leagues = []
        for league_id in league_ids:
            doc = db.collection('leagues').document(league_id).get()
            if doc.exists:
                data = doc.to_dict()
                leagues.append(LeagueResponse(
                    id=doc.id,
                    name=data.get('name', ''),
                    description=data.get('description'),
                    sport=data.get('sport', 'football'),
                    join_code=data.get('join_code', ''),
                    created_at=data.get('created_at', ''),
                    owner_id=data.get('owner_id', '')
                ))
        
        return leagues
    except Exception as e:
        logging.error(f"Error listing leagues: {e}")
        raise HTTPException(status_code=500, detail="Failed to list leagues")


@router.post("/leagues", response_model=LeagueResponse, dependencies=[Depends(write_rate_limit)])
async def create_league(league: LeagueCreate, user=Depends(get_current_user)):
    """Create a new league."""
    try:
        join_code = generate_join_code()
        now = datetime.now(timezone.utc).isoformat()
        
        league_data = {
            'name': league.name,
            'description': league.description,
            'sport': league.sport,
            'join_code': join_code,
            'created_at': now,
            'owner_id': user['uid']
        }
        
        # Create league document
        doc_ref = db.collection('leagues').add(league_data)
        league_id = doc_ref[1].id
        
        # Add owner as member
        db.collection('league_members').add({
            'league_id': league_id,
            'user_id': user['uid'],
            'role': 'organizer',
            'joined_at': now
        })
        
        return LeagueResponse(
            id=league_id,
            **league_data
        )
    except Exception as e:
        logging.error(f"Error creating league: {e}")
        raise HTTPException(status_code=500, detail="Failed to create league")


@router.get("/leagues/{league_id}", response_model=LeagueResponse, dependencies=[Depends(read_rate_limit)])
async def get_league(league_id: str, user=Depends(get_current_user)):
    """Get a specific league by ID."""
    try:
        doc = db.collection('leagues').document(league_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="League not found")
        
        data = doc.to_dict()
        return LeagueResponse(
            id=doc.id,
            name=data.get('name', ''),
            description=data.get('description'),
            sport=data.get('sport', 'football'),
            join_code=data.get('join_code', ''),
            created_at=data.get('created_at', ''),
            owner_id=data.get('owner_id', '')
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting league: {e}")
        raise HTTPException(status_code=500, detail="Failed to get league")


@router.post("/leagues/join", dependencies=[Depends(write_rate_limit)])
async def join_league(join_code: str, user=Depends(get_current_user)):
    """Join a league using a join code."""
    try:
        # Find league by join code
        leagues = db.collection('leagues').where('join_code', '==', join_code.upper()).limit(1).stream()
        league_doc = next(leagues, None)
        
        if not league_doc:
            raise HTTPException(status_code=404, detail="Invalid join code")
        
        league_id = league_doc.id
        
        # Check if already a member
        existing = db.collection('league_members').where('league_id', '==', league_id).where('user_id', '==', user['uid']).limit(1).stream()
        if next(existing, None):
            raise HTTPException(status_code=400, detail="Already a member of this league")
        
        # Add as member
        db.collection('league_members').add({
            'league_id': league_id,
            'user_id': user['uid'],
            'role': 'coach',
            'joined_at': datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Successfully joined league", "league_id": league_id}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error joining league: {e}")
        raise HTTPException(status_code=500, detail="Failed to join league")
