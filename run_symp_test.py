import time
from core import PhilosopherCore
from symposium import Symposium

core = PhilosopherCore()
personas = core.get_valid_personas()
if len(personas) < 2:
    print('Need at least 2 personas')
    raise SystemExit(1)

p1 = personas[0]
p2 = personas[1]
print('Using personas:', p1['name'], 'vs', p2['name'])

sym = Symposium(core, p1, p2, 'Testing Symposum')

for token_obj in sym.next_turn():
    if token_obj['type'] == 'token':
        print(token_obj['content'], end='', flush=True)
    elif token_obj['type'] == 'complete':
        print('\n---TURN COMPLETE---')

print('Done')
