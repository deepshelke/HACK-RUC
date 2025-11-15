#!/usr/bin/env python3

"""
Clear all vectors from Pinecone index
"""

from pinecone import Pinecone
import os
from dotenv import load_dotenv
from pathlib import Path
import time

load_dotenv(Path(__file__).parent.parent / ".env")

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY', 'pcsk_2N3E6V_QHopkTxvTXj957o8w1eCYPyzm9RH3KgGrsfySya3fqwwmX9sWE2znGijnbt1LeH')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'domestic-worker-rights')

print('='*70)
print('CLEARING PINECONE INDEX')
print('='*70)

try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    print('✅ Connected to Pinecone')
    
    # Get index
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    
    if PINECONE_INDEX_NAME in existing_indexes:
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Get stats before deletion
        stats = index.describe_index_stats()
        total_before = stats.get('total_vector_count', 0)
        print(f'\nVectors in index before: {total_before}')
        
        if total_before > 0:
            print('\n🗑️  Deleting all vectors...')
            # Delete all vectors
            try:
                # Try delete_all
                index.delete(delete_all=True)
                print('✅ Deleted all vectors using delete_all()')
            except Exception as e:
                # Fallback: delete and recreate index
                print(f'   delete_all() not available, deleting and recreating index...')
                pc.delete_index(PINECONE_INDEX_NAME)
                print('   ✅ Index deleted')
                print('   📇 Recreating index...')
                pc.create_index(
                    name=PINECONE_INDEX_NAME,
                    dimension=3072,
                    metric='cosine',
                    spec={
                        'serverless': {
                            'cloud': 'aws',
                            'region': 'us-east-1'
                        }
                    }
                )
                print('   ✅ Index recreated (empty)')
                time.sleep(5)  # Wait for index to be ready
                index = pc.Index(PINECONE_INDEX_NAME)
        
        # Verify
        stats = index.describe_index_stats()
        total_after = stats.get('total_vector_count', 0)
        print(f'\nVectors in index after: {total_after}')
        
        if total_after == 0:
            print('\n✅ Pinecone index is now empty!')
        else:
            print(f'\n⚠️  Warning: {total_after} vectors still remain')
    else:
        print(f'⚠️  Index "{PINECONE_INDEX_NAME}" does not exist')
        print('   Creating empty index...')
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=3072,
            metric='cosine',
            spec={
                'serverless': {
                    'cloud': 'aws',
                    'region': 'us-east-1'
                }
            }
        )
        print('✅ Empty index created')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()

