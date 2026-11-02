"""Explainable supply-chain scoring; no remote AI calls or sensitive data transmission."""
from __future__ import annotations
import csv
from datetime import date, datetime
from pathlib import Path
from statistics import mean

FIELDS = {'order_id','supplier','sku','category','origin','destination','quantity','unit_cost_usd','inventory_units','daily_demand','lead_time_days','transit_days','days_until_due','on_time_rate','status'}
MAX_ROWS = 10000

class DataError(ValueError):
    pass

def load_orders(path: Path) -> list[dict]:
    if not path.is_file() or path.stat().st_size > 5_000_000:
        raise DataError('Archivo de datos inexistente o demasiado grande')
    rows = []
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not FIELDS.issubset(reader.fieldnames or []):
            raise DataError('Columnas requeridas ausentes')
        for raw in reader:
            if len(rows) >= MAX_ROWS:
                raise DataError('Se excedió el límite de registros')
            try:
                entry = {key: str(raw[key]).strip()[:100] for key in ('order_id','supplier','sku','category','origin','destination','status')}
                for key in ('quantity','inventory_units','lead_time_days','transit_days','days_until_due'):
                    entry[key] = int(raw[key])
                for key in ('unit_cost_usd','daily_demand','on_time_rate'):
                    entry[key] = float(raw[key])
                if not entry['order_id'] or not entry['sku'] or not entry['supplier']:
                    raise ValueError('Identificador vacío')
                if any(entry[k] < 0 for k in ('quantity','inventory_units','lead_time_days','transit_days','unit_cost_usd','daily_demand')):
                    raise ValueError('Cantidad negativa')
                if not (0 <= entry['on_time_rate'] <= 1) or not (-365 <= entry['days_until_due'] <= 365):
                    raise ValueError('Rango inválido')
                if entry['status'] not in {'in_transit','processing','delivered','delayed'}:
                    raise ValueError('Estado inválido')
            except (ValueError, TypeError, KeyError) as exc:
                raise DataError(f'Dato inválido en fila {reader.line_num}') from exc
            rows.append(entry)
    if not rows:
        raise DataError('Archivo sin registros')
    if len({r['order_id'] for r in rows}) != len(rows):
        raise DataError('IDs duplicados')
    return rows

def analyze(orders: list[dict]) -> dict:
    scored = []
    alerts = []
    for row in orders:
        coverage = round(row['inventory_units'] / row['daily_demand'], 1) if row['daily_demand'] > 0 else None
        projected = max(0, row['lead_time_days'] - row['days_until_due'])
        reasons = []
        score = 0
        if row['status'] == 'delayed':
            score += 45; reasons.append('Envío marcado como demorado')
        elif row['status'] == 'delivered':
            score = 0
        else:
            if row['transit_days'] > row['lead_time_days']:
                score += 30; reasons.append('Tránsito excede plazo previsto')
            if row['days_until_due'] < 0:
                score += 35; reasons.append('Fecha de entrega vencida')
            elif row['days_until_due'] <= 2:
                score += 15; reasons.append('Entrega próxima')
            if coverage is not None and coverage < 7:
                score += 30; reasons.append('Cobertura de inventario menor a 7 días')
            elif coverage is not None and coverage < 14:
                score += 15; reasons.append('Cobertura de inventario menor a 14 días')
            if row['on_time_rate'] < .8:
                score += 20; reasons.append('Historial de puntualidad bajo')
        score = min(score, 100)
        level = 'alto' if score >= 60 else 'medio' if score >= 30 else 'bajo'
        item = {**row, 'inventory_coverage_days':coverage, 'risk_score':score, 'risk_level':level, 'risk_reasons':reasons, 'estimated_delay_days':projected if row['status'] != 'delivered' else 0,
                'value_usd':round(row['quantity'] * row['unit_cost_usd'], 2)}
        scored.append(item)
        if level in {'alto','medio'} and row['status'] != 'delivered':
            alerts.append({'order_id':row['order_id'], 'supplier':row['supplier'], 'sku':row['sku'], 'risk_level':level, 'risk_score':score, 'reasons':reasons,
                           'suggestion': ('Revisar stock de seguridad y proveedor alternativo' if coverage is not None and coverage < 14 else 'Contactar al transportista y confirmar ETA')})
    alerts.sort(key=lambda a:(-a['risk_score'], a['order_id']))
    n = len(scored)
    active = [r for r in scored if r['status'] != 'delivered']
    summary = {'orders_total':n, 'orders_active':len(active), 'orders_delayed':sum(r['status']=='delayed' for r in scored),
               'high_risk':sum(r['risk_level']=='alto' and r['status']!='delivered' for r in scored),
               'inventory_value_usd':round(sum(r['inventory_units'] * r['unit_cost_usd'] for r in scored),2),
               'on_time_rate_pct':round(mean(r['on_time_rate'] for r in scored)*100,1),
               'alerts_total':len(alerts)}
    by_status = [{'name':status, 'count':sum(r['status']==status for r in scored)} for status in ['processing','in_transit','delayed','delivered']]
    return {'overview':summary, 'orders':scored, 'alerts':alerts, 'by_status':by_status,
            'model': {'type':'reglas explicables v1', 'note':'Puntuaciones heurísticas para priorización; no son probabilidades ni pronósticos estadísticos validados.'}}
