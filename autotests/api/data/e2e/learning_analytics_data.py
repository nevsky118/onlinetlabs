# Test data generators for the Learning Analytics e2e tests.


class MCPContextTestData:
    """
    Test data for the e2e check of the MCP → AgentContext → LLM pipeline.

    :ivar project_name: GNS3 project name.
    :ivar user_question: Student question for the TutorAgent.
    :ivar struggle_type: Problem type for the AgentContext.
    :ivar dominant_error: Dominant error.
    """

    def __init__(self):
        self.project_name = "e2e-la-test"
        self.user_question = "Почему PC1 и PC2 не могут обмениваться данными?"
        self.struggle_type = "repeating_errors"
        self.dominant_error = "VLAN 10 not found"


class HintTestData:
    """
    Test data for checking the HintAgent.

    :ivar step_slug: The step where the student got stuck.
    :ivar last_error: Last error.
    :ivar attempts_count: Number of attempts, which determines hint_level.
    """

    def __init__(self, attempts_count: int = 4):
        self.step_slug = "step-1"
        self.last_error = "VLAN 10 not found on SW1"
        self.attempts_count = attempts_count
