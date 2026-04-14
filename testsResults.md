infra test :
************************
(.venv) PS D:\TEKUP\Cours\2iem Année\Biométrie et Tatouage\Projects\biogait\backend> python -m pyest tests/test_infra.py -v
====================================== test session starts ======================================
platform win32 -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- D:\TEKUP\Cours\2iem Année\Biométri et Tatouage\Projects\biogait\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\TEKUP\Cours\2iem Année\Biométrie et Tatouage\Projects\biogait\backend\tests
configfile: pytest.ini
plugins: anyio-4.13.0, asyncio-1.3.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=session, asyncio_defaulttest_loop_scope=session
collected 2 items

tests\test_infra.py::test_register_and_login PASSED                                        [ 50%]
tests\test_infra.py::test_rbac_restriction PASSED                                          [100%]

======================================= warnings summary ========================================
test_infra.py::test_register_and_login
test_infra.py::test_rbac_restriction
  D:\TEKUP\Cours\2iem Année\Biométrie et Tatouage\Projects\biogait\backend\app\core\auth.py:16: DprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future ersion. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.TC).
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIREMINUTES))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================================= 2 passed, 2 warnings in 1.25s =================================




IA PIPELINE TEST
**********************

(.venv) PS D:\TEKUP\Cours\2iem Année\Biométrie et Tatouage\Projects\biogait\backend> python -m pytest tests/test_ia_pipeline.py tests/test_ia_benchmark.py -v
============================================= test session starts =============================================
platform win32 -- Python 3.12.3, pytest-7.4.3, pluggy-1.6.0 -- D:\TEKUP\Cours\2iem Année\Biométrie et Tatouage\Projects\biogait\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\TEKUP\Cours\2iem Année\Biométrie et Tatouage\Projects\biogait\backend\tests
configfile: pytest.ini
plugins: anyio-3.7.1, asyncio-0.23.2
asyncio: mode=Mode.AUTO
collected 7 items

tests\test_ia_pipeline.py::test_normalize_keypoints PASSED                                               [ 14%]
tests\test_ia_pipeline.py::test_compute_joint_angles PASSED                                              [ 28%]
tests\test_ia_pipeline.py::test_extract_gait_vector PASSED                                               [ 42%]
tests\test_ia_pipeline.py::test_faiss_index_add_and_search PASSED                                        [ 57%]
tests\test_ia_pipeline.py::test_pipeline_enroll_and_recognize PASSED                                     [ 71%]
tests\test_ia_pipeline.py::test_evaluate_far_frr PASSED                                                  [ 85%]
tests\test_ia_benchmark.py::test_faiss_benchmark PASSED                                                  [100%]

============================================== warnings summary =============================================== 
..\.venv\Lib\site-packages\_pytest\config\__init__.py:1373
  D:\TEKUP\Cours\2iem Année\Biométrie et Tatouage\Projects\biogait\.venv\Lib\site-packages\_pytest\config\__init__.py:1373: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

..\.venv\Lib\site-packages\_pytest\config\__init__.py:1373
  D:\TEKUP\Cours\2iem Année\Biométrie et Tatouage\Projects\biogait\.venv\Lib\site-packages\_pytest\config\__init__.py:1373: PytestConfigWarning: Unknown config option: asyncio_default_test_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

test_ia_pipeline.py::test_normalize_keypoints
  D:\TEKUP\Cours\2iem Année\Biométrie et Tatouage\Projects\biogait\.venv\Lib\site-packages\pytest_asyncio\plugin.py:647: DeprecationWarning: There is no current event loop
    old_loop = asyncio.get_event_loop()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================================== 7 passed, 3 warnings in 1.14s ========================================
