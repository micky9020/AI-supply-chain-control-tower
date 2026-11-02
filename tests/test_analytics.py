from pathlib import Path
from app.analytics import analyze, load_orders, DataError

DATA = Path(__file__).resolve().parents[1] / 'data' / 'demo_orders.csv'

def test_demo_data_and_summary():
    result = analyze(load_orders(DATA))
    assert result['overview']['orders_total'] == 12
    assert result['overview']['orders_delayed'] == 3
    assert result['overview']['alerts_total'] > 0
    assert len(result['orders']) == 12
    assert all(0 <= o['risk_score'] <= 100 for o in result['orders'])

def test_delivered_has_zero_risk():
    delivered = [x for x in analyze(load_orders(DATA))['orders'] if x['status'] == 'delivered']
    assert all(x['risk_score']==0 for x in delivered)

def test_rejects_duplicate_order_ids(tmp_path):
    lines = DATA.read_text().splitlines()
    p = tmp_path/'duplicate.csv'
    p.write_text('\n'.join([lines[0],lines[1],lines[1]]))
    try:
        load_orders(p)
    except DataError:
        pass
    else:
        raise AssertionError('Duplicates must be rejected')
