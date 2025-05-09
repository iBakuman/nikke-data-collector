from repository.character_dao import CharacterDAO
from repository.importers.character_importer import CharacterImporter


def test_character_importer():
    character_dao = CharacterDAO()
    importer = CharacterImporter(character_dao)
    importer.import_from_directory("testdata/ref")

