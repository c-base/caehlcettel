#!/usr/bin/env python3
# import tempfile
import json
import sys
import os
from decimal import Decimal
from datetime import datetime
import requests
from pyfiglet import Figlet
from rich import box
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print
# from textual_inputs import IntegerInput, TextInput
from textual.reactive import Reactive
from textual.app import App, ComposeResult, RenderResult
from textual.widget import Widget
from textual.widgets import Header, Footer, Static, Input
from textual.containers import Container, Horizontal


from rich.text import Text
# from rendering import print_zettel


BACKEND = 'pyusb'
MODEL = 'QL-700'
# Find out using lsusb or with the MacOS system report
# 0x04f9 is the vendor ID, 0x2042 is the model, then the serial number
PRINTER = 'usb://0x04f9:0x2042/000M3Z986950'

VALUES =  [
    '200,00',
    '100,00',
    '50,00',
    '20,00',
    '10,00',
    '5,00',
    '2,00',
    '1,00',
    '0,50',
    '0,20',
    '0,10'
]

state = {
    "barbot": None
}

class TotalContainer(Static):

    def compose(self) -> ComposeResult:
        yield CountLabel("Summe")
        yield Total()

class Total(Static):

    mouse_over = Reactive(False)
        
    def render(self) -> RenderResult:
        sum = Decimal(313.37)
        #for value in VALUES:
            # if state[value] is None:
            #     continue
            # sum += state[value] * Decimal(value.replace(',', '.'))
        font = Figlet(font='clb6x10')
        return font.renderText(f'{sum:.2f}'.replace('.', ',')).rstrip("\n")
            
    def on_enter(self) -> None:
        self.mouse_over = True

    def on_leave(self) -> None:
        self.mouse_over = False


class DateTimeDisplay(Widget):

    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self) -> Panel:
        time = datetime.now().strftime("%Y-%m-%d %H:%M")
        return Panel(time, title="Datum / Uhrzeit")


class TitleDisplay(Static):

    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self) -> Panel:
        time = datetime.now().strftime("%c")
        return Panel(time, title="Datum / Uhrzeit")

class CountLabel(Static):
    pass

class CountInput(Static):
    """An input widget."""

    def __init__(self, *args, **kwargs):
        self.label = kwargs.pop('label')
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield CountLabel(self.label)
        yield Input(placeholder="0", value="")


class MainApp(App):
    """Demonstrates custom widgets"""

    CSS_PATH = "caehlcettel.css"
    BINDINGS = [("Ctrl+C", "action_print", "Quit"), ("F11", "action_print", "Print and quit")]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        value_fields = []
        for value in VALUES:
            title=f"{value}"
            name=f"input_{value}".replace(',', '')
            my_id=f"id_input_{value}".replace(',', '')
            yield CountInput(name=name, id=my_id, label=title)
        yield TotalContainer()
        yield Footer()


    def __do_not_init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.tab_index = []
        self.rows = []
        for value in VALUES:
            name=f"input_{value}".replace(',', '')
            self.tab_index.append(name)
            row = Widget(     # IntegerInput(
                name=f"input_{value}",
                placeholder="0",
                title=f"{value}",
            )
            attr_name=f"input_{value}".replace(',', '')
            self.rows.append(row)
            setattr(self, attr_name, row)
        self.current_index = 0

    async def do_not_on_load(self, event) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        # await self.bind("b", "view.toggle('sidebar')", "Toggle sidebar")
        await self.bind("ctrl+c", "quit", "Quit")
        await self.bind("f11", "print", "Print & Quit")
        await self.bind("ctrl+i", "next_tab_index", show=False)
        # await self.bind("down", "next_tab_index", show=False)
        await self.bind("enter", "next_tab_index", show=False)
        await self.bind("shift+tab", "previous_tab_index", show=False)

    async def action_next_tab_index(self) -> None:
        """Changes the focus to the next form field"""
        if self.current_index < len(self.tab_index) - 1:
            self.current_index += 1
        else:
            self.current_index = 0

        await getattr(self, self.tab_index[self.current_index]).focus()

    async def action_previous_tab_index(self) -> None:
        """Changes the focus to the previous form field"""
        self.log(f"PREVIOUS {self.current_index}")
        if self.current_index > 0:
            self.current_index -= 1
            await getattr(self, self.tab_index[self.current_index]).focus()

    async def action_reset_focus(self) -> None:
        self.current_index = -1
        await self.header.focus()

    async def action_print(self):
        context = {
            'state': [],
            'total': None,
            'datetime': datetime.now().strftime('%Y-%m-%d, %H:%M Uhr'),
        }
        sum = Decimal(0)

        for value in VALUES:
            if state[value] is None:
                val = 0
            else:
                val = state[value]
            sub_total = val * Decimal(value.replace(',', '.'))
            sum += sub_total
            context['state'].append({
                'label': value,
                'amount': val,
                'sub_total': sub_total
            })
        context['total'] = sum

        access_token = os.environ.get('ACCESS_TOKEN', None)
        if not access_token:
            raise ValueError("Environment variable ACCESS_TOKEN not set!")

        api_base_url = os.environ.get('API_BASE_URL', None)
        if not api_base_url:
            raise ValueError('Environment variable API_BASE_URL not set!')


        # Send a barbot name even if the field is empty.
        barbot_name = state.get('barbot')
        if not barbot_name:
            barbot_name = 'Anonymer Barbot'

        json_data = {
            "username": barbot_name,
        }
        
        for value in VALUES:
            int_val = int(Decimal(value.replace(',', '.')) * 100)
            json_name = f"number_of_{str(int_val).zfill(5)}"
            # The API does not accept a value that is `null` or a negative value.
            the_value = state[value]
            if the_value is None or the_value < 0:
                the_value = 0
            json_data[json_name] = the_value

        counting_url = api_base_url + '/counting/'
        resp = requests.post(
            url=counting_url,
            json=json_data,
            headers={
                "Authorization": f"Token {access_token}"
            },
            timeout=5
        )
        if resp.status_code not in [200, 201, 204]:
            self._exit_renderables.extend([
                Text.from_markup(f"URL: [i blue underline]{counting_url}[/]\n"),
                Text.from_markup(f'JSON content sent: {json.dumps(json_data, indent=2)}'),
                Text.from_markup(f'HTTP status code: {resp.status_code}'),
                Text.from_markup(f'HTTP response content: {resp.content}'),
            ])
        resp.raise_for_status()

        receipt_url = resp.json()['url']
        print_url = receipt_url + 'print/'
        print_resp = requests.get(
            url=print_url,
            headers={
                "Authorization": f"Token {access_token}"
            },
            timeout=5
        )
        if print_resp.status_code not in [200, 201, 204]:
            self._exit_renderables.extend([
                Text.from_markup(f"URL: [i blue underline]{print_url}[/]\n"),
                Text.from_markup(f'HTTP status code: {print_resp.status_code}'),
                Text.from_markup(f'HTTP response content: {print_resp.content}'),
            ])
        resp.raise_for_status()
        sys.exit(0)
    
    async def do_not_on_mount(self) -> None:
        # INIT state
        for value in VALUES:
            state[value] = 0

        self.title="c-base console-based caehlcettel"
        self.my_total = Total()
        self.my_dtd = DateTimeDisplay()
        self.input_barbot = TextInput(name="input_barbot", placeholder="Anonymer barbot", title="Barbot")
        self.tab_index.append('input_barbot')

        await self.view.dock(Header(style="white on blue"), edge="top")
        await self.view.dock(Footer(), edge="bottom")

        await self.view.dock(*(self.rows + [self.input_barbot]), edge="top", size=3)
        await self.view.dock(self.my_dtd, edge='bottom', size=3)
        await self.view.dock(self.my_total, edge='bottom', size=12)

        # start at the first input field
        await getattr(self, self.tab_index[0]).focus()

    async def handle_input_on_change(self, message) -> None:
        global state
        name = f"{message.sender.name}".replace('input_', '')
        state[name] = message.sender.value
        self.my_total.refresh()
        self.log(f"Input: {message.sender.name} changed, val: {message.sender.value}, state={state}")


if __name__ == '__main__':
    try:
        app = MainApp()
        app.run()
    except Exception as err:
        print(err)
