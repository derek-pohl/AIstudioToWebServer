#!/usr/bin/env python3
"""
Test script for AI Studio Automated API Server
Verifies core functionality without running the full server.
"""

import json
import sys
import os

# Add the current directory to path so we can import api_server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_server import transform_to_gemini_format

def test_transformation():
    """Test the OpenAI to Gemini format transformation"""
    print("Testing OpenAI to Gemini format transformation...")
    
    # Sample OpenAI request
    openai_request = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "What's the weather like?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    # Transform to Gemini format
    gemini_request = transform_to_gemini_format(openai_request)
    
    # Verify transformation
    assert "runSettings" in gemini_request
    assert "systemInstruction" in gemini_request
    assert "chunkedPrompt" in gemini_request
    assert "chunks" in gemini_request["chunkedPrompt"]
    
    # Check system instruction
    assert gemini_request["systemInstruction"]["text"] == "You are a helpful assistant."
    
    # Check chunks
    chunks = gemini_request["chunkedPrompt"]["chunks"]
    assert len(chunks) == 3  # user, assistant, user
    
    assert chunks[0]["role"] == "user"
    assert chunks[0]["text"] == "Hello, how are you?"
    
    assert chunks[1]["role"] == "model"
    assert chunks[1]["text"] == "I'm doing well, thank you!"
    
    assert chunks[2]["role"] == "user"
    assert chunks[2]["text"] == "What's the weather like?"
    
    print("✓ Transformation test passed!")
    
    # Print sample output
    print("\nSample transformation output:")
    print(json.dumps(gemini_request, indent=2)[:500] + "...")

def test_file_operations():
    """Test file operations"""
    print("\nTesting file operations...")
    
    test_content = {"test": "data"}
    test_file = "test_output.json"
    
    # Write test file
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_content, f, indent=2)
    
    # Verify file exists and is readable
    assert os.path.exists(test_file)
    
    with open(test_file, 'r', encoding='utf-8') as f:
        loaded_content = json.load(f)
    
    assert loaded_content == test_content
    
    # Clean up
    os.remove(test_file)
    
    print("✓ File operations test passed!")

def main():
    print("="*50)
    print("  AI Studio API Server - Functionality Test")
    print("="*50)
    
    try:
        test_transformation()
        test_file_operations()
        
        print("\n" + "="*50)
        print("All tests passed! ✓")
        print("The core functionality is working correctly.")
        print("\nNext steps:")
        print("1. Run 'python setup.py' to configure URLs")
        print("2. Run 'python api_server.py' to start the server")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
