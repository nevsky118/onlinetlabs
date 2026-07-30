import json
from pathlib import Path

from autotests.settings.utils.utils import get_current_test_name, get_path_file


class DataAbstractionGenerator:
    """
    Abstract test data generator that handles loading and validation.
    """

    def __init__(self):
        self.data = {}
        self.required_fields = []
        self.optional_fields = []
        self.default_data = {}
        self.file_data = []

    def get_data(self, path: Path = None, name: str = None, required: bool = True, optional: bool = False):
        """
        Loads data from a JSON file located next to the test.

        :param path: Path to the folder with test data.
        :param name: File name in the <name>.json format.
        :param required: Whether to fill in missing required fields automatically.
        :param optional: Whether to fill in optional fields.
        :return: The loaded data (dict).
        """
        with open(get_path_file(path=path, name=name, ext="[jJ][sS][oO][nN]"), encoding="utf-8") as file:
            self.data = json.load(file)

        if required or optional:
            self.file_data = list(self.data.keys())

        if required:
            self.validate_data(file_fields=self.file_data, data_fields=self.required_fields)

        if optional:
            self.validate_data(file_fields=self.file_data, data_fields=self.optional_fields)

        return self.data

    def validate_data(self, file_fields: list, data_fields: list):
        """
        Checks that the fields are present in the data. Missing fields are added from default_data.

        :param file_fields: Fields present in the file.
        :param data_fields: Fields that must be present.
        """
        for field in data_fields:
            if field not in file_fields:
                self.data.update({f"{field}": f"{self.default_data.get(field)}"})

    @staticmethod
    def generate_entity_name(id_: str, name: str) -> str:
        """
        Builds a unique entity name for the current test, including the external ID and part of the entity identifier.

        :param id_: Unique entity identifier (for example, a UUID or an int64).
        :param name: Short entity label (for example, "user", "session").
        :return: A string in the `<test_id>_<label>_00000000_<entity_id[:10]>` format.
        """
        test_name = get_current_test_name()
        prefix = test_name[5:13] if test_name else "unknown"

        return f"{prefix}_{name}_00000000_{id_[:10]}"

    @staticmethod
    def generate_test_email(id_: str, name: str = "Autotest_mail_") -> str:
        """
        Generates a test email on the @test.com domain, by analogy with generate_entity_name.
        Format: <prefix>_<name>_00000000_<short_id>@test.com

        :param id_: Unique identifier (for example, a UUID or an int64).
        :param name: Name prefix for the email (for example, 'Autotest_mail_').
        :return: A test email in the 'prefix_name_00000000_shortid@test.com' format.
        """
        test_name = get_current_test_name()
        prefix = test_name[5:13] if test_name else "unknown"

        short_id = id_[:6]

        return f"{prefix}_{name}00000000_{short_id}@test.com"
