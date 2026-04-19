from gemini import Gemini

# Replace these with your actual cookie values
cookies = {
    "__Secure-1PSID": "g.a0009AjZKKdp-GwZ5hDDCe1KcnZx38vFL_WlxG-fj8PPqoKlDTereWgruZ0l8X4BsPiTVK8_5QACgYKAR0SARYSFQHGX2MiySpeecaB9u3bvU_IdBua0hoVAUF8yKqwFi744s2Yam4qi2rHp1iL0076",
    "__Secure-1PSIDTS": "sidts-CjcBWhotCbjiR7qrx7t4LetgUjg-_WYOe87M0E9J4jmaLhF01OZqRoa4Yq6GEEMcNVvay58NK1v7EAA",
    "__Secure-1PSIDCC": "AKEyXzV6rKPk5Ozws4860vfGzTbpAVTolNUv_b67YSC_KWKfdYoEDsYjLRxN5uzvy-YnQbKFCY0",
}

# Initialize the client
client = Gemini(cookies=cookies)

chat_log = []  # List to store the conversation history locally

print("Chat started. Type 'quit' to exit.")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "exit"]:
        break

    # Add user message to history
    chat_log.append({"role": "user", "content": user_input})

    # Generate response
    response = client.generate_content(user_input)
    model_text = response.text

    # Add model response to history
    chat_log.append({"role": "model", "content": model_text})

    print(f"Gemini: {model_text}\n")

# Optional: Save the history to a file when finished
with open("chat_history.txt", "w") as f:
    for entry in chat_log:
        f.write(f"{entry['role'].capitalize()}: {entry['content']}\n")