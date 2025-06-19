import flask
from flask import request, jsonify, Response
import pyperclip
import json
from datetime import datetime
import time
import uuid
import threading
import asyncio
import os
from playwright.async_api import async_playwright
import logging

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 8383
LOG_FILE = 'api_requests.log'
TRANSFORMED_REQUEST_FILE = 'CodeRequest' # The file to save the transformed request (no extension)

# --- AI Studio Configuration ---
DRIVE_FOLDER_URL = 'https://drive.google.com/drive/folders/1fGd5atPaKuuVj8k5M8V4ZvblXHI9y95O'  # Replace with your Google Drive folder URL
AISTUDIO_URL = 'https://aistudio.google.com/app/prompts/1krB5jGaqT9_5iNPGMcjTejpUfUE-g8v1'    # Replace with your AI Studio project URL
BROWSER_DATA_DIR = './browser_data'  # Local browser data storage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Flask App Initialization ---
app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'a-super-secret-key-that-you-dont-need-to-change'

# --- Browser Automation Class ---
class AIStudioAutomation:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.is_authenticated = False
    
    async def initialize_browser(self, headless=False):
        """Initialize browser with persistent data"""
        self.playwright = await async_playwright().start()
        
        # Ensure browser data directory exists
        os.makedirs(BROWSER_DATA_DIR, exist_ok=True)
        
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            headless=headless,
            args=['--no-first-run', '--disable-blink-features=AutomationControlled']
        )
        
        # Check if we have existing authentication
        pages = self.browser.pages
        if pages:
            self.page = pages[0]
        else:
            self.page = await self.browser.new_page()
        
        await self.check_authentication()
    
    async def check_authentication(self):
        """Check if user is authenticated with Google"""
        try:
            await self.page.goto('https://accounts.google.com/')
            await self.page.wait_for_load_state('networkidle')
              # Check if we're already logged in
            current_url = self.page.url
            if 'myaccount.google.com' in current_url or 'accounts.google.com/ManageAccount' in current_url:
                self.is_authenticated = True
                logging.info("User is already authenticated with Google")
            else:
                self.is_authenticated = False
                logging.info("User needs to authenticate with Google")
                
        except Exception as e:
            logging.error(f"Error checking authentication: {e}")
            self.is_authenticated = False
    
    async def upload_to_drive(self, file_path):
        """Upload file to Google Drive folder"""
        try:
            await self.page.goto(DRIVE_FOLDER_URL)
            await self.page.wait_for_load_state('networkidle')
            
            # Use keyboard shortcut Alt+C then U to start upload
            await self.page.keyboard.press('Alt+c')
            await asyncio.sleep(0.5)
            await self.page.keyboard.press('u')
            
            # Wait for file input to appear and handle file selection
            await asyncio.sleep(2)
            
            # Try to find file input element
            try:
                file_input = await self.page.wait_for_selector('input[type="file"]', timeout=5000)
                await file_input.set_input_files(file_path)
            except:
                # Alternative approach: use expect_file_chooser
                async with self.page.expect_file_chooser() as fc_info:
                    # Trigger file chooser if not already open
                    await self.page.keyboard.press('Alt+c')
                    await asyncio.sleep(0.5)
                    await self.page.keyboard.press('u')
                
                file_chooser = await fc_info.value
                await file_chooser.set_files(file_path)
              # Find and click the Upload button
            try:
                upload_button = self.page.get_by_role('button', name='Upload')
                await upload_button.click()
            except:
                # Alternative selector for upload button
                upload_button = await self.page.wait_for_selector('button:has-text("Upload")', timeout=5000)
                await upload_button.click()
            
            # Wait for upload to complete
            await asyncio.sleep(5)
            logging.info(f"Successfully uploaded {file_path} to Drive")
            
        except Exception as e:
            logging.error(f"Error uploading to Drive: {e}")
            raise
    
    async def run_ai_studio_prompt(self):
        """Navigate to AI Studio and run the prompt"""
        try:
            await self.page.goto(AISTUDIO_URL)
            await self.page.wait_for_load_state('networkidle')
            
            # Find and click the Run button
            run_button = self.page.locator('button[aria-label="Run"]')
            
            # Check initial state
            initial_state = await run_button.get_attribute('aria-disabled')
            logging.info(f"Initial button state: aria-disabled='{initial_state}'")
            
            await run_button.click()
            logging.info("Clicked Run button")
            
            # Wait a moment for the button state to change
            await asyncio.sleep(2)
            
            # Monitor the aria-disabled attribute - wait for it to become true (processing)
            logging.info("Waiting for AI Studio to start processing...")
            max_wait_start = 30  # 30 seconds timeout
            wait_count = 0
            
            while wait_count < max_wait_start:
                disabled_state = await run_button.get_attribute('aria-disabled')
                logging.info(f"Button state check: aria-disabled='{disabled_state}'")
                
                if disabled_state == 'true':
                    logging.info("AI Studio is processing...")
                    break
                    
                await asyncio.sleep(1)
                wait_count += 1
            
            if wait_count >= max_wait_start:
                logging.warning("Timeout waiting for processing to start - continuing anyway")
            
            # Wait for processing to complete - wait for aria-disabled to become false
            logging.info("Waiting for AI Studio to complete processing...")
            max_wait_complete = 5  # 5 seconds timeout to account for aistudio.google.com delay
            wait_count = 0
            
            while wait_count < max_wait_complete:
                disabled_state = await run_button.get_attribute('aria-disabled')
                
                if disabled_state == 'false':
                    logging.info("AI Studio processing complete")
                    break
                    
                # Log every 10 seconds to show progress
                if wait_count % 10 == 0:
                    logging.info(f"Still processing... (waited {wait_count} seconds)")
                    
                await asyncio.sleep(1)
                wait_count += 1
            
            if wait_count >= max_wait_complete:
                logging.warning("Timeout waiting for processing to complete - continuing anyway")
            
            # Wait additional 5 seconds as specified
            logging.info("Waiting additional 5 seconds...")
            await asyncio.sleep(5)
            
        except Exception as e:
            logging.error(f"Error running AI Studio prompt: {e}")
            raise
    
    async def copy_response(self):
        """Copy the markdown response from AI Studio"""
        try:
            # Find and click the copy markdown button
            copy_button = self.page.locator('button:has-text("Copy markdown")')
            await copy_button.click()
            
            # Wait a moment for clipboard to update
            await asyncio.sleep(1)
            
            # Get content from clipboard
            response_content = pyperclip.paste()
            logging.info("Successfully copied response from AI Studio")
            
            return response_content
            
        except Exception as e:
            logging.error(f"Error copying response: {e}")
            return "[Error: Could not retrieve response from AI Studio]"
    
    async def close(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def is_browser_ready(self):
        """Check if browser is ready for use"""
        return (self.browser is not None and 
                not self.browser.is_closed() and 
                self.page is not None)

# Global automation instance
automation = AIStudioAutomation()

# --- Transformation Logic (Unchanged) --- e/82&O(H@_Zb:7Z=2*frRs)LtWp(2q-sch%\bN=3PO6R?3'fJAc8^\<f{z4m{88V&]WT|9Mk97/v%w`lVNN(-B:fI)`}})
def transform_to_gemini_format(openai_request_data):
    GEMINI_BOILERPLATE = {
      "runSettings": {
        "temperature": 0.3,
        "model": "models/gemini-2.5-pro",
        "topP": 0.95,
        "topK": 64,
        "maxOutputTokens": 65536,
        "safetySettings": [{
          "category": "HARM_CATEGORY_HARASSMENT",
          "threshold": "OFF"
        }, {
          "category": "HARM_CATEGORY_HATE_SPEECH",
          "threshold": "OFF"
        }, {
          "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
          "threshold": "OFF"
        }, {
          "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
          "threshold": "OFF"
        }],
        "responseMimeType": "text/plain",
        "enableCodeExecution": False,
        "enableSearchAsATool": False,
        "enableBrowseAsATool": False,
        "enableAutoFunctionResponse": False,
        "thinkingBudget": -1
      },
      "systemInstruction": {},
      "chunkedPrompt": {
          "chunks": [],
          "pendingInputs": [{"text": "", "role": "user"}]
      }
    }
    
    transformed_data = GEMINI_BOILERPLATE.copy()
    chunks = []
    
    messages = openai_request_data.get("messages", [])
    for message in messages:
        role = message.get("role")
        content = message.get("content")

        if role == "system":
            transformed_data["systemInstruction"] = {"text": content}
            continue

        chunk = {}
        if role == "assistant":
            chunk["role"] = "model"
            chunk["text"] = content
            chunk["finishReason"] = "STOP"
        elif role == "user":
            chunk["role"] = "user"
            if isinstance(content, list):
                text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
                chunk["text"] = "\n".join(text_parts)
            else:
                chunk["text"] = content
        
        if chunk:
            chunks.append(chunk)

    transformed_data["chunkedPrompt"]["chunks"] = chunks
    return transformed_data

# --- Unchanged Functions ---
# --- Helper Functions ---
def log_to_file(content):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"--- Log Entry: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(content)
        f.write("\n\n")

def stream_generator(response_id, model_name, content):
    start_chunk = {
        "id": response_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
        "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
    }
    yield f"data: {json.dumps(start_chunk)}\n\n"
    content_chunk = {
        "id": response_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
        "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}]
    }
    yield f"data: {json.dumps(content_chunk)}\n\n"
    end_chunk = {
        "id": response_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
    }
    yield f"data: {json.dumps(end_chunk)}\n\n"
    yield "data: [DONE]\n\n"

async def process_request_with_automation(transformed_data):
    """Process the request using browser automation"""
    browser_automation = None
    try:
        # Create a fresh browser instance for this request
        browser_automation = AIStudioAutomation()
        await browser_automation.initialize_browser(headless=False)
        
        # Check authentication
        if not browser_automation.is_authenticated:
            return "[Error: Not authenticated with Google. Please run the server first to authenticate.]"
        
        # Save transformed request to file
        abs_file_path = os.path.abspath(TRANSFORMED_REQUEST_FILE)
        with open(abs_file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(transformed_data, indent=2))
        
        # Upload to Google Drive
        await browser_automation.upload_to_drive(abs_file_path)
        
        # Run AI Studio prompt
        await browser_automation.run_ai_studio_prompt()
        
        # Copy response
        response_content = await browser_automation.copy_response()
        
        return response_content
        
    except Exception as e:
        logging.error(f"Error in automation process: {e}")
        return f"[Error: Automation failed - {str(e)}]"
    finally:
        # Clean up browser resources
        if browser_automation:
            try:
                await browser_automation.close()
            except:
                pass


# --- API Endpoint ---
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    try:
        request_data = request.get_json()
        is_streaming = request_data.get("stream", False)
        
        transformed_data = transform_to_gemini_format(request_data)
        pretty_request = json.dumps(transformed_data, indent=2)

        print("="*50)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INCOMING REQUEST (Stream: {is_streaming})")
        print("="*50)
        
        # Log original request
        print("--- Original Request (for logging) ---")
        log_to_file(json.dumps(request_data, indent=2))
        print(json.dumps(request_data, indent=2))
        
        # Display, copy, and save the transformed request
        print("\n--- Transformed Request (shown in UI) ---")
        print(pretty_request)
        pyperclip.copy(pretty_request)
        
        print(f"\n[INFO] Transformed request saved to '{TRANSFORMED_REQUEST_FILE}'")
        print("[INFO] Starting automated AI Studio process...")        # Process request using browser automation in the same event loop
        try:
            # Use a simple approach - create new loop each time but ensure browser is ready
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                ai_response_content = loop.run_until_complete(
                    process_request_with_automation(transformed_data)
                )
            finally:
                loop.close()
        except Exception as e:
            print(f"[ERROR] Automation failed: {e}")
            ai_response_content = f"[Error: Automation failed - {str(e)}]"

        response_id = f"chatcmpl-{uuid.uuid4().hex}"
        model_name = "ai-studio-automated-v1"

        if is_streaming:
            print("\n--- SENDING STREAMING RESPONSE ---")
            return Response(stream_generator(response_id, model_name, ai_response_content), mimetype='text/event-stream')
        else:
            response_payload = {
                "id": response_id, "object": "chat.completion", "created": int(time.time()), "model": model_name,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": ai_response_content}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
            print("\n--- SENDING NON-STREAMING RESPONSE ---")
            print(json.dumps(response_payload, indent=2))
            return jsonify(response_payload)

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

async def setup_automation():
    """Initialize browser automation for first-time authentication"""
    temp_automation = AIStudioAutomation()
    
    print("Initializing browser automation...")
    await temp_automation.initialize_browser(headless=False)
    
    if not temp_automation.is_authenticated:
        print("="*60)
        print("FIRST TIME SETUP REQUIRED")
        print("="*60)
        print("Please log in to your Google account in the browser window that opened.")
        print("After logging in, close this program and restart it.")
        print("Authentication state will be saved for future use.")
        print("="*60)
        
        # Keep browser open for authentication
        input("Press Enter after logging in to close the program...")
        await temp_automation.close()
        exit(0)
    else:
        print("Authentication verified. Ready to process requests.")
        # Close the test browser
        await temp_automation.close()

def run_setup():
    """Run initial setup if needed"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(setup_automation())
    finally:
        loop.close()

if __name__ == '__main__':
    print("="*60)
    print("   AI Studio Automated API Server - OpenAI Compatible")
    print("="*60)
    print(f"\nServer starting on http://{HOST}:{PORT}")
    print("This version supports both STREAMING and NON-STREAMING requests.")
    print(">>> FULLY AUTOMATED VERSION USING PLAYWRIGHT <<<")
    print("\nIMPORTANT: Configure these URLs at the top of the script:")
    print(f"- DRIVE_FOLDER_URL: {DRIVE_FOLDER_URL}")
    print(f"- AISTUDIO_URL: {AISTUDIO_URL}")
    print("\nConfigure your client application with the Base URL:")
    print(f" -> http://{HOST}:{PORT}/v1")
    print("\nTo stop the server, press CTRL+C in this window.")
    
    # Run initial setup
    run_setup()
    
    # Start the Flask server
    app.run(host=HOST, port=PORT, debug=False)