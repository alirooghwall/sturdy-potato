"""Start the data ingestion system."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.ingestion_manager import get_ingestion_manager


async def main():
    """Start ingestion manager."""
    print("Starting ISR Platform Data Ingestion System...")
    print("="*60)
    
    manager = get_ingestion_manager()
    
    # Start all enabled connectors
    print("\nStarting connectors...")
    await manager.start()
    
    print("\n" + "="*60)
    print("Ingestion system started successfully!")
    print("Press Ctrl+C to stop...")
    print("="*60 + "\n")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(60)
            
            # Print status every minute
            status = await manager.get_status()
            print(f"\nStatus update: {status['total_connectors']} connectors")
            for conn in status['connectors']:
                print(f"  - {conn['name']}: {conn['status']}")
    
    except KeyboardInterrupt:
        print("\n\nStopping ingestion system...")
        await manager.stop()
        print("Ingestion system stopped.")


if __name__ == "__main__":
    asyncio.run(main())
