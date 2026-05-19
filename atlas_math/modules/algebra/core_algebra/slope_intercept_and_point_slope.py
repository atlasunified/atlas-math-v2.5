from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

INSTRUCTIONS = [
    "{instruction}: {problem}",
    "Solve and report the result: {problem}",
    "Work the problem and give the final answer: {problem}",
    "Compute the requested result: {problem}",
]

MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096


def _level_num(difficulty: str) -> int:
    try:
        value = int(str(difficulty).rsplit("_", 1)[-1])
    except Exception:
        value = 1
    return max(1, min(5, value))


def _stable_seed(*parts) -> str:
    return "|".join(str(p) for p in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _fmt_number(value) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    return str(value)

MODULE_INFO = {"module_id": "algebra.slope_intercept_and_point_slope", "name": "Slope-Intercept and Point-Slope", "topic": "algebra", "subtopic": "core_algebra", "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"], "enabled": True}
LEVEL_SPEC_CAPS = {"level_1": 600, "level_2": 800, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {"level_1": {"to_slope_intercept": 600}, "level_2": {"to_point_slope": 800}, "level_3": {"convert_between_forms": 1000}, "level_4": {"fractional_slope": 1200}, "level_5": {"parallel_perpendicular_forms": 1400}}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k,v in LEVEL_SPEC_CAPS.items()}

def _spec(family, values, problem, answer):
    canonical=':'.join([family]+[str(v) for v in values]); return {"family":family,"values":values,"problem":problem,"answer":answer,"canonical_key":canonical,"case_id":canonical,"family_id":family}

def _sample_from_spec(spec,difficulty,instruction_idx=0):
    answer=spec['answer']; metadata={"family":spec['family'],"level_number":_level_num(difficulty),"structured":True,"canonical_key":spec['canonical_key'],"case_id":spec['case_id'],"family_id":spec['family_id'],"template_id":spec['family'],"final_answer":answer,"values":list(spec.get('values',[]))}
    instruction=INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction="Write the line in the requested form", problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)

def iter_level1_specs():
    emitted=0; limit=FAMILY_CAPS['level_1']['to_slope_intercept']
    for m in [-5,-4,-3,-2,-1,1,2,3,4,5]:
        for b in range(-10,11):
            yield _spec('to_slope_intercept',(m,b),f"Given slope {m} and y-intercept {b}, write the line in slope-intercept form.",f"y = {m}x + {b}")
            emitted+=1
            if emitted>=limit:return

def iter_level2_specs():
    emitted=0; limit=FAMILY_CAPS['level_2']['to_point_slope']
    for m in [-5,-4,-3,-2,-1,1,2,3,4,5]:
        for x1 in range(-6,7):
            for y1 in range(-10,11):
                yield _spec('to_point_slope',(m,x1,y1),f"Write the equation of the line with slope {m} through ({x1}, {y1}) in point-slope form.",f"y - ({y1}) = {m}(x - ({x1}))")
                emitted+=1
                if emitted>=limit:return

def iter_level3_specs():
    emitted=0; limit=FAMILY_CAPS['level_3']['convert_between_forms']
    for m in [-4,-3,-2,-1,1,2,3,4]:
        for x1 in range(-5,6):
            for b in range(-8,9):
                y1=m*x1+b
                yield _spec('convert_between_forms',(m,x1,b),f"Convert the point-slope equation y - ({y1}) = {m}(x - ({x1})) to slope-intercept form.",f"y = {m}x + {b}")
                emitted+=1
                if emitted>=limit:return

def iter_level4_specs():
    emitted=0; limit=FAMILY_CAPS['level_4']['fractional_slope']
    for num in [-5,-4,-3,-2,-1,1,2,3,4,5]:
        for den in [2,3,4,5]:
            for x1 in range(-4,5):
                for b in range(-6,7):
                    m=Fraction(num,den); y1=m*x1+b
                    yield _spec('fractional_slope',(num,den,x1,b),f"A line has slope {num}/{den} and passes through ({x1}, {_fmt_number(y1)}). Write it in point-slope form.",f"y - ({_fmt_number(y1)}) = {num}/{den}(x - ({x1}))")
                    emitted+=1
                    if emitted>=limit:return

def iter_level5_specs():
    emitted=0; limit=FAMILY_CAPS['level_5']['parallel_perpendicular_forms']
    for m in [-4,-3,-2,-1,1,2,3,4]:
        for x1 in range(-5,6):
            for y1 in range(-8,9):
                for mode in ['parallel','perpendicular']:
                    target = Fraction(m,1) if mode=='parallel' else Fraction(-1,m)
                    yield _spec('parallel_perpendicular_forms',(m,x1,y1,mode),f"Write the equation in point-slope form of the line {mode} to y = {m}x + 1 through ({x1}, {y1}).",f"y - ({y1}) = {_fmt_number(target)}(x - ({x1}))")
                    emitted+=1
                    if emitted>=limit:return

def _iter_specs(difficulty='level_1'):
    level=_level_num(difficulty)
    if level==1:return _take(iter_level1_specs(),LEVEL_SPEC_CAPS['level_1'])
    if level==2:return _take(iter_level2_specs(),LEVEL_SPEC_CAPS['level_2'])
    if level==3:return _take(iter_level3_specs(),LEVEL_SPEC_CAPS['level_3'])
    if level==4:return _take(iter_level4_specs(),LEVEL_SPEC_CAPS['level_4'])
    return _take(iter_level5_specs(),LEVEL_SPEC_CAPS['level_5'])

def curriculum(): return {'level_1':['write slope-intercept form from slope and intercept'],'level_2':['write point-slope form from point and slope'],'level_3':['convert point-slope to slope-intercept'],'level_4':['handle fractional slopes'],'level_5':['parallel and perpendicular line forms']}
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


