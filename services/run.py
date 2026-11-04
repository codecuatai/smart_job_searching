"""Run either Python service using the root environment settings."""
import argparse
import os
import uvicorn
from services.config import ROOT  # Loads .env before server settings are read.


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('service', choices=['api', 'ai'])
    parser.add_argument('--reload', action='store_true')
    args = parser.parse_args()
    port_name, default = ('API_PORT', '8000') if args.service == 'api' else ('AI_PORT', '8001')
    uvicorn.run(f'services.{args.service}.app.main:app', host=os.getenv('SERVICE_HOST', '127.0.0.1'),
                port=int(os.getenv(port_name, default)), reload=args.reload, app_dir=str(ROOT))


if __name__ == '__main__':
    main()
