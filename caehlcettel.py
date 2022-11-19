#!/usr/bin/env python3
import json
import sys
import os
from decimal import Decimal
from datetime import datetime

import requests
from pyfiglet import Figlet
from rich import print
from rich.panel import Panel
from rich.text import Text

from textual.app import App, ComposeResult, RenderResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Header, Footer, Static, Input, Button
from textual.reactive import reactive
from textual.containers import Grid
from textual.screen import Screen
from textual import events
from textual import log

# from rendering import print_zettel

DEFAULT_PRINTER = 'bondruccer.cbrp3.c-base.org'


class TotalContainer(Static):
    def compose(self) -> ComposeResult:
        yield CountLabel("Summe")
        yield Total()


class Total(Static):
    """
    Big number display renders that shows a number in a figlet font.
    """
    sum = reactive(0.0)

    def render(self) -> RenderResult:
        font = Figlet(font='clb6x10')
        return font.renderText(f'{self.sum:.2f}'.replace('.', ',')).rstrip("\n")


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
            Static("Bitte Barbot eingeben.", id="question"),
            Button("Okay", variant="primary", id="okay_button"),
            id="dialog",
        )

    def on_mount(self):
        self.query_one('#okay_button').focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


class DateTimeDisplay(Static):
    DATE_FORMAT = "%Y-%m-%d %H:%M"
    time = reactive('Titten Gna')

    def on_mount(self) -> None:
        self.update_time()
        self.set_interval(1.0, self.update_time)

    def update_time(self) -> None:
        self.time = f'Datum / Uhrzeit: [b]{datetime.now().strftime(self.DATE_FORMAT)}[/]'

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        self.update(time)


class MainApp(App):
    """Demonstrates custom widgets"""

    CSS_PATH = "caehlcettel.css"
    BINDINGS = [
        Binding(key="Ctrl+C", action="quit", description="Quit"),
        Binding(key="f11", action="print", description="Print and quit"),
    ]
    DENOMINATIONS =  [
        # ('500,00',  '50000'),
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
        ('0,05', '5'),
        ('0,02', '2'),
        ('0,01', '1'),
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
        yield DateTimeDisplay('Datum / Uhrzeit')
        yield Footer()

    def on_mount(self) -> None:
        self.title = 'c-base console-based caehlcettel'
        self.query_one(PositiveNumberInput).focus()

    def collect_values(self):
        """
        Collect the entered values to get a JSON dict like
        {
            'umber_of_00500': 23,
            ... 
        }
        """
        json_data = {}
        for number_input in self.query(PositiveNumberInput):
            int_val = int(Decimal(number_input.id.rsplit('_', 1)[1]))
            json_name = f"number_of_{str(int_val).zfill(5)}"
            # The API does not accept a value that is `null` or a negative value.
            the_value = 0
            if number_input.value:
                try:
                    the_value = int(number_input.value)
                    if the_value < 0:
                        the_value = 0   # negative values not allowed.
                except ValueError:
                    pass
            if the_value is None or the_value < 0:
                the_value = 0
            json_data[json_name] = the_value
        # finished
        return json_data
    
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
        # Get the access tokens for the REST-API
        access_token = os.environ.get('ACCESS_TOKEN', None)
        if not access_token:
            raise ValueError("Environment variable ACCESS_TOKEN not set!")
        api_base_url = os.environ.get('API_BASE_URL', None)
        if not api_base_url:
            raise ValueError('Environment variable API_BASE_URL not set!')
        # Create the JSON object that will be sent to the API
        json_data = self.collect_values()
        json_data["username"] = barbot_name
        # json_data["count_type"] = count_type
        json_data["count_type"] = os.environ.get('COUNT_TYPE', 'tresencasse')
        counting_url = f'{api_base_url}/count/'
        # Do the request
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
            params={
                'printer': os.environ.get('PRINTER_HOSTNAME', DEFAULT_PRINTER),
            },
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
        self.exit()


if __name__ == '__main__':
    try:
        app = MainApp()
        app.run()
    except Exception as err:
        print(err)
