# AI Studio to Web Server

A Flask-based web server that provides an OpenAI-compatible API interface for Google's AI Studio. This tool automates the process of sending prompts to AI Studio through browser automation, allowing you to use AI Studio models through standard OpenAI compatible API calls.

## Features

- **OpenAI-Compatible API**: Drop-in replacement for OpenAI's chat completions endpoint
- **Browser Automation**: Uses Playwright to automate Google AI Studio interactions
- **Google Drive Integration**: Automatically uploads request files to Google Drive
- **Persistent Authentication**: Saves Google account login for future sessions
- **Configurable Settings**: Extensive configuration options (change model, model tempature, etc) via JSON file

## Prerequisites

- Python 3.7 or higher
- Google account with access to AI Studio (personal google account is fine, )
- Google Drive folder (for file uploads)
- AI Studio prompt URL

## One time User Setup

- In your browser, with your google account logged in, go to aistudio

## Installation

1. Clone or download this repository.
2. Install required dependencies from a terminal window located inside the folder:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```bash
   python -m playwright install chromium
   ```

## Configuration

Before running the server, you need to configure the `config.json` file:

### Required Configuration

1. **Google Drive Folder URL**: Replace `FILL_IN_YOUR_FOLDER_URL` with your Google Drive folder URL for AI studio
2. **AI Studio Prompt URL**: Replace `FILL_IN_YOUR_PROMPT_URL` with your AI Studio prompt URL

### Configuration Options (You don't need to change these)

#### Server Settings
```json
"server": {
  "host": "127.0.0.1",        // Server host (localhost)
  "port": 8383,               // Server port
  "secret_key": "..."         // Flask secret key
}
```

#### Browser Settings
```json
"browser": {
  "headless_mode": false,     // Run browser in background (true) or visible (false)
  "visual_debug_mode": false, // Show visual debugging indicators
  "data_dir": "./browser_data" // Directory for browser data persistence
}
```

#### Hover Configuration
```json
"hover_config": {
  "offset_x": -15,           // Mouse hover X offset for button clicking
  "offset_y": 10             // Mouse hover Y offset for button clicking
}
```

#### File Paths
```json
"files": {
  "log_file": "api_requests.log",        // Log file name
  "transformed_request_file": "CodeRequest" // Temporary request file name
}
```

#### Gemini Model Settings (eg, you might want to adjust model temperature or the model used)
```json
"gemini": {
  "model": "models/gemini-2.5-pro",     // Gemini model to use
  "temperature": 0.3,                   // Response creativity (0.0-2.0)
  "top_p": 0.95,                       // Nucleus sampling parameter
  "top_k": 64,                         // Top-k sampling parameter
  "max_output_tokens": 65536,          // Maximum response length
  "response_mime_type": "text/plain",  // Response format
  "enable_code_execution": false,      // Enable code execution in AI Studio
  "enable_search_as_tool": false,      // Enable search tool
  "enable_browse_as_tool": false,      // Enable browse tool
  "enable_auto_function_response": false, // Enable auto function responses
  "thinking_budget": -1                // Thinking time budget (-1 = unlimited). I wouldn't change this
}
```

#### Timeout Settings
```json
"timeouts": {
  "max_wait_start": 1000,              // Max wait for processing to start (seconds)
  "max_wait_complete": 1,              // Max wait for processing to complete (seconds)
  "additional_wait": 1,                // Additional wait after completion (seconds)
  "before_run_button_click": 1         // Wait before clicking run button (seconds)
}
```

## Setup and First Run

1. **Configure URLs**: Edit `config.json` and fill in your Google Drive folder URL and AI Studio prompt URL

2. **First-time Authentication**: 
   ```bash
   python api_server.py
   ```
   - The server will open a browser window for Google authentication
   - Log in to your Google account (this can be a alt account, just any personal google account)
   - Authentication state will be saved for future use (so you don't have to log in again!)
   - Follow the on-screen instructions in the terminal

3. **Subsequent Runs**:
   ```bash
   python api_server.py
   ```
   - The server will start immediately using saved authentication

## Usage

### API Endpoint

The server provides an OpenAI-compatible endpoint at:
```
POST http://127.0.0.1:8383/v1/chat/completions
```
Of course, 127.0.0.1:8383 can be different based on what you set in the config file.

### Example Request (try it out while the program is running!)

```bash
curl -X POST http://127.0.0.1:8383/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-pro",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "stream": false
  }'
```

## How It Works

1. **Request Reception**: Server receives OpenAI-format API request
2. **Format Transformation**: Converts OpenAI format to Gemini/AI Studio format
3. **File Upload**: Saves transformed request and uploads to Google Drive
4. **Browser Automation**: 
   - Navigates to AI Studio prompt URL
   - Clicks the "Run" button
   - Waits for processing to complete
   - Copies the markdown response
5. **Response Delivery**: Returns response in OpenAI-compatible format

## File Structure

```
AIstudioToWebServer/
├── api_server.py          # Main server script
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
├── browser_data/          # Browser persistence data (created automatically)
├── CodeRequest            # Temporary request file uploaded to drive (created automatically)
└── README.md             # This file (hello!)
```

## Security Notes

- The server runs on localhost by default for security, no other computer on the network can connect to the API.
- No API key validation is performed (again, intended for local use)
- Browser data is stored locally for persistent authentication
- Consider the security implications of saving authentication data of your google account.