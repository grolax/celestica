"""Configuración de pytest.

Los scripts test_e2e.py / test_fase*.py son verificaciones de la sesión 2 que
corren como scripts (`python tests/test_fase1.py`) con checks a nivel de
módulo, no como tests de pytest: se excluyen de la recolección para que un
`pytest` a secas ejecute solo los tests reales sin importarlos."""
collect_ignore = ["test_e2e.py", "test_fase1.py", "test_fase3.py", "test_fase5.py"]
