import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import time
import random
import sys
import requests
import os
import json
import webbrowser
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# Import the SYNC version of Playwright and its error classes
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

# --- Standalone function to load theme before creating the main window ---
def load_theme_from_settings():
    try:
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
                return settings.get("theme", "vapor")
    except (json.JSONDecodeError, FileNotFoundError):
        return "vapor"
    return "vapor"

# --- Anonymous Usage Ping Function (Optional) ---
def send_usage_ping():
    try:
        # NOTE: Replace "https://webhook.site/your-unique-url-goes-here" with your actual webhook URL
        webhook_url = "https://webhook.site/your-unique-url-goes-here"
        # Updated application name and version
        payload = {"event": "ApplicationStarted", "application_name": "InstaAutomate Pro", "version": "1.01"}
        requests.post(webhook_url, json=payload, timeout=5)
    except requests.exceptions.RequestException:
        pass

# --- Helper class to redirect print statements to the GUI ---
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        try:
            self.widget.config(state=tk.NORMAL)
            self.widget.insert(tk.END, text)
            self.widget.see(tk.END)
            self.widget.config(state=tk.DISABLED)
        except tk.TclError:
            pass

    def flush(self):
        pass

# --- Main Application Class ---
class InstagramBotApp:
    def __init__(self, root):
        self.root = root
        # Updated application title
        self.root.title("InstaAutomate Pro (v1.01)")
        self.root.geometry("700x800")

        # Sidebar properties
        self.sidebar_width = 220
        self.sidebar_open = False
        self.animation_speed = 10
        self.animation_steps = 22

        # Core app properties
        self.stop_event = threading.Event()
        self.automation_thread = None
        self.accounts = []
        self.settings_file = "settings.json"
        self.theme_var = tk.StringVar()

        self._create_widgets()
        self._redirect_logging()
        self._load_initial_accounts()
        self._load_settings()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- NEW: Show donation popup on startup ---
        self.root.after(500, self._show_donation_popup)


    def _create_widgets(self):
        # --- LAYOUT STRUCTURE ---
        top_bar = ttk.Frame(self.root)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        self.menu_button = ttk.Button(top_bar, text="☰", command=self.toggle_sidebar, bootstyle=(INFO, OUTLINE))
        self.menu_button.pack(side=tk.LEFT, padx=5, pady=5)

        main_container = ttk.Frame(self.root)
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.main_content_frame = ttk.Frame(main_container)
        self.main_content_frame.place(x=0, y=0, relwidth=1, relheight=1)
        
        self.sidebar_frame = ttk.Frame(main_container, bootstyle=SECONDARY)
        self.sidebar_frame.place(x=-self.sidebar_width, y=0, relheight=1, width=self.sidebar_width)
        
        # --- WIDGETS FOR THE SIDEBAR ---
        sidebar_title = ttk.Label(self.sidebar_frame, text="Settings", font=("Segoe UI", 14, "bold"), bootstyle=(INVERSE, SECONDARY))
        sidebar_title.pack(pady=20, fill=tk.X)
        appearance_frame = ttk.LabelFrame(self.sidebar_frame, text="Appearance", padding="10", bootstyle=INFO)
        appearance_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(appearance_frame, text="Theme:").pack(pady=(0, 5))
        self.theme_combobox = ttk.Combobox(
            appearance_frame, textvariable=self.theme_var, state="readonly",
            values=["cerculean", "cosmo", "cyborg", "darkly", "litera", "lumen", "minty", "pulse", "sandstone", "slate", "solar", "superhero", "vapor", "yeti"]
        )
        self.theme_combobox.pack(fill=tk.X, padx=5)
        self.theme_combobox.bind("<<ComboboxSelected>>", self.apply_theme)
        
        about_frame = ttk.LabelFrame(self.sidebar_frame, text="About & Support", padding="10", bootstyle=INFO)
        about_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=15)
        
        donation_button = ttk.Button(about_frame, text="Buy Me a Coffee ☕", bootstyle=SUCCESS, command=self.open_donation_link)
        donation_button.pack(fill=tk.X, pady=4)

        github_button = ttk.Button(about_frame, text="View on GitHub 💻", bootstyle=PRIMARY, command=self.open_github_link)
        github_button.pack(fill=tk.X, pady=4)

        credit_label = ttk.Label(about_frame, text="Created by: zamakanino", font=("Segoe UI", 8, "italic"))
        credit_label.pack(pady=(8, 0))

        # --- WIDGETS FOR THE MAIN CONTENT AREA ---
        config_frame = ttk.LabelFrame(self.main_content_frame, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5, padx=10)
        config_frame.columnconfigure(1, weight=1)
        
        ttk.Label(config_frame, text="Target Username:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.entry_target = ttk.Entry(config_frame)
        self.entry_target.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(config_frame, text="Instagram Post URL:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.entry_post_url = ttk.Entry(config_frame)
        self.entry_post_url.grid(row=1, column=1, sticky="ew", padx=5)

        actions_frame = ttk.LabelFrame(self.main_content_frame, text="Actions", padding="10")
        actions_frame.pack(fill=tk.X, pady=10, padx=10)
        actions_frame.columnconfigure(1, weight=1)
        actions_frame.columnconfigure(3, weight=1)
        
        self.do_follow_var = tk.BooleanVar(value=True)
        self.do_like_var = tk.BooleanVar(value=True)
        self.do_comment_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(actions_frame, text="Follow", variable=self.do_follow_var, style="primary.TCheckbutton").grid(row=0, column=0, padx=5)
        self.entry_follow = ttk.Entry(actions_frame, width=8)
        self.entry_follow.grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(actions_frame, text="Like", variable=self.do_like_var, style="primary.TCheckbutton").grid(row=0, column=2, padx=(20, 5))
        self.entry_like = ttk.Entry(actions_frame, width=8)
        self.entry_like.grid(row=0, column=3, sticky="w")
        ttk.Checkbutton(actions_frame, text="Comment", variable=self.do_comment_var, style="primary.TCheckbutton").grid(row=0, column=4, padx=(20, 5))
        self.entry_comment = ttk.Entry(actions_frame, width=8)
        self.entry_comment.grid(row=0, column=5, sticky="w")
        self.same_account_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(actions_frame, text="Use one account for all its selected actions", variable=self.same_account_var, style='info.TCheckbutton').grid(row=1, column=0, columnspan=6, sticky="w", pady=(10, 5), padx=5)
        ttk.Label(actions_frame, text="Comment Options (one per line):").grid(row=2, column=0, columnspan=6, sticky="w", pady=(10, 5), padx=5)
        self.text_comments = scrolledtext.ScrolledText(actions_frame, height=5, wrap=tk.WORD, font=("Segoe UI", 9))
        self.text_comments.grid(row=3, column=0, columnspan=6, sticky="ew", pady=4, padx=5)

        advanced_frame = ttk.LabelFrame(self.main_content_frame, text="Advanced Settings", padding="10")
        advanced_frame.pack(fill=tk.X, pady=10, padx=10)
        self.headless_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Run in background (headless)", variable=self.headless_var, style="info.TCheckbutton").pack(side=tk.LEFT, padx=5)
        self.use_proxy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Enable Proxy (from accounts.txt)", variable=self.use_proxy_var, style="info.TCheckbutton").pack(side=tk.LEFT, padx=15)

        delay_frame = ttk.LabelFrame(self.main_content_frame, text="Delay Settings (seconds)", padding="10")
        delay_frame.pack(fill=tk.X, pady=10, padx=10)
        ttk.Label(delay_frame, text="Action Delay:").grid(row=0, column=0, sticky="w", padx=5)
        self.entry_action_delay_min = ttk.Entry(delay_frame, width=5)
        self.entry_action_delay_min.grid(row=0, column=1, padx=5)
        ttk.Label(delay_frame, text="to").grid(row=0, column=2)
        self.entry_action_delay_max = ttk.Entry(delay_frame, width=5)
        self.entry_action_delay_max.grid(row=0, column=3, padx=5)
        ttk.Label(delay_frame, text="Rest Between Accounts:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_rest_delay_min = ttk.Entry(delay_frame, width=5)
        self.entry_rest_delay_min.grid(row=1, column=1, padx=5)
        ttk.Label(delay_frame, text="to").grid(row=1, column=2)
        self.entry_rest_delay_max = ttk.Entry(delay_frame, width=5)
        self.entry_rest_delay_max.grid(row=1, column=3, padx=5)
        
        control_frame = ttk.Frame(self.main_content_frame)
        control_frame.pack(fill=tk.X, pady=10, padx=10)
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        self.btn_run = ttk.Button(control_frame, text="Run Automation", command=self.start_automation, bootstyle=(SUCCESS, OUTLINE))
        self.btn_run.grid(row=0, column=0, sticky="ew", padx=2, ipady=10)
        self.btn_stop = ttk.Button(control_frame, text="Stop", command=self.stop_automation, state=tk.DISABLED, bootstyle=(DANGER, OUTLINE))
        self.btn_stop.grid(row=0, column=1, sticky="ew", padx=2, ipady=10)
        
        self.status_label = ttk.Label(self.main_content_frame, text="Initializing...", font=("Segoe UI", 10, "italic"))
        self.status_label.pack(pady=5, padx=10)
        log_frame = ttk.LabelFrame(self.main_content_frame, text="Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        self.log_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Courier New", 9))
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def _show_donation_popup(self):
        """Shows a popup asking the user to donate."""
        title = "Support the Developer"
        message = "Thank you for using this application!\n\nWould you like to support its development with a small donation?"
        
        if messagebox.askyesno(title, message):
            self.open_donation_link()

    def open_donation_link(self):
        url = "https://ko-fi.com/zamakanino"
        webbrowser.open_new_tab(url)
        print(f"Opening donation page: {url}")

    def open_github_link(self):
        url = "https://github.com/zamakanino"
        webbrowser.open_new_tab(url)
        print(f"Opening GitHub page: {url}")
        
    def toggle_sidebar(self):
        self.menu_button.config(state=tk.DISABLED)
        if self.sidebar_open:
            self.animate_sidebar_close()
        else:
            self.animate_sidebar_open()

    def animate_sidebar_open(self, current_x=None):
        if current_x is None:
            current_x = -self.sidebar_width
        new_x = current_x + self.animation_steps
        if new_x < 0:
            self.sidebar_frame.place(x=new_x, y=0, relheight=1, width=self.sidebar_width)
            self.root.after(self.animation_speed, self.animate_sidebar_open, new_x)
        else:
            self.sidebar_frame.place(x=0, y=0, relheight=1, width=self.sidebar_width)
            self.sidebar_open = True
            self.menu_button.config(state=tk.NORMAL)

    def animate_sidebar_close(self, current_x=None):
        if current_x is None:
            current_x = 0
        new_x = current_x - self.animation_steps
        if new_x > -self.sidebar_width:
            self.sidebar_frame.place(x=new_x, y=0, relheight=1, width=self.sidebar_width)
            self.root.after(self.animation_speed, self.animate_sidebar_close, new_x)
        else:
            self.sidebar_frame.place(x=-self.sidebar_width, y=0, relheight=1, width=self.sidebar_width)
            self.sidebar_open = False
            self.menu_button.config(state=tk.NORMAL)
            
    def apply_theme(self, event=None):
        new_theme = self.theme_var.get()
        self.root.style.theme_use(new_theme)
        print(f"Theme changed to: {new_theme}")

    def _redirect_logging(self):
        sys.stdout = TextRedirector(self.log_widget)
        sys.stderr = TextRedirector(self.log_widget)

    def _save_settings(self):
        settings = {
            "theme": self.theme_var.get(),
            "target_username": self.entry_target.get(), "post_url": self.entry_post_url.get(),
            "headless": self.headless_var.get(), "use_proxy": self.use_proxy_var.get(),
            "action_delay_min": self.entry_action_delay_min.get(), "action_delay_max": self.entry_action_delay_max.get(),
            "rest_delay_min": self.entry_rest_delay_min.get(), "rest_delay_max": self.entry_rest_delay_max.get()
        }
        try:
            with open(self.settings_file, "w") as f: json.dump(settings, f, indent=4)
        except Exception as e: 
            print(f"Error saving settings: {e}")

    def _load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                saved_theme = settings.get("theme", "vapor")
                self.theme_var.set(saved_theme)
                
                self.entry_target.delete(0, tk.END); self.entry_target.insert(0, settings.get("target_username", ""))
                self.entry_post_url.delete(0, tk.END); self.entry_post_url.insert(0, settings.get("post_url", ""))
                self.headless_var.set(settings.get("headless", False))
                self.use_proxy_var.set(settings.get("use_proxy", False))
                self.entry_action_delay_min.delete(0, tk.END); self.entry_action_delay_min.insert(0, settings.get("action_delay_min", "2"))
                self.entry_action_delay_max.delete(0, tk.END); self.entry_action_delay_max.insert(0, settings.get("action_delay_max", "5"))
                self.entry_rest_delay_min.delete(0, tk.END); self.entry_rest_delay_min.insert(0, settings.get("rest_delay_min", "30"))
                self.entry_rest_delay_max.delete(0, tk.END); self.entry_rest_delay_max.insert(0, settings.get("rest_delay_max", "60"))
                print("Saved settings loaded.")
            else:
                self.theme_var.set("vapor")
        except Exception as e: 
            print(f"Error loading settings: {e}")
            self.theme_var.set("vapor")
            
    def on_closing(self):
        self._save_settings()
        self.root.destroy()

    def _load_initial_accounts(self):
        try:
            with open("accounts.txt", "r") as f: self.accounts = [line.strip() for line in f if ":" in line.strip()]
            if not self.accounts: self.status_label.config(text="⚠️ accounts.txt is empty. Please add accounts.")
            else: self.status_label.config(text=f"✅ {len(self.accounts)} accounts loaded successfully.")
        except FileNotFoundError: self.status_label.config(text="❌ accounts.txt not found. Please create it.")
        except Exception as e: self.status_label.config(text=f"❌ Error loading accounts: {e}")
    
    def _update_status_label(self, message):
        self.root.after(0, lambda: self.status_label.config(text=message))

    def start_automation(self):
        if not self.accounts:
            messagebox.showerror("No Accounts", "Cannot start automation because no accounts were loaded.")
            return
        self.stop_event.clear()
        self.btn_run.config(state=tk.DISABLED); self.btn_stop.config(state=tk.NORMAL)
        self.automation_thread = threading.Thread(target=self._run_bot_logic, daemon=True)
        self.automation_thread.start()

    def stop_automation(self):
        if self.automation_thread:
            print("\n--- STOPPING ---\nPlease wait for the current account to finish...")
            self.stop_event.set()
            self.btn_stop.config(state=tk.DISABLED)
    
    def _run_bot_logic(self):
        processed_count, total_to_process = 0, 0
        stats = {"logins": 0, "follows": 0, "likes": 0, "comments": 0, "failures": 0}
        
        try:
            try:
                action_delay = (float(self.entry_action_delay_min.get()), float(self.entry_action_delay_max.get()))
                rest_delay = (float(self.entry_rest_delay_min.get()), float(self.entry_rest_delay_max.get()))
            except ValueError:
                messagebox.showerror("Invalid Delays", "Delay values must be numbers. Using defaults.")
                action_delay, rest_delay = (2.0, 5.0), (30.0, 60.0)

            send_usage_ping()
            target = self.entry_target.get().strip()
            post_url = self.entry_post_url.get().strip()
            num_follow = int(self.entry_follow.get() or 0)
            num_like = int(self.entry_like.get() or 0)
            num_comment = int(self.entry_comment.get() or 0)
            comment_list = [c.strip() for c in self.text_comments.get("1.0", "end").split("\n") if c.strip()]
            if self.do_comment_var.get() and num_comment > 0 and not comment_list: raise ValueError("Comment action selected but no comments provided.")

            all_active_accounts = self._get_account_action_list(self.accounts, num_follow, num_like, num_comment)
            total_to_process = len(all_active_accounts)

            with sync_playwright() as p:
                for idx, acc_details in enumerate(all_active_accounts):
                    processed_count = idx + 1
                    if self.stop_event.is_set():
                        print("\nAutomation stopped by user."); processed_count -= 1; break

                    acc, actions = acc_details
                    parts = acc.split(":")
                    username, password = parts[0], parts[1]
                    proxy_details = {"host": parts[2], "port": parts[3]} if len(parts) == 4 else None
                    
                    self._update_status_label(f"Processing: {processed_count}/{total_to_process} | Current: {username}")
                    print(f"\n▶️ [{processed_count}/{total_to_process}] Processing: {username}")
                    print(f"   Actions: {', '.join(actions.keys())}")

                    launch_options = {"headless": self.headless_var.get()}
                    if self.use_proxy_var.get() and proxy_details:
                        launch_options["proxy"] = {"server": f"http://{proxy_details['host']}:{proxy_details['port']}"}
                        print(f"   - Using Proxy: {proxy_details['host']}:{proxy_details['port']}")
                    
                    browser = p.chromium.launch(**launch_options)
                    cookie_file = f"cookies_{username}.json"
                    
                    try:
                        context = None
                        if os.path.exists(cookie_file):
                            with open(cookie_file, 'r') as f: 
                                storage_state = json.load(f)
                            context = browser.new_context(storage_state=storage_state, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
                        else:
                            context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
                        
                        page = context.new_page()
                        page.goto("https://www.instagram.com/", wait_until="load", timeout=60000)
                        time.sleep(random.uniform(2, 4))
                        
                        login_needed = page.locator('input[name="password"]').is_visible()

                        if login_needed:
                            print(f"   - Login required for {username}.")
                            if not self._login(page, username, password, action_delay):
                                stats["failures"] += 1
                                browser.close()
                                continue
                            with open(cookie_file, 'w') as f: 
                                f.write(json.dumps(context.storage_state()))
                            stats["logins"] += 1
                        else:
                            print(f"   - Already logged in as {username} (using cookies).")

                        if "follow" in actions:
                            if self._perform_follow(page, target, username, action_delay): 
                                stats["follows"] += 1
                        
                        if "like" in actions or "comment" in actions:
                            if not post_url: 
                                print("⚠️ No post URL provided for like/comment.")
                            else:
                                if page.url != post_url:
                                    page.goto(post_url, wait_until="load", timeout=60000)
                                    time.sleep(random.uniform(*action_delay))
                                if "like" in actions:
                                    if self._perform_like(page, username, action_delay): 
                                        stats["likes"] += 1
                                if "comment" in actions:
                                    if self._perform_comment(page, random.choice(comment_list), username, action_delay): 
                                        stats["comments"] += 1
                    except Exception as e:
                        print(f"❌ An error occurred with account {username}: {e}")
                        stats["failures"] += 1
                    finally:
                        browser.close()
                        
                        # --- Updated Copyright Message ---
                        print("\n" + "="*40)
                        print("© 2025 InstaAutomate Pro. All rights reserved.")
                        print("="*40)

                        if idx < total_to_process - 1 and not self.stop_event.is_set():
                            sleep_time = random.uniform(*rest_delay)
                            print(f"\n--- Resting for {sleep_time:.0f} seconds ---")
                            self.stop_event.wait(sleep_time)

        except Exception as e:
            print(f"\n❌ An unexpected critical error occurred: {e}")
            messagebox.showerror("Runtime Error", f"An unexpected error occurred:\n{e}")
            self._update_status_label(f"Error! Processed {processed_count}/{total_to_process} accounts.")
        finally:
            self.btn_run.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            report_string = f"Automation Finished\n\n--- Session Summary ---\n"
            report_string += f"Accounts Processed: {processed_count}/{total_to_process}\n"
            report_string += f"Successful Logins: {stats['logins']}\n"
            report_string += f"Failed Accounts: {stats['failures']}\n\n"
            report_string += f"Follows Performed: {stats['follows']}\n"
            report_string += f"Likes Performed: {stats['likes']}\n"
            report_string += f"Comments Performed: {stats['comments']}\n"
            final_message = f"Finished. Processed {processed_count}/{total_to_process} accounts."
            self._update_status_label(final_message)
            print(f"\n--- {final_message} ---")
            self.root.after(100, lambda: messagebox.showinfo("Run Summary", report_string))

    def _get_account_action_list(self, accounts, num_f, num_l, num_c):
        available_accounts = list(accounts)
        random.shuffle(available_accounts)
        actions_map = {}

        if self.same_account_var.get():
            max_needed = max(num_f, num_l, num_c)
            if max_needed > len(available_accounts): 
                raise ValueError(f"Not enough accounts ({len(available_accounts)}) for the required actions ({max_needed}).")
            
            for i in range(max_needed):
                acc = available_accounts[i]
                actions_map[acc] = {}
                if self.do_follow_var.get() and i < num_f: actions_map[acc]["follow"] = True
                if self.do_like_var.get() and i < num_l: actions_map[acc]["like"] = True
                if self.do_comment_var.get() and i < num_c: actions_map[acc]["comment"] = True
        else:
            total_needed = (num_f if self.do_follow_var.get() else 0) + \
                            (num_l if self.do_like_var.get() else 0) + \
                            (num_c if self.do_comment_var.get() else 0)
            if total_needed > len(available_accounts): 
                raise ValueError(f"Total actions ({total_needed}) exceed available accounts ({len(available_accounts)}).")
            
            if self.do_follow_var.get():
                for _ in range(num_f): actions_map.setdefault(available_accounts.pop(0), {})["follow"] = True
            if self.do_like_var.get():
                for _ in range(num_l): actions_map.setdefault(available_accounts.pop(0), {})["like"] = True
            if self.do_comment_var.get():
                for _ in range(num_c): actions_map.setdefault(available_accounts.pop(0), {})["comment"] = True
        
        return list(actions_map.items())

    def _login(self, page, username, password, delay):
        try:
            print("   - Navigating to explicit login page...")
            page.goto("https://www.instagram.com/accounts/login/", wait_until="load", timeout=60000)
            time.sleep(random.uniform(1, 2))
            print("   - Entering credentials...")
            page.locator('input[name="username"]').fill(username)
            time.sleep(random.uniform(0.5, 1.2))
            page.locator('input[name="password"]').fill(password)
            time.sleep(random.uniform(0.5, 1.2))
            page.get_by_role('button', name='Log in', exact=True).click()
            
            home_icon_locator = page.get_by_label("Home", exact=True)
            home_icon_locator.wait_for(timeout=15000)

            print("   - Checking for pop-ups...")
            time.sleep(random.uniform(2,3))
            if page.get_by_role('button', name='Not Now', exact=True).first.is_visible():
                page.get_by_role('button', name='Not Now', exact=True).first.click(timeout=5000)
                print("   - Handled 'Save Info' popup.")
            
            time.sleep(random.uniform(1,2))
            if page.get_by_role('button', name='Not Now', exact=True).first.is_visible():
                page.get_by_role('button', name='Not Now', exact=True).first.click(timeout=5000)
                print("   - Handled 'Notifications' popup.")

            print("✅ Login successful.")
            return True
        except Exception as e:
            print(f"❌ Login failed for {username}: {e}")
            return False

    def _perform_follow(self, page, target_username, current_user, delay):
        try:
            print(f"   - Navigating to profile: {target_username}")
            page.goto(f"https://www.instagram.com/{target_username}/", wait_until="load", timeout=60000)
            time.sleep(random.uniform(*delay))
            
            follow_button = page.locator('button:has-text("Follow")').first
            following_button = page.locator('button:has-text("Following")').first
            
            if follow_button.is_visible():
                time.sleep(random.uniform(*delay))
                follow_button.click()
                print(f"✅ {current_user} followed {target_username}")
                return True
            elif following_button.is_visible():
                print(f"ℹ️ {current_user} is already following {target_username}.")
                return True
            else:
                print(f"⚠️ Could not determine follow status for {target_username}.")
                return False
        except Exception as e:
            print(f"❌ Failed to perform follow for {current_user}: {e}")
            return False

    def _perform_like(self, page, current_user, delay):
        try:
            like_button_container = page.locator("main section span button").nth(0)
            
            unlike_svg = like_button_container.locator('svg[aria-label="Unlike"]')
            like_svg = like_button_container.locator('svg[aria-label="Like"]')

            if unlike_svg.is_visible(timeout=5000):
                print(f"ℹ️ {current_user} already liked this post.")
                return True 

            if like_svg.is_visible():
                time.sleep(random.uniform(*delay))
                like_button_container.click()
                print(f"   - 'Like' action sent for {current_user}.")
                unlike_svg.wait_for(timeout=7000)
                print(f"❤️ {current_user} liked the post (Confirmed).")
                return True
            else:
                print(f"⚠️ Could not find Like/Unlike button for {current_user}.")
                return False

        except Exception as e:
            print(f"❌ Failed to perform like for {current_user}: {e}")
            return False

    def _perform_comment(self, page, comment_text, current_user, delay):
        try:
            comment_box = page.get_by_aria_label('Add a comment…')
            comment_box.wait_for(timeout=10000)
            time.sleep(random.uniform(*delay))
            comment_box.click()
            time.sleep(random.uniform(1, 2))
            comment_box.fill(comment_text)
            time.sleep(random.uniform(*delay))
            post_button = page.get_by_role('button', name='Post', exact=True)
            post_button.click()
            
            page.wait_for_selector(f'text="{comment_text}"', timeout=10000)
            print(f"💬 {current_user} commented: '{comment_text}'")
            return True
        except Exception as e:
            print(f"❌ Failed to perform comment for {current_user}: {e}")
            if "try again later" in str(e).lower():
                print("   - Probable comment block detected.")
            return False

if __name__ == "__main__":
    saved_theme = load_theme_from_settings()
    root = ttk.Window(themename=saved_theme)
    app = InstagramBotApp(root)
    root.mainloop()
