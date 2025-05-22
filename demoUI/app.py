from flask import Flask, render_template, request, jsonify
import requests
import os
from pathlib import Path
import logging
import time
import soundfile as sf
import numpy as np
from pydub import AudioSegment
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# API configuration
API_URL = "http://127.0.0.1:8000"
API_KEY = "your-secret-key-here"  # This matches the default SECRET_KEY in the main API

# Ensure upload directory exists
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def check_api_connection():
    """Check if the API is accessible"""
    try:
        response = requests.get(f"{API_URL}/docs", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"API connection check failed: {str(e)}")
        return False

def save_audio_file(audio_file, temp_path):
    """Save audio file in proper WAV format"""
    try:
        # Read the audio data
        audio_data = audio_file.read()
        logger.info(f"Read audio data: {len(audio_data)} bytes")
        
        # Convert WebM to WAV using pydub
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
        logger.info(f"Loaded audio: {len(audio)}ms, {audio.channels} channels, {audio.frame_rate}Hz")
        
        # Convert to mono and set sample rate
        audio = audio.set_channels(1).set_frame_rate(16000)
        logger.info(f"Converted audio: {len(audio)}ms, {audio.channels} channels, {audio.frame_rate}Hz")
        
        # Export as WAV
        audio.export(temp_path, format="wav")
        logger.info(f"Saved WAV file at {temp_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error saving audio file: {str(e)}", exc_info=True)
        return False

@app.route('/')
def index():
    api_status = check_api_connection()
    return render_template('index.html', api_status=api_status)

@app.route('/enroll', methods=['POST'])
def enroll():
    try:
        # Check API connection first
        if not check_api_connection():
            return jsonify({
                'error': 'Voice authentication API is not accessible. Please ensure it is running on port 8000.'
            }), 503

        user_id = request.form.get('user_id')
        audio_file = request.files.get('audio')
        
        if not user_id or not audio_file:
            logger.error("Missing user_id or audio file")
            return jsonify({'error': 'Missing user_id or audio file'}), 400
        
        # Save the audio file temporarily
        temp_path = UPLOAD_DIR / 'temp_audio.wav'
        if not save_audio_file(audio_file, temp_path):
            return jsonify({'error': 'Failed to save audio file in correct format'}), 400
            
        logger.info(f"Saved temporary audio file for user {user_id}")
        
        # Call the enrollment API with timeout
        files = {'voice_sample': open(temp_path, 'rb')}
        headers = {'X-API-Key': API_KEY}
        logger.info(f"Calling enrollment API for user {user_id}")
        
        response = requests.post(
            f"{API_URL}/api/v1/auth/enroll",
            files=files,
            headers=headers,
            params={'user_id': user_id},
            timeout=30  # 30 second timeout
        )
        
        logger.info(f"API Response Status: {response.status_code}")
        logger.info(f"API Response: {response.text}")
        
        # Clean up
        temp_path.unlink()
        
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return jsonify({'error': 'Request timed out. The API is taking too long to respond.'}), 504
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to API")
        return jsonify({'error': 'Could not connect to the voice authentication API. Please ensure it is running.'}), 503
    except Exception as e:
        logger.error(f"Error during enrollment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/verify', methods=['POST'])
def verify():
    try:
        # Check API connection first
        if not check_api_connection():
            return jsonify({
                'error': 'Voice authentication API is not accessible. Please ensure it is running on port 8000.'
            }), 503

        user_id = request.form.get('user_id')
        audio_file = request.files.get('audio')
        
        if not user_id or not audio_file:
            logger.error("Missing user_id or audio file")
            return jsonify({'error': 'Missing user_id or audio file'}), 400
        
        # Save the audio file temporarily
        temp_path = UPLOAD_DIR / 'temp_audio.wav'
        if not save_audio_file(audio_file, temp_path):
            return jsonify({'error': 'Failed to save audio file in correct format'}), 400
            
        logger.info(f"Saved temporary audio file for user {user_id}")
        
        # Call the verification API with timeout
        files = {'voice_sample': open(temp_path, 'rb')}
        headers = {'X-API-Key': API_KEY}
        logger.info(f"Calling verification API for user {user_id}")
        
        response = requests.post(
            f"{API_URL}/api/v1/auth/verify",
            files=files,
            headers=headers,
            params={'user_id': user_id},
            timeout=30  # 30 second timeout
        )
        
        logger.info(f"API Response Status: {response.status_code}")
        logger.info(f"API Response: {response.text}")
        
        # Clean up
        temp_path.unlink()
        
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return jsonify({'error': 'Request timed out. The API is taking too long to respond.'}), 504
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to API")
        return jsonify({'error': 'Could not connect to the voice authentication API. Please ensure it is running.'}), 503
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True) 