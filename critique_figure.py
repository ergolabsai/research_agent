"""
Research Figure Critique AI Agent using smolagents and OpenRouter

This agent helps graduate students improve their figures by:
- Analyzing uploaded figures
- Asking critical questions a professor might ask
- Suggesting improvements to clarity and presentation
"""

import os
import base64
from PIL import Image
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel

# Set up your OpenRouter API key
os.environ["OPENROUTER_API_KEY"] = "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"

# Initialize the LLM model through OpenRouter (using a vision-capable model)
model = LiteLLMModel(
    model_id="openrouter/mistralai/pixtral-12b",
    api_key=os.environ["OPENROUTER_API_KEY"],
    api_base="https://openrouter.ai/api/v1"
)

# Create the agent with search capabilities
agent = CodeAgent(
    tools=[DuckDuckGoSearchTool()],
    model=model,
    max_steps=10
)


def encode_image(image_path):
    """Encode image to base64 for API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def critique_figure(image_path, research_area, figure_description, figure_conclusion):
    """
    Analyze a research figure and ask critical questions

    Args:
        image_path: Path to the figure image file
        research_area: The research field/area
        figure_description: Optional description of what the figure shows
    """

    # Encode the image
    image = Image.open(image_path)

    prompt = f"""
    I'm a first-year graduate student in {research_area}. I've created a research figure and need feedback.
    Here is a basic description of the figure:
    {figure_description}

    Please start by giving a basic critique of the figure.  Check for:
    
    1. **Data Clarity & Presentation**
       - Are the axes clearly labeled with units?
       - Is the data easy to interpret?
       - Are error bars/statistical measures shown where needed?
       
    2. **Design & Communication**
       - Is the color scheme accessible and clear?
       - Would a different plot type communicate the data better?
       - Is the figure legend complete and informative?
       - Are there any misleading visual elements?
    
    Next, let's determine if this figure actually supports my conclusions.  Here is my conclusions:
    Here is my conclusion:
    {figure_conclusion}
    Check for the following:
    
    1. **Scientific Rigor**
       - What alternative explanations are there for these results?
       - Are there sufficient statistics for the conclusion?

    2. **Context & Interpretation**
       - How does this compare to published literature?
       - What are the limitations of this data?

    Ask 4-6 specific, probing questions based on what you see in this figure. Be constructive but critical, like a good mentor would be.
    """

    # For models that support vision, we need to pass the image differently
    # This is a simplified version - you may need to adjust based on the exact API format
    result = agent.run(
        prompt,
        images=[image]
    )

    return result


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("RESEARCH FIGURE CRITIQUE ASSISTANT")
    print("=" * 60)
    print("\nUpload your figure and get critical feedback!\n")

    # Get information
    research_area = input("What is your research area/field? ")
    image_path = input("Enter the path to your figure (e.g., figure1.png): ").strip()

    # Check if file exists
    if not os.path.exists(image_path):
        print(f"\nError: Could not find file at {image_path}")
        exit()

    figure_desc = input("Briefly describe what this figure shows: ").strip()

    figure_conc = input("What key conclusions are you drawing from this figure?: ").strip()

    print(f"\n🔍 Analyzing your figure...\n")

    try:
        # Get critique
        critique = critique_figure(
            image_path=image_path,
            research_area=research_area,
            figure_description=figure_desc,
            figure_conclusion=figure_conc
        )

        print("\n" + "=" * 60)
        print("PROFESSOR'S QUESTIONS")
        print("=" * 60)
        print(critique)
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\nError analyzing figure: {e}")
        print("\nMake sure:")
        print("1. Your image file path is correct")
        print("2. The file is a common image format (PNG, JPG, etc.)")
        print("3. Your API key is set correctly")