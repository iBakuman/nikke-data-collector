from dataclasses import dataclass

from dataclass_wizard import JSONWizard

from collector.mixin import JSONSerializableMixin


def test_json_serializable():
    @dataclass
    class TestClass(JSONWizard, JSONSerializableMixin):
        name: str
        value: int

    test_obj = TestClass(name="爱丽丝", value=100)
    test_obj.save_as_json("testdata/mixin/test_obj.json")
    with open("testdata/mixin/test_obj.json", "r", encoding="utf-8") as f:
        json_str = f.read()
    test_obj2 = TestClass.from_json(json_str)
    assert test_obj2.name == "爱丽丝"
    assert test_obj2.value == 100
