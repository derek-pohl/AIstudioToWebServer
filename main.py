import flask
from flask import request, jsonify, render_template_string, redirect, url_for, Response
import pyperclip
import json
from datetime import datetime
import time
import uuid
import threading
import webbrowser

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 8383
LOG_FILE = 'api_requests.log'

# --- Flask App Initialization ---
app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'a-super-secret-key-that-you-dont-need-to-change'

# --- Global state management ---
request_state = {
    "data": None,
    "event": threading.Event()
}

# --- HTML Template (Unchanged) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {% if not request_in_progress %}
    <meta http-equiv="refresh" content="3">
    {% endif %}
    <title>Human-in-the-Loop API</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #1e1e1e; color: #d4d4d4; margin: 0; padding: 2rem;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1, h2 { color: #569cd6; border-bottom: 1px solid #444; padding-bottom: 10px; }
        pre { 
            background-color: #252526; border: 1px solid #444; padding: 15px; 
            border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; 
            font-family: "Consolas", "Courier New", monospace; font-size: 14px;
        }
        textarea {
            width: 100%; box-sizing: border-box; background-color: #3c3c3c;
            color: #d4d4d4; border: 1px solid #444; border-radius: 5px;
            padding: 10px; font-family: inherit; font-size: 16px; height: 200px;
            margin-top: 1rem;
        }
        button {
            background-color: #0e639c; color: white; border: none; padding: 12px 20px;
            border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 1rem;
            display: block; width: 100%;
        }
        button:hover { background-color: #1177bb; }
        .status-box {
            background-color: #252526; border: 1px solid #444; padding: 20px;
            border-radius: 5px; text-align: center; font-size: 1.2rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Human-in-the-Loop API</h1>
        {% if request_in_progress %}
            <h2>Incoming Request (Transformed)</h2>
            <pre><code>{{ request_json }}</code></pre>
            
            <h2>Your Response</h2>
            <form action="/submit" method="post">
                <textarea name="response_text" autofocus placeholder="Type or paste your response here..."></textarea>
                <button type="submit">Send Response</button>
            </form>
        {% else %}
            <div class="status-box">
                <p>Waiting for a new request...</p>
                <p>This page will automatically refresh.</p>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- NEW: Transformation Logic ---
def transform_to_gemini_format(openai_request_data):
    """
    Transforms an OpenAI-style request to the Gemini-style format.
    """
    # This is the static boilerplate for the Gemini format you provided.
    GEMINI_BOILERPLATE = {
      "runSettings": {
        "temperature": 1.0,
        "model": "models/gemini-2.5-pro-preview-06-05",
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
            # The system prompt becomes the systemInstruction content
            transformed_data["systemInstruction"] = {"text": content}
            continue

        chunk = {}
        if role == "assistant":
            chunk["role"] = "model"
            chunk["text"] = content
            chunk["finishReason"] = "STOP"
        elif role == "user":
            chunk["role"] = "user"
            # Handle cases where user content is a list of dicts
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
def log_to_file(content):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"--- Log Entry: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(content)
        f.write("\n\n")

@app.route('/')
def index():
    request_json = json.dumps(request_state.get("data"), indent=2) if request_state.get("data") else None
    return render_template_string(
        HTML_TEMPLATE,
        request_in_progress=bool(request_state.get("data")),
        request_json=request_json
    )

@app.route('/submit', methods=['POST'])
def submit():
    response_content = request.form.get('response_text', '[No response provided]')
    # We will modify the original request data for the response, not the transformed one
    if request_state.get("original_data"):
         request_state["original_data"]["response"] = response_content
    # Fallback for safety
    elif request_state["data"]:
        request_state["data"]["response"] = response_content
    request_state["event"].set()
    return redirect(url_for('index'))

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


# --- MODIFIED API Endpoint ---
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    if request_state["event"].is_set():
        return jsonify({"error": "Server is busy processing another request."}), 503

    try:
        # 1. Get the original request data
        request_data = request.get_json()
        is_streaming = request_data.get("stream", False)
        
        # 2. **Perform the transformation**
        transformed_data = transform_to_gemini_format(request_data)

        # 3. Use the transformed data for display, logging, and clipboard
        pretty_request = json.dumps(transformed_data, indent=2)
        print("="*50)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INCOMING REQUEST (Stream: {is_streaming})")
        print("="*50)
        print("--- Original Request (for logging) ---")
        log_to_file(json.dumps(request_data, indent=2))
        print(json.dumps(request_data, indent=2))
        print("\n--- Transformed Request (shown in UI) ---")
        print(pretty_request)
        pyperclip.copy(pretty_request)
        print("\n[INFO] Transformed request logged and copied. Check your browser to respond.")

        # 4. Store BOTH original and transformed data in the global state
        request_state["data"] = transformed_data # For the UI
        request_state["original_data"] = request_data # To get the human response later
        request_state["event"].clear()
        
        # 5. Wait for the human to submit a response via the UI
        request_state["event"].wait()

        # 6. Retrieve the human response attached to the *original* data
        human_response_content = request_state["original_data"].get("response", "[Error: Response not found]")
        response_id = f"chatcmpl-{uuid.uuid4().hex}"
        model_name = "human-in-the-loop-v1-webui"

        if is_streaming:
            print("\n--- SENDING STREAMING RESPONSE ---")
            return Response(stream_generator(response_id, model_name, human_response_content), mimetype='text/event-stream')
        else:
            response_payload = {
                "id": response_id, "object": "chat.completion", "created": int(time.time()), "model": model_name,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": human_response_content}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
            print("\n--- SENDING NON-STREAMING RESPONSE ---")
            print(json.dumps(response_payload, indent=2))
            return jsonify(response_payload)

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        # 7. Reset state for the next request
        request_state["data"] = None
        request_state["original_data"] = None
        request_state["event"].set()
        request_state["event"].clear()
        print("\n[INFO] State reset. Waiting for next request...")


# --- Unchanged Startup Logic ---
def open_browser():
    webbrowser.open_new(f"http://{HOST}:{PORT}")

if __name__ == '__main__':
    print("="*60)
    print("      Human-in-the-Loop - OpenAI Compatible API Server (Web UI)")
    print("="*60)
    print("\nServer starting on http://{HOST}:{PORT}")
    print("This version supports both STREAMING and NON-STREAMING requests.")
    print(">>> THIS VERSION TRANSFORMS OPENAI REQUESTS TO GEMINI FORMAT FOR DISPLAY <<<")
    print("\nConfigure your client application with the Base URL:")
    print(f" -> http://{HOST}:{PORT}/v1")
    print("\nTo stop the server, press CTRL+C in this window.")
    
    threading.Timer(1, open_browser).start()
    app.run(host=HOST, port=PORT, debug=False)