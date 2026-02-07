"""
PROJEKT ZALICZENIOWY: FIZYKA OGÓLNA
TEMAT: Simulated Annealing - interpetacja Pythonowa

AUTORZY:
1. Bartosz Wojtaś
2. Norbert Gościcki

OPIS FIZYCZNY:
Program symuluje proces stygnięcia ciała (układu punktów), dążącego do stanu
o najniższej energii (najkrótsza trasa). Wykorzystuje statystykę Boltzmanna
do ucieczki z minimów lokalnych poprzez fluktuacje termiczne.
"""

import math
import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button

# --- KONFIGURACJA SYMULACJI (PARAMETRY TERMODYNAMICZNE) ---
LICZBA_MIAST = 60  # Liczba stopni swobody układu
TEMP_POCZATKOWA = 2500.0  # T_0: Wysoka temperatura = duża entropia (faza "ciecz")
TEMP_KONCOWA = 0.01  # T_k: Niska temperatura = zamrożenie (faza "kryształ")
WSPOLCZYNNIK_CHLODZENIA = 0.9993  # Parametr alfa: określa szybkość dyssypacji ciepła (im bliżej 1, tym wolniejsze chłodzenie)
KROKI_NA_KLATKE = 15  # Liczba iteracji Monte Carlo na jedną klatkę animacji


class SymulowaneWyzarzanieTSP:
    """
    Silnik fizyczny symulacji. Odpowiada za ewolucję układu zgodnie z zasadami termodynamiki.
    """

    def __init__(self, miasta):
        self.miasta = miasta
        self.liczba_miast = len(miasta)

        # Inicjalizacja stanu początkowego (stan o wysokiej energii/entropii)
        self.obecna_trasa = list(range(self.liczba_miast))
        random.shuffle(self.obecna_trasa)

        # Obliczenie energii początkowej (Hamiltonianu)
        self.obecna_energia = self.oblicz_energie(self.obecna_trasa)

        # Zmienne do śledzenia stanu podstawowego (najlepszego znalezionego)
        self.najlepsza_trasa = self.obecna_trasa[:]
        self.najlepsza_energia = self.obecna_energia

        self.temperatura = TEMP_POCZATKOWA
        self.aktywne_miasta = []

    def dystans(self, miasto_a, miasto_b):
        """Metryka euklidesowa przestrzeni."""
        return math.hypot(miasto_a[0] - miasto_b[0], miasto_a[1] - miasto_b[1])

    def oblicz_energie(self, trasa):
        """
        HAMILTONIAN UKŁADU (Funkcja Celu).
        W tym modelu energią całkowitą jest suma długości połączeń między miastami.
        Układ dąży do minimalizacji tej wartości.
        """
        suma = 0
        for i in range(self.liczba_miast):
            poczatek = self.miasta[trasa[i]]
            koniec = self.miasta[trasa[(i + 1) % self.liczba_miast]]  # Zamknięcie pętli (warunki brzegowe)
            suma += self.dystans(poczatek, koniec)
        return suma

    def krok_symulacji(self):
        """
        Pojedynczy krok algorytmu Metropolisa-Hastingsa.
        Implementuje fluktuacje termiczne pozwalające na wyjście z minimów lokalnych.
        """
        if self.temperatura <= TEMP_KONCOWA:
            return

        # 1. Propozycja zmiany stanu (mutacja topologiczna typu 2-opt)
        # Odpowiada to lokalnej zmianie konfiguracji sieci krystalicznej
        nowa_trasa = self.obecna_trasa[:]
        i, j = random.sample(range(self.liczba_miast), 2)
        if i > j: i, j = j, i

        self.aktywne_miasta = [self.obecna_trasa[i], self.obecna_trasa[j]]
        # Odwrócenie fragmentu trasy (kluczowe dla usuwania przecięć)
        nowa_trasa[i:j + 1] = reversed(nowa_trasa[i:j + 1])

        # 2. Obliczenie zmiany energii (Delta E)
        nowa_energia = self.oblicz_energie(nowa_trasa)
        delta_e = nowa_energia - self.obecna_energia

        # 3. KRYTERIUM METROPOLISA (Fizyka Statystyczna)
        # Jeśli energia spada (delta_e < 0) -> Zawsze akceptujemy zmianę (układ dąży do minimum).
        # Jeśli energia rośnie (delta_e > 0) -> Akceptujemy z p-stwem Boltzmanna: P = exp(-dE / T).
        if delta_e < 0 or (self.temperatura > 0 and random.random() < math.exp(-delta_e / self.temperatura)):
            self.obecna_trasa = nowa_trasa
            self.obecna_energia = nowa_energia

            # Aktualizacja stanu podstawowego (Global Minimum Tracker)
            if self.obecna_energia < self.najlepsza_energia:
                self.najlepsza_energia = self.obecna_energia
                self.najlepsza_trasa = self.obecna_trasa[:]

        # 4. Chłodzenie układu (Schemat geometryczny)
        self.temperatura *= WSPOLCZYNNIK_CHLODZENIA


class SymulacjaApp:
    """
    Klasa odpowiedzialna za wizualizację procesu i GUI.
    """

    def __init__(self):
        # Stylizacja wykresu na "Dark Mode" dla lepszego kontrastu
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(11, 8))
        self.fig.patch.set_facecolor('#0b0e14')
        self.ax.set_facecolor('#0b0e14')

        self.show_legend = True
        self.init_data()

        # Konfiguracja interfejsu (Przycisk Reset)
        self.ax_button = plt.axes([0.76, 0.03, 0.18, 0.05])
        self.btn = Button(self.ax_button, 'RESETUJ PUNKTY', color='#1a1c23', hovercolor='#238636')
        self.btn.label.set_color('#00f2ff')
        self.btn.label.set_fontweight('bold')
        self.btn.on_clicked(self.reset_callback)

        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.ani = FuncAnimation(self.fig, self.update, interval=30, cache_frame_data=False)

    def init_data(self):
        # Generowanie losowych położeń miast (Stan nieuporządkowany)
        miasta = [(random.uniform(5, 95), random.uniform(5, 95)) for _ in range(LICZBA_MIAST)]
        self.sa = SymulowaneWyzarzanieTSP(miasta)

    def reset_callback(self, event):
        self.init_data()

    def on_key(self, event):
        if event.key and event.key.lower() == 'h':
            self.show_legend = not self.show_legend

    def update(self, frame):
        # Wykonanie serii kroków symulacji przed odświeżeniem klatki
        for _ in range(KROKI_NA_KLATKE):
            self.sa.krok_symulacji()

        self.ax.clear()
        self.ax.axis('off')

        miasta = self.sa.miasta
        trasa = self.sa.obecna_trasa

        # Rysowanie krawędzi (wiązań między atomami/miastami)
        trasa_x = [miasta[i][0] for i in trasa] + [miasta[trasa[0]][0]]
        trasa_y = [miasta[i][1] for i in trasa] + [miasta[trasa[0]][1]]

        self.ax.plot(trasa_x, trasa_y, c='#00f2ff', lw=1.2, zorder=1, alpha=0.7)
        self.ax.scatter([m[0] for m in miasta], [m[1] for m in miasta],
                        c='#ff006e', s=40, zorder=2, edgecolors='white', lw=0.5)

        # Wyświetlanie parametrów makroskopowych układu (HUD)
        if self.show_legend:
            status = "ANALIZA W TOKU" if self.sa.temperatura > TEMP_KONCOWA else "STAN ZAMROŻONY"
            info = (
                f" STATUS: {status}\n"
                f" ───────────────────────────\n"
                f" TEMPERATURA (T): {self.sa.temperatura:8.2f} K\n"
                f" ENERGIA (E):     {self.sa.obecna_energia:8.2f}\n"
                f" MINIMUM (E_min): {self.sa.najlepsza_energia:8.2f}\n"
                f" ───────────────────────────\n"
                f" [H] - Ukryj HUD"
            )
            self.ax.text(0.02, 0.98, info, transform=self.ax.transAxes, verticalalignment='top',
                         fontsize=10, family='monospace', color='white',
                         bbox=dict(boxstyle='round,pad=0.5', facecolor='#161b22', alpha=0.9, edgecolor='#3a3f4b'))

        self.ax.set_title("OPTYMALIZACJA TRASY (SIMULATED ANNEALING)", color='white', fontsize=14, fontweight='bold')


if __name__ == "__main__":
    app = SymulacjaApp()
    plt.show()