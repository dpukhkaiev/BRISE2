from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_APPLIED = False


def _reconstruct_categorical(cls, state: tuple) -> Any:
    """Reconstruct CategoricalHyperparameter from old Cython tuple state."""
    import ConfigSpace.hyperparameters as csh
    # state: (default_indices_set, choices, default_indices_list,
    #         default_value, meta, name, default_float_idx, num_choices, weights)
    # Positions are best-guesses from pickle disassembly; be defensive.
    try:
        choices = state[1]  # tuple or list of choice values
        default_value = state[3]
        meta = state[4]
        name = state[5]
        weights = state[8] if len(state) > 8 else None
        if not isinstance(choices, (list, tuple)) or not choices:
            choices = [default_value] if default_value is not None else ['unknown']
        return csh.CategoricalHyperparameter(
            name=str(name) if name else 'unknown',
            choices=list(choices),
            default_value=default_value,
            weights=list(weights) if weights else None,
            meta=meta,
        )
    except Exception as e:
        logger.debug("CategoricalHP tuple reconstruct fallback: %s (state=%s)", e, state)
        # Last-resort: minimal object
        obj = cls.__new__(cls)
        try:
            obj.__dict__['name'] = str(state[5]) if len(state) > 5 else 'unknown'
            obj.__dict__['choices'] = list(state[1]) if len(state) > 1 else []
        except Exception:
            pass
        return obj


def _reconstruct_uniform_int(cls, state: tuple) -> Any:
    """Reconstruct UniformIntegerHyperparameter from old Cython tuple state."""
    import ConfigSpace.hyperparameters as csh
    try:
        lower = int(state[0]) if state[0] is not None else 0
        upper = int(state[2]) if state[2] is not None else 1  # position 2 = default_int
        actual_upper = int(state[10]) if len(state) > 10 and state[10] is not None else upper + 1
        default = int(state[2]) if state[2] is not None else lower
        log = bool(state[3]) if len(state) > 3 and state[3] is not None else False
        meta = state[5] if len(state) > 5 else None
        name = str(state[6]) if len(state) > 6 and state[6] else 'unknown'
        # lower is often None (stored in sub-HP); use 0
        if lower is None or lower >= actual_upper:
            lower = 0
        return csh.UniformIntegerHyperparameter(
            name=name,
            lower=lower,
            upper=actual_upper,
            default_value=max(lower, min(default, actual_upper)),
            log=log,
            meta=meta,
        )
    except Exception as e:
        logger.debug("UniformIntHP tuple reconstruct fallback: %s (state=%s)", e, state)
        obj = cls.__new__(cls)
        try:
            obj.__dict__['name'] = str(state[6]) if len(state) > 6 else 'unknown'
        except Exception:
            pass
        return obj


def _reconstruct_uniform_float(cls, state: tuple) -> Any:
    """Reconstruct UniformFloatHyperparameter from old Cython tuple state."""
    import ConfigSpace.hyperparameters as csh
    try:
        lower = float(state[0]) if state[0] is not None else 0.0
        upper = float(state[1]) if state[1] is not None else 1.0
        default = float(state[4]) if len(state) > 4 and state[4] is not None else lower
        log = bool(state[3]) if len(state) > 3 and state[3] is not None else False
        meta = state[5] if len(state) > 5 else None
        name = str(state[6]) if len(state) > 6 and state[6] else 'unknown'
        if lower >= upper:
            upper = lower + 1.0
        return csh.UniformFloatHyperparameter(
            name=name,
            lower=lower,
            upper=upper,
            default_value=max(lower, min(default, upper)),
            log=log,
            meta=meta,
        )
    except Exception as e:
        logger.debug("UniformFloatHP tuple reconstruct fallback: %s (state=%s)", e, state)
        obj = cls.__new__(cls)
        try:
            obj.__dict__['name'] = str(state[6]) if len(state) > 6 else 'unknown'
        except Exception:
            pass
        return obj


def _reconstruct_equals_condition(cls, state: tuple) -> Any:
    """Reconstruct EqualsCondition from old Cython tuple state."""
    import ConfigSpace.conditions as csc
    try:
        child, parent, value = state[0], state[1], state[2]
        return csc.EqualsCondition(child=child, parent=parent, value=value)
    except Exception as e:
        logger.debug("EqualsCondition tuple reconstruct fallback: %s (state=%s)", e, state)
        obj = cls.__new__(cls)
        try:
            if len(state) >= 3:
                obj.__dict__.update({'child': state[0], 'parent': state[1], 'value': state[2]})
        except Exception:
            pass
        return obj


_RECONSTRUCTORS = {
    'CategoricalHyperparameter': _reconstruct_categorical,
    'UniformIntegerHyperparameter': _reconstruct_uniform_int,
    'UniformFloatHyperparameter': _reconstruct_uniform_float,
    'EqualsCondition': _reconstruct_equals_condition,
}


def _make_pyx_unpickle(cls_attr_name: str):
    """
    Return a ``__pyx_unpickle_<ClassName>`` shim compatible with legacy reducers.

    When ``state`` is ``None`` (the common case for old pickles), the object is
    created bare; the BUILD opcode will then call ``obj.__setstate__(tuple_state)``.

    We monkey-patch a ``__setstate__`` onto the object instance itself so that
    when BUILD fires it will use our tuple-aware handler instead of the new
    Python ``__setstate__`` that only accepts dicts.
    """
    reconstructor = _RECONSTRUCTORS.get(cls_attr_name)

    def __pyx_unpickle(*args):
        if not args:
            raise TypeError(f"__pyx_unpickle_{cls_attr_name} missing required class argument")

        cls = args[0]
        # Old pickles typically pass (cls, checksum, state); some pass (cls, state).
        state = args[-1] if len(args) > 1 else None

        if state is not None:
            # State was passed directly - uncommon but handle it
            if reconstructor and isinstance(state, tuple):
                return reconstructor(cls, state)
            obj = cls.__new__(cls)
            if isinstance(state, dict):
                if hasattr(obj, '__setstate__'):
                    obj.__setstate__(state)
                else:
                    obj.__dict__.update(state)
            return obj

        obj = cls.__new__(cls)

        if reconstructor:
            cls_setstate = getattr(cls, '__setstate__', None)

            # Wrap __setstate__ on this specific instance to intercept the
            # tuple BUILD call and reconstruct properly.
            def _tuple_aware_setstate(tuple_state, _cls=cls, _recon=reconstructor):
                # Replace self (obj) with a fully initialized instance.
                # We cannot swap obj in-place since it's already on the pickle stack,
                # so we copy the __dict__ of the new instance into obj.
                if isinstance(tuple_state, dict):
                    # New format - delegate to normal __setstate__
                    if callable(cls_setstate):
                        cls_setstate(obj, tuple_state)
                    else:
                        obj.__dict__.update(tuple_state)
                    return
                try:
                    new_inst = _recon(_cls, tuple_state)
                    obj.__dict__.clear()
                    obj.__dict__.update(new_inst.__dict__)
                except Exception as exc:
                    logger.debug(
                        "Tuple __setstate__ reconstruction failed for %s: %s",
                        cls_attr_name, exc
                    )

            import types
            obj.__setstate__ = types.MethodType(
                lambda self, s, f=_tuple_aware_setstate: f(s), obj
            )
        return obj

    __pyx_unpickle.__name__ = f"__pyx_unpickle_{cls_attr_name}"
    __pyx_unpickle.__qualname__ = __pyx_unpickle.__name__
    return __pyx_unpickle


_PATCH_MAP = {
    'ConfigSpace.hyperparameters': [
        ('__pyx_unpickle_CategoricalHyperparameter', 'CategoricalHyperparameter'),
        ('__pyx_unpickle_UniformIntegerHyperparameter', 'UniformIntegerHyperparameter'),
        ('__pyx_unpickle_UniformFloatHyperparameter', 'UniformFloatHyperparameter'),
        ('__pyx_unpickle_NormalIntegerHyperparameter', 'NormalIntegerHyperparameter'),
        ('__pyx_unpickle_NormalFloatHyperparameter', 'NormalFloatHyperparameter'),
        ('__pyx_unpickle_OrdinalHyperparameter', 'OrdinalHyperparameter'),
        ('__pyx_unpickle_UnParametrizedHyperparameter', 'UnParametrizedHyperparameter'),
    ],
    'ConfigSpace.conditions': [
        ('__pyx_unpickle_EqualsCondition', 'EqualsCondition'),
        ('__pyx_unpickle_NotEqualsCondition', 'NotEqualsCondition'),
        ('__pyx_unpickle_GreaterThanCondition', 'GreaterThanCondition'),
        ('__pyx_unpickle_LessThanCondition', 'LessThanCondition'),
        ('__pyx_unpickle_InCondition', 'InCondition'),
        ('__pyx_unpickle_AndConjunction', 'AndConjunction'),
        ('__pyx_unpickle_OrConjunction', 'OrConjunction'),
    ],
    'ConfigSpace.forbidden': [
        ('__pyx_unpickle_ForbiddenEqualsClause', 'ForbiddenEqualsClause'),
        ('__pyx_unpickle_ForbiddenInClause', 'ForbiddenInClause'),
        ('__pyx_unpickle_ForbiddenAndConjunction', 'ForbiddenAndConjunction'),
    ],
    'ConfigSpace.configuration_space': [
        ('__pyx_unpickle_ConfigurationSpace', 'ConfigurationSpace'),
        ('__pyx_unpickle_Configuration', 'Configuration'),
    ],
}


def apply() -> None:
    """
    Inject missing ``__pyx_unpickle_*`` shims into ConfigSpace submodules.

    Safe to call multiple times (idempotent).
    """
    global _APPLIED
    if _APPLIED:
        return

    import importlib
    import sys

    patched = []

    for module_fqn, entries in _PATCH_MAP.items():
        try:
            mod = sys.modules.get(module_fqn) or importlib.import_module(module_fqn)
        except ImportError:
            logger.debug("Legacy compat: module %s not found, skipping", module_fqn)
            continue

        for func_name, cls_name in entries:
            if hasattr(mod, func_name):
                continue  # already present (old ConfigSpace)
            shim = _make_pyx_unpickle(cls_name)
            setattr(mod, func_name, shim)
            patched.append(f"{module_fqn}.{func_name}")

    if patched:
        logger.debug("Legacy ConfigSpace pickle shims installed: %s", patched)

    _APPLIED = True

