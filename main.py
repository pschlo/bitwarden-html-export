import json
from typing import Any
from pathlib import Path, PurePath



import dominate
from dominate.tags import *



class URIs(tuple):
    def __new__(cls, data:list[dict[Any,Any]]):
        # ignore uris that are None
        _data = tuple(uri['uri'] for uri in data if uri['uri'] is not None)
        super().__new__(cls, _data)

    def __str__(self) -> str:
        return '\n'.join(self)


class Entry(dict):
    IGNORE_FIELDS = {'type', 'organizationId', 'folderId', 'reprompt', 'collectionIds', 'id', 'favorite'}

    def __init__(self, data:dict[Any,Any]) -> None:
        super().__init__(data)

        # parse uris
        if 'uris' in self:
            self['uris'] = URIs(self['uris'])

        # run here, because empty uri lists should be removed, but empty custom fields should still appear
        self.del_fields()

        # parse custom fields
        # ignore custom fields with key None, i.e. that have no key
        if 'fields' in self:
            for field in self['fields']:
                key, value = field['name'], field['value']
                if key is not None:
                    self[key] = value if value is not None else ''
            del self['fields']
    
    def del_fields(self) -> None:
        # get fields that map to something valid
        nonempty_fields = set()
        for key, val in self.items():
            if val is None:
                continue
            try:
                if len(val) == 0:
                    continue
            except TypeError:
                pass
            nonempty_fields.add(key)

        all_fields = set(self.keys())
        delete_fields = (all_fields - nonempty_fields) | Entry.IGNORE_FIELDS
        for key in delete_fields:
            del self[key]

    

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
                                    #print("FIELDNAME:", fieldname)
                                    #print("entry:", entry['name'])
                                    p(fieldname, cls="fieldname")
                                    p(value, cls="fieldvalue")
        return str(doc)



path = r'bitwarden_export.json'
data = BitwardenData(path)
#print([e for e in data.entries if isinstance(e,Login)])

html = data.create_html()

with open('out.html', 'w') as f:
    f.write(html)
