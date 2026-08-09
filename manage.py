#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import subprocess
import atexit

_background_processes = []

def cleanup_services():
    for p in _background_processes:
        try:
            p.terminate()
        except:
            pass

def start_background_services():
    # Only start services in the main Django process, not the auto-reloader worker
    if os.environ.get('RUN_MAIN') == 'true':
        return
        
    if 'runserver' not in sys.argv:
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Start Redis
    redis_path = os.path.join(base_dir, 'redis', 'redis-server.exe')
    if os.path.exists(redis_path):
        print("=> Starting Redis Server...")
        try:
            p = subprocess.Popen([redis_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            _background_processes.append(p)
        except Exception as e:
            print(f"Failed to start Redis: {e}")

    # 2. Start Celery
    celery_path = os.path.join(base_dir, '.venv', 'Scripts', 'celery.exe')
    if os.path.exists(celery_path):
        print("=> Starting Celery Worker...")
        try:
            p = subprocess.Popen(
                [celery_path, '-A', 'recruitment', 'worker', '--loglevel=info', '--pool=solo'],
                cwd=base_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            _background_processes.append(p)
        except Exception as e:
            print(f"Failed to start Celery: {e}")
            
    atexit.register(cleanup_services)



def main():
    """Run administrative tasks."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    start_background_services()
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
