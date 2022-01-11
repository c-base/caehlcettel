import tempfile
from decimal import Decimal

from rendering import make_zettel


def test_make_zettel():
    context = {
        'state': [
            {
                'label': '100,00',
                'amount': Decimal(10),
                'sub_total': Decimal(1000)
            }, {
                'label': '50,00',
                'amount': Decimal(10),
                'sub_total': Decimal(500)
            }, {
                'label': '20,00',
                'amount': Decimal(10),
                'sub_total': Decimal(200)
            }, {
                'label': '10,00',
                'amount': Decimal(10),
                'sub_total': Decimal(100)
            }, {
                'label': '5,00',
                'amount': Decimal(10),
                'sub_total': Decimal(50)
            }, {
                'label': '2,00',
                'amount': Decimal(10),
                'sub_total': Decimal(20)
            }, {
                'label': '1,00',
                'amount': Decimal(10),
                'sub_total': Decimal(10)
            }, {
                'label': '0,50',
                'amount': Decimal(10),
                'sub_total': Decimal(5)
            }, {
                'label': '0,20',
                'amount': Decimal(10),
                'sub_total': Decimal(2)
            }, {
                'label': '0,10',
                'amount': Decimal(10),
                'sub_total': Decimal(1)
            }
        ],
        'total': Decimal('1888'),
        'datetime': '2022-01-01 08:30 Uhr'
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        res = make_zettel(context, tmpdir, do_open=True)
        assert res == tmpdir + 'out.png'