from __future__ import annotations

import itertools
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

INSTRUCTIONS = ["{instruction}: {problem}", "Solve and report the result: {problem}", "Work the problem and give the final answer: {problem}", "Compute the requested result: {problem}"]
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096


def _level_num(difficulty: str) -> int:
    try: value = int(str(difficulty).rsplit('_', 1)[-1])
    except Exception: value = 1
    return max(1, min(5, value))


def _stable_seed(*parts) -> str: return '|'.join(str(p) for p in parts)

def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)): break
        yield item

MODULE_INFO = {"module_id": "algebra.factoring_trinomials_basic", "name": "Factoring Trinomials Basic", "topic": "algebra", "subtopic": "core_algebra", "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"], "enabled": True}
LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 850, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {"level_1": {"sum_positive": 700}, "level_2": {"sum_negative": 850}, "level_3": {"difference_signs": 1000}, "level_4": {"leading_coefficient_one": 1200}, "level_5": {"with_gcf_then_factor": 1400}}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}


def _spec(family, values, problem, answer):
    canonical=':'.join([family]+[str(v) for v in values])
    return {"family":family,"values":values,"problem":problem,"answer":answer,"canonical_key":canonical,"case_id":canonical,"family_id":family}


def _sample_from_spec(spec,difficulty,instruction_idx=0):
    answer=spec['answer']
    metadata={"family":spec['family'],"level_number":_level_num(difficulty),"structured":True,"canonical_key":spec['canonical_key'],"case_id":spec['case_id'],"family_id":spec['family_id'],"template_id":spec['family'],"final_answer":answer,"values":list(spec.get('values',[]))}
    instruction=INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction="Factor the trinomial", problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


def iter_level1_specs():
    emitted=0
    for m in range(1,21):
        for n in range(1,21):
            b=m+n; c=m*n
            yield _spec('sum_positive',(m,n),f"Factor x^2 + {b}x + {c}.",f"(x + {m})(x + {n})")
            emitted+=1
            if emitted>=FAMILY_CAPS['level_1']['sum_positive']: return

def iter_level2_specs():
    emitted=0
    for m in range(1,21):
        for n in range(1,21):
            b=-(m+n); c=m*n
            yield _spec('sum_negative',(m,n),f"Factor x^2 {b:+d}x + {c}.",f"(x - {m})(x - {n})")
            emitted+=1
            if emitted>=FAMILY_CAPS['level_2']['sum_negative']: return

def iter_level3_specs():
    emitted=0
    for m in range(1,21):
        for n in range(1,21):
            b=m-n; c=-m*n
            if b>=0:
                prob=f"Factor x^2 + {b}x - {m*n}."
            else:
                prob=f"Factor x^2 - {abs(b)}x - {m*n}."
            ans=f"(x + {m})(x - {n})"
            yield _spec('difference_signs',(m,n),prob,ans)
            emitted+=1
            if emitted>=FAMILY_CAPS['level_3']['difference_signs']: return

def iter_level4_specs():
    emitted=0
    for m in range(1,21):
        for n in range(1,21):
            b=m+n; c=m*n
            yield _spec('leading_coefficient_one',(m,n),f"Factor completely: x^2 + {b}x + {c}.",f"(x + {m})(x + {n})")
            emitted+=1
            if emitted>=FAMILY_CAPS['level_4']['leading_coefficient_one']: return

def iter_level5_specs():
    emitted=0
    for g in range(2,11):
        for m in range(1,16):
            for n in range(1,16):
                b=m+n; c=m*n
                yield _spec('with_gcf_then_factor',(g,m,n),f"Factor completely: {g}x^2 + {g*b}x + {g*c}.",f"{g}(x + {m})(x + {n})")
                emitted+=1
                if emitted>=FAMILY_CAPS['level_5']['with_gcf_then_factor']: return


def _iter_specs(difficulty='level_1'):
    level=_level_num(difficulty)
    if level==1:return _take(iter_level1_specs(),LEVEL_SPEC_CAPS['level_1'])
    if level==2:return _take(iter_level2_specs(),LEVEL_SPEC_CAPS['level_2'])
    if level==3:return _take(iter_level3_specs(),LEVEL_SPEC_CAPS['level_3'])
    if level==4:return _take(iter_level4_specs(),LEVEL_SPEC_CAPS['level_4'])
    return _take(iter_level5_specs(),LEVEL_SPEC_CAPS['level_5'])


def curriculum(): return {'level_1':['factor x^2 + bx + c with positive binomial terms'],'level_2':['factor x^2 + bx + c with both negative binomial terms'],'level_3':['factor trinomials with opposite-sign binomial factors'],'level_4':['repeat complete basic-trinomial factoring'],'level_5':['factor out a GCF and then factor the trinomial']}

def estimate_capacity(difficulty='level_1'): return dict(CAPACITY_HINTS.get(difficulty, {'value': None, 'quality': 'unknown'}))

def generate(count=10,difficulty='level_1',seed=None):
    count=max(0,int(count)); prefix=min(max(count*MAX_GENERATE_MULTIPLIER,256),MAX_SPEC_PREFIX); pool=list(itertools.islice(_iter_specs(difficulty),0,prefix));
    if not pool or count==0:return []
    rng=random.Random(_stable_seed(MODULE_INFO['module_id'],difficulty,seed,'generate')); rng.shuffle(pool); return [_sample_from_spec(spec,difficulty,i) for i,spec in enumerate(pool[:count])]

def generate_unique(count=10,difficulty='level_1',offset=0,stride=1,seed=None):
    count=max(0,int(count)); offset=max(0,int(offset)); stride=max(1,int(stride)); pool=list(itertools.islice(_iter_specs(difficulty),0,MAX_SPEC_PREFIX)); rng=random.Random(_stable_seed(MODULE_INFO['module_id'],difficulty,seed,offset,stride,'unique')); rng.shuffle(pool); seen=set(); ordered=[]
    for spec in pool:
        if spec['canonical_key'] in seen: continue
        seen.add(spec['canonical_key']); ordered.append(spec)
    return [_sample_from_spec(spec,difficulty,i) for i,spec in enumerate(ordered[offset::stride][:count])]

def iter_samples(difficulty='level_1',seed=None):
    max_items=min(LEVEL_SPEC_CAPS.get(difficulty,1000),MAX_ITER_SAMPLES); pool=list(itertools.islice(_iter_specs(difficulty),0,max_items)); rng=random.Random(_stable_seed(MODULE_INFO['module_id'],difficulty,seed,'iter')); rng.shuffle(pool); seen=set()
    for idx,spec in enumerate(pool):
        if spec['canonical_key'] in seen: continue
        seen.add(spec['canonical_key']); yield _sample_from_spec(spec,difficulty,idx)


