"""
Utility functions for the Vigil OSINT Bot commands
"""

import sys
import asyncio
import logging
from pathlib import Path
import subprocess
import shlex
import os

# Configure logging
logger = logging.getLogger("vigil_bot")

# Create temp directory if it doesn't exist
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Fix the execute_command function to work properly on Windows
async def execute_command(cmd, timeout=60):
    """Execute a shell command asynchronously"""
    logger.info(f"Executing command: {cmd}")
    
    # On Windows, we need to handle asyncio subprocess differently
    if sys.platform == 'win32':
        try:
            # For Windows, fall back to a more reliable approach
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            try:
                # Wait for process to complete with timeout
                # Use a slightly shorter timeout to ensure we can handle cleanup
                actual_timeout = max(1, timeout - 5)
                stdout, stderr = process.communicate(timeout=actual_timeout)
                
                # Capture the output regardless of return code
                result = stdout
                if stderr:
                    logger.info(f"Command produced stderr: {stderr[:500]}...")
                    # Include stderr in the result for better debugging
                    result += "\n" + stderr
                
                # Return success even if returncode is non-zero for tools like Maigret
                # that might have partial success but exit with error
                if process.returncode != 0:
                    logger.warning(f"Command returned non-zero code {process.returncode} but may have partial results")
                
                return True, result
                
            except subprocess.TimeoutExpired:
                # Kill the process if it times out
                process.kill()
                stdout, stderr = process.communicate()
                logger.error(f"Command timed out after {timeout} seconds")
                return False, f"Command timed out after {timeout} seconds"
        
        except Exception as e:
            logger.error(f"Exception in execute_command: {str(e)}")
            return False, f"Error executing command: {str(e)}"
    else:
        # For non-Windows systems, use asyncio
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                # Wait for process with timeout
                stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout)
                
                # Decode output
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                
                # Check return code
                if process.returncode != 0:
                    logger.error(f"Command failed with code {process.returncode}: {stderr}")
                    return False, stderr
                
                return True, stdout
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.error(f"Command timed out after {timeout} seconds")
                return False, f"Command timed out after {timeout} seconds"
                
        except Exception as e:
            logger.error(f"Exception in execute_command: {str(e)}")
            return False, f"Error executing command: {str(e)}"

def get_python_executable():
    """Returns the Python executable path"""
    return sys.executable

def chunk_message(message, limit=2000):
    """Splits a message into chunks below Discord's character limit"""
    chunks = []
    current_chunk = ""
    
    for line in message.split('\n'):
        if len(current_chunk) + len(line) + 1 > limit:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

# Module availability checks
try:
    from CheckLeaked.checkleaked_api import CheckLeakedAPI
    checkleaked_available = True
except ImportError:
    logger.warning("CheckLeaked modules not found - !breach commands will be unavailable")
    checkleaked_available = False

try:
    import socialscan
    socialscan_available = True
except ImportError:
    logger.warning("socialscan module not available - !socialscan command will use limited functionality")
    socialscan_available = False

try:
    import toutatis
    toutatis_available = True
except ImportError:
    logger.warning("toutatis module not available - !toutatis command will use limited functionality")
    toutatis_available = False

try:
    from WhatsMyName.whatsmyname_discord import check_username_existence
    whatsmyname_available = True
except ImportError:
    logger.warning("WhatsMyName module not available - !whatsmyname command will be unavailable")
    whatsmyname_available = False

try:
    from xeuledoc.core import doc_hunt
    xeuledoc_available = True
except ImportError:
    logger.warning("xeuledoc module not available - !gdoc command will be unavailable")
    xeuledoc_available = False

try:
    from Masto.masto import username_search, username_search_api, instance_search
    masto_available = True
except ImportError:
    logger.warning("masto module not available - !masto command will be unavailable")
    masto_available = False

# Check if Sherlock is properly installed
try:
    # Check for the installed sherlock package
    import importlib.util
    
    # Check for the correct module name
    sherlock_installed = importlib.util.find_spec("sherlock_project") is not None
    
    if sherlock_installed:
        logger.info("Found sherlock_project installed as a package")
        sherlock_available = True
    else:
        logger.warning("sherlock_project module not found")
        
        # Try to install it if missing
        try:
            import subprocess
            logger.info("Attempting to install sherlock-project package...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "sherlock-project"])
            logger.info("Successfully installed sherlock-project")
            sherlock_available = True
        except Exception as install_error:
            logger.error(f"Failed to install sherlock-project: {str(install_error)}")
            sherlock_available = False
    
    if sherlock_available:
        logger.info("Sherlock is available for use")
        
except Exception as e:
    logger.warning(f"Error checking sherlock availability: {str(e)}")
    sherlock_available = False

# Check if Maigret is properly installed
try:
    # Check for Maigret in the Python path
    maigret_spec = importlib.util.find_spec("maigret")
    
    if maigret_spec is not None:
        logger.info("Found maigret installed as a package")
        maigret_available = True
    else:
        logger.warning("maigret package not found in Python path")
        
        # Check for local Maigret files
        maigret_path = Path("Maigret")
        if maigret_path.exists() and maigret_path.is_dir():
            logger.info(f"Found local Maigret directory at: {maigret_path}")
            
            # Check for data.json file
            data_file_paths = [
                Path("Maigret/data/data.json"),
                Path("Maigret/resources/data.json"),
                Path("Maigret/maigret/resources/data.json")
            ]
            
            for path in data_file_paths:
                if path.exists():
                    logger.info(f"Found Maigret data file at: {path}")
                    maigret_available = True
                    break
            else:
                logger.warning("Could not find Maigret data file")
                maigret_available = False
        else:
            logger.warning("Local Maigret directory not found")
            
            # Try to install it
            try:
                import subprocess
                logger.info("Attempting to install maigret package...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "maigret"])
                logger.info("Successfully installed maigret")
                maigret_available = True
            except Exception as install_error:
                logger.error(f"Failed to install maigret: {str(install_error)}")
                maigret_available = False
except Exception as e:
    logger.warning(f"Error checking maigret availability: {str(e)}")
    maigret_available = False