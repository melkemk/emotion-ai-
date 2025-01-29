
## Open the Application

1. **Start the Flask server** by running the `app.py` script.
2. **Open your web browser** and navigate to `http://localhost:5000`.

## Adjust Emotional Parameters

- You will see several sliders labeled "Valence", "Arousal", "Selection Threshold", "Resolution Level", "Goal-Directedness", and "Securing Rate".
- Adjust these sliders to set the emotional parameters. Each slider ranges from 1 to 7.

## Send a Message

- Type your message in the input box at the bottom of the screen.
- Press the "Enter" key or click the "Send" button to send your message.

## View the Response

- The application will process your message and the emotional parameters.
- The response from the AI will be displayed in the chat container along with the emotional indicators for anger and sadness.

## Emotional Indicators

- The current levels of anger and sadness will be displayed as bars in the "Emotion Indicators" section.
- These levels are updated based on the response from the AI.


This script sets up a Flask web application that uses the LangChain and Groq APIs to process chat messages and analyze emotional content.

Modules:
- dotenv: Loads environment variables from a .env file.
- flask: A micro web framework for Python.
- flask_cors: A Flask extension for handling Cross-Origin Resource Sharing (CORS).
- langchain_community.chat_message_histories: Manages chat message histories.
- langchain_groq: Provides access to the Groq API for language models.
- pydantic: Data validation and settings management using Python type annotations.
- os: Provides a way of using operating system dependent functionality.
- json: Provides methods for parsing JSON.

Classes:
- EmotionOutput: A Pydantic model for validating the output of the emotion analysis.

Functions:
- load_dotenv: Loads environment variables from a .env file.
- get_history(user_id): Retrieves or initializes the chat message history for a given user.
- index(): A route that returns a simple greeting message.
- chat_route(): A route that processes chat messages, analyzes emotional content, and returns the results.

Routes:
- '/': Returns a JSON message saying "Hello, world!".
- '/chat': Accepts POST requests with user messages and parameters, processes the messages, and returns emotional analysis and AI responses.

Environment Variables:
- GROQ_API_KEY: The API key for accessing the Groq API.

Usage:
1. Ensure that the required environment variables are set.
2. Run the script to start the Flask web application.
3. Send POST requests to the '/chat' endpoint with the required parameters to receive emotional analysis and AI responses.
This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
