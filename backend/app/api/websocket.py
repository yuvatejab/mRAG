"""WebSocket endpoints for real-time updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio
import json
from datetime import datetime, timedelta

from app.utils.logger import logger

router = APIRouter(tags=["websocket"])

# Store active connections with timestamp
active_connections: Dict[str, Dict] = {}  # {session_id: {"ws": WebSocket, "connected_at": datetime}}


async def cleanup_stale_connections():
    """Remove stale connections older than 1 hour"""
    stale_threshold = datetime.now() - timedelta(hours=1)
    stale_sessions = []
    
    for session_id, conn_info in active_connections.items():
        if conn_info["connected_at"] < stale_threshold:
            stale_sessions.append(session_id)
    
    for session_id in stale_sessions:
        try:
            await active_connections[session_id]["ws"].close()
        except:
            pass
        del active_connections[session_id]
        logger.info(f"Cleaned up stale WebSocket connection: {session_id}")


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time progress updates.
    
    Args:
        websocket: WebSocket connection
        session_id: Session identifier
    """
    # Close existing connection for this session if any
    if session_id in active_connections:
        try:
            old_ws = active_connections[session_id]["ws"]
            await old_ws.close()
            logger.info(f"Closed previous WebSocket connection for session: {session_id}")
        except:
            pass
    
    # Clean up stale connections periodically
    await cleanup_stale_connections()
    
    await websocket.accept()
    active_connections[session_id] = {
        "ws": websocket,
        "connected_at": datetime.now()
    }
    
    logger.info(f"WebSocket connected: {session_id} (Total active: {len(active_connections)})")
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket connection established"
        })
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Receive messages (ping/pong for keep-alive)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Echo back for keep-alive
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send keep-alive ping
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
    finally:
        if session_id in active_connections:
            del active_connections[session_id]
            logger.info(f"Removed WebSocket connection: {session_id} (Remaining: {len(active_connections)})")


async def send_progress_update(session_id: str, progress_data: dict):
    """
    Send progress update to a specific session.
    
    Args:
        session_id: Session identifier
        progress_data: Progress data to send
    """
    if session_id in active_connections:
        try:
            ws = active_connections[session_id]["ws"]
            logger.info(f"Sending progress update to {session_id}: {progress_data.get('stage')} - {progress_data.get('progress')}%")
            await ws.send_json({
                "type": "progress",
                **progress_data
            })
            logger.info(f"Progress update sent successfully to {session_id}")
        except Exception as e:
            logger.error(f"Failed to send progress update to {session_id}: {e}")
            # Remove dead connection
            if session_id in active_connections:
                del active_connections[session_id]
                logger.info(f"Removed dead WebSocket connection: {session_id}")
    else:
        # Only log as debug for the first few seconds (connection might be establishing)
        active_session_ids = list(active_connections.keys())
        logger.warning(
            f"No active WebSocket connection for session {session_id}. "
            f"Active sessions ({len(active_session_ids)}): {active_session_ids[:5]}"  # Show first 5
        )
