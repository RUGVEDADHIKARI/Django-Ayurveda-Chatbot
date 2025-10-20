# ai_chat/service.py
import os
import hashlib
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_community.chat_message_histories.upstash_redis import UpstashRedisChatMessageHistory
from langchain_together import ChatTogether
from langchain.memory import ConversationBufferMemory

load_dotenv() # Load env vars here for the service

# --- Configuration Constants (Move from app.py) ---
SYSTEM_MESSAGE = """You are AyurVeda Wellness Assistant, an AI consultant specialized in Ayurvedic medicine, wellness practices, and holistic health.

You provide guidance on:
- Ayurvedic principles and doshas (Vata, Pitta, Kapha)
- Herbal remedies and natural treatments
- Lifestyle recommendations and daily routines (Dinacharya)
- Diet and nutrition based on Ayurvedic principles
- Yoga and meditation practices
- Seasonal wellness practices (Ritucharya)
- Body constitution analysis
- Panchakarma and detoxification methods

You must ONLY provide information related to Ayurveda. If the user asks anything unrelated, politely refuse to answer.
Example refusal: "I'm here to provide information related to Ayurveda. Please let me know how I can assist you with Ayurvedic wellness."

IMPORTANT DISCLAIMERS:
- All advice is for educational purposes only.
- Always recommend consulting qualified Ayurvedic practitioners for personalized treatment.
- Never diagnose or treat serious medical conditions.
- Suggest seeking immediate medical attention for emergencies.
- Emphasize that Ayurveda complements but does not replace modern medicine.

If asked about non-Ayurvedic topics, gently redirect to Ayurvedic wellness and holistic health, and provide a disclaimer that you are only designed to provide information related to Ayurveda.

Provide practical, safe, and authentic Ayurvedic guidance rooted in traditional texts and modern research.
"""
VECTOR_STORE_PATH = r"ai_chat/vectorstore" # ADJUST THIS PATH

class AyurVedaAgentService:
    def __init__(self):
        offline = os.getenv("OFFLINE", "").lower() in ("1", "true", "yes")

        # 1) Tools
        self.tools = []
        if not offline:
            try:
                tavily_key = os.getenv("TAVILY")
                if tavily_key:
                    self.tools.append(TavilySearchResults(tavily_api_key=tavily_key))
            except Exception as e:
                print(f"Warning: Tavily disabled: {e}")

        # 2) Optional RAG tool (FAISS)
        try:
            embeddings = HuggingFaceEmbeddings()
            vectorstore = FAISS.load_local(
                VECTOR_STORE_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            retriever_tool = create_retriever_tool(
                retriever,
                "Ayurveda_knowledge_search",
                "Search for information about Ayurvedic medicine, treatments, herbs, and wellness practices"
            )
            self.tools.append(retriever_tool)
        except Exception as e:
            print(f"Warning: Could not load FAISS vectorstore. RAG disabled. Error: {e}")

        # 3) LLM
        self.llm = None
        if not offline:
            try:
                self.llm = ChatTogether(
                    model="meta-llama/Llama-3-70b-chat-hf",
                    temperature=0.7,
                    max_tokens=1024,
                    api_key=os.getenv("TOGETHER")
                )
            except Exception as e:
                print(f"Warning: LLM initialization failed: {e}")

        # 4) Prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_MESSAGE),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 5) Agent
        self.agent = None
        if self.llm:
            try:
                self.agent = create_openai_functions_agent(
                    llm=self.llm,
                    prompt=self.prompt,
                    tools=self.tools
                )
            except Exception as e:
                print(f"Warning: Agent creation failed: {e}")
        
    def get_agent_executor(self, session_id: str) -> AgentExecutor:
        """Creates a new AgentExecutor instance with memory for a given session."""
        
        # History setup using Upstash (fallback to in-memory on failure)
        redis_history = None
        try:
            redis_history = UpstashRedisChatMessageHistory(
                url=os.getenv("UPSTASH_URL"),
                token=os.getenv("UPSTASH_TOKEN"),
                session_id=session_id,
                ttl=0
            )
        except Exception as e:
            print(f"Warning: Upstash disabled, using in-memory history. Error: {e}")

        chat_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=redis_history
        ) if redis_history else ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        if not self.agent:
            raise RuntimeError("Agent is not available. Check network/API keys or set OFFLINE=true for local UI testing.")

        # Agent Executor
        return AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=chat_memory,
            verbose=True,
            handle_parsing_errors=True
        )

# Initialize the service instance ONCE when Django starts
# bottom of service.py
_AG = None
def get_agent_service():
    global _AG
    if _AG is None:
        _AG = AyurVedaAgentService()
    return _AG
