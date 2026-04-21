from nicegui import ui
print("Attributs de ui :", [attr for attr in dir(ui) if not attr.startswith('_')])
