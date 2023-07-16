import json
import requests
import pymongo
import pinecone
import datetime

vertex_api_key = "YOUR_VERTEX_API_KEY"
pinecone_environment = "YOUR_PINECONE_ENVIRONMENT"
pinecone_api = "YOUR_PINECONE_API"
mongodb_uri = "YOUR_MONGODB_URI"

client = pymongo.MongoClient(mongodb_uri)
db = client["chatbot"]
collection = db["conversations"]

client = pinecone.Client(pinecone_environment, pinecone_api)

def get_response(question):
    response = None

    # Check the MongoDB database
    memories = collection.find({"question": question})

    for memory in memories:
        response = memory["response"]
        break

    # Check the Pinecone database
    if response is None:
        response = client.query(question)

    # Use the Vertex API
    if response is None:
        response = requests.post(
            f"https://api.vertex.ai/v1/inference/{pinecone_environment}/models/{pinecone_api}",
            json={"question": question},
             headers={"Authorization": f"Bearer {vertex_api_key}"},
        )
        response_json = json.loads(response.content)
        response = response_json["answer"]

    # Upsert the time into the MongoDB database
    time = datetime.datetime.now()

    memory = {"question": question, "response": response, "time": time}

    collection.replace_one({"question": question}, memory, upsert=True)

    return response

def main():
    question = input("What is your question? ")

    # Add a system message to control the personality and time awareness
    personality = "friendly"
    time = datetime.datetime.now()

    if question == "personality":
        print("The current personality is '{}'.".format(personality))
        print("To change the personality, pass the personality as a system message.")
        print("For example, to set the personality to 'formal', you would pass the system message 'personality=formal'.")

    if question == "time":
        print("The current time is {}.".format(time))

    # Greet the user
    print("I'm Lexand, how can I help?")

    response = get_response(question)
    print(response)

if __name__ == "__main__":
    main()
