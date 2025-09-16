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
from models import ChatSession, ChatMessage, Document as DocModel, MCPTool
from search_service import search_service

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
    
    async def _maybe_execute_mcp_tool(self, query: str, session_id: str, db: AsyncSession) -> str | None:
        """Detect and execute a session MCP tool if the user asks for it.
        Heuristics:
        - If message contains `run <tool_name>` or mentions exact tool name, execute it.
        - Optional payload: `run <tool_name> with {json}` → used as params/body or kwargs.
        - API tools: HTTP call with basic timeout; Function tools: exec and call.
        """
        # Load tools for session
        result = await db.execute(select(MCPTool).where(MCPTool.session_id == session_id))
        tools = result.scalars().all()
        if not tools:
            return None

        lowered = query.lower()
        chosen = None
        for t in tools:
            if f"run {t.name.lower()}" in lowered or t.name.lower() in lowered:
                chosen = t
                break
        if not chosen:
            return None

        # Try to extract optional JSON payload after "with"
        payload = None
        try:
            import re, json
            m = re.search(r"with\s*(\{[\s\S]*\}|\[[\s\S]*\])", query, re.IGNORECASE)
            if m:
                payload = json.loads(m.group(1))
        except Exception:
            payload = None

        try:
            if chosen.tool_type == 'api' and chosen.api_url:
                method = (chosen.http_method or 'GET').upper()
                url = chosen.api_url
                headers = {"Accept": "application/json, text/plain;q=0.9"}
                body_bytes = None

                # Build query/body
                if method == 'GET':
                    # Append query params if payload is dict
                    if isinstance(payload, dict):
                        from urllib.parse import urlencode, urlsplit, urlunsplit
                        parts = list(urlsplit(url))
                        query = parts[3]
                        extra = urlencode(payload, doseq=True)
                        parts[3] = (query + '&' if query else '') + extra
                        url = urlunsplit(parts)
                else:
                    headers["Content-Type"] = "application/json"
                    if payload is not None:
                        import json as _json
                        body_bytes = _json.dumps(payload).encode('utf-8')

                print(f"[MCP][EXECUTE] session={session_id} tool={chosen.name} type=api method={method} url={url} payload={payload}")

                # Try requests first; fallback to urllib to avoid dependency issues
                text = ""
                status_code = 0
                try:
                    import requests  # type: ignore
                    resp = requests.request(method, url, headers=headers, data=body_bytes, timeout=15)
                    text = resp.text
                    status_code = resp.status_code
                except Exception:
                    # Fallback
                    from urllib.request import Request, urlopen
                    req = Request(url=url, data=body_bytes, headers=headers, method=(method if method in ("GET","POST","PUT","DELETE","PATCH") else "GET"))
                    with urlopen(req, timeout=15) as r:  # nosec - demo only
                        status_code = getattr(r, 'status', 200)
                        text = r.read().decode('utf-8', errors='replace')

                print(f"[MCP][RESULT] session={session_id} tool={chosen.name} status={status_code} bytes={len(text)}")

                preview = text[:2000]
                meta = []
                if chosen.description:
                    meta.append(f"Description: {chosen.description}")
                if chosen.params_docstring:
                    meta.append(f"Params: {chosen.params_docstring}")
                if chosen.returns_docstring:
                    meta.append(f"Returns: {chosen.returns_docstring}")
                meta_block = ("\n" + "\n".join(meta)) if meta else ""
                return f"[MCP API '{chosen.name}' executed] Status {status_code}{meta_block}\nResponse preview:\n{preview}"

            elif chosen.tool_type == 'python_function' and chosen.function_code:
                import inspect
                local_env = {}
                exec(chosen.function_code, {}, local_env)
                # Find a callable defined in code (first def)
                func = None
                for k, v in local_env.items():
                    if callable(v):
                        func = v
                        break
                if func is None:
                    return "MCP function code did not define a callable."

                print(f"[MCP][EXECUTE] session={session_id} tool={chosen.name} type=python_function payload={payload}")

                # Try to call with kwargs if payload is dict
                result_value = None
                try:
                    if isinstance(payload, dict):
                        sig = inspect.signature(func)
                        # Filter kwargs to function parameters
                        filtered = {k: v for k, v in payload.items() if k in sig.parameters}
                        result_value = func(**filtered)
                    else:
                        result_value = func()
                except TypeError:
                    # Fallback: call without args
                    result_value = func()

                print(f"[MCP][RESULT] session={session_id} tool={chosen.name} return_type={type(result_value).__name__}")

                meta = []
                if chosen.description:
                    meta.append(f"Description: {chosen.description}")
                if chosen.params_docstring:
                    meta.append(f"Params: {chosen.params_docstring}")
                if chosen.returns_docstring:
                    meta.append(f"Returns: {chosen.returns_docstring}")
                meta_block = ("\n" + "\n".join(meta)) if meta else ""
                return f"[MCP Function '{chosen.name}' executed]{meta_block}\nReturn: {result_value}"
            else:
                return "MCP tool is misconfigured."
        except Exception as e:
            return f"Error while executing MCP tool '{chosen.name}': {e}"

    async def _auto_route_mcp_tool(self, query: str, session_id: str, db: AsyncSession) -> str | None:
        """LLM-driven tool selection and execution based on tool metadata and user query.
        Returns a string result if a tool is executed; otherwise None.
        """
        # Load tools for session
        result = await db.execute(select(MCPTool).where(MCPTool.session_id == session_id))
        tools = result.scalars().all()
        if not tools:
            return None

        # Build tool catalog text for the model
        catalog_lines = []
        for t in tools:
            if t.tool_type == 'api':
                extra = f"method={t.http_method or 'GET'} url={t.api_url}"
            else:
                extra = "python_function"
            catalog_lines.append(
                f"- name: {t.name}\n  type: {t.tool_type}\n  extra: {extra}\n  description: {t.description or ''}\n  params: {t.params_docstring or ''}\n"
            )
        catalog = "\n".join(catalog_lines)

        # Ask LLM to decide
        decision_prompt = f"""
You are a smart routing controller. Decide if any of the following tools should be used to answer the user's query. 
Return ONLY a compact JSON object with keys: use_tool (bool), tool_name (string|null), args (object|null), reason (string).
Tools:\n{catalog}\n
User query: {query}
Provide JSON only, no extra text.
"""
        try:
            decision = self.llm.invoke(decision_prompt)
            content = getattr(decision, 'content', str(decision))
        except Exception as e:
            print(f"[MCP][ROUTER][ERROR] session={session_id} decision LLM error: {e}")
            return None

        # Parse JSON
        import re, json
        data = None
        try:
            m = re.search(r"\{[\s\S]*\}", content)
            if m:
                data = json.loads(m.group(0))
        except Exception as e:
            print(f"[MCP][ROUTER][ERROR] session={session_id} parse error: {e}; content={content!r}")
            return None

        if not data or not data.get('use_tool'):
            return None

        tool_name = (data.get('tool_name') or '').strip()
        args = data.get('args') if isinstance(data.get('args'), dict) else None
        chosen = next((t for t in tools if t.name.lower() == tool_name.lower()), None)
        if not chosen:
            print(f"[MCP][ROUTER] session={session_id} suggested tool not found: {tool_name}")
            return None

        # Execute selected tool (similar to heuristic path)
        try:
            if chosen.tool_type == 'api' and chosen.api_url:
                method = (chosen.http_method or 'GET').upper()
                url = chosen.api_url
                headers = {"Accept": "application/json, text/plain;q=0.9"}
                body_bytes = None

                if method == 'GET':
                    if isinstance(args, dict):
                        from urllib.parse import urlencode, urlsplit, urlunsplit
                        parts = list(urlsplit(url))
                        q = parts[3]
                        extra = urlencode(args, doseq=True)
                        parts[3] = (q + '&' if q else '') + extra
                        url = urlunsplit(parts)
                else:
                    headers["Content-Type"] = "application/json"
                    if args is not None:
                        import json as _json
                        body_bytes = _json.dumps(args).encode('utf-8')

                print(f"[MCP][EXECUTE] session={session_id} tool={chosen.name} type=api method={method} url={url} args={args}")

                text = ""
                status_code = 0
                try:
                    import requests  # type: ignore
                    resp = requests.request(method, url, headers=headers, data=body_bytes, timeout=15)
                    text = resp.text
                    status_code = resp.status_code
                except Exception:
                    from urllib.request import Request, urlopen
                    req = Request(url=url, data=body_bytes, headers=headers, method=(method if method in ("GET","POST","PUT","DELETE","PATCH") else "GET"))
                    with urlopen(req, timeout=15) as r:  # nosec - demo only
                        status_code = getattr(r, 'status', 200)
                        text = r.read().decode('utf-8', errors='replace')

                print(f"[MCP][RESULT] session={session_id} tool={chosen.name} status={status_code} bytes={len(text)}")

                preview = text[:2000]
                meta = []
                if chosen.description:
                    meta.append(f"Description: {chosen.description}")
                if chosen.params_docstring:
                    meta.append(f"Params: {chosen.params_docstring}")
                if chosen.returns_docstring:
                    meta.append(f"Returns: {chosen.returns_docstring}")
                meta_block = ("\n" + "\n".join(meta)) if meta else ""
                return f"[MCP API '{chosen.name}' executed] Status {status_code}{meta_block}\nResponse preview:\n{preview}"

            elif chosen.tool_type == 'python_function' and chosen.function_code:
                import inspect
                local_env = {}
                exec(chosen.function_code, {}, local_env)
                func = None
                for k, v in local_env.items():
                    if callable(v):
                        func = v
                        break
                if func is None:
                    return "MCP function code did not define a callable."

                print(f"[MCP][EXECUTE] session={session_id} tool={chosen.name} type=python_function args={args}")

                result_value = None
                try:
                    if isinstance(args, dict):
                        sig = inspect.signature(func)
                        filtered = {k: v for k, v in args.items() if k in sig.parameters}
                        result_value = func(**filtered)
                    else:
                        result_value = func()
                except TypeError:
                    result_value = func()

                print(f"[MCP][RESULT] session={session_id} tool={chosen.name} return_type={type(result_value).__name__}")

                meta = []
                if chosen.description:
                    meta.append(f"Description: {chosen.description}")
                if chosen.params_docstring:
                    meta.append(f"Params: {chosen.params_docstring}")
                if chosen.returns_docstring:
                    meta.append(f"Returns: {chosen.returns_docstring}")
                meta_block = ("\n" + "\n".join(meta)) if meta else ""
                return f"[MCP Function '{chosen.name}' executed]{meta_block}\nReturn: {result_value}"
            else:
                return "MCP tool is misconfigured."
        except Exception as e:
            print(f"[MCP][ERROR] session={session_id} tool_exec_failed: {e}")
            return None

    async def _get_internet_search_results(self, query: str, session_id: str, db: AsyncSession, force: bool = False) -> Optional[str]:
        """Get internet search results if enabled for the session.
        When force=True, bypass the heuristic check and always perform the search.
        """
        try:
            # Check if internet search is enabled for this session
            result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
            session = result.scalar_one_or_none()
            
            if not session or not session.enable_internet_search:
                return None
            
            # Heuristic gate only when not forced
            if not force:
                if not search_service.is_search_needed(query):
                    return None
            
            # Perform search
            search_results = search_service.search(query, max_results=5)
            
            if not search_results:
                return None
            
            # Format results for LLM
            formatted_results = search_service.format_search_results_for_llm(search_results)
            
            return formatted_results
            
        except Exception as e:
            print(f"Error in internet search: {e}")
            return None

    async def chat_with_memory(self, query: str, session_id: str, db: AsyncSession, strategy: str = "contextual", **kwargs) -> str:
        """Main chat function with memory support + automatic MCP tool routing + internet search"""
        # 1) Explicit tool invocation (heuristics still respected)
        mcp_response = await self._maybe_execute_mcp_tool(query, session_id, db)
        if mcp_response is not None:
            # Summarize tool output via LLM to produce a clean user-facing answer
            try:
                prompt = f"""
Summarize the following tool output to directly answer the user's question.

User question:
{query}

Tool output:
{mcp_response}

Provide a concise, user-friendly answer. If the tool output is an error, explain it briefly and suggest next steps.
"""
                _sum = self.llm.invoke(prompt)
                return getattr(_sum, "content", str(_sum))
            except Exception:
                return mcp_response

        # 2) Automatic tool routing
        auto_response = await self._auto_route_mcp_tool(query, session_id, db)
        if auto_response is not None:
            # Summarize auto tool output via LLM
            try:
                prompt = f"""
Summarize the following tool output to directly answer the user's question.

User question:
{query}

Tool output:
{auto_response}

Provide a concise, user-friendly answer. If the tool output is an error, explain it briefly and suggest next steps.
"""
                _sum = self.llm.invoke(prompt)
                return getattr(_sum, "content", str(_sum))
            except Exception:
                return auto_response

        # 3) Internet search (if enabled)
        internet_results = await self._get_internet_search_results(query, session_id, db)
        if internet_results:
            try:
                # Combine internet search with RAG strategy
                rag_response = await self._get_rag_response(query, session_id, db, strategy, **kwargs)
                
                # Combine both responses
                combined_prompt = f"""
Based on the following information sources, provide a comprehensive answer to the user's question.

User Question: {query}

Document Context (from uploaded PDFs):
{rag_response}

Internet Search Results:
{internet_results}

Please provide a well-structured answer that combines relevant information from both the uploaded documents and current internet sources. 
If there are conflicts between sources, mention them and provide the most recent/authoritative information.
If the internet search provides more current information, prioritize that while still referencing the document context where relevant.
"""
                
                response = self.llm.invoke(combined_prompt)
                return response.content
                
            except Exception as e:
                print(f"Error combining internet search with RAG: {e}")
                # Fall back to just internet search
                try:
                    internet_prompt = f"""
Based on the following internet search results, answer the user's question.

User Question: {query}

Search Results:
{internet_results}

Provide a comprehensive answer based on the search results.
"""
                    response = self.llm.invoke(internet_prompt)
                    return response.content
                except Exception:
                    return internet_results

        # 4) Fall back to selected RAG strategy
        return await self._get_rag_response(query, session_id, db, strategy, **kwargs)

    async def _get_rag_response(self, query: str, session_id: str, db: AsyncSession, strategy: str, **kwargs) -> str:
        """Get RAG response using the specified strategy"""
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