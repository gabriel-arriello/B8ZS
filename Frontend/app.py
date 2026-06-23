"""
Codificação de Linha — B8ZS | UTFPR
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os, threading

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Backend.crypto import criptografar, descriptografar, bytes_para_binario, binario_para_bytes
from Backend.b8zs import codificar, decodificar
from Backend.rede import Servidor, enviar_niveis

# ─── Paleta ──────────────────────────────────────────────────────────────────
C_BG        = "#F0F2F5"   
C_SIDEBAR   = "#1E2A3A"   
C_CARD      = "#FFFFFF"   
C_BORDER    = "#DDE1E7"   
C_ACCENT    = "#2563EB"   
C_ACCENT2   = "#059669"   
C_WARN      = "#DC2626"   
C_WAVE_POS  = "#2563EB"   
C_WAVE_NEG  = "#DC2626"   
C_WAVE_ZERO = "#94A3B8"   
C_WAVE_BG   = "#F8FAFC"   
C_TEXT      = "#1E293B"   
C_TEXT2     = "#64748B"   
C_SIDEBAR_T = "#CBD5E1"   
C_SIDEBAR_A = "#FFFFFF"   

FONT_HEAD   = ("Segoe UI", 11, "bold")
FONT_LABEL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 9)
FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_BADGE  = ("Segoe UI", 8, "bold")

# ─── Utilitários de widget ────────────────────────────────────────────────────
def make_card(parent, title="", pady=8):
    outer = tk.Frame(parent, bg=C_CARD, highlightthickness=1, highlightbackground=C_BORDER, bd=0)
    if title:
        tk.Label(outer, text=title.upper(), bg=C_CARD, fg=C_TEXT2, font=FONT_BADGE, anchor="w").pack(fill="x", padx=14, pady=(10, 2))
    inner = tk.Frame(outer, bg=C_CARD)
    inner.pack(fill="both", expand=True, padx=14, pady=(2, 10))
    return outer, inner

def make_entry(parent, placeholder="", width=28):
    e = tk.Entry(parent, bg=C_BG, fg=C_TEXT, relief="flat", font=FONT_MONO, insertbackground=C_ACCENT,
                 highlightthickness=1, highlightbackground=C_BORDER, highlightcolor=C_ACCENT, width=width)
    if placeholder: e.insert(0, placeholder)
    return e

def make_text(parent, height=3, color=C_TEXT, mono=True):
    fnt = FONT_MONO if mono else ("Segoe UI", 10)
    return tk.Text(parent, height=height, bg=C_BG, fg=color, font=fnt, relief="flat", bd=0,
                   insertbackground=C_ACCENT, wrap="word", highlightthickness=1, highlightbackground=C_BORDER, highlightcolor=C_ACCENT)

def make_readonly(parent, height=2, color=C_TEXT2):
    return tk.Text(parent, height=height, bg=C_CARD, fg=color, font=FONT_MONO, relief="flat", bd=0,
                   insertbackground=C_ACCENT, wrap="word", state="disabled", cursor="arrow", highlightthickness=0)

def set_ro(widget, text, color=None):
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", text)
    if color: widget.config(fg=color)
    widget.config(state="disabled")

def btn(parent, text, color=C_ACCENT, text_color="#FFFFFF", cmd=None, width=None, pady=8):
    kw = dict(bg=color, fg=text_color, text=text, font=FONT_HEAD, relief="flat", bd=0, cursor="hand2",
              activebackground=color, activeforeground=text_color, command=cmd or (lambda: None), pady=pady, padx=16)
    if width: kw["width"] = width
    return tk.Button(parent, **kw)

# ─── Gráfico de onda ──────────────────────────────────────────────────────────
class WaveCanvas(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C_WAVE_BG, bd=0, highlightthickness=1, highlightbackground=C_BORDER, **kw)
        self._niveis = []
        self.bind("<Configure>", lambda e: self._redraw())

    def set(self, niveis):
        self._niveis = niveis
        self._redraw()

    def _redraw(self):
        self.delete("all")
        if not self._niveis:
            self.create_text(self.winfo_width() // 2 or 200, self.winfo_height() // 2 or 50,
                             text="— sem sinal —", fill=C_WAVE_ZERO, font=FONT_LABEL)
            return
        w, h = self.winfo_width() or 500, self.winfo_height() or 90
        mid, amp = h // 2, (h // 2) - 14
        n, step = self._niveis, max(3, w // len(self._niveis))

        self.create_line(0, mid, w, mid, fill=C_BORDER, dash=(4, 3), width=1)
        self.create_text(6, mid - amp + 2, text="+V", fill=C_WAVE_POS, font=("Segoe UI", 7), anchor="w")
        self.create_text(6, mid + amp - 2, text="−V", fill=C_WAVE_NEG, font=("Segoe UI", 7), anchor="w")

        x = 20
        for i, nivel in enumerate(n):
            y = mid - nivel * amp
            cor = C_WAVE_POS if nivel > 0 else C_WAVE_NEG if nivel < 0 else C_WAVE_ZERO
            x2 = x + step
            self.create_line(x, y, x2, y, fill=cor, width=2)
            if i + 1 < len(n):
                y2 = mid - n[i + 1] * amp
                if y != y2: self.create_line(x2, y, x2, y2, fill=C_TEXT2, width=1)
            x = x2

# ─── Painel Host A (Envio) ────────────────────────────────────────────────────
class PainelEnvio(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C_BG)
        self._niveis = []
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C_BG)
        hdr.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(hdr, text="Host A", bg=C_BG, fg=C_ACCENT, font=FONT_TITLE).pack(side="left")
        tk.Label(hdr, text="  envio e codificação B8ZS", bg=C_BG, fg=C_TEXT2, font=("Segoe UI", 11)).pack(side="left", anchor="s", pady=(0, 3))

        row1 = tk.Frame(self, bg=C_BG)
        row1.pack(fill="x", padx=24, pady=4)
        row1.columnconfigure(0, weight=3)
        row1.columnconfigure(1, weight=2)

        c_msg, f_msg = make_card(row1, "mensagem")
        c_msg.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.txt_msg = make_text(f_msg, height=4)
        self.txt_msg.pack(fill="x")

        c_net, f_net = make_card(row1, "Conexão e Destino")
        c_net.grid(row=0, column=1, sticky="nsew")

        tk.Label(f_net, text="Porta COM Local (ex: COM3)", bg=C_CARD, fg=C_TEXT2, font=FONT_LABEL, anchor="w").pack(fill="x")
        self.e_porta = make_entry(f_net, "COM3", width=20)
        self.e_porta.pack(fill="x", pady=(2, 8))

        tk.Label(f_net, text="Nó Destino", bg=C_CARD, fg=C_TEXT2, font=FONT_LABEL, anchor="w").pack(fill="x")
        self.combo_dest = ttk.Combobox(f_net, values=["Master", "Slave 1", "Slave 2"], state="readonly")
        self.combo_dest.current(1) # Padrão: Enviar para Slave 1
        self.combo_dest.pack(fill="x", pady=(2, 0))

        f_btns = tk.Frame(self, bg=C_BG)
        f_btns.pack(fill="x", padx=24, pady=8)

        btn(f_btns, "▶  Processar", color=C_ACCENT, cmd=self._processar).pack(side="left", padx=(0, 8))
        btn(f_btns, "📡  Enviar pela Rede", color=C_ACCENT2, cmd=self._enviar_rede).pack(side="left")

        self.lbl_status = tk.Label(f_btns, text="", bg=C_BG, fg=C_TEXT2, font=FONT_LABEL)
        self.lbl_status.pack(side="left", padx=12)

        row2 = tk.Frame(self, bg=C_BG)
        row2.pack(fill="x", padx=24, pady=4)
        for i in range(3): row2.columnconfigure(i, weight=1)

        specs = [("criptografado (hex)", "f_cripto", C_TEXT2), ("binário", "f_binario", C_TEXT2), ("níveis b8zs", "f_b8zs", C_ACCENT)]
        for col, (titulo, attr, cor) in enumerate(specs):
            c, f = make_card(row2, titulo)
            c.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0))
            ro = make_readonly(f, height=3, color=cor)
            ro.pack(fill="x")
            setattr(self, attr, ro)

        c_wave, f_wave = make_card(self, "forma de onda b8zs — host a")
        c_wave.pack(fill="x", padx=24, pady=(4, 20))
        self.wave = WaveCanvas(f_wave, height=90)
        self.wave.pack(fill="x")

    def _processar(self):
        msg = self.txt_msg.get("1.0", "end").strip()
        if not msg:
            messagebox.showwarning("Atenção", "Digite uma mensagem."); return
        try:
            enc = criptografar(msg)
            bin_ = bytes_para_binario(enc)
            nivs = codificar(bin_)
            self._niveis = nivs
            set_ro(self.f_cripto, enc.hex())
            set_ro(self.f_binario, bin_)
            set_ro(self.f_b8zs, " ".join(str(n) for n in nivs), color=C_ACCENT)
            self.after(80, lambda: self.wave.set(nivs))
            self.lbl_status.config(text="✓ processado", fg=C_ACCENT2)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _enviar_rede(self):
        if not self._niveis:
            messagebox.showwarning("Atenção", "Processe uma mensagem antes de enviar."); return
        
        porta_com = self.e_porta.get().strip()
        id_dest = self.combo_dest.current() # 0, 1, ou 2

        self.lbl_status.config(text="⏳ enviando...", fg=C_TEXT2)
        self.update_idletasks()

        def _t():
            try:
                enviar_niveis(porta_com, id_dest, self._niveis)
                self.after(0, lambda: self.lbl_status.config(text=f"✓ enviado → {self.combo_dest.get()}", fg=C_ACCENT2))
            except Exception as e:
                self.after(0, lambda: (self.lbl_status.config(text=f"✗ falha", fg=C_WARN), messagebox.showerror("Erro na Serial", str(e))))
        threading.Thread(target=_t, daemon=True).start()

# ─── Painel Host B (Recepção) ─────────────────────────────────────────────────
class PainelRecepcao(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C_BG)
        self._servidor = None
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C_BG)
        hdr.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(hdr, text="Host B", bg=C_BG, fg=C_ACCENT2, font=FONT_TITLE).pack(side="left")
        tk.Label(hdr, text="  recepção e decodificação B8ZS", bg=C_BG, fg=C_TEXT2, font=("Segoe UI", 11)).pack(side="left", anchor="s", pady=(0, 3))

        row1 = tk.Frame(self, bg=C_BG)
        row1.pack(fill="x", padx=24, pady=4)
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(1, weight=3)

        c_srv, f_srv = make_card(row1, "Conexão Serial")
        c_srv.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(f_srv, text="Porta COM Local", bg=C_CARD, fg=C_TEXT2, font=FONT_LABEL, anchor="w").pack(fill="x")
        self.e_porta_srv = make_entry(f_srv, "COM4", width=10)
        self.e_porta_srv.pack(fill="x", pady=(2, 10))

        self.btn_srv = btn(f_srv, "▶  Iniciar", color=C_ACCENT2, cmd=self._toggle)
        self.btn_srv.pack(fill="x")

        self.lbl_srv = tk.Label(f_srv, text="● parado", bg=C_CARD, fg=C_WARN, font=("Segoe UI", 8))
        self.lbl_srv.pack(anchor="w", pady=(6, 0))

        c_in, f_in = make_card(row1, "níveis b8zs recebidos")
        c_in.grid(row=0, column=1, sticky="nsew")
        
        self.lbl_origem = tk.Label(f_in, text="Origem: Nenhuma", bg=C_CARD, fg=C_TEXT2, font=FONT_BADGE)
        self.lbl_origem.pack(anchor="ne", pady=(0, 4))
        
        self.txt_nivs = make_text(f_in, height=4, color=C_ACCENT2)
        self.txt_nivs.pack(fill="x")

        f_btns = tk.Frame(self, bg=C_BG)
        f_btns.pack(fill="x", padx=24, pady=8)
        btn(f_btns, "▶  Decodificar", color=C_ACCENT2, cmd=self._processar).pack(side="left")

        c_wave, f_wave = make_card(self, "forma de onda recebida — host b")
        c_wave.pack(fill="x", padx=24, pady=(4, 8))
        self.wave = WaveCanvas(f_wave, height=90)
        self.wave.pack(fill="x")

        row2 = tk.Frame(self, bg=C_BG)
        row2.pack(fill="x", padx=24, pady=(4, 20))
        for i in range(3): row2.columnconfigure(i, weight=1)

        specs = [("binário decodificado", "f_binario", C_TEXT2), ("bytes (hex)", "f_hex", C_TEXT2), ("mensagem original", "f_msg", C_ACCENT2)]
        for col, (titulo, attr, cor) in enumerate(specs):
            c, f = make_card(row2, titulo)
            c.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0))
            ro = make_readonly(f, height=3, color=cor)
            ro.pack(fill="x")
            setattr(self, attr, ro)

    def _toggle(self):
        if self._servidor is None:
            porta_com = self.e_porta_srv.get().strip()
            if not porta_com: messagebox.showerror("Erro", "Digite a porta COM"); return
            self._servidor = Servidor(porta_com=porta_com, callback=self._ao_receber)
            self._servidor.iniciar()
            self.lbl_srv.config(text=f"● ouvindo {porta_com}", fg=C_ACCENT2)
            self.btn_srv.config(text="■  Parar", bg=C_WARN)
        else:
            self._servidor.parar()
            self._servidor = None
            self.lbl_srv.config(text="● parado", fg=C_WARN)
            self.btn_srv.config(text="▶  Iniciar", bg=C_ACCENT2)

    def _ao_receber(self, id_origem, niveis, addr, erro=None):
        if erro:
            self.after(0, lambda: messagebox.showerror("Erro na recepção", f"De {addr}: {erro}")); return
        
        nomes = {0: "Master", 1: "Slave 1", 2: "Slave 2"}
        nome_origem = nomes.get(id_origem, "Desconhecido")
        
        s = " ".join(str(n) for n in niveis)
        self.after(0, lambda: (self._injetar(s), self.lbl_origem.config(text=f"Origem: {nome_origem}")))

    def _injetar(self, s):
        self.txt_nivs.delete("1.0", "end")
        self.txt_nivs.insert("1.0", s)
        self._processar()

    def _processar(self):
        raw = self.txt_nivs.get("1.0", "end").strip()
        if not raw: return
        try:
            niveis = [int(x) for x in raw.split()]
            self.after(80, lambda: self.wave.set(niveis))
            bin_ = decodificar(niveis)
            enc = binario_para_bytes(bin_)
            msg = descriptografar(enc)
            set_ro(self.f_binario, bin_)
            set_ro(self.f_hex, enc.hex())
            set_ro(self.f_msg, msg, color=C_ACCENT2)
        except Exception as e:
            messagebox.showerror("Erro na decodificação", str(e))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("B8ZS — Codificação de Linha · UTFPR")
        self.geometry("960x640")
        self.minsize(860, 580)
        self.configure(bg=C_BG)
        self._paineis, self._ativo = {}, None
        self._build()
        self._nav("envio")

    def _build(self):
        sb = tk.Frame(self, bg=C_SIDEBAR, width=180)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        tk.Label(sb, text="B8ZS", bg=C_SIDEBAR, fg="#FFFFFF", font=("Segoe UI", 22, "bold")).pack(pady=(28, 0))
        tk.Label(sb, text="Line Coding", bg=C_SIDEBAR, fg=C_SIDEBAR_T, font=("Segoe UI", 8)).pack()
        tk.Label(sb, text="UTFPR", bg=C_SIDEBAR, fg=C_SIDEBAR_T, font=("Segoe UI", 8)).pack(pady=(0, 24))
        tk.Frame(sb, bg="#2E3E52", height=1).pack(fill="x", padx=16, pady=8)

        self._nav_btns = {}
        nav_items = [("envio", "📤  Host A — Envio", PainelEnvio), ("recepcao", "📥  Host B — Recepção", PainelRecepcao)]
        for key, label, cls in nav_items:
            b = tk.Button(sb, text=label, bg=C_SIDEBAR, fg=C_SIDEBAR_T, font=("Segoe UI", 10), relief="flat", bd=0, cursor="hand2", anchor="w", padx=20, pady=10, activebackground="#2E3E52", activeforeground=C_SIDEBAR_A, command=lambda k=key: self._nav(k))
            b.pack(fill="x")
            self._nav_btns[key] = b

        tk.Frame(sb, bg="#2E3E52", height=1).pack(fill="x", padx=16, pady=8, side="bottom")
        tk.Label(sb, text="AES-128 · ESP-NOW · B8ZS", bg=C_SIDEBAR, fg="#3D5166", font=("Segoe UI", 7)).pack(side="bottom", pady=8)

        self._content = tk.Frame(self, bg=C_BG)
        self._content.pack(side="left", fill="both", expand=True)
        for key, _, cls in nav_items:
            self._paineis[key] = cls(self._content)

    def _nav(self, key):
        if self._ativo:
            self._paineis[self._ativo].pack_forget()
            self._nav_btns[self._ativo].config(bg=C_SIDEBAR, fg=C_SIDEBAR_T, font=("Segoe UI", 10))
        self._ativo = key
        self._paineis[key].pack(fill="both", expand=True)
        self._nav_btns[key].config(bg="#2E3E52", fg=C_SIDEBAR_A, font=("Segoe UI", 10, "bold"))

if __name__ == "__main__":
    App().mainloop()