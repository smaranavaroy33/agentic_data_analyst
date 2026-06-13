from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

def get_chat_model():
    """
    Returns the primary Chat Model for the application.
    """
    # The client automatically picks up the NVIDIA_API_KEY environment variable
    return ChatNVIDIA(
        model="nvidia/nemotron-3-super-120b-a12b",
        temperature=0,
        max_tokens=16384,
        reasoning_budget=16384,
        chat_template_kwargs={"enable_thinking":True},
    )
