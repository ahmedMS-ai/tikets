
def test_imports():
    import app.main as main
    import app.services.gemini_client as gc
    import app.services.sheets_client as sc
    import app.auth.oauth as oauth

    assert hasattr(gc, "evaluate_strict")
    assert hasattr(sc, "append_ticket_row")
    assert hasattr(oauth, "login_button")
