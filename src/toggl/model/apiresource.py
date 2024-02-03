from dataclasses import fields


class ApiResource:
    @classmethod
    def from_dict(cls, data: dict) -> "ApiResource":
        obj = cls()
        for field in fields(obj):
            if field.name in data:
                if hasattr(field.type, "__origin__") and field.type.__origin__ is list:
                    setattr(
                        obj,
                        field.name,
                        (
                            list(
                                map(
                                    lambda o: cls.__from_dict_value(
                                        field.type.__args__[0], o
                                    ),
                                    data[field.name],
                                )
                            )
                            if data[field.name] is not None
                            else []
                        ),
                    )
                else:
                    setattr(
                        obj,
                        field.name,
                        cls.__from_dict_value(field.type, data[field.name]),
                    )
        return obj

    @classmethod
    def from_dict_list(cls, data_list: list[dict]) -> list["ApiResource"]:
        return list(map(lambda s: cls.from_dict(s), data_list))

    @classmethod
    def __from_dict_value(cls, field_type: type, data_value: object) -> object:
        if field_type in [int, float, bool, str]:
            return data_value
        elif issubclass(field_type, ApiResource):
            return field_type.from_dict(data_value)
        else:
            raise ValueError("unknown type")

    def to_dict(self) -> dict:
        result = {}
        for field in fields(self):
            if (
                hasattr(field.type, "__origin__")
                and field.type.__origin__ is list
                and len(getattr(self, field.name)) > 0
            ):
                result[field.name] = list(
                    map(
                        lambda o: self.__to_dict_value(field.type.__args__[0], o),
                        getattr(self, field.name),
                    )
                )
            elif getattr(self, field.name) != None:
                result[field.name] = self.__to_dict_value(
                    field.type, getattr(self, field.name)
                )
        return result

    def __to_dict_value(self, field_type: type, attr_value: object) -> object:
        if field_type in [int, float, bool, str]:
            return attr_value
        elif issubclass(field_type, ApiResource):
            return field_type.to_dict(attr_value)
        else:
            raise ValueError("unknown type")
