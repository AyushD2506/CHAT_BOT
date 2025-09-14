import streamlit as st
import os
import tempfile
from typing import List, Dict, Any
import time

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.prompts import PromptTemplate

class MultiRAGSystem:
    def __init__(self, groq_api_key: str):
        self.groq_api_key = "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"
        self.llm = ChatGroq(
            groq_api_key="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",
            model_name="llama-3.3-70b-versatile",
            temperature=0.1
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = None
        self.documents = []
        
    def load_pdf(self, pdf_file) -> List[Document]:
        """Load PDF and extract text"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_file.getvalue())
            temp_file_path = temp_file.name
        
        try:
            loader = PyPDFLoader(temp_file_path)
            documents = loader.load()
            self.documents = documents
            return documents
        finally:
            os.unlink(temp_file_path)
    
    def naive_rag(self, query: str, k: int = 5) -> str:
        """Simple top-k retrieval"""
        if not self.vectorstore:
            return "Please upload a PDF first."
        
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        result = qa_chain({"query": query})
        return result["result"]
    
    def chunking_rag(self, query: str, chunk_size: int = 1000, chunk_overlap: int = 200, k: int = 5) -> str:
        """Split documents into chunks and retrieve"""
        if not self.documents:
            return "Please upload a PDF first."
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_documents(self.documents)
        
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
    
    def contextual_rag(self, query: str, k: int = 5, expand_context: int = 1) -> str:
        """Retrieve with neighboring chunks for better context"""
        if not self.vectorstore:
            return "Please upload a PDF first."
        
        # Get initial results
        docs = self.vectorstore.similarity_search(query, k=k)
        
        # Expand context by including neighboring chunks
        expanded_docs = []
        for doc in docs:
            # Add the document itself
            expanded_docs.append(doc)
            
            # Try to find neighboring documents (simplified approach)
            # In a real implementation, you'd maintain chunk relationships
            for other_doc in self.documents:
                if (other_doc.page_content != doc.page_content and 
                    len(set(doc.page_content.split()[:10]) & 
                        set(other_doc.page_content.split()[:10])) > 3):
                    expanded_docs.append(other_doc)
                    break
        
        # Create context from expanded docs
        context = "\n\n".join([doc.page_content for doc in expanded_docs])
        
        prompt = f"""
        Context: {context}
        
        Question: {query}
        
        Based on the provided context, please answer the question comprehensively:
        """
        
        response = self.llm.invoke(prompt)
        return response.content
    
    def multi_query_rag(self, query: str, k: int = 5) -> str:
        """Generate multiple query variations for broader coverage"""
        if not self.vectorstore:
            return "Please upload a PDF first."
        
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
            docs = self.vectorstore.similarity_search(q, k=k//len(all_queries) + 1)
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
    
    def create_vectorstore(self):
        """Create vectorstore from documents"""
        if self.documents:
            self.vectorstore = FAISS.from_documents(self.documents, self.embeddings)

def main():
    st.set_page_config(
        page_title="Multi-RAG System",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("🤖 Multi-RAG System")
    st.markdown("Upload a PDF and choose your RAG strategy for intelligent document querying!")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Groq API Key input
        groq_api_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Enter your Groq API key"
        )
        
        if not groq_api_key:
            st.warning("Please enter your Groq API key to continue.")
            return
        
        # RAG Type Selection
        st.header("🔧 RAG Strategy")
        rag_type = st.selectbox(
            "Choose RAG Type",
            options=[
                "Naive RAG",
                "Chunking RAG", 
                "Contextual RAG",
                "Multi-Query RAG"
            ],
            help="Select the RAG strategy for document retrieval"
        )
        
        # Advanced parameters
        st.header("🎛️ Parameters")
        k_value = st.slider("Number of retrieved documents (k)", 1, 10, 5)
        
        if rag_type == "Chunking RAG":
            chunk_size = st.slider("Chunk Size", 500, 2000, 1000)
            chunk_overlap = st.slider("Chunk Overlap", 50, 500, 200)
    
    # Initialize RAG system
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = MultiRAGSystem(groq_api_key)
    
    # PDF Upload Section
    st.header("📄 Document Upload")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload a PDF document to analyze"
    )
    
    if uploaded_file is not None:
        if 'current_file' not in st.session_state or st.session_state.current_file != uploaded_file.name:
            with st.spinner("Processing PDF..."):
                # Load PDF
                documents = st.session_state.rag_system.load_pdf(uploaded_file)
                st.session_state.rag_system.create_vectorstore()
                st.session_state.current_file = uploaded_file.name
                
            st.success(f"✅ PDF processed successfully! Found {len(documents)} pages.")
            
            # Display document info
            with st.expander("📋 Document Information"):
                st.write(f"**File:** {uploaded_file.name}")
                st.write(f"**Pages:** {len(documents)}")
                st.write(f"**Total characters:** {sum(len(doc.page_content) for doc in documents)}")
    
    # Chat Interface
    if uploaded_file is not None:
        st.header("💬 Chat Interface")
        
        # Initialize chat history
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about your document..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Choose RAG method based on selection
                    if rag_type == "Naive RAG":
                        response = st.session_state.rag_system.naive_rag(prompt, k=k_value)
                    elif rag_type == "Chunking RAG":
                        response = st.session_state.rag_system.chunking_rag(
                            prompt, chunk_size=chunk_size, chunk_overlap=chunk_overlap, k=k_value
                        )
                    elif rag_type == "Contextual RAG":
                        response = st.session_state.rag_system.contextual_rag(prompt, k=k_value)
                    elif rag_type == "Multi-Query RAG":
                        response = st.session_state.rag_system.multi_query_rag(prompt, k=k_value)
                    
                st.markdown(response)
                
                # Show current RAG strategy
                st.caption(f"*Response generated using: {rag_type}*")
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.experimental_rerun()
    
    else:
        st.info("👆 Please upload a PDF file to start chatting!")
    
    # Information about RAG types
    with st.expander("ℹ️ About RAG Strategies"):
        st.markdown("""
        **Naive RAG**: Simple top-k document retrieval. Best for basic chatbots and simple questions.
        
        **Chunking RAG**: Splits documents into smaller chunks before retrieval. Ideal for large documents and manuals.
        
        **Contextual RAG**: Retrieves documents with neighboring context. Perfect for legal documents and research papers.
        
        **Multi-Query RAG**: Generates multiple query variations for comprehensive coverage. Great for complex, broad questions.
        """)

if __name__ == "__main__":
    main()