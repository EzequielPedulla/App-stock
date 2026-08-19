import tkinter as tk
import ttkbootstrap as ttk


class ScrollableFrame(tk.Frame):
    """Contenedor con scroll vertical. Si el contenido no entra en la
    ventana (monitor chico, ventana achicada), se puede llegar a todo con
    la scrollbar o la rueda del mouse, en vez de quedar cortado sin forma
    de alcanzarlo.

    El contenido real va dentro de `self.interior` (un Frame normal).
    """

    def __init__(self, parent, bg="white"):
        super().__init__(parent, bg=bg)

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self._canvas.yview)
        self.interior = tk.Frame(self._canvas, bg=bg)

        self._window = self._canvas.create_window(
            (0, 0), window=self.interior, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)

        self.interior.bind("<Configure>", self._on_interior_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        self._canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll con la rueda del mouse, solo mientras el mouse está sobre
        # esta pestaña (no global: no tiene que afectar a las otras).
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_interior_configure(self, event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfig(self._window, width=event.width)

    def _bind_mousewheel(self, event) -> None:
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event) -> None:
        self._canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event) -> None:
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
