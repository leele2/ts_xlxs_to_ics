from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import io
import logging
from utils.excel import read_xls, find_shifts
from utils.ics_gen import generate_ics

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-vercel-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for request body
class ProcessRequest(BaseModel):
    fileUrl: str
    name_to_search: str

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/api/process", 
          response_description="An ICS calendar file containing work shifts",
          tags=["Shift Processing"],
          responses={
              400: {"description": "Bad Request - Missing or invalid input"},
              500: {"description": "Internal Server Error - Processing failed"}
          })
async def process_file(data: ProcessRequest):
    """Process an Excel file URL and generate an ICS calendar for a given employee's shifts.
    
    Args:
        request: A JSON object with `fileUrl` (URL of the Excel file) and `name_to_search` (employee name).
    
    Returns:
        A downloadable ICS file with shift events.
    
    Raises:
        HTTPException: 400 if file download fails, 500 for processing errors.
    """
    logger.info(f"Received data: {data.dict()}")
    try:
        file_url = data.fileUrl
        name_to_search = data.name_to_search

        if not file_url or not name_to_search:
            raise HTTPException(status_code=400, detail="Missing fileUrl or name_to_search")

        # Download the file
        logger.info(f"Downloading file from: {file_url}")
        response = requests.get(file_url)
        response.raise_for_status()
        file_stream = io.BytesIO(response.content)
        logger.info("File downloaded successfully")

        # Process the Excel file
        logger.info("Reading Excel file")
        data_frames = read_xls(file_stream)
        logger.info("Excel file read successfully")

        logger.info("Reading shift information")
        shifts = find_shifts(data_frames, name_to_search)
        logger.info("Shift information read successfully")

        # Generate ICS file
        logger.info("Generating ICS file")
        ics_content = generate_ics(shifts, name_to_search)
        logger.info("ICS file generated successfully")

        return Response(content=ics_content, media_type="text/calendar",
                        headers={"Content-Disposition": "attachment; filename=shifts.ics"})
    except requests.RequestException as e:
        logger.error(f"Failed to download file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to download file: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}