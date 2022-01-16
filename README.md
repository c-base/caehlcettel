# caehlcettel
Text-based interace for keeping track of cash

![Screenshot](screenshot.png)

# Installing

- Check out this repo using `git clone <repo>`
- `sudo apt install libjpeg-dev libpng-dev`
- `pip install poetry`
- `cd <repo-name>`
- `poetry install`

# Running

- `poetry run python caehlcettel.py`

## Testing the label printer

```
brother_ql -b pyusb -m QL-700 -p usb://0x04f9:0x2042/000M3Z986950 print -l 62 testimg.png
```
