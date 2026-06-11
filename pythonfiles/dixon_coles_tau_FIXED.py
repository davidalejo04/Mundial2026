def dixon_coles_tau(x, y, lam1, lam2, rho, fase):
    """
    Factor de ajuste tau del modelo Dixon-Coles.
    
    Modificaciones:
    - Ajuste de rho por fase (fases eliminatorias más cerradas)
    - Penalización de marcadores extremos (x > 3 AND y > 3)
    
    FIXES APLICADOS:
    - ✅ Eliminado código muerto en la penalización de marcadores extremos.
    - ✅ Separación limpia de la regla estocástica (Dixon-Coles) y la regla de negocio.
    """
    
    # 1. Ajuste de rho por fase
    # En fases eliminatorias, se reduce el parámetro de dependencia
    if fase != 'Grupos':
        rho = rho * 0.85
    
    # 2. Regla de Negocio: Penalizar marcadores extremos (ej: 4-4, 5-4, 4-5)
    # El base_tau teórico de Dixon-Coles para estos marcadores es siempre 1.0.
    # Aplicamos directamente la penalización del 50%.
    if x > 3 and y > 3:
        return 0.6
    
    # 3. Casos estándar Dixon-Coles para marcadores bajos (ajuste de baja anotación)
    if x == 0 and y == 0:
        return 1 - lam1 * lam2 * rho
    elif x == 0 and y == 1:
        return 1 + lam1 * rho
    elif x == 1 and y == 0:
        return 1 + lam2 * rho
    elif x == 1 and y == 1:
        return 1 - rho
    
    # 4. Marcadores normales genéricos (2-0, 3-1, 2-2, etc.)
    return 1.0

