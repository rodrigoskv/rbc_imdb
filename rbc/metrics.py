from typing import List

def acuracia(y_true: List[str], y_pred: List[str]) -> float:
    """
    Retorna a fração de acertos.
    """
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return 0.0
    acertos = sum(1 for a, b in zip(y_true, y_pred) if a == b)
    return acertos / len(y_true)
