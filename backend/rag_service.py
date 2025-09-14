import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import ChatSession, ChatMessage, Document as DocModel

class RAGService:
    def __init__(self):
        # Use the API key from environment variables
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.llm = ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.1
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # Store vector stores per session
        self.session_vectorstores = {}
        # Store conversation memories per session
        self.session_memories = {}
        # Store documents per session
        self.session_documents = {}
        
        # Create storage directories
        self.storage_dir = Path("storage")
        self.uploads_dir = self.storage_dir / "uploads"
        self.vectorstores_dir = self.storage_dir / "vectorstores"
        
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.vectorstores_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_pdf(self, pdf_file, session_id: str, filename: str) -> List[Document]:
        """Process PDF and create/update vector store"""
        # Save uploaded file
        file_path = self.uploads_dir / f"{session_id}_{filename}"
        with open(file_path, "wb") as f:
            f.write(pdf_file)
        
        # Load PDF
        loader = PyPDFLoader(str(file_path))
        documents = loader.load()
        
        # Store documents for the session
        if session_id not in self.session_documents:
            self.session_documents[session_id] = []
        self.session_documents[session_id].extend(documents)
        
        # Create or update vector store
        await self._update_vectorstore(session_id)
        
        return documents
    
    async def _update_vectorstore(self, session_id: str):
        """Update vector store for a session"""
        if session_id not in self.session_documents or not self.session_documents[session_id]:
            return
        
        documents = self.session_documents[session_id]
        vectorstore = FAISS.from_documents(documents, self.embeddings)
        self.session_vectorstores[session_id] = vectorstore
        
        # Save vector store to disk
        vectorstore_path = self.vectorstores_dir / session_id
        vectorstore.save_local(str(vectorstore_path))
    
    async def _load_vectorstore(self, session_id: str):
        """Load vector store from disk"""
        vectorstore_path = self.vectorstores_dir / session_id
        if vectorstore_path.exists():
            try:
                vectorstore = FAISS.load_local(str(vectorstore_path), self.embeddings, allow_dangerous_deserialization=True)
                self.session_vectorstores[session_id] = vectorstore
                return vectorstore
            except Exception as e:
                print(f"Error loading vectorstore for session {session_id}: {e}")
        return None
    
    async def get_conversation_memory(self, session_id: str, db: AsyncSession) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for a session"""
        if session_id not in self.session_memories:
            memory = ConversationBufferWindowMemory(
                k=10,  # Keep last 10 exchanges
                memory_key="chat_history",
                return_messages=True
            )
            
            # Load existing chat history from database
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.timestamp)
                .limit(20)  # Last 20 messages
            )
            messages = result.scalars().all()
            
            # Add to memory
            for msg in messages:
                if msg.message_type == "user":
                    memory.chat_memory.add_user_message(msg.content)
                else:
                    memory.chat_memory.add_ai_message(msg.content)
            
            self.session_memories[session_id] = memory
        
        return self.session_memories[session_id]
    
    async def naive_rag(self, query: str, session_id: str, k: int = 5) -> str:
        """Simple top-k retrieval"""
        vectorstore = self.session_vectorstores.get(session_id)
        if not vectorstore:
            vectorstore = await self._load_vectorstore(session_id)
        
        if not vectorstore:
            return "Please upload a PDF to this session first."
        
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        result = qa_chain({"query": query})
        return result["result"]
    
    async def chunking_rag(self, query: str, session_id: str, chunk_size: int = 1000, chunk_overlap: int = 200, k: int = 5) -> str:
        """Split documents into chunks and retrieve"""
        documents = self.session_documents.get(session_id, [])
        if not documents:
            return "Please upload a PDF to this session first."
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_documents(documents)
        
        # Create vectorstore with chunks
        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        result = qa_chain({"query": query})
        return result["result"]
    
    async def contextual_rag(self, query: str, session_id: str, db: AsyncSession, k: int = 5, expand_context: int = 1) -> str:
        """Retrieve with neighboring chunks and conversation memory"""
        vectorstore = self.session_vectorstores.get(session_id)
        if not vectorstore:
            vectorstore = await self._load_vectorstore(session_id)
        
        if not vectorstore:
            return "Please upload a PDF to this session first."
        
        # Get conversation memory
        memory = await self.get_conversation_memory(session_id, db)
        
        # Get initial results
        docs = vectorstore.similarity_search(query, k=k)
        
        # Create context from retrieved docs
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Get conversation history
        chat_history = memory.chat_memory.messages if memory.chat_memory.messages else []
        history_text = ""
        if chat_history:
            history_text = "\n".join([f"{msg.type}: {msg.content}" for msg in chat_history[-6:]])
        
        prompt = f"""
        Conversation History:
        {history_text}
        
        Context from documents: 
        {context}
        
        Current Question: {query}
        
        Based on the conversation history and document context, please provide a comprehensive answer:
        """
        
        response = self.llm.invoke(prompt)
        
        # Update memory
        memory.chat_memory.add_user_message(query)
        memory.chat_memory.add_ai_message(response.content)
        
        return response.content
    
    async def multi_query_rag(self, query: str, session_id: str, k: int = 5) -> str:
        """Generate multiple query variations for broader coverage"""
        vectorstore = self.session_vectorstores.get(session_id)
        if not vectorstore:
            vectorstore = await self._load_vectorstore(session_id)
        
        if not vectorstore:
            return "Please upload a PDF to this session first."
        
        # Generate query variations
        query_generation_prompt = f"""
        Generate 3 different ways to ask the following question to get comprehensive information:
        
        Original question: {query}
        
        Provide 3 alternative questions (one per line, no numbering):
        """
        
        response = self.llm.invoke(query_generation_prompt)
        alternative_queries = [q.strip() for q in response.content.split('\n') if q.strip()]
        
        # Add original query
        all_queries = [query] + alternative_queries[:3]
        
        # Retrieve documents for all queries
        all_docs = []
        for q in all_queries:
            docs = vectorstore.similarity_search(q, k=k//len(all_queries) + 1)
            all_docs.extend(docs)
        
        # Remove duplicates
        unique_docs = []
        seen_content = set()
        for doc in all_docs:
            if doc.page_content not in seen_content:
                unique_docs.append(doc)
                seen_content.add(doc.page_content)
        
        # Create comprehensive context
        context = "\n\n".join([doc.page_content for doc in unique_docs[:k]])
        
        prompt = f"""
        Context: {context}
        
        Question: {query}
        
        Based on the comprehensive context gathered from multiple query variations, 
        please provide a detailed answer:
        """
        
        response = self.llm.invoke(prompt)
        return response.content
    
    async def chat_with_memory(self, query: str, session_id: str, db: AsyncSession, strategy: str = "contextual", **kwargs) -> str:
        """Main chat function with memory support"""
        if strategy == "naive":
            return await self.naive_rag(query, session_id, k=kwargs.get('k', 5))
        elif strategy == "chunking":
            return await self.chunking_rag(
                query, session_id, 
                chunk_size=kwargs.get('chunk_size', 1000),
                chunk_overlap=kwargs.get('chunk_overlap', 200),
                k=kwargs.get('k', 5)
            )
        elif strategy == "contextual":
            return await self.contextual_rag(query, session_id, db, k=kwargs.get('k', 5))
        elif strategy == "multi_query":
            return await self.multi_query_rag(query, session_id, k=kwargs.get('k', 5))
        else:
            return await self.contextual_rag(query, session_id, db, k=kwargs.get('k', 5))
    
    async def delete_session_data(self, session_id: str):
        """Delete all data for a session"""
        # Remove from memory
        if session_id in self.session_vectorstores:
            del self.session_vectorstores[session_id]
        if session_id in self.session_memories:
            del self.session_memories[session_id]
        if session_id in self.session_documents:
            del self.session_documents[session_id]
        
        # Remove files
        vectorstore_path = self.vectorstores_dir / session_id
        if vectorstore_path.exists():
            import shutil
            shutil.rmtree(vectorstore_path)

# Global RAG service instance
rag_service = RAGService()