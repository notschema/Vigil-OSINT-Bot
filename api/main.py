#!/usr/bin/env python3
"""
FastAPI backend for VigilBot management
"""

import os
import time
import asyncio
import logging
import subprocess
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vigilbot_api")

# Initialize FastAPI app
app = FastAPI(title="VigilBot API", description="API for managing VigilBot")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global variables for bot process management
bot_process: Optional[subprocess.Popen] = None
log_buffer: List[str] = []
MAX_LOG_BUFFER = 1000  # Maximum log lines to keep
active_websockets: List[WebSocket] = []

# Queue for communication between threads
log_queue = queue.Queue()

# Data models
class StatusResponse(BaseModel):
    status: str
    pid: Optional[int] = None
    uptime: Optional[str] = None
    memory_usage: Optional[str] = None

class BotActionResponse(BaseModel):
    success: bool
    message: str
    status: StatusResponse

class LogsResponse(BaseModel):
    logs: List[str]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

# Helper functions
def get_status() -> StatusResponse:
    """Get the current status of the bot process"""
    global bot_process
    
    # Check if process is running
    if bot_process is not None:
        try:
            if bot_process.poll() is None:
                return StatusResponse(
                    status="running",
                    pid=bot_process.pid,
                    uptime=get_process_uptime(bot_process.pid),
                    memory_usage=get_process_memory(bot_process.pid)
                )
        except Exception as e:
            logger.error(f"Error checking process status: {e}")
    
    return StatusResponse(
        status="stopped",
        pid=None,
        uptime=None,
        memory_usage=None
    )

def get_process_uptime(pid: int) -> str:
    """Get the uptime of a process in a human-readable format"""
    try:
        process = psutil.Process(pid)
        uptime_seconds = time.time() - process.create_time()
        
        # Convert to human-readable format
        minutes, seconds = divmod(uptime_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        if days > 0:
            return f"{int(days)}d {int(hours)}h {int(minutes)}m"
        elif hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
    except Exception as e:
        logger.error(f"Error getting process uptime: {e}")
        return "Unknown"

def get_process_memory(pid: int) -> str:
    """Get the memory usage of a process in a human-readable format"""
    try:
        process = psutil.Process(pid)
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
        
        if memory_mb > 1024:
            return f"{memory_mb/1024:.2f} GB"
        else:
            return f"{memory_mb:.2f} MB"
    except Exception as e:
        logger.error(f"Error getting process memory: {e}")
        return "Unknown"

# FIX: Use a queue to handle the output from threads safely
def read_bot_output(process: subprocess.Popen):
    """Read bot output and push to a queue for processing in the main thread"""
    global log_queue
    
    for line in iter(process.stdout.readline, b''):
        if line:
            try:
                decoded_line = line.decode('utf-8').rstrip()
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_entry = f"[{timestamp}] {decoded_line}"
                
                # Push to queue instead of directly broadcasting
                log_queue.put(log_entry)
            except Exception as e:
                logger.error(f"Error processing bot output: {e}")
    
    # If we get here, the process has terminated
    log_queue.put("Bot process has terminated.")

# Process queue items in the main asyncio thread
async def process_log_queue():
    """Process log queue items in the main asyncio thread"""
    global log_queue, log_buffer
    
    while True:
        # Check if there are items in the queue
        if not log_queue.empty():
            try:
                # Get log entry from the queue
                log_entry = log_queue.get_nowait()
                
                # Add to log buffer (limit size)
                log_buffer.append(log_entry)
                if len(log_buffer) > MAX_LOG_BUFFER:
                    log_buffer.pop(0)
                
                # Broadcast to WebSocket clients
                await manager.broadcast(log_entry)
                
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Error processing log queue: {e}")
        
        # Sleep briefly to avoid high CPU usage
        await asyncio.sleep(0.1)

def start_bot() -> BotActionResponse:
    """Start the VigilBot process"""
    global bot_process, log_buffer
    
    if bot_process is not None and bot_process.poll() is None:
        return BotActionResponse(
            success=False,
            message="Bot is already running",
            status=get_status()
        )
    
    try:
        # Clear log buffer on new start
        log_buffer = []
        
        # Start the bot process
        bot_process = subprocess.Popen(
            ["python", "vigil.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=False
        )
        
        # Start output reader thread
        output_thread = threading.Thread(target=read_bot_output, args=(bot_process,))
        output_thread.daemon = True
        output_thread.start()
        
        return BotActionResponse(
            success=True,
            message=f"Bot started with PID {bot_process.pid}",
            status=get_status()
        )
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return BotActionResponse(
            success=False,
            message=f"Error starting bot: {str(e)}",
            status=get_status()
        )

def stop_bot() -> BotActionResponse:
    """Stop the VigilBot process"""
    global bot_process
    
    if bot_process is None or bot_process.poll() is not None:
        return BotActionResponse(
            success=False,
            message="Bot is not running",
            status=get_status()
        )
    
    try:
        # Send termination signal
        bot_process.terminate()
        
        # Wait for process to end (with timeout)
        try:
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't respond to terminate
            bot_process.kill()
            bot_process.wait()
        
        return BotActionResponse(
            success=True,
            message="Bot stopped successfully",
            status=get_status()
        )
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return BotActionResponse(
            success=False,
            message=f"Error stopping bot: {str(e)}",
            status=get_status()
        )

# API Routes
@app.get("/")
async def root():
    """API root endpoint"""
    return {"message": "VigilBot API", "status": "operational"}

@app.get("/status", response_model=StatusResponse)
async def status():
    """Get bot status"""
    return get_status()

@app.get("/logs", response_model=LogsResponse)
async def logs():
    """Get log buffer"""
    return LogsResponse(logs=log_buffer)

@app.post("/start", response_model=BotActionResponse)
async def start():
    """Start the bot"""
    return start_bot()

@app.post("/stop", response_model=BotActionResponse)
async def stop():
    """Stop the bot"""
    return stop_bot()

@app.post("/restart", response_model=BotActionResponse)
async def restart():
    """Restart the bot"""
    stop_result = stop_bot()
    time.sleep(1)  # Brief delay to ensure proper shutdown
    start_result = start_bot()
    
    return BotActionResponse(
        success=start_result.success,
        message=f"Bot restart: {start_result.message}",
        status=start_result.status
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        # Send existing logs to the new client
        for log in log_buffer:
            await websocket.send_text(log)
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Currently, we don't process any incoming WebSocket messages
            # but this keeps the connection open
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Application startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("VigilBot API starting up")
    
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("temp").mkdir(exist_ok=True)
    
    # Start the background task to process log messages
    asyncio.create_task(process_log_queue())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global bot_process
    
    logger.info("VigilBot API shutting down")
    
    # Terminate bot process if running
    if bot_process is not None and bot_process.poll() is None:
        try:
            bot_process.terminate()
            try:
                bot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                bot_process.kill()
        except Exception as e:
            logger.error(f"Error terminating bot process: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
