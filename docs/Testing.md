# Testing your UI

No terminal needed: render to text and simulate input.

```python
def test_login_form():
    name = TextArea(id="name", height=1)
    submitted = []
    app = App(Box(name, Button("Login", on_click=lambda e: submitted.append(name.value.text))))

    app.render(40, 5)
    app.feed("alice")          # raw terminal input: text, escape sequences, mouse reports
    app.press("tab", "enter")  # key names
    assert submitted == ["alice"]
    assert "alice" in app.snapshot()
    app.click(0, 1)            # mouse click at screen coordinates
```

## Writing frames to a file

To write frames to a file instead of a terminal, give the app's canvas a
{class}`~pytui.FileScreen`:

```python
app.canvas.screen = FileScreen("frame.txt")  # colors=True keeps styles as ANSI codes
app.render(80, 24)
app.canvas.present()                         # frame.txt now holds the UI
app.press("tab")
app.canvas.present()                         # rewritten with the new frame
```
