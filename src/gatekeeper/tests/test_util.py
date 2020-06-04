from gatekeeper.util.casing import snakecaseDictKeys


def testSnakecaseDictKeys():
    assert {"some_key": 0, "other_key": {"nested_key": 1}} == snakecaseDictKeys(
        {"someKey": 0, "otherKey": {"nestedKey": 1}}
    )
