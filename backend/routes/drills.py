"""
Drills routes - manages drill definitions and templates.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..auth import get_current_user
from ..middleware.rate_limiting import read_rate_limit, write_rate_limit
from ..firestore_client import db
from ..services.schema_registry import SchemaRegistry
import logging

router = APIRouter()


class DrillDefinition(BaseModel):
    key: str
    label: str
    unit: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    lower_is_better: bool = False
    default_weight: float = 1.0


class DrillTemplate(BaseModel):
    id: str
    name: str
    sport: str
    drills: List[DrillDefinition]


@router.get("/drills", dependencies=[Depends(read_rate_limit)])
async def list_drills(sport: str = "football", user=Depends(get_current_user)):
    """List all available drills for a sport."""
    try:
        schema = SchemaRegistry.get_schema(sport)
        if not schema:
            raise HTTPException(status_code=404, detail=f"No schema found for sport: {sport}")
        
        return {
            "sport": sport,
            "drills": [
                {
                    "key": d.key,
                    "label": d.label,
                    "unit": d.unit,
                    "min_value": d.min_value,
                    "max_value": d.max_value,
                    "lower_is_better": d.lower_is_better,
                    "default_weight": d.default_weight
                }
                for d in schema.drills
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error listing drills: {e}")
        raise HTTPException(status_code=500, detail="Failed to list drills")


@router.get("/drills/templates", dependencies=[Depends(read_rate_limit)])
async def list_templates(user=Depends(get_current_user)):
    """List all available drill templates/sports."""
    try:
        templates = []
        for sport_key in SchemaRegistry.list_sports():
            schema = SchemaRegistry.get_schema(sport_key)
            if schema:
                templates.append({
                    "id": sport_key,
                    "name": schema.sport_name,
                    "sport": sport_key,
                    "drill_count": len(schema.drills)
                })
        return templates
    except Exception as e:
        logging.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates")


@router.get("/drills/{drill_key}", dependencies=[Depends(read_rate_limit)])
async def get_drill(drill_key: str, sport: str = "football", user=Depends(get_current_user)):
    """Get details for a specific drill."""
    try:
        schema = SchemaRegistry.get_schema(sport)
        if not schema:
            raise HTTPException(status_code=404, detail=f"No schema found for sport: {sport}")
        
        for drill in schema.drills:
            if drill.key == drill_key:
                return {
                    "key": drill.key,
                    "label": drill.label,
                    "unit": drill.unit,
                    "min_value": drill.min_value,
                    "max_value": drill.max_value,
                    "lower_is_better": drill.lower_is_better,
                    "default_weight": drill.default_weight
                }
        
        raise HTTPException(status_code=404, detail=f"Drill not found: {drill_key}")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting drill: {e}")
        raise HTTPException(status_code=500, detail="Failed to get drill")
