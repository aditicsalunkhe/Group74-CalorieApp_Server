import os
import pinecone
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.vectorstores import Pinecone
from langchain.llms import Replicate
from langchain.text_splitter import CharacterTextSplitter


chat_history = []
Replicate.api_key = os.getenv("REPLICATE_API_TOKEN")
PINECONE_API_KEY = os.getenv("PINCONE_API_KEY")
pinecone.init(api_key=PINECONE_API_KEY, environment='gcp-starter')
embeddings = HuggingFaceBgeEmbeddings()
index_name = "burnt"
index = pinecone.Index(index_name)


food_data_file_path = "./food_data/calories.csv"


def food_data_loader(food_data_file_path):
   food_data_loader = CSVLoader(file_path=food_data_file_path)
   food_data = food_data_loader.load()
   return food_data


def food_data_splitter(food_data):
   food_data_splitter = CharacterTextSplitter(chunk_size = 1000, chunk_overlap = 0)
   food_data_chunks = food_data_splitter.split_documents(food_data)
   return food_data_chunks
  
def get_qa_chain(llm, vectordb):
   return ConversationalRetrievalChain.from_llm(
       llm,
       vectordb.as_retriever(search_kwargs={'k':2})
   )


def get_burnbot_reply(user_query, chat_history):
   food_data = food_data_loader(food_data_file_path)


   food_data_chunks = food_data_splitter(food_data)


   vectordb = Pinecone.from_documents(food_data_chunks, embeddings, index_name = index_name)


   llm = Replicate(
       model = "a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5",
       model_kwargs = {"temperature": 0.5, "max_length": 3000}
   )


   qa_chain = get_qa_chain(llm, vectordb)


   result = qa_chain({'question': user_query, 'chat_history': chat_history})
   return result


def main():
   pass


if __name__ == "__main__":
   main()
