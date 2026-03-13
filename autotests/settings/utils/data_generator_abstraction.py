import json
from pathlib import Path

from autotests.settings.utils.utils import get_current_test_name, get_path_file


class DataAbstractionGenerator:
    """
    Абстрактный генератор тестовых данных, обеспечивающий загрузку и валидацию.
    """

    def __init__(self):
        self.data = {}
        self.required_fields = []
        self.optional_fields = []
        self.default_data = {}
        self.file_data = []

    def get_data(self, path: Path = None, name: str = None, required: bool = True, optional: bool = False):
        """
        Загружает данные из JSON-файла рядом с тестом.

        :param path: Путь до папки с тестовыми данными.
        :param name: Имя файла в формате <name>.json.
        :param required: Заполнять ли автоматически недостающие обязательные поля.
        :param optional: Заполнять ли необязательные поля.
        :return: Загруженные данные (dict).
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
        Проверяет наличие полей в данных. Недостающие поля добавляются из default_data.

        :param file_fields: Поля, присутствующие в файле.
        :param data_fields: Поля, которые должны быть.
        """
        for field in data_fields:
            if field not in file_fields:
                self.data.update({f"{field}": f"{self.default_data.get(field)}"})

    @staticmethod
    def generate_entity_name(id_: str, name: str) -> str:
        """
        Формирует уникальное имя сущности для текущего теста, включая внешний ID и часть идентификатора сущности.

        :param id_: Уникальный идентификатор сущности (например, UUID или int64).
        :param name: Краткое название сущности (например, "user", "session").
        :return: Строка в формате `<test_id>_<label>_00000000_<entity_id[:10]>`.
        """
        test_name = get_current_test_name()
        prefix = test_name[5:13] if test_name else "unknown"

        return f"{prefix}_{name}_00000000_{id_[:10]}"

    @staticmethod
    def generate_test_email(id_: str, name: str = "Autotest_mail_") -> str:
        """
        Генерирует тестовый email с доменом @test.com по аналогии с generate_entity_name.
        Формат: <prefix>_<name>_00000000_<short_id>@test.com

        :param id_: Уникальный идентификатор (например, UUID или int64).
        :param name: Префикс имени для email (например, 'Autotest_mail_').
        :return: Тестовый email в формате 'prefix_name_00000000_shortid@test.com'.
        """
        test_name = get_current_test_name()
        prefix = test_name[5:13] if test_name else "unknown"

        short_id = id_[:6]

        return f"{prefix}_{name}00000000_{short_id}@test.com"
