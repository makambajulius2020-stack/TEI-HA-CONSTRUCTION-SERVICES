#!/usr/bin/env python3
"""
TEI-HA Backend Server Launcher
Automatically checks dependencies and starts the server
"""
import sys
import subprocess
import os

def check_python():
    """Check if Python is available"""
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✓ Python {sys.version.split()[0]} found")
    return True

def check_dependencies():
    """Check and install required dependencies"""
    required_packages = ['fastapi', 'uvicorn', 'httpx']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} is missing")
    
    if missing:
        print(f"\nInstalling missing packages: {', '.join(missing)}")
        requirements_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        try:
            # First, try to upgrade pip and setuptools to avoid build issues
            print("Upgrading pip and setuptools...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'
            ], timeout=120)
            
            # Install requirements with increased timeout and retry
            print(f"Installing packages from {requirements_path}...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '--timeout', '60',
                '--retries', '3',
                '-r', requirements_path
            ], timeout=600)
            print("✓ Dependencies installed successfully")
            return True
        except subprocess.TimeoutExpired:
            print("ERROR: Installation timed out. This might be due to network issues.")
            print(f"Please run manually: {sys.executable} -m pip install -r {requirements_path}")
            return False
        except subprocess.CalledProcessError as e:
            print("ERROR: Failed to install dependencies")
            print(f"Error code: {e.returncode}")
            print(f"Please run manually: {sys.executable} -m pip install -r {requirements_path}")
            print("\nIf you continue to have issues, try:")
            print(f"  {sys.executable} -m pip install --upgrade pip setuptools wheel")
            print(f"  {sys.executable} -m pip install -r {requirements_path}")
            return False
    
    return True

def check_port():
    """Check if port 8000 is already in use"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()
    return result == 0

def start_server():
    """Start the uvicorn server"""
    # Check if port is already in use
    if check_port():
        print("\n⚠ WARNING: Port 8000 is already in use!")
        print("The backend server might already be running.")
        print("Check http://localhost:8000/health to verify")
        response = input("\nDo you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return False
    
    print("\n" + "="*50)
    print("Starting TEI-HA Backend Server")
    print("="*50)
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'server:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\nERROR: Failed to start server: {e}")
        return False
    
    return True

def main():
    """Main launcher function"""
    print("="*50)
    print("TEI-HA Backend Server Launcher")
    print("="*50 + "\n")
    
    if not check_python():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    print("\nAll checks passed! Starting server...\n")
    start_server()

if __name__ == '__main__':
    main()

