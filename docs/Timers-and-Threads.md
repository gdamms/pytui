# Timers and threads

```python
timer = app.set_interval(1.0, update_clock)  # timer.cancel() to stop
app.call_later(0.5, lambda: status.set_style(display="none"))

def worker():                                # in another thread
    result = slow_computation()
    app.call_from_thread(show_result, result)  # thread-safe, redraws afterwards
```

The UI is redrawn after every timer and thread callback. See {class}`~pytui.App` and
{class}`~pytui.Timer`.
