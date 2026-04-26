from nicegui import ui

ui.button('Test Prop').props('onclick="alert(\'prop\')"')
ui.button('Test JS Handler').on('click', js_handler='() => alert("js_handler")')

ui.run(port=8089, host="0.0.0.0")
