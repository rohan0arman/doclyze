from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


SUMMARIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a document summarizer. Provide a clear, concise summary in 5-10 sentences."),
    ("human", "Summarize the following document:\n\n{text}"),
])

COMBINE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a document summarizer. Combine the following partial summaries into one coherent summary of 5-10 sentences."),
    ("human", "Partial summaries:\n\n{text}"),
])


def summarize_text(text: str, openai_api_key: str) -> str:
    """Summarize document text using LangChain + OpenAI."""
    if not text.strip():
        return "Document is empty or could not be parsed."

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=openai_api_key,
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=8000,
        chunk_overlap=200,
    )
    chunks = splitter.split_text(text)

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
