import sys
import importlib
import traceback
import os

# Ensure repository root and backend app package dir are on sys.path
ROOT = os.path.abspath(os.path.dirname(__file__))
BACKEND_APP = os.path.abspath(os.path.join(ROOT, 'app', 'backend', 'ledger_api'))
if BACKEND_APP not in sys.path:
    sys.path.insert(0, BACKEND_APP)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

modules = [
    'app.st_app.logic.manage.block_unit_price_interactive',
    'app.st_app.logic.manage.block_unit_price_interactive_main',
]

results = {}
for mod in modules:
    try:
        m = importlib.import_module(mod)
        cls = getattr(m, 'BlockUnitPriceInteractive', None)
        results[mod] = f'OK, class={cls!r}'
    except Exception as e:
        results[mod] = 'ERROR: ' + ''.join(traceback.format_exception_only(type(e), e)).strip()

for k, v in results.items():
    print(f'{k}: {v}')

# exit with non-zero if any failed
if any(v.startswith('ERROR') for v in results.values()):
    raise SystemExit(2)