# Receipt and Refund Request Tracker

A comprehensive application for managing receipts and processing refund requests, featuring AI-powered audio and image processing capabilities.

## Features

### Receipt Processing
- Upload and store receipt images
- Extract amount information from receipts
- Store receipt data in Supabase database

### Audio Processing
- Process audio files from refund requests using Groq's whisper-large-v3-turbo model
- Automatic transcription of audio content
- AI-powered summarization of transcriptions
- Support for direct URL audio file processing

### Database Integration
- Supabase backend for secure data storage
- Real-time data synchronization
- Efficient query operations

## Setup

1. Install required packages:
```bash
pip install streamlit supabase langchain-groq requests python-dotenv
```

2. Set up environment variables in `.env`:
```
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

3. Launch the application:
```bash
streamlit run app.py
```

## Usage

### Processing Refund Requests
1. Upload receipt images through the Streamlit interface
2. Record or upload audio explanations for refund requests
3. View processed results including:
   - Extracted receipt amounts
   - Audio transcriptions
   - AI-generated summaries

### Audio Processing Features
- Automatic download and processing of audio files
- High-accuracy transcription using Groq's whisper model
- Concise summaries of audio content
- Batch processing capabilities
- Comprehensive error handling

## Technical Details

### Database Schema
- `refund_requests` table:
  - `id`: Primary key
  - `amount`: Numeric (receipt amount)
  - `image_url`: Text (receipt image location)
  - `audio_url`: Text (refund request audio location)

### Key Components
1. `app.py`: Main Streamlit application
2. `audio_processor.py`: Audio processing functionality
3. `database_operations.py`: Supabase database interactions
4. `receipt_processor.py`: Receipt image processing

## Error Handling
- Robust error management for file operations
- Graceful handling of processing failures
- Detailed error reporting
- Automatic cleanup of temporary files

## Security
- Secure handling of API keys through environment variables
- Safe temporary file management
- Secure URL processing
- Protected database operations

## Requirements
- Python 3.7+
- Streamlit
- Supabase
- langchain-groq
- requests
- python-dotenv

## Support
For issues and feature requests, please create an issue in the repository.
# Hackfest
