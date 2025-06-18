# AI Studio Automated API Server

A fully automated system that uses a local, OpenAI-compatible API endpoint as a front-end for Google's AI Studio. This bridges the gap between tools that expect an OpenAI endpoint and Google AI Studio, using browser automation via Playwright.

## Features

- **OpenAI-compatible API**: Drop-in replacement for OpenAI API endpoints
- **Fully automated**: No manual intervention required after initial setup
- **Browser automation**: Uses Playwright to interact with Google Drive and AI Studio
- **Streaming support**: Supports both streaming and non-streaming responses
- **Persistent authentication**: Saves browser session for future use

## Prerequisites

- Python 3.8 or higher
- Google account with access to Google Drive and AI Studio
- Chrome/Chromium browser (automatically managed by Playwright)

## Installation

1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```bash
   python -m playwright install
   ```

## Setup

### Step 1: Configure URLs

Run the setup script to configure your Google Drive folder and AI Studio project URLs:

```bash
python setup.py
```

You'll need:
- **Google Drive Folder URL**: Create a folder in Google Drive and copy its URL
- **AI Studio Project URL**: Create or open a project in AI Studio and copy its URL

### Step 2: First-time Authentication

Run the server for the first time:

```bash
python api_server.py
```

The system will:
1. Open a browser window
2. Navigate to Google accounts page
3. Wait for you to log in manually
4. Save your authentication state for future use

After logging in, press Enter in the terminal to close the program.

### Step 3: Start the Server

Run the server again:

```bash
python api_server.py
```

Now the system is fully automated and ready to accept API requests.

## Usage

### API Endpoint

The server provides an OpenAI-compatible endpoint at:
```
http://127.0.0.1:8383/v1/chat/completions
```

### Example Request

```bash
curl -X POST http://127.0.0.1:8383/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "stream": false
  }'
```

### Configuration

You can modify these settings at the top of `api_server.py`:

- `HOST`: Server host (default: 127.0.0.1)
- `PORT`: Server port (default: 8383)
- `DRIVE_FOLDER_URL`: Your Google Drive folder URL
- `AISTUDIO_URL`: Your AI Studio project URL
- `BROWSER_DATA_DIR`: Browser data storage location

## How It Works

For each API request, the system:

1. **Receives Request**: Flask server receives OpenAI-format request
2. **Transforms Format**: Converts to Gemini-format JSON
3. **Saves to File**: Saves transformed request to local file
4. **Uploads to Drive**: Uses browser automation to upload file to Google Drive
5. **Runs AI Studio**: Navigates to AI Studio and clicks "Run" button
6. **Waits for Completion**: Monitors the run button until processing completes
7. **Copies Response**: Clicks "Copy markdown" and retrieves response from clipboard
8. **Returns Response**: Sends response back to API client

## Troubleshooting

### Authentication Issues
- Delete the `browser_data` folder and restart the server to re-authenticate
- Ensure you're logged into the correct Google account

### Upload Failures
- Verify your Google Drive folder URL is correct
- Check that the folder is accessible and not restricted

### AI Studio Issues
- Verify your AI Studio project URL is correct
- Ensure the project is properly configured and accessible

### Browser Issues
- The system uses a persistent browser context
- If issues persist, delete `browser_data` folder to start fresh

## File Structure

```
├── api_server.py          # Main server application
├── setup.py              # Configuration helper script
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
├── README.md            # This file
└── browser_data/        # Browser session data (auto-created)
```

## Security Notes

- The system stores browser authentication data locally
- API server runs on localhost by default
- No API keys or credentials are stored in code
- Uses your existing Google account permissions

## Limitations

- Requires GUI environment for initial authentication
- Depends on Google Drive and AI Studio web interfaces
- May break if Google changes their UI significantly
- Processing speed depends on network and AI Studio response times

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your URLs are correctly configured
3. Ensure browser automation permissions are granted
4. Try deleting `browser_data` folder to reset authentication
