"""
Setup script to create necessary directories for BharatVaani
Run this before starting the application for the first time
"""

import os

def setup_directories():
    """Create all necessary directories for the application."""
    directories = [
        'data',
        'static/audio',
        'logs'
    ]
    
    print("🚀 Setting up BharatVaani directories...")
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created/verified: {directory}/")
    
    print("\n✅ All directories setup complete!")
    print("📝 Next step: Configure your .env file with API keys")

if __name__ == "__main__":
    setup_directories()
