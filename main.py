"""
Graduate Research Assistant AI Agent using smolagents and OpenRouter

This agent helps first-year graduate students navigate their research by:
- Answering questions about their research topic
- Finding relevant literature and resources
- Explaining complex concepts
- Suggesting research directions
"""

import os
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel

# Set up your OpenRouter API key
os.environ["OPENROUTER_API_KEY"] = "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"

# Initialize the LLM model through OpenRouter
model = LiteLLMModel(
    model_id="openrouter/deepseek/deepseek-chat",
    api_key=os.environ["OPENROUTER_API_KEY"],
    api_base="https://openrouter.ai/api/v1"
)

# Create the agent with search capabilities
agent = CodeAgent(
    tools=[DuckDuckGoSearchTool()],
    model=model,
    max_steps=10
)

def answer_research_question(research_area, question):
    """
    Answer a graduate student's research question

    Args:
        research_area: The student's general research area/field
        question: The specific question they have
    """

    prompt = f"""
    I'm a first-year graduate student working in {research_area}.
    
    My question is: {question}
    
    Please help me by:
    1. Searching for relevant, current information to answer this question
    2. Explaining the answer in a clear, educational way
    3. Providing citations or references to key papers/resources if relevant
    4. Suggesting related topics or questions I should explore
    
    Remember I'm just starting out, so please explain technical concepts clearly.
    """

    result = agent.run(prompt)
    return result

# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("GRADUATE RESEARCH ASSISTANT")
    print("=" * 60)
    print("\nWelcome! I'm here to help you with your research questions.")

    # Get research area
    research_area = input("\nWhat is your research area/field? ")

    print("\nGreat! Now you can ask me questions about your research.")
    print("Type 'quit' to exit.\n")

    # Interactive question loop
    while True:
        question = input("\nYour question: ").strip()

        if question.lower() in ['quit', 'exit', 'q']:
            print("\nGood luck with your research!")
            break

        if not question:
            continue

        print(f"\n🔍 Researching your question...\n")

        # Get answer
        answer = answer_research_question(research_area, question)

        print("\n" + "=" * 60)
        print("ANSWER")
        print("=" * 60)
        print(answer)
        print("\n" + "=" * 60)