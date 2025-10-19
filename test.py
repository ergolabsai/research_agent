"""
AI Agent using smolagents and instructor with Claude - Image Analysis
"""

from smolagents import (
    CodeAgent,
    tool
)
import instructor
from anthropic import Anthropic
from pydantic import BaseModel, Field
from typing import List
import base64

# Set up instructor with Anthropic Claude
client = instructor.from_anthropic(Anthropic())


# Define structured output model
class ImageAnalysis(BaseModel):
    """Structured analysis of an image"""
    description: str = Field(description="Detailed description of the image")
    objects_detected: List[str] = Field(description="List of objects or elements in the image")
    scene_type: str = Field(description="Type of scene (indoor, outdoor, product, etc.)")
    colors: List[str] = Field(description="Dominant colors in the image")
    suggested_use_cases: List[str] = Field(description="Potential use cases for this image")
    quality_score: float = Field(description="Image quality score from 0-1")


# Create a tool for analyzing images with structured output
@tool
def analyze_image(image_path: str) -> str:
    """
    Analyzes an image and returns structured information about it.

    Args:
        image_path: Path to the image file to analyze

    Returns:
        A structured analysis of the image
    """
    # Read and encode the image
    with open(image_path, "rb") as image_file:
        image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")

    # Determine image type from extension
    if image_path.lower().endswith('.png'):
        media_type = "image/png"
    elif image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
        media_type = "image/jpeg"
    elif image_path.lower().endswith('.gif'):
        media_type = "image/gif"
    elif image_path.lower().endswith('.webp'):
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"  # default

    # Use instructor with Claude to get structured analysis
    analysis = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        response_model=ImageAnalysis,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Analyze this image in detail. Identify objects, describe the scene, note dominant colors, and suggest potential use cases."
                    }
                ],
            }
        ],
    )

    # Format the structured output
    objects_text = "\n".join([f"  • {obj}" for obj in analysis.objects_detected])
    colors_text = ", ".join(analysis.colors)
    use_cases_text = "\n".join([f"  • {use}" for use in analysis.suggested_use_cases])

    return f"""Image Analysis Results:

Description:
  {analysis.description}

Objects Detected:
{objects_text}

Scene Type: {analysis.scene_type}

Dominant Colors: {colors_text}

Suggested Use Cases:
{use_cases_text}

Quality Score: {analysis.quality_score:.2%}"""


# Initialize the agent
def create_image_agent():
    """Creates an AI agent with image analysis capabilities using Claude"""

    from smolagents import LiteLLMModel
    model = LiteLLMModel(model_id="anthropic/claude-sonnet-4-5-20250929")

    agent = CodeAgent(
        tools=[analyze_image],
        model=model,
        max_steps=5,
        verbosity_level=1
    )

    return agent


# Example usage
if __name__ == "__main__":
    # Create the agent
    agent = create_image_agent()

    print("=" * 60)
    print("Image Analysis with Claude Agent")
    print("=" * 60)

    # Analyze an image
    result = agent.run(
        "Analyze the image at 'example_image.jpg' and provide a structured breakdown."
    )
    print(result)