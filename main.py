import json
from typing import Any
from pathlib import Path, PurePath



import dominate
from dominate.tags import *


class Entry(dict):
    DEL_FIELDS = {'type', 'organizationId', 'folderId', 'reprompt', 'collectionIds', 'id', 'favorite'}

    def __init__(self, data:dict[Any,Any]) -> None:
        super().__init__(data)
        # remove some fields
        empty_fields = {f for f in self if self[f] is None}
        for field in Entry.DEL_FIELDS | empty_fields:
            del self[field]
    

class Login(Entry):
    def __init__(self, data:dict[Any,Any]) -> None:
        _data = data.copy()
        _data |= _data['login']
        del _data['login']
        super().__init__(_data)

class Card(Entry):
    def __init__(self, data:dict[Any,Any]) -> None:
        _data = data.copy()
        _data |= _data['card']
        del _data['card']
        super().__init__(_data)

class Identity(Entry):
    def __init__(self, data:dict[Any,Any]) -> None:
        _data = data.copy()
        _data |= _data['identity']
        del _data['identity']
        super().__init__(_data)

class Note(Entry):
    def __init__(self, data:dict[Any,Any]) -> None:
        _data = data.copy()
        del _data['secureNote']
        super().__init__(_data)


TYPE_TO_ENTRY:dict[Any,Any] = {
    1: Login,
    2: Note,
    3: Card,
    4: Identity
}


class BitwardenData():
    raw_data:dict[Any,Any]
    entries:list[Entry]

    def __init__(self, data:PurePath|str|dict[Any, Any]):
        if isinstance(data, dict):
            self.raw_data = data
        else:
            with open(data, encoding='utf8') as json_data:
                self.raw_data = json.load(json_data)
        self.entries = BitwardenData.parse_entries(self.raw_data)

    @staticmethod
    def parse_entries(data:dict[Any,Any]) -> list[Entry]:
        raw_entries:list[Entry] = data['items']
        parsed_entries:list[Entry] = []

        for entry in raw_entries:
            t = entry['type']
            if t not in TYPE_TO_ENTRY:
                raise ValueError(f"Invalid entry type: {t}")
            parsed_entries.append(TYPE_TO_ENTRY[t](entry))

        return parsed_entries

    def create_html(self):
        doc = dominate.document(title='Bitwarden Export')

        with doc.head:  # type: ignore
            link(rel='stylesheet', href='style.css')

        with doc:
            with ul(cls="container"):
                for entry in self.entries:
                    # bitwarden entry
                    with li(cls="entry"):
                        with ul():
                            for fieldname, value in entry.items():
                                value = str(value)
                                # one field of an entry
                                with li(cls="field"):
                                    p(fieldname, cls="fieldname")
                                    p(value, cls="fieldvalue")
        return str(doc)



path = r'D:\bitwarden_export.json'
data = BitwardenData(path)
print([e for e in data.entries if isinstance(e,Login)])

html = data.create_html()

with open('out.html', 'w') as f:
    f.write(html)
