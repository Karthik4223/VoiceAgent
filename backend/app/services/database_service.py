import chromadb
import uuid
import time
from datetime import datetime
from loguru import logger

class DatabaseService:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path="./chroma_db")
            self.collection = self.client.get_or_create_collection(name="conversation_history")
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.collection = None

    async def store_interaction(self, session_id: str, role: str, text: str):
        if not self.collection:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.collection.add(
                ids=[str(uuid.uuid4())],
                documents=[text],
                metadatas=[{
                    "session_id": session_id,
                    "role": role,
                    "timestamp": timestamp,
                    "epoch": time.time()
                }]
            )
            logger.debug(f"Stored {role} interaction for session {session_id}")
        except Exception as e:
            logger.error(f"Error storing in ChromaDB: {e}")

    async def get_previous_conversations(self, limit: int = 20):
        if not self.collection:
            return []
        
        try:
            results = self.collection.get(
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            conversations = []
            for i in range(len(results['ids'])):
                conversations.append({
                    "text": results['documents'][i],
                    "metadata": results['metadatas'][i]
                })
            
            # Sort by timestamp (epoch) descending
            conversations.sort(key=lambda x: x['metadata']['epoch'], reverse=True)
            return conversations
        except Exception as e:
            logger.error(f"Error fetching from ChromaDB: {e}")
            return []

db_service = DatabaseService()
