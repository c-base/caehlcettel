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
from textual.app import App, ComposeResult, RenderResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Header, Footer, Static, Input, Button
from textual.reactive import reactive
from textual.containers import Grid
from textual.screen import Screen
from textual import events
from textual import log

from rich.text import Text
# from rendering import print_zettel


BACKEND = 'pyusb'
MODEL = 'QL-700'
# Find out using lsusb or with the MacOS system report
# 0x04f9 is the vendor ID, 0x2042 is the model, then the serial number
PRINTER = 'usb://0x04f9:0x2042/000M3Z986950'

state = {
    "barbot": None
}

class TotalContainer(Static):

    def compose(self) -> ComposeResult:
        yield CountLabel("Summe")
        yield Total()

class Total(Static):

    mouse_over = reactive(False)
    sum = reactive(0.0)

    def render(self) -> RenderResult:
        # sum = Decimal(313.37)
        #for value in VALUES:
            # if state[value] is None:
            #     continue
            # sum += state[value] * Decimal(value.replace(',', '.'))
        font = Figlet(font='clb6x10')
        return font.renderText(f'{self.sum:.2f}'.replace('.', ',')).rstrip("\n")
            
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


class PositiveNumberInput(Input):

    def on_key(self, event: events.Key) -> None:

        try:
            my_val = int(self.value)
        except ValueError:
            my_val = 0

        if event.key == 'up':
            self.value = str(my_val + 1)
        if event.key == 'down':
            if my_val == 0:
                self.value = '0'
            else:
                self.value = str(my_val - 1)

        return super().on_key(event)
            

class CountInput(Static):
    """An input widget with a title."""

    def __init__(self, *args, **kwargs):
        self.label = kwargs.pop('label')
        self.default_bg = None
        super().__init__(*args, **kwargs)
        

    async def on_input_changed(self, message: Input.Changed) -> None:
        if self.default_bg is None:
            self.default_bg = self.styles.background
        if message.value == '':
            return
        try:
            if int(message.value) < 0:
                raise ValueError("negative not allowed")
        except ValueError:
            # self.default_bg = self.styles.background
            def reset_bg():
                self.styles.background = self.default_bg
            self.styles.background = 'red'
            self.set_timer(1.0, reset_bg)

    def compose(self) -> ComposeResult:
        yield CountLabel(self.label)
        yield PositiveNumberInput(placeholder="0", id=self.id)


class QuitScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Grid(
            Static("Bitte Barbot eingegeben.", id="question"),
            Button("Okay", variant="primary", id="okay_button"),
            id="dialog",
        )

    def on_mount(self):
        self.query_one('#okay_button').focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


class MainApp(App):
    """Demonstrates custom widgets"""

    CSS_PATH = "caehlcettel.css"
    BINDINGS = [
        Binding(key="Ctrl+C", action="quit", description="Quit"),
        Binding(key="f11", action="print", description="Print and quit"),
    ]
    DENOMINATIONS =  [
        ('200,00',  '20000'),
        ('100,00', '10000'),
        ('50,00', '5000'),
        ('20,00', '2000'),
        ('10,00', '1000'),
        ('5,00', '500'),
        ('2,00', '200'),
        ('1,00', '100'),
        ('0,50', '50'),
        ('0,20', '20'),
        ('0,10', '10'),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        for denom, id_name in self.DENOMINATIONS:
            title=f"{denom}"
            name=f"input_{denom}".replace(',', '')
            my_id=f"id_input_{id_name}".replace(',', '')
            yield CountInput(name=name, id=my_id, label=title)
        yield TotalContainer()
        yield Input(name="barbot", id="barbot", placeholder='Barbot')
        yield Footer()

    def on_mount(self) -> None:
        self.title = 'caehlcettel'
        self.query_one(PositiveNumberInput).focus()
    
    def calculate_total(self):
        grand_total = Decimal(0)
        for number_input in self.query(PositiveNumberInput):
            denomination = Decimal(number_input.id.rsplit('_', 1)[1]) / 100
            if number_input.value:
                try:
                    val = int(number_input.value)
                    if val < 0:
                        continue
                    grand_total += denomination * val
                except ValueError:
                    pass
        return grand_total

    async def on_input_changed(self, message: Input.Changed) -> None:
        grand_total = self.calculate_total()
        self.query_one(Total).sum = grand_total

    async def action_quit(self) -> None:
        await self.shutdown()

    async def action_print(self) -> None:
         # check if barbot name field is empty.
        barbot_name = self.query_one('#barbot').value.strip()
        if not barbot_name:
            self.push_screen(QuitScreen())
            return
        
        context = {
            'state': [],
            'total': self.calculate_total(),
            'datetime': datetime.now().strftime('%Y-%m-%d, %H:%M Uhr'),
        }

        access_token = os.environ.get('ACCESS_TOKEN', None)
        if not access_token:
            raise ValueError("Environment variable ACCESS_TOKEN not set!")

        api_base_url = os.environ.get('API_BASE_URL', None)
        if not api_base_url:
            raise ValueError('Environment variable API_BASE_URL not set!')

       
        if not barbot_name:
            barbot_name = 'Anonymer Barbot'

        json_data = {
            "username": barbot_name,
        }
        

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
        for value in DENOMINATIONS:
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
