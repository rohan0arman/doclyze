import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError


SUMMARIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a document summarizer. Provide a clear, concise summary in 5-10 sentences."),
    ("human", "Summarize the following document:\n\n{text}"),
])

COMBINE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a document summarizer. Combine the following partial summaries into one coherent summary of 5-10 sentences."),
    ("human", "Partial summaries:\n\n{text}"),
])


def summarize_text(text: str, google_api_key: str) -> str:
    """Summarize document text using LangChain + Google Gemini."""
    if not text.strip():
        return "Document is empty or could not be parsed."

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        api_key=google_api_key,
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=8000,
        chunk_overlap=200,
    )
    chunks = splitter.split_text(text)

    try:
        if len(chunks) == 1:
            chain = SUMMARIZE_PROMPT | llm
            result = chain.invoke({"text": chunks[0]})
            return result.content

        partial_summaries = []
        for chunk in chunks:
            chain = SUMMARIZE_PROMPT | llm
            result = chain.invoke({"text": chunk})
            partial_summaries.append(result.content)

        combined_text = "\n\n".join(partial_summaries)
        chain = COMBINE_PROMPT | llm
        result = chain.invoke({"text": combined_text})
        return result.content
    
    except ChatGoogleGenerativeAIError as e:
        error_msg = str(e)
        if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
            return (
                "Error: Google Gemini API quota exceeded. "
                "Please enable billing on your Google Cloud project or try again later. "
                "Visit: https://console.cloud.google.com/billing"
            )
        elif "UNAUTHENTICATED" in error_msg or "401" in error_msg:
            return "Error: Invalid Google API key. Please check your GOOGLE_API_KEY in .env file."
        else:
            return f"Error: {error_msg}"
