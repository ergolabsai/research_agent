import os
from pathlib import Path
from PIL import Image
from output_classes import *
import instructor
from anthropic import Anthropic
from smolagents import LiteLLMModel, DuckDuckGoSearchTool, ToolCallingAgent
import base64
import io
from pydantic import BaseModel
from create_plots import ask_claude_for_plot
import shutil

SIMPLIFY = False
MAKE_PLOTS = False

# Set up your OpenRouter API key
os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["CLAUDE_API_KEY"] = "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"

class ReviewSession:

    def __init__(self):
        self.tex_folder = ''
        self.client = instructor.from_anthropic(Anthropic(api_key=os.environ.get("CLAUDE_API_KEY")))
        self.model_id = "claude-sonnet-4-5-20250929"

        self.context = ''
        self.current_context = None
        self.text = ''
        self.images = []
        self.media_types = []
        self.current_response_model = BaseModel
        self.current_request = ""
        self.current_media_type = []
        self.current_image_data = []
        self.current_response = ''
        self.expected_descriptions = {}
        self.figure_differences = {}
        self.figure_similarities = {}
        self.claim_confirmations = {}
        self.claim_contradictions = {}
        self.question = ''
        self.answer = ''
        self.review = ''
        self.supporting_claims_dict = {}
        self.image_names = []


    def ask(self, use_image=False, use_context=False):

        content = [{"type": "text",
                    "text": self.current_request}]
        if use_image:
            for image, media in zip(self.current_image_data, self.current_media_type):
                content = content + [{"type": "image", "source": {"type": "base64", "media_type": media, "data": image}}]

        api_params = {
            "model": self.model_id,
            "max_tokens": 4096,
            "response_model": self.current_response_model,
            "messages": [{"role": "user", "content": content}]
        }

        if use_context:
            api_params["system"] = [{"type": "text", "text": self.current_context}]

        self.current_response = self.client.messages.create(**api_params)

    def load_document(self, tex_folder, max_dim=800):
        print('loading document')
        self.tex_folder = Path(tex_folder)
        txt_file = self.tex_folder / 'main_text.tex'
        with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        self.text = text

        filenames = []
        images = {}
        media_types = {}

        image_folder = self.tex_folder / 'images'

        image_files = list(image_folder.iterdir())

        for img_path in image_files:

            img, media_type = encode_image(img_path)

            filenames.append(img_path.name)
            images[img_path.name] = img
            media_types[img_path.name] = media_type

        self.image_names = filenames
        self.images = images
        self.media_types = media_types

        return {'text': text, 'images': images, 'filenames': filenames, 'media_types': media_types}

    def create_context(self):
        print('creating context')
        self.current_request = """You are reviewing a paper for publication.  
You are going to use Claude to assist you.  You want to create context for claude requests.  
Please generate context that would be helpful to you in future API calls but that would not bias you towards the author's conclusions and instead would help you generate useful answers about the figures without having to read the text.
Here is my text {}""".format(self.text)
        self.current_response_model = ContextString
        self.ask()
        self.context = self.current_response.context

    def create_expected_figure_descriptions(self):
        print('creating expected figure descriptions')
        kk = 0
        for image_name in self.image_names:
            if SIMPLIFY:
                if kk > 0:
                    break
                kk = kk + 1
            self.current_response_model = ExpectedFigureDescription
            self.current_request = "Read the text for this paper and tell me what you expect the figure {} to look like.  Here is the text {}".format(image_name, self.text)
            self.ask()
            if MAKE_PLOTS:
                ask_claude_for_plot(self.current_response.description)
                destination_path = os.path.join('/Users/chelsea/python_projects/project_files/outputs',
                                                'expectation_' + image_name)
                shutil.move('reconstructed_figure.jpg', destination_path)
            self.expected_descriptions[image_name] = self.current_response.description

    def compare_expected_figure_to_figure(self):
        print('comparing expected figure descriptions')
        kk=0
        for image_name in self.image_names:
            if SIMPLIFY:
                if kk > 0:
                    break
                kk = kk + 1
            self.current_request = """
You are reviewing a paper and have created an description of what you expect the figure {} to look like.
{}
Evaluate which features are similar between the figure and where the expected figure and original figure are different.
Return your answer as a dictionary of differences and similarties.""".format(image_name, self.expected_descriptions[image_name])
            self.current_response_model = Comparison
            self.current_image_data = [self.images[image_name]]
            self.current_media_type = [self.media_types[image_name]]
            self.current_context = self.context
            self.ask(use_image=True, use_context=True)
            self.figure_similarities[image_name] = self.current_response.similarities
            self.figure_differences[image_name] = self.current_response.differences

    def make_figure_differences_and_similarities(self):
        print('making figure differences and similarities')
        self.create_context()
        self.create_expected_figure_descriptions()
        self.compare_expected_figure_to_figure()

    def get_supporting_findings(self):
        print('getting supporting findings')
        figure_names = ", ".join(self.image_names)
        self.current_request = """
Please read the article and find the main question being asked, the article's answer to the question, and the supporting claims.
For each claim, list the evidence for the claim.
Include which figures are relevant, any specific numeric values quoted, and citations.
Finally assign an importance score from 1 to n, where n is the number of claims and 1 is the most important claim.
Return the following as a dictionary in the form:

("question": "the main question in 2-3 sentences",
"answer": "the author's answer",
"supporting_claims": ("importance score":
    ("description": "3-4 sentence description of claim.",
    "Figure": "value": "number", "units": "unit", "source": ))))

When you list the figure, write the name of the figure from this list: {}

Here is the text of the document in latex format:
""".format(figure_names) + self.text
        self.current_response_model = ResearchAnalysis
        self.ask()
        self.question = self.current_response.question
        self.answer = self.current_response.answer
        self.supporting_claims_dict = self.current_response.supporting_claims

    def find_claims_for_figure(self, figure_name):
        figure_claims_list = []
        for key in self.supporting_claims_dict.keys():
            for figure in self.supporting_claims_dict[key].figures:
                if figure.name == figure_name:
                    figure_claims_list = figure_claims_list + [key]

        return figure_claims_list

    def combine_figure_findings_and_supporting_findings(self):
        print('combining figure findings and supporting findings')
        self.claim_confirmations = {i: {} for i in self.supporting_claims_dict.keys()}
        self.claim_contradictions = {i: {} for i in self.supporting_claims_dict.keys()}
        kk = 0
        for figure_name in self.image_names:
            if SIMPLIFY:
                if kk > 0:
                    break
                kk = kk + 1
            claims_list = self.find_claims_for_figure(figure_name)
            for claim in claims_list:
                self.current_request = """The following is a claim from a paper you are reviewing using evidence from the figure {}:
{}
You have previously compared this figure to how the text describes it.  These are the key differences you found: {}
Here are the key confirmed observations: {}
Create a list of how differences undermine the claim validity.
Make a list of how confirmations support the claim validity.  
Do not include confirmations or differences that are not scientifically impactful such as formatting.""".format(figure_name, self.supporting_claims_dict[claim].description, self.figure_differences[figure_name], self.figure_similarities[figure_name])
                self.current_response_model = ClaimValidity
                self.ask()
                self.claim_confirmations[claim].update({figure_name: self.current_response.confirmations})
                self.claim_contradictions[claim].update({figure_name: self.current_response.contradictions})

    def evaluate_supporting_findings(self):
        print('evaluating supporting findings')
        self.get_supporting_findings()
        self.combine_figure_findings_and_supporting_findings()

    def discuss_reliability(self):
        print('building claim request')
        claim_request = """The following are a set of claims made in a paper you are reviewing.  
Along with each claim is a set of a set of confirmations and contradictions of the claim based on a separate review of the relevant figures.
Use these observations to evaluate the overall validity of the author's final conclusion, which is:
{}
""".format(self.answer)
        for claim_key in self.supporting_claims_dict.keys():
            claim_request = claim_request + 'first claim: ' + self.supporting_claims_dict[claim_key].description
            for figure_key in self.claim_confirmations[claim_key].keys():
                claim_request = claim_request + '\nRelevant confirmations from figure {}:  '.format(figure_key) + ".  ".join(self.claim_confirmations[claim_key][figure_key])
            for figure_key in self.claim_contradictions[claim_key].keys():
                claim_request = claim_request + '\nRelevant contradictions from figure {}:  '.format(figure_key) + ".  ".join(self.claim_contradictions[claim_key][figure_key])

        self.current_request = claim_request
        self.current_response_model = OverAllReview
        self.current_context = self.context
        self.ask(use_context=True)
        self.review = self.current_response.review


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
    review.make_figure_differences_and_similarities()
    review.evaluate_supporting_findings()
    review.discuss_reliability()

