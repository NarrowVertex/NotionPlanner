from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_core.documents import Document

import os
from dotenv import load_dotenv
import uuid

class RAG:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

        load_dotenv("../.env")
        embedding_deployment = os.getenv("OEPNAI_EMBEDDING_DEPLOYMENT")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_api_version = os.getenv("OPENAI_API_VERSION")
        if not embedding_deployment:
            raise ValueError("Missing OPENAI_EMBEDDING_DEPLOYMENT in environment variables")
        if not openai_api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment variables")
        if not openai_api_version:
            raise ValueError("Missing OPENAI_API_VERSION in environment variables")

        self.embeddings = OpenAIEmbeddings(
            model=embedding_deployment,
            openai_api_key=openai_api_key,
            openai_api_base="https://api.openai.com/v1",
            openai_api_version=openai_api_version,
            openai_api_type="open_ai",
        )

        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            persist_directory=f"./{self.path}/chroma.db",
            collection_name=self.name,
        )

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 1}
        )

    def add_document(self, data: str):
        metadata = {"id": str(uuid.uuid4())}
        document = Document(page_content=data, metadata=metadata)
        
        self.vector_store.add_documents(
            [document], embeddings=self.embeddings, ids=[metadata["id"]]
        )
        return metadata["id"]

    def update_document(self, id: str, data: str):
        metadata = {"id": id}
        new_document = Document(page_content=data, metadata=metadata)

        self.vector_store.update_document(
            id, 
            new_document
        )
    
    def delete_document(self, id: str):
        self.vector_store.delete(ids=[id])

    def get_document(self, id: str):
        document = self.vector_store.get(ids=[id])
        return document

    def search(self, query: str):
        results = self.retriever.invoke(query)

        context = ""
        for document in results:
            context += document.page_content

        return context
    

if __name__ == "__main__":
    rag = RAG("test_collection")
    """
    # Add a document
    id = rag.add_document("This is a test document.")
    print(f"Document ID: {id}")
    pprint(rag.get_document(id))

    # Update the document
    rag.update_document(id, "This is an updated test document.")
    pprint(rag.get_document(id))
    """
    # Delete the document
    rag.delete_document("290169ba-e938-445f-b680-6882bdc97593")

