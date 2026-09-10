# -*- coding: utf-8 -*-
import time
import threading
import json
import os
import requests

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

CONFIG_FILE = "beast_trader_config.json"

class BeastAITraderApp(App):
    def build(self):
        self.title = "BEAST AI TRADER"
        self.bot_running = False
        self.symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "AVAXUSDT"]
        self.logs_list = []
        
        self.load_settings()
        
        root = BoxLayout(orientation='vertical', padding=12, spacing=8)
        
        with root.canvas.before:
            Color(0.03, 0.05, 0.1, 1)
            self.rect = Rectangle(size=(2000, 3000), pos=root.pos)
            
        header = BoxLayout(size_hint_y=0.08, spacing=10)
        header_title = Label(text="🐅 BEAST AI ULTRA v4.0", font_size='16sp', bold=True, color=(0.93, 0.28, 0.6, 1))
        self.status_badge = Label(text="ДЕМО СЧЕТ", size_hint_x=0.35, bold=True, color=(0, 1, 0.8, 1))
        header.add_widget(header_title)
        header.add_widget(self.status_badge)
        root.add_widget(header)
        
        balance_card = BoxLayout(orientation='vertical', size_hint_y=0.14, padding=8, spacing=3)
        with balance_card.canvas.before:
            Color(0.07, 0.1, 0.18, 1)
            self.bc_rect = Rectangle(size=(2000, 2000), pos=balance_card.pos)
            
        balance_title = Label(text="КАПИТАЛ НА СЧЕТЕ", font_size='10sp', color=(0.6, 0.6, 0.6, 1))
        self.balance_val = Label(text="10000.00 USDT", font_size='22sp', bold=True, color=(1, 1, 1, 1))
        balance_card.add_widget(balance_title)
        balance_card.add_widget(self.balance_val)
        root.add_widget(balance_card)
        
        settings_grid = GridLayout(cols=2, size_hint_y=0.28, spacing=6)
        settings_grid.add_widget(Label(text="API Key:", size_hint_x=0.35, font_size='11sp', color=(0.8, 0.8, 0.8, 1)))
        self.api_key_input = TextInput(text=self.config.get("api_key", ""), password=True, multiline=False, background_color=(0.1, 0.12, 0.2, 1), foreground_color=(1,1,1,1))
        settings_grid.add_widget(self.api_key_input)
        
        settings_grid.add_widget(Label(text="API Secret:", size_hint_x=0.35, font_size='11sp', color=(0.8, 0.8, 0.8, 1)))
        self.api_secret_input = TextInput(text=self.config.get("api_secret", ""), password=True, multiline=False, background_color=(0.1, 0.12, 0.2, 1), foreground_color=(1,1,1,1))
        settings_grid.add_widget(self.api_secret_input)
        
        settings_grid.add_widget(Label(text="Сделка ($):", size_hint_x=0.35, font_size='11sp', color=(0.8, 0.8, 0.8, 1)))
        self.trade_amount_input = TextInput(text=str(self.config.get("trade_amount", 10.0)), multiline=False, background_color=(0.1, 0.12, 0.2, 1), foreground_color=(1,1,1,1))
        settings_grid.add_widget(self.trade_amount_input)
        
        settings_grid.add_widget(Label(text="РЕАЛ Режим:", size_hint_x=0.35, font_size='11sp', color=(0.8, 0.8, 0.8, 1)))
        self.real_mode_switch = Switch(active=(self.config.get("mode") == "real"))
        self.real_mode_switch.bind(active=self.on_switch_change)
        settings_grid.add_widget(self.real_mode_switch)
        root.add_widget(settings_grid)
        
        btn_layout = BoxLayout(size_hint_y=0.1, spacing=8)
        self.save_btn = Button(text="СОХРАНИТЬ", font_size='11sp', bold=True, background_color=(0.3, 0.1, 0.5, 1))
        self.save_btn.bind(on_press=self.save_settings)
        self.start_btn = Button(text="СТАРТ ИИ", font_size='12sp', bold=True, background_color=(0.1, 0.6, 0.3, 1))
        self.start_btn.bind(on_press=self.toggle_bot)
        btn_layout.add_widget(self.save_btn)
        btn_layout.add_widget(self.start_btn)
        root.add_widget(btn_layout)
        
        terminal_box = BoxLayout(orientation='vertical', size_hint_y=0.4, padding=4)
        with terminal_box.canvas.before:
            Color(0.02, 0.02, 0.04, 1)
            self.term_rect = Rectangle(size=(2000, 2000), pos=terminal_box.pos)
            
        term_label = Label(text="🧠 ЛОГ СКАНЕРА ИИ", font_size='10sp', bold=True, color=(0.93, 0.28, 0.6, 1), size_hint_y=0.12)
        terminal_box.add_widget(term_label)
        
        self.scroll = ScrollView(size_hint=(1, 0.88))
        self.log_text = Label(text="[Система] Готов к запуску...\n", font_size='10sp', color=(0.8, 0.8, 0.8, 1), size_hint_y=None, halign='left', valign='top')
        self.log_text.bind(texture_size=self.log_text.setter('size'))
        self.scroll.add_widget(self.log_text)
        terminal_box.add_widget(self.scroll)
        root.add_widget(terminal_box)
        
        root.bind(size=self._update_rects)
        Clock.schedule_interval(self.update_ui_tick, 1.0)
        return root

    def _update_rects(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception:
                self.set_default_config()
        else:
            self.set_default_config()

    def set_default_config(self):
        self.config = {"api_key": "", "api_secret": "", "trade_amount": 10.0, "mode": "demo", "demo_bal": 10000.0}

    def save_settings(self, instance=None):
        self.config["api_key"] = self.api_key_input.text.strip()
        self.config["api_secret"] = self.api_secret_input.text.strip()
        try:
            self.config["trade_amount"] = float(self.trade_amount_input.text)
        except ValueError:
            self.config["trade_amount"] = 10.0
        self.config["mode"] = "real" if self.real_mode_switch.active else "demo"
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False)
        self.add_log("⚙️ Настройки сохранены!")

    def on_switch_change(self, switch_instance, value):
        if value:
            self.status_badge.text = "РЕАЛЬНЫЙ"
            self.status_badge.color = (1, 0.2, 0.2, 1)
        else:
            self.status_badge.text = "ДЕМО СЧЕТ"
            self.status_badge.color = (0, 1, 0.8, 1)

    def add_log(self, text):
        t = time.strftime('%H:%M:%S')
        self.logs_list.append(f"[{t}] {text}")
        if len(self.logs_list) > 50:
            self.logs_list.pop(0)
        self.log_text.text = "\n".join(self.logs_list)

    def toggle_bot(self, instance):
        if not self.bot_running:
            if self.real_mode_switch.active and (not self.api_key_input.text or not self.api_secret_input.text):
                self.add_log("❌ ОШИБКА: Заполните API ключи!")
                return
            self.bot_running = True
            self.start_btn.text = "СТОП ЗВЕРЯ"
            self.start_btn.background_color = (0.8, 0.1, 0.2, 1)
            self.add_log("🐅 МУЛЬТИ-ИИ ЗВЕРЬ ЗАПУЩЕН!")
            threading.Thread(target=self.trading_thread, daemon=True).start()
        else:
            self.bot_running = False
            self.start_btn.text = "СТАРТ ИИ"
            self.start_btn.background_color = (0.1, 0.6, 0.3, 1)
            self.add_log("🛑 Зверь остановлен.")

    def update_ui_tick(self, dt):
        if self.real_mode_switch.active:
            self.status_badge.text = "РЕАЛЬНЫЙ"
            self.status_badge.color = (1, 0.2, 0.2, 1)
            self.balance_val.text = "РЕАЛ BYBIT"
        else:
            self.status_badge.text = "ДЕМО СЧЕТ"
            self.status_badge.color = (0, 1, 0.8, 1)
            self.balance_val.text = f"{self.config.get('demo_bal', 10000.0):.2f} USDT"

    def trading_thread(self):
        price_history = {s: [] for s in self.symbols}
        while self.bot_running:
            try:
                for symbol in self.symbols:
                    if not self.bot_running:
                        break
                    try:
                        url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
                        res = requests.get(url, timeout=4).json()
                        if res.get("retCode") == 0:
                            price = float(res["result"]["list"][0]["lastPrice"])
                            price_history[symbol].append(price)
                            if len(price_history[symbol]) > 6:
                                price_history[symbol].pop(0)
                            avg = sum(price_history[symbol]) / len(price_history[symbol])
                            change = ((price - avg) / avg) * 100
                            if change > 0.25:
                                self.add_log(f"🔥 [{symbol}] Импульс РОСТА! ({change:+.2f}%)")
                            elif change < -0.25:
                                self.add_log(f"⚡ [{symbol}] Импульс ПАДЕНИЯ! ({change:+.2f}%)")
                            else:
                                self.add_log(f"🔍 [{symbol}] {price}$ | Сканирование...")
                    except Exception:
                        pass
                    time.sleep(1.5)
                time.sleep(3)
            except Exception as e:
                self.add_log(f"⚠️ Ошибка сети: {e}")
                time.sleep(5)

if __name__ == '__main__':
    BeastAITraderApp().run()
