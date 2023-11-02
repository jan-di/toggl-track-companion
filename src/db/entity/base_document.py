from mongoengine import Document
from bson import DBRef
from typing import Any


class BaseDocument(Document):
    COLLECTION_NAME = ""

    @classmethod
    def to_dbref_pk(cls, primary_key: Any | None):
        return (
            DBRef(cls.COLLECTION_NAME, primary_key) if primary_key is not None else None
        )

    @classmethod
    def to_dbref_pks(cls, primary_keys: list[Any] | None):
        return (
            list(map(cls.to_dbref_pk, primary_keys))
            if primary_keys is not None
            else None
        )

    meta = {"abstract": True}
