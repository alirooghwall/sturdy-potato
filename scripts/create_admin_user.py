"""Create initial admin user for ISR Platform."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.auth_service import get_password_hash


async def create_admin_user():
    """Create default admin user."""
    print("Creating admin user...")
    
    # Default admin credentials
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "changeme")
    email = os.getenv("ADMIN_EMAIL", "admin@isr-platform.local")
    
    # Hash password
    hashed_password = get_password_hash(password)
    
    # TODO: Insert into database
    # For now, just print instructions
    print(f"\n{'='*60}")
    print(f"Admin user configured:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"  Email: {email}")
    print(f"\n⚠️  IMPORTANT: Change the default password after first login!")
    print(f"{'='*60}\n")
    
    # SQL for manual creation if needed
    sql = f"""
-- Run this SQL to create admin user manually:
INSERT INTO users (user_id, username, email, hashed_password, roles, is_active, created_at)
VALUES (
    gen_random_uuid(),
    '{username}',
    '{email}',
    '{hashed_password}',
    ARRAY['admin', 'analyst'],
    true,
    NOW()
) ON CONFLICT (username) DO NOTHING;
"""
    
    print("SQL for manual user creation:")
    print(sql)
    
    return True


if __name__ == "__main__":
    asyncio.run(create_admin_user())
