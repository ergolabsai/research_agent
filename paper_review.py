"""
Journal Article Review AI Agent using smolagents and OpenRouter

This agent helps graduate students critically review journal articles by:
- Reading and analyzing uploaded papers
- Asking critical questions a professor might ask
- Identifying strengths, weaknesses, and gaps
"""

import os
from smolagents import ToolCallingAgent, DuckDuckGoSearchTool, LiteLLMModel
from pdf2image import convert_from_path

# Set up your OpenRouter API key
os.environ["OPENROUTER_API_KEY"] = "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"

# Initialize the LLM model through OpenRouter
# Using GPT-4o Mini - affordable and reliable
model = LiteLLMModel(
    # model_id="openrouter/openai/gpt-4o-mini",
    model_id="openai/gpt-4.1-mini",
    api_key=os.environ["OPENROUTER_API_KEY"],
    api_base="https://openrouter.ai/api/v1"
)

# Create the agent with search capabilities
agent = ToolCallingAgent(
    tools=[DuckDuckGoSearchTool()],
    model=model,
    max_steps=10
)


def pdf_to_images(pdf_path, max_pages=10):
    """
    Convert PDF pages to images

    Args:
        pdf_path: Path to the PDF file
        max_pages: Maximum number of pages to convert (to manage costs)

    Returns:
        List of PIL Image objects
    """
    print(f"Converting PDF to images (max {max_pages} pages)...")
    page_images = convert_from_path(pdf_path, first_page=1, last_page=max_pages)
    print(f"Converted {len(page_images)} pages")
    return page_images


def review_article(file_path, research_area, max_pages=10):
    """
    Review a journal article and provide critical analysis

    Args:
        file_path: Path to the article (PDF, TXT, or other text file)
        research_area: The research field/area
        max_pages: Maximum number of pages to analyze
    """

    # Read the article
    try:
        page_images = pdf_to_images(file_path, max_pages=max_pages)
    except Exception as e:
        return f"Error reading file: {e}"

    prompt = f"""
    Assume you are a seasoned {research_area} researcher who is really good at identifying problematic research and analysis techniques.
    People in your field appreciate your honest and useful feedback.
    
    One of the key reasons you are so respected for this work is because you are really good at identifying where people make leaps in their causal associations.
    You have a deep understanding for why this happens.  
    Researchers are pushed by a multitude of factors to over-inflate claims or overlook logical errors and they can tend to cherry pick data.
    A good reviewer can catch these things, but it is hard to do, especially because the readers are good at filling in the blanks in the author's favor.
    
    With all this in mind, before you is a journal article up for review.  
    You really care about ensuring that the papers in your field are accurate so you take on an adversarial position against the paper to make sure you're best instincts for excellent science are heightened.  
    You goal is to make sure the logic in the paper is sound.
    
    In order to do this review we will go through the following steps in order to make a map of the paper's logical conclusions for proper consideration:
    1) summarize the paper
    2) determine the key findings associated with each figure
    3) judge the findings of each figure
    4) identify other supporting evidence that are only supported by text
    5) judge this evidence
    6) create a map of the logic that brings the author to their conclusions
    7) evaluate the map to make a statement about what logical conclusions could be suspect and provide a recommendation as to how to address these concerns
    
    We will do this in stages so that the I can give you feedback.  Let's start with step 1.  

    Please read the article and provide the following:

    1. **Summary** (2-3 sentences)
       - What is the main research question?
       - What are the key findings?

    2. **Figures**
       - Tabulate what the key conclusions of each figure is 
    2. **Key causal claims**
       - What is the key causal claim in this paper?
       - What are the key pieces of evidence that support this claim?
       - What are the key citations that contribute to this claim?
       
    3. **Supporting claims**
       - What other cause-effect relationships must be true for the primary claim to hold?
       - What are the key pieces of evidence that support each claim?
       - Are there any citations that are required for these supporting claims?
       
    After you are done with these evaluations, double check, are there any claims that are asserted without direct evidence in this paper?

    """

    result = agent.run(prompt, images=page_images)
    return result


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("JOURNAL ARTICLE REVIEW ASSISTANT")
    print("=" * 60)
    print("\nUpload your article and get critical feedback!\n")

    # Get information
    research_area = input("What is your research area/field? ")
    file_path = input("Enter the path to your article (e.g., paper.pdf): ").strip()

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"\nError: Could not find file at {file_path}")
        exit()

    # Ask about page limit
    max_pages_input = input("How many pages to analyze? (default: 10, more pages = higher cost): ").strip()
    max_pages = int(max_pages_input) if max_pages_input.isdigit() else 10

    print(f"\n🔍 Reading and analyzing the article...\n")
    print("This may take a minute or two...\n")

    try:
        # Get review
        review = review_article(
            file_path=file_path,
            research_area=research_area,
            max_pages=max_pages
        )

        print("\n" + "=" * 60)
        print("ARTICLE REVIEW")
        print("=" * 60)
        print(review)
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\nError analyzing article: {e}")
        print("\nMake sure:")
        print("1. Your file path is correct")
        print("2. The file is a PDF format")
        print("3. Your API key is set correctly")
        print("4. Poppler is installed (brew install poppler on Mac)")