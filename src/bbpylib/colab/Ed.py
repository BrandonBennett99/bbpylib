from pathlib import Path
import ipywidgets as w
from IPython.display import display, Javascript

class Ed:
    def __init__(self, path_str, height="200px", path_chars=80, visible=True):
        self.path = Path(path_str)

        self.editor = w.Textarea(layout=w.Layout(width="100%", height=height))
        self.editor.add_class("monospace")

        full = str(self.path)
        shown = ("…" + full[-path_chars:]) if len(full) > path_chars else full
        self.path_text = w.HTML(f"<code>{shown}</code>")

        self.status = w.Label("")

        self.save_button = w.Button(description="Saved", button_style="success")
        self.quit_button = w.Button(description="Quit", button_style="success")
        self.reload_button = w.Button(description="Reload")

        self._ui = w.VBox([
            self.path_text,
            w.HBox([#self.reload_button, 
                    self.save_button, 
                    self.quit_button]),
            self.status,
            self.editor
        ])

        self._baseline_text = ""
        self._dirty = False

        self.save_button.on_click(self._save)
        self.reload_button.on_click(self._reload)
        self.quit_button.on_click(self._quit)
        self.editor.observe(self._on_edit, names="value")

        self._reload()

        # ---- NEW: disable spellcheck for this editor only ----
        display(Javascript("""
        document.querySelectorAll('.ed-editor textarea').forEach(t => {
            t.setAttribute('spellcheck', 'false');
        });
        """))

        if visible:
             self.display()

    def _set_dirty(self, dirty: bool):
        self._dirty = dirty
        if dirty:
            self.save_button.description = "Save"
            self.save_button.button_style = "warning"
            self.quit_button.button_style = "warning"
        else:
            self.save_button.description = "Saved"
            self.save_button.button_style = "success"
            self.quit_button.button_style = "success"

    def _on_edit(self, change):
        self._set_dirty(change["new"] != self._baseline_text)

    def _reload(self, *_):
        text = self.path.read_text(encoding="utf-8")
        self.editor.unobserve(self._on_edit, names="value")
        self.editor.value = text
        self.editor.observe(self._on_edit, names="value")
        self._baseline_text = text
        self._set_dirty(False)
        self.status.value = f"Loaded: {self.path.name}"

    def _save(self, *_):
        self.path.write_text(self.editor.value, encoding="utf-8")
        self._baseline_text = self.editor.value
        self._set_dirty(False)
        self.status.value = f"Saved: {self.path.name}"

    def _quit(self, *_):
        self._ui.layout.display = "none"

    def display(self):
        display(self._ui)
