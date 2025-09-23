import ttkbootstrap as ttk


class ReportForm(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Reportes", padding=20, **kwargs)
        self.pack(fill="x", pady=(0, 20))
        self._create_widgets()
        self.editing_mode = False

    def _create_widgets(self):
        pass
