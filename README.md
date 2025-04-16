# Excel to ICS Converter [![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://ts-xlxs-to-ics-2zqc.vercel.app/)

## Overview
This project provides a web-based tool for uploading an Excel file containing work shifts and converting it into an ICS calendar file. Users can import the generated ICS file into their preferred calendar applications.

## Features
- Upload an Excel (.xlsx) file containing shift data (handled client-side using Vercel Blob Storage).
- Search for shifts based on a provided name.
- Generate an ICS calendar file containing the retrieved shifts.
- Uses a hashing function to create a unique UID for each event based on the shift name and date, ensuring no duplicate entries and allowing updates if the shift moves to a time on the same date (depending on calendar app support).
- Download the ICS file for easy import into calendar applications.
- Responsive frontend with real-time status updates.

## Tech Stack
- **Frontend**: Next.js (React framework hosted on Vercel)
- **Backend**: FastAPI (Python API hosted on Render)
- **Libraries Used**:
  - `pytz` (timezone handling in Python)
  - `ics` (ICS file generation in Python)
  - `pandas`/`openpyxl` (Excel processing in Python)
  - `axios` (HTTP requests in Next.js)
- **Hosting**:
  - Frontend: Vercel
  - Backend: Render
  - File Upload Storage: Vercel Blob Storage

## 📤 How to Upload Your File
1. Open the application in your web browser: [Live Demo](https://ts-xlxs-to-ics-2zqc.vercel.app/).
2. Select a correctly formatted Excel file (`.xlsx` format).
3. Enter the name you want to search shifts for.
4. Click "Upload" to process the file and download the generated ICS file.

### 🗓 Table Format Example
Below is an example of the required Excel structure:

|          | Sunday      | Monday      | Tuesday     | Wednesday   | Thursday    | Friday      | Saturday    |
|----------|------------|------------|------------|------------|------------|------------|------------|
| **Date** | 26th Jan   | 27th Jan   | 28th Jan   | 29th Jan   | 30th Jan   | 31st Jan   | 1st Feb    |
| 9:00-17:00  | Alice       | Bob        | Charlie    | David      | Emma       | Finn       | Grace      |
| 10:00-15:00 | Henry       | Isla       | Jack       | Karen      | Liam       | Mia        | Noah       |
| 10:30-15:30 | Olivia      | Peter      | Quinn      | Rachel     | Sam        | Tina       | Victor     |
| 11:30-16:30 | Wendy       | Xavier     | Yvonne     | Zach       | Amy        | Brian      | Chloe      |

## ✅ Accepted Data Formats
To ensure proper processing, use the following formats:

### **1. Days of the Week**
- Must be: `Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday`

### **2. Dates**
- Format: `26th Jan`, `27th Jan`, `28th Jan`
- Day with `st`, `nd`, `rd`, or `th` suffix, followed by a three-letter month abbreviation.

### **3. Shift Times**
- Format: `HH:MM-HH:MM` (24-hour)
- Example: `09:00-17:00`, `10:30-15:30`

### **4. Employee Names**
- One name per shift slot (e.g., `Alice`, `Bob`).

## Installation
### Prerequisites
- **Python 3.8+** (for backend)
- **Node.js 18+** (for frontend)
- **pip** and **npm**

### Backend Setup
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/excel-to-ics-converter.git
   cd excel-to-ics-converter/backend
   ```
2. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set environment variables (e.g., in `backend/.env`):
   ```text
   CORS_ORIGIN_REGEX=http://localhost:3000|https://.*\.vercel\.app
   ```
5. Run the FastAPI server:
   ```sh
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```sh
   cd ../frontend
   ```
2. Install dependencies:
   ```sh
   npm install
   ```
3. Set environment variables (e.g., in `frontend/.env.local`):
   ```text
   NEXT_PUBLIC_PYTHON_API_URL=http://localhost:8000
   VERCEL_BLOB_SECRET=your-vercel-blob-secret-key
   ```
4. Run the Next.js development server:
   ```sh
   npm run dev
   ```
5. Access the app at `http://localhost:3000`.

## Usage
1. Start the backend (`uvicorn app.main:app --port 8000`).
2. Start the frontend (`npm run dev`).
3. Open `http://localhost:3000`, upload an Excel file, enter a name, and download the ICS file.

## Deployment
### Frontend (Vercel)
- Deployed on Vercel with automatic scaling.
- Environment variables in Vercel dashboard:
  ```text
  NEXT_PUBLIC_PYTHON_API_URL=https://your-python-api.onrender.com
  VERCEL_BLOB_SECRET=your-vercel-blob-secret-key
  ```

### Backend (Render)
- Deployed on Render as a single web service.
- API available at `https://your-python-api.onrender.com`
- Environment variables:
  ```text
  CORS_ORIGIN_REGEX=https://.*\.vercel\.app
  ```
- Auto-deploy from GitHub on push to `main` branch.


## Troubleshooting
- **504 Timeout**: Processing exceeds Vercel’s 60-second limit (Hobby plan). Optimize backend or upgrade to Vercel Pro.
- **CORS Errors**: Verify `CORS_ORIGIN_REGEX` matches your frontend URL.
- **File Upload Errors**: Ensure Excel file follows the specified format.
- **Calendar Import Issues**: Confirm your calendar app supports `.ics` files.

## Future Features
- **🔹 More Flexible Parsing** – Support for different table structures, date formats, and column arrangements.
- **🔹 Direct Calendar Integration** – Option to sync shifts directly to Google Calendar or Outlook.
- **🔹 Web API Support** – Expose an API endpoint for programmatic access.
