from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from datetime import datetime
import csv
import os

Window.clearcolor = get_color_from_hex("#1a1a1a")
GOLD = get_color_from_hex("#d4a017")
DARK_GRAY = get_color_from_hex("#2b2b2b")
WHITE = get_color_from_hex("#f5f5f5")

FILENAME = "trades.csv"
FIELDS = ["date", "time", "pair", "direction", "emotion", "outcome", "followed_plan"]

def save_trade(pair, direction, emotion, outcome, followed_plan):
    file_exists = os.path.exists(FILENAME)
    now = datetime.now()
    with open(FILENAME, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "pair": pair,
            "direction": direction,
            "emotion": emotion,
            "outcome": outcome,
            "followed_plan": followed_plan
        })

def load_trades():
    if not os.path.exists(FILENAME):
        return []
    with open(FILENAME, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)

def rewrite_trades(trades):
    with open(FILENAME, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for t in trades:
            writer.writerow(t)

def trades_today():
    today = datetime.now().strftime("%Y-%m-%d")
    return [t for t in load_trades() if t["date"] == today]

def win_rate_today():
    t = trades_today()
    if len(t) == 0:
        return 0
    wins = [x for x in t if x["outcome"] == "win"]
    return round(len(wins) / len(t) * 100, 1)

def discipline_score_today():
    t = trades_today()
    if len(t) == 0:
        return 0
    disciplined = [x for x in t if x["followed_plan"] == "yes"]
    return round(len(disciplined) / len(t) * 100, 1)

def within_trading_hours():
    now = datetime.now()
    return 12 <= now.hour < 17

def styled_button(text, **kwargs):
    return Button(text=text, background_color=GOLD, background_normal="", color=(0.1, 0.1, 0.1, 1), **kwargs)

def styled_label(text="", **kwargs):
    return Label(text=text, color=WHITE, **kwargs)

def styled_input(**kwargs):
    return TextInput(background_color=DARK_GRAY, foreground_color=WHITE, cursor_color=GOLD, **kwargs)

def styled_toggle(text, **kwargs):
    return ToggleButton(text=text, background_color=GOLD, background_normal="", color=(0.1, 0.1, 0.1, 1), **kwargs)


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        title = styled_label(text="=== Vin Trades ===", font_size=26, bold=True, size_hint=(1, 0.2))
        layout.add_widget(title)

        btn_new_trade = styled_button("New Trade Plan")
        btn_new_trade.bind(on_press=self.go_to_new_trade)
        layout.add_widget(btn_new_trade)

        btn_stats = styled_button("View Today's Stats")
        btn_stats.bind(on_press=self.go_to_stats)
        layout.add_widget(btn_stats)

        btn_update = styled_button("Update Trade Outcome")
        btn_update.bind(on_press=self.go_to_update)
        layout.add_widget(btn_update)

        btn_progress = styled_button("Progress Chart")
        btn_progress.bind(on_press=self.go_to_progress)
        layout.add_widget(btn_progress)

        self.lock_label = styled_label(text="", size_hint=(1, 0.1))
        layout.add_widget(self.lock_label)

        self.add_widget(layout)

    def on_pre_enter(self, *args):
        self.lock_label.text = ""

    def go_to_new_trade(self, instance):
        if len(trades_today()) >= 5:
            self.lock_label.text = "Daily limit reached (5 trades) - locked until tomorrow."
            return

        if not within_trading_hours():
            self.lock_label.text = "Outside trading hours (12:00-17:00) - locked."
            return

        self.lock_label.text = ""
        self.manager.current = "new_trade"

    def go_to_stats(self, instance):
        self.manager.current = "stats"

    def go_to_update(self, instance):
        self.manager.current = "update_outcome"

    def go_to_progress(self, instance):
        self.manager.current = "progress"


class NewTradeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        title = styled_label(text="Pre-Trade Checklist", font_size=22, bold=True, size_hint=(1, 0.1))
        layout.add_widget(title)

        self.zone_btn = styled_toggle("Price in supply/demand zone?")
        layout.add_widget(self.zone_btn)

        self.candle_btn = styled_toggle("Shooting star / hammer candle?")
        layout.add_widget(self.candle_btn)

        self.rejection_btn = styled_toggle("Multi-week rejection confirmed?")
        layout.add_widget(self.rejection_btn)

        ma_label = styled_label(text="How many candles crossed the MA?", size_hint=(1, 0.08))
        layout.add_widget(ma_label)
        self.ma_input = styled_input(text="", multiline=False, input_filter="int", size_hint=(1, 0.1))
        layout.add_widget(self.ma_input)

        check_button = styled_button("Check Criteria")
        check_button.bind(on_press=self.check_criteria)
        layout.add_widget(check_button)

        self.result_label = styled_label(text="", size_hint=(1, 0.1))
        layout.add_widget(self.result_label)

        self.continue_button = styled_button("Continue", disabled=True)
        self.continue_button.bind(on_press=self.go_to_details)
        layout.add_widget(self.continue_button)

        back_button = styled_button("Back to Menu")
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def check_criteria(self, instance):
        in_zone = self.zone_btn.state == "down"
        right_candle = self.candle_btn.state == "down"
        rejection = self.rejection_btn.state == "down"

        if self.ma_input.text == "":
            self.result_label.text = "Enter number of candles."
            self.continue_button.disabled = True
            return

        ma_candles = int(self.ma_input.text)

        if in_zone and right_candle and rejection and ma_candles <= 3:
            self.result_label.text = "Criteria passed!"
            self.continue_button.disabled = False
        else:
            self.result_label.text = "Criteria not met."
            self.continue_button.disabled = True

    def go_to_details(self, instance):
        self.manager.current = "trade_details"

    def go_back(self, instance):
        self.manager.current = "menu"


class TradeDetailsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stop_confirmed = False

        layout = BoxLayout(orientation="vertical", padding=20, spacing=8)

        title = styled_label(text="Trade Details", font_size=22, bold=True, size_hint=(1, 0.08))
        layout.add_widget(title)

        self.pair_input = styled_input(hint_text="Pair (e.g. EURUSD)", multiline=False)
        layout.add_widget(self.pair_input)

        self.direction_btn = styled_toggle("Long / Short (tap to toggle)")
        layout.add_widget(self.direction_btn)

        self.entry_input = styled_input(hint_text="Entry price", multiline=False, input_filter="float")
        layout.add_widget(self.entry_input)

        self.stop_input = styled_input(hint_text="Stop loss", multiline=False, input_filter="float")
        layout.add_widget(self.stop_input)

        self.tp_input = styled_input(hint_text="Take profit", multiline=False, input_filter="float")
        layout.add_widget(self.tp_input)

        self.balance_input = styled_input(hint_text="Account balance", multiline=False, input_filter="float")
        layout.add_widget(self.balance_input)

        self.risk_input = styled_input(hint_text="Risk % (max 10)", multiline=False, input_filter="float")
        layout.add_widget(self.risk_input)

        calc_button = styled_button("Calculate Risk")
        calc_button.bind(on_press=self.calculate)
        layout.add_widget(calc_button)

        self.result_label = styled_label(text="", size_hint=(1, 0.2))
        layout.add_widget(self.result_label)

        self.confirm_stop_button = styled_button("Confirm Stop Loss Anyway", disabled=True, size_hint=(1, 0.08))
        self.confirm_stop_button.bind(on_press=self.confirm_stop_loss)
        layout.add_widget(self.confirm_stop_button)

        self.emotion_input = styled_input(hint_text="How do you feel entering this trade?", multiline=False)
        layout.add_widget(self.emotion_input)

        self.save_button = styled_button("Log This Trade", disabled=True)
        self.save_button.bind(on_press=self.save_this_trade)
        layout.add_widget(self.save_button)

        self.save_status = styled_label(text="", size_hint=(1, 0.1))
        layout.add_widget(self.save_status)

        back_button = styled_button("Back")
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def calculate(self, instance):
        self.save_button.disabled = True
        self.confirm_stop_button.disabled = True

        try:
            entry = float(self.entry_input.text)
            stop_loss = float(self.stop_input.text)
            take_profit = float(self.tp_input.text)
            balance = float(self.balance_input.text)
            risk_percent = float(self.risk_input.text)
            pair = self.pair_input.text
        except ValueError:
            self.result_label.text = "Please fill in all fields with valid numbers."
            return

        if pair == "":
            self.result_label.text = "Please enter a pair."
            return

        stop_distance = abs(entry - stop_loss)

        if stop_distance == 0:
            self.result_label.text = "Stop loss can't equal entry price."
            return

        if stop_distance > entry * 0.05 and not self.stop_confirmed:
            self.result_label.text = (
                "That stop loss is " + str(round(stop_distance, 5)) +
                " away from entry - unusually far.\nTap 'Confirm Stop Loss Anyway' to proceed, " +
                "or fix the stop loss and tap Calculate again."
            )
            self.confirm_stop_button.disabled = False
            return

        risk_amount = balance * (risk_percent / 100)
        reward_distance = abs(take_profit - entry)
        risk_reward = reward_distance / stop_distance

        if "JPY" in pair.upper():
            pips_at_risk = stop_distance * 100
        else:
            pips_at_risk = stop_distance * 10000

        if "XAU" in pair.upper():
            position_size = risk_amount / (stop_distance * 100)
        else:
            pip_value_per_lot = 10
            position_size = risk_amount / (pips_at_risk * pip_value_per_lot)

        self.calculated_pair = pair

        self.result_label.text = (
            "Risk: $" + str(round(risk_amount, 2)) +
            "\nPosition Size: " + str(round(position_size, 2)) + " lots" +
            "\nRatio: 1:" + str(round(risk_reward, 1))
        )

        self.save_button.disabled = False
        self.stop_confirmed = False

    def confirm_stop_loss(self, instance):
        self.stop_confirmed = True
        self.calculate(None)

    def save_this_trade(self, instance):
        if len(trades_today()) >= 5:
            self.save_status.text = "Daily limit reached - trade not saved."
            self.save_button.disabled = True
            return

        direction = "long" if self.direction_btn.state == "down" else "short"
        emotion = self.emotion_input.text
        if emotion == "":
            self.save_status.text = "Please enter how you feel."
            return
        save_trade(self.calculated_pair, direction, emotion, "pending", "yes")
        self.save_status.text = "Trade logged!"

    def go_back(self, instance):
        self.manager.current = "new_trade"


class StatsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        title = styled_label(text="Today's Stats", font_size=24, bold=True, size_hint=(1, 0.15))
        layout.add_widget(title)

        self.stats_label = styled_label(text="", font_size=20, size_hint=(1, 0.6))
        layout.add_widget(self.stats_label)

        refresh_button = styled_button("Refresh")
        refresh_button.bind(on_press=self.refresh_stats)
        layout.add_widget(refresh_button)

        back_button = styled_button("Back to Menu")
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def on_pre_enter(self, *args):
        self.refresh_stats(None)

    def refresh_stats(self, instance):
        trades_count = len(trades_today())
        win_rate = win_rate_today()
        discipline = discipline_score_today()

        self.stats_label.text = (
            "Trades today: " + str(trades_count) + " / 5\n" +
            "Win rate: " + str(win_rate) + "%\n" +
            "Discipline score: " + str(discipline) + "%"
        )

    def go_back(self, instance):
        self.manager.current = "menu"


class UpdateOutcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_trade = None

        self.outer_layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        title = styled_label(text="Update Trade Outcome", font_size=22, bold=True, size_hint=(1, 0.1))
        self.outer_layout.add_widget(title)

        self.trades_list_layout = BoxLayout(orientation="vertical", size_hint=(1, None), spacing=5)
        self.trades_list_layout.bind(minimum_height=self.trades_list_layout.setter("height"))

        scroll = ScrollView(size_hint=(1, 0.5))
        scroll.add_widget(self.trades_list_layout)
        self.outer_layout.add_widget(scroll)

        self.selected_label = styled_label(text="No trade selected", size_hint=(1, 0.1))
        self.outer_layout.add_widget(self.selected_label)

        button_row = BoxLayout(orientation="horizontal", size_hint=(1, 0.1), spacing=10)
        win_button = styled_button("Mark Win")
        win_button.bind(on_press=self.mark_win)
        loss_button = styled_button("Mark Loss")
        loss_button.bind(on_press=self.mark_loss)
        button_row.add_widget(win_button)
        button_row.add_widget(loss_button)
        self.outer_layout.add_widget(button_row)

        self.status_label = styled_label(text="", size_hint=(1, 0.1))
        self.outer_layout.add_widget(self.status_label)

        back_button = styled_button("Back to Menu", size_hint=(1, 0.1))
        back_button.bind(on_press=self.go_back)
        self.outer_layout.add_widget(back_button)

        self.add_widget(self.outer_layout)

    def on_pre_enter(self, *args):
        self.build_trade_list()

    def build_trade_list(self):
        self.trades_list_layout.clear_widgets()
        self.selected_trade = None
        self.selected_label.text = "No trade selected"
        self.status_label.text = ""

        trades = trades_today()
        if len(trades) == 0:
            no_trades_label = styled_label(text="No trades logged today.", size_hint_y=None, height=40)
            self.trades_list_layout.add_widget(no_trades_label)
            return

        for t in trades:
            btn_text = t["pair"] + " " + t["direction"] + " - " + t["outcome"]
            trade_button = styled_button(btn_text, size_hint_y=None, height=50)
            trade_button.trade_data = t
            trade_button.bind(on_press=self.select_trade)
            self.trades_list_layout.add_widget(trade_button)

    def select_trade(self, instance):
        self.selected_trade = instance.trade_data
        self.selected_label.text = "Selected: " + instance.trade_data["pair"] + " " + instance.trade_data["direction"]

    def mark_win(self, instance):
        self.set_outcome("win")

    def mark_loss(self, instance):
        self.set_outcome("loss")

    def set_outcome(self, outcome):
        if self.selected_trade is None:
            self.status_label.text = "Please select a trade first."
            return

        all_trades = load_trades()
        for t in all_trades:
            if (t["date"] == self.selected_trade["date"] and
                    t["time"] == self.selected_trade["time"] and
                    t["pair"] == self.selected_trade["pair"]):
                t["outcome"] = outcome

        rewrite_trades(all_trades)
        self.status_label.text = "Trade updated to " + outcome + "!"
        self.build_trade_list()

    def go_back(self, instance):
        self.manager.current = "menu"


class ProgressScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        title = styled_label(text="Progress Chart", font_size=22, bold=True, size_hint=(1, 0.1))
        layout.add_widget(title)

        self.chart_label = styled_label(text="", size_hint=(1, None), halign="left", valign="top")
        self.chart_label.bind(texture_size=self.chart_label.setter("size"))

        scroll = ScrollView(size_hint=(1, 0.75))
        scroll.add_widget(self.chart_label)
        layout.add_widget(scroll)

        back_button = styled_button("Back to Menu", size_hint=(1, 0.1))
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def on_pre_enter(self, *args):
        self.build_chart()

    def build_chart(self):
        all_trades = load_trades()
        if len(all_trades) == 0:
            self.chart_label.text = "No trades logged yet."
            return

        dates = sorted(set(t["date"] for t in all_trades))
        lines = []

        for d in dates:
            day_trades = [t for t in all_trades if t["date"] == d]
            wins = [t for t in day_trades if t["outcome"] == "win"]
            disciplined = [t for t in day_trades if t["followed_plan"] == "yes"]

            win_rate = round(len(wins) / len(day_trades) * 100, 1)
            discipline = round(len(disciplined) / len(day_trades) * 100, 1)

            win_bar = "#" * int(win_rate / 10) + "-" * (10 - int(win_rate / 10))
            disc_bar = "#" * int(discipline / 10) + "-" * (10 - int(discipline / 10))

            lines.append(d + "  Win:  [" + win_bar + "] " + str(win_rate) + "%")
            lines.append(d + "  Disc: [" + disc_bar + "] " + str(discipline) + "%")
            lines.append("")

        self.chart_label.text = "\n".join(lines)

    def go_back(self, instance):
        self.manager.current = "menu"


class VinTradesApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(NewTradeScreen(name="new_trade"))
        sm.add_widget(TradeDetailsScreen(name="trade_details"))
        sm.add_widget(StatsScreen(name="stats"))
        sm.add_widget(UpdateOutcomeScreen(name="update_outcome"))
        sm.add_widget(ProgressScreen(name="progress"))
        return sm

VinTradesApp().run()
