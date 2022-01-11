#!/usr/bin/env python3
import tempfile
import sys
from decimal import Decimal
from datetime import datetime

from pyfiglet import Figlet
from rich import box
from rich.panel import Panel
from rich.prompt import Prompt
from textual_inputs import IntegerInput
from textual.app import App
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Header, Footer
from rendering import print_zettel


BACKEND = 'pyusb'
MODEL = 'QL-700'
# Find out using lsusb or with the MacOS system report
# 0x04f9 is the vendor ID, 0x2042 is the model, then the serial number
PRINTER = 'usb://0x04f9:0x2042/000M3Z986950'

VALUES =  [
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

state = {}


class Total(Widget):

    mouse_over = Reactive(False)

    def render(self) -> Panel:
        sum = Decimal(0.0)
        for value in VALUES:
            if state[value] is None:
                continue
            sum += state[value] * Decimal(value.replace(',', '.'))

        font = Figlet(font='xsansb')
        return Panel(
            font.renderText(str(sum).replace('.', ',')).rstrip("\n"), 
            title="Summe", 
            border_style="green",
            style=("black on green" if self.mouse_over else "white"),
            height=14,
            box=box.DOUBLE
        )

    def on_enter(self) -> None:
        self.mouse_over = True

    def on_leave(self) -> None:
        self.mouse_over = False


class DateTimeDisplay(Widget):

    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self) -> Panel:
        time = datetime.now().strftime("%c")
        return Panel(time, title="Datum / Uhrzeit")


class TitleDisplay(Widget):

    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self) -> Panel:
        time = datetime.now().strftime("%c")
        return Panel(time, title="Datum / Uhrzeit")


class HoverApp(App):
    """Demonstrates custom widgets"""

    async def on_load(self, event) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        # await self.bind("b", "view.toggle('sidebar')", "Toggle sidebar")
        await self.bind("q", "quit", "Quit")
        await self.bind("p", "print", "Print & Quit")


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

        with tempfile.TemporaryDirectory() as tmpdir:
            print_zettel(context, tmpdir, BACKEND, MODEL, PRINTER)
            sys.exit(0)

    
    async def on_mount(self) -> None:
        # INIT state
        for value in VALUES:
            state[value] = 0

        self.title="c-base console-based caehlcettel"
        rows = [
            
        ]
        for value in VALUES:
            row = IntegerInput(
                name=f"input_{value}",
                placeholder="0",
                title=f"{value}",
            )
            rows.append(row)
        self.my_total = Total()
        self.my_dtd = DateTimeDisplay()

        await self.view.dock(Header(style="white on blue"), edge="top")
        await self.view.dock(Footer(), edge="bottom")

        await self.view.dock(*rows, edge="top", size=3)
        await self.view.dock(self.my_dtd, edge='bottom', size=3)
        await self.view.dock(self.my_total, edge='bottom', size=14)

    async def handle_input_on_change(self, message) -> None:
        global state
        name = f"{message.sender.name}".replace('input_', '')
        state[name] = message.sender.value
        self.my_total.refresh()
        self.log(f"Input: {message.sender.name} changed, val: {message.sender.value}, state={state}")


HoverApp.run(log="textual.log")
