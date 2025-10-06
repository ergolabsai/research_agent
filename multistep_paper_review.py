import os
from smolagents import ToolCallingAgent, DuckDuckGoSearchTool, LiteLLMModel
from pdf2image import convert_from_path
import PyPDF2
import pymupdf
from PIL import Image
import json
import re

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
chosen_agent = ToolCallingAgent(
    tools=[DuckDuckGoSearchTool()],
    model=model,
    max_steps=10
)

class ReviewSession:
    def __init__(self, agent, pdf_text, page_images):
        self.agent = agent
        self.page_images = page_images
        self.pdf_text = pdf_text
        self.current_prompt = ''
        self.current_result = ''
        self.history = []

        self.main_research_question = ''
        self.key_finding = ''
        self.supporting_findings = ''
        self.current_json_response = ''

    def ask(self, include_history=True):
        """Ask a question with optional history context"""

        if include_history and self.history:
            # Build context from previous steps
            context = "Previous analysis:\n\n"
            for i, step in enumerate(self.history):
                context += f"STEP {i + 1}:\n{step['result']}\n\n"

            full_prompt = context + self.current_prompt
        else:
            full_prompt = self.current_prompt

        self.current_result = self.agent.run(full_prompt, images=self.page_images)

        self.history.append({
            "prompt": self.current_prompt,
            "result": self.current_result
        })


    def write_start_of_review_prompt(self, research_area):

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
        Therefore, do not believe the author.  Instead, assume that they could be making intentional or unintentional logical errors.

        Please read the article and find the main question being asked, the article's answer to the question, and the supporting claims.
        For each claim, list the evidence for the claim.
        Include which figures are relevant, any specific numeric values quoted, and citations.
        Finally assign an importance score from 1 to n, where n is the number of claims and 1 is the most important claim.
        Return the following in ONLY valid JSON (no markdown, no extra text):
        
        {{"question": "the main question in 2-3 sentences",
        "answer": "the author's answer to this question",
        "supporting_claims": {{"3-4 word claim description",
            {{"description": "3-4 sentence description of claim.",
            "evidence_figures": ["Figure n", "Figure m"],
            "evidence_numbers": {{"1-2 word description": {{"value": "number", "units": "unit", "source": "Figure(s) or citation"}},
            "1-2 word description": {{"value": "number", "units": "unit", "source": "Figure(s), or citation"}}}},
            "evidence_citations": ["Author year"],
            "importance": "number"}}}}}}

        I am attaching the image of the document, and the text of the document: {self.pdf_text}

        """

        self.current_prompt = prompt

    def ingest_findings(self):

        json_response = json.loads(review.current_result)

        self.current_json_response = json_response


    def write_describe_figures_prompt(self):

        prompt = f"""
        Look at each figure and create a description of what is happening in the plot.  
        Focus on constructing a description that is based on the figure itself, not how it is described in the text.
        
        Format your answer in ONLY JSON format (no markdown, no extra text) like this:
        
        {{"figure number": "description in less than 10 sentences"}}
        
        """

        self.current_prompt = prompt


def extract_pdf_text(pdf_path):

    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            text += f"\n--- Page {page_num + 1} ---\n"
            text += page.extract_text()

        return text


def pdf_to_images(pdf_path, max_pages=10):

    print(f"Converting PDF to images (max {max_pages} pages)...")
    page_images = convert_from_path(pdf_path, first_page=1, last_page=max_pages)
    print(f"Converted {len(page_images)} pages")

    return page_images


def extract_pdf_content(pdf_path, output_dir="extracted_content"):

    print(f"Extracting content from {pdf_path}...")

    # Extract text
    print("\nExtracting text...")
    text = extract_pdf_text(pdf_path)

    # Extract figures
    print("\nExtracting figures...")
    pages = pdf_to_images(pdf_path)

    print(f"\nExtraction complete:")
    print(f"  - Text: {len(text)} characters")
    print(f"  - Figures: {len(pages)} pages")

    return {
        'text': text,
        'pages': pages
    }


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("JOURNAL ARTICLE REVIEW ASSISTANT")
    print("=" * 60)
    print("\nUpload your article and get critical feedback!\n")

    # Get information
    research_area = 'plasma physics' #input("What is your research area/field? ")
    file_path = '/Users/chelsea/python_projects/project_files/shumlak2009.pdf' #input("Enter the path to your article (e.g., paper.pdf): ").strip()

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"\nError: Could not find file at {file_path}")
        exit()

    print(f"\n🔍 Reading the article...\n")

    pdf_content = extract_pdf_content(file_path)

    review = ReviewSession(chosen_agent, pdf_content['text'], pdf_content['pages'])

    review.write_start_of_review_prompt(research_area)
    review.ask()

    review.write_describe_figures_prompt()
    review.ask()




