import os
from pathlib import Path
from PIL import Image
from output_classes import FigureDescription
import instructor
from anthropic import Anthropic
from smolagents import LiteLLMModel, DuckDuckGoSearchTool, ToolCallingAgent
import base64
import io

# Set up your OpenRouter API key
os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["CLAUDE_API_KEY"] = "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"

class ReviewSession:

    def __init__(self):
        self.tex_folder = ''
        self.client = instructor.from_anthropic(Anthropic(
            api_key=os.environ.get("CLAUDE_API_KEY")
        ))
        self.model_id = "claude-sonnet-4-5-20250929"

    def load_document(self, tex_folder, max_dim=800):
        self.tex_folder = Path(tex_folder)
        txt_file = self.tex_folder / 'main_text.tex'
        with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        self.text = text

        images = []
        filenames = []
        media_types = []

        image_folder = self.tex_folder / 'images'

        image_files = list(image_folder.iterdir())

        for img_path in image_files:

            img, media_type = encode_image(img_path)

            filenames.append(img_path.name)
            images.append(img)
            media_types.append(media_type)

        self.images = images
        self.media_types = media_types
        self.filenames = filenames


        return {'text': text, 'images': images, 'filenames': filenames, 'media_types': media_types}

    def ask(self):
        self.current_response = self.client.messages.create(
            model=self.model_id,
            max_tokens=4096,
            response_model=self.current_response_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": self.current_media_type,
                                "data": self.current_image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": self.current_content
                        }
                    ],
                }
            ],
        )
    def describe_figures(self):
        self.current_response_model = FigureDescription
        self.current_content = "Make a description of this plot that could be used to reconstruct the image."
        self.current_media_type = self.media_types[0]
        self.current_image_data = self.images[0]
        self.ask()

    def create_expected_figure_description(self):
        pass

    def compare_figures_to_paper(self):
        self.create_expected_figure_description()
        self.describe_figures()

    def get_supporting_findings(self):
        pass

    def check_supporting_findings(self):
        pass

    def combine_figure_findings_and_supporting_findings(self):
        pass

    def cross_reference_supporting_findings(self):
        pass

    def evaluated_supporting_findings(self):
        self.get_supporting_findings()
        self.check_supporting_findings()
        self.combine_figure_findings_and_supporting_findings()
        self.cross_reference_supporting_findings()

    def look_for_unstated_issues(self):
        pass

    def discuss_reliability(self):
        pass

    def make_figure_visualization(self):
        pass

    def make_logic_visualization(self):
        pass


def encode_image(image_path: Path, max_size=800) -> tuple[str, str]:
        # Resize if image is larger than max_size

    # Open the image
    img = Image.open(image_path)

    if max(img.size) > max_size:
        # Calculate new size maintaining aspect ratio
        ratio = max_size / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Determine format and media type from extension
    if image_path.name.endswith('.png'):
        img_format = "PNG"
        media_type = "image/png"
    elif image_path.name.endswith('.jpg') or image_path.name.endswith('.jpeg'):
        img_format = "JPEG"
        media_type = "image/jpeg"
    elif image_path.name.endswith('.gif'):
        img_format = "GIF"
        media_type = "image/gif"
    elif image_path.name.endswith('.webp'):
        img_format = "WEBP"
        media_type = "image/webp"
    else:
        img_format = "JPEG"
        media_type = "image/jpeg"

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format=img_format)
    image_data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")


    return image_data, media_type


if __name__ == '__main__':

    review = ReviewSession()

    review.load_document('/Users/chelsea/python_projects/project_files/shumlak2009_latex')
    review.compare_figures_to_paper()
    review.evaluated_supporting_findings()
    review.look_for_unstated_issues()
    review.discuss_reliability()
    review.make_figure_visualization()
    review.make_logic_visualization()
