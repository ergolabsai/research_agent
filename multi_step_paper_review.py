
class ReviewSession():

    def __init__(self):
        pass

    def load_document(self):
        pass

    def make_agent(self):
        pass

    def ask(self):
        pass

    def describe_figures(self):
        pass

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


if __name__ == '__main__':

    review = ReviewSession()

    review.load_document()
    review.make_agent()
    review.compare_figures_to_paper()
    review.evaluated_supporting_findings()
    review.look_for_unstated_issues()
    review.discuss_reliability()
    review.make_figure_visualization()
    review.make_logic_visualization()
