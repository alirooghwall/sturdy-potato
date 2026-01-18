"""Start the stream processing pipeline."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.stream_processor import get_stream_processor


async def main():
    """Start stream processor."""
    print("Starting ISR Platform Stream Processor...")
    print("="*60)
    
    processor = get_stream_processor()
    
    print("\nStarting stream processing pipeline...")
    await processor.start()
    
    print("\n" + "="*60)
    print("Stream processor started successfully!")
    print("Processing messages from Kafka topics...")
    print("Press Ctrl+C to stop...")
    print("="*60 + "\n")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(60)
            
            # Print stats every minute
            stats = processor.get_stats()
            print(f"\nProcessing stats:")
            print(f"  Messages processed: {stats.get('messages_processed', 0)}")
            print(f"  Messages enriched: {stats.get('messages_enriched', 0)}")
            print(f"  Processing rate: {stats.get('messages_per_second', 0):.2f} msg/s")
    
    except KeyboardInterrupt:
        print("\n\nStopping stream processor...")
        await processor.stop()
        print("Stream processor stopped.")


if __name__ == "__main__":
    asyncio.run(main())
