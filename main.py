import json
from typing import Any
from pathlib import Path, PurePath
from datetime import datetime
import dominate
import dominate.tags as dom
import sys
import webbrowser
import tempfile
import shutil
from threading import Thread, Lock, Event
import time


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

        # run here, because empty uri lists and everything else that is empty/irrelevant should be removed,
        # but empty custom fields should still appear
        self.del_fields()

        # parse custom fields
        if 'fields' in self:
            for field in self['fields']:
                key, value = field['name'], field['value']
                if key is None and value is None:
                    # skip completely empty field
                    continue
                if key is None:
                    key = ''
                if value is None:
                    value = ''
                self[key] = value
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
        time_now:str = datetime.now().astimezone().strftime('%d %b %Y, %H:%M:%S UTC%z')
        doc = dominate.document(title='Bitwarden Export')

        with doc.head:  # type: ignore
            dom.link(rel='stylesheet', href='style.css')

        with doc:
            with dom.header():
                dom.h1('Bitwarden Backup')
                dom.p(time_now)
            with dom.ul(cls="container"):
                for entry in self.entries:
                    # bitwarden entry
                    with dom.li(cls="entry"):
                        with dom.ul():
                            for fieldname, value in entry.items():
                                value = str(value)
                                # one field of an entry
                                with dom.li(cls="field"):
                                    #print("FIELDNAME:", fieldname)
                                    #print("entry:", entry['name'])
                                    dom.p(fieldname, cls="fieldname")
                                    dom.p(value, cls="fieldvalue")
        return str(doc)



if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise ValueError("Please provide json-encoded bitwarden export")
    elif len(sys.argv) > 2:
        raise ValueError("Too many arguments")
    json_path = Path(sys.argv[1])

    temp_dir = Path(tempfile.gettempdir())
    html_path = temp_dir / json_path.with_suffix('.html').name
    css_path = Path('style.css')
    shutil.copy(css_path, temp_dir)

    data = BitwardenData(json_path)
    html = data.create_html()

    with open(html_path, 'w') as f:
        f.write(html)
    print("Successfully created html document")


    # html file can be deleted either by key press or when the auto timer finishes
    # both threads will try to delete file at most once

    def delete_file(file:Path):
        lock.acquire()
        # check if other thread already deleted file
        if flag_deleted.is_set():
            lock.release()
            return
        # file should exist; attempt deletion
        try:
            file.unlink()
            print("\nFile deleted")
        except FileNotFoundError:
            print("HTML file deleted from outside")
        flag_deleted.set()
        lock.release()

    def autodelete(file:Path, delay_secs:int):
        t0 = time.time()
        while time.time() - t0 < delay_secs:
            # return if other process deleted file
            if flag_deleted.is_set():
                return
            time.sleep(0.1)
        delete_file(file)
        print("Press Enter to exit")
    

    webbrowser.open(str(html_path))

    flag_deleted = Event()
    lock = Lock()

    timer_thread = Thread(target=autodelete, args=[html_path, 10])
    timer_thread.start()
    
    # wait for key press
    input("Press Enter to delete html export\n")
    delete_file(html_path)
    timer_thread.join()


