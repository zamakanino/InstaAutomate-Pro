# InstaAutomate Pro (v1.01)

<p align="center">
  <img src="https://placehold.co/600x300/e0e0e0/333333?text=Application+Screenshot+Goes+Here" alt="Application Screenshot" width="600"/>
</p>

A powerful and user-friendly desktop application built with Python and Playwright for automating Instagram actions like following, liking, and commenting. This tool allows users to manage multiple Instagram accounts and perform actions efficiently, with customizable delays and proxy support.

## ✨ Features

* **Multi-Account Support:** Load multiple Instagram accounts from a simple `accounts.txt` file (username:password:proxy_host:proxy_port).
* **Automated Actions:**
    * **Follow:** Automatically follow a target Instagram user's profile.
    * **Like:** Like posts from a specified Instagram URL.
    * **Comment:** Post comments from a predefined list on a specified Instagram URL.
* **Customizable Action Counts:** Define how many follows, likes, and comments to perform.
* **Flexible Account Usage:** Choose to use one account for all its selected actions, or cycle accounts for each action type.
* **Headless Mode:** Run the automation in the background without a visible browser window.
* **Proxy Support:** Integrate proxies with your accounts for enhanced privacy and avoiding rate limits.
* **Intelligent Login Management:** Utilizes cookies to minimize repeated logins, enhancing efficiency.
* **Randomized Delays:** Mimics human behavior with adjustable random delays between actions and between accounts to reduce detection risk.
* **Real-time Logging:** Comprehensive logging displayed directly within the application's GUI.
* **User-Friendly GUI:** Intuitive interface built with `tkinter` and `ttkbootstrap`.
* **Session Summary:** Provides a detailed report of actions performed after each automation run.

## 🚀 Getting Started

### Installation (for Windows .exe users)

1.  **Download the latest executable:**
    Go to the [Releases](https://github.com/your-username/your-repo-name/releases) section of this repository and download the `InstaAutomate_Pro_v1.01.exe` file.
2.  **Create `accounts.txt`:** In the same directory as the `.exe`, create a file named `accounts.txt`.
    * Each line should contain an Instagram account's credentials.
    * Format for accounts without proxy: `username:password`
    * Format for accounts with proxy: `username:password:proxy_host:proxy_port`
    * Example `accounts.txt`:
        ```
        myinstaaccount1:password123
        myinstaaccount2:passwordabc:192.168.1.1:8888
        myinstaaccount3:anotherpass:proxy.example.com:8080
        ```
3.  **Prepare `comments.txt` (Optional):** If you plan to use the commenting feature, create a file named `comments.txt` in the same directory.
    * Each line should contain a single comment you want to use.
    * The bot will randomly select comments from this list.
    * Example `comments.txt`:
        ```
        Great post!
        Awesome content, keep it up!
        Love this!
        ```
4.  **Run the application:** Double-click `InstaAutomate_Pro_v1.01.exe` to launch the GUI.

### Usage

1.  **Fill in Configuration:**
    * **Target Username:** The Instagram username you want to follow (e.g., `instagram`).
    * **Instagram Post URL:** The URL of the post you want to like or comment on (e.g., `https://www.instagram.com/p/abcdefg123/`).
2.  **Select Actions:** Check the boxes for "Follow", "Like", and "Comment" as desired.
3.  **Set Action Counts:** Enter the number of times you want each selected action to be performed.
4.  **Comment Options:** If commenting, enter your desired comments (one per line) in the "Comment Options" text area.
5.  **Advanced Settings:**
    * **Run in background (headless):** Check this to hide the browser window during automation.
    * **Enable Proxy:** Check this if you are using proxies in your `accounts.txt`.
6.  **Delay Settings:** Adjust the minimum and maximum delays for actions and rests between accounts to fine-tune bot behavior.
7.  **Run/Stop:** Click "Run Automation" to start and "Stop" to halt the process.
8.  **Logs:** Monitor the automation progress and any errors in the "Logs" section.

### Building from Source (for Developers)

If you wish to run the script directly or modify it:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    playwright install
    ```
    (You'll need to create a `requirements.txt` file containing `tkinter`, `ttkbootstrap`, `requests`, `playwright`).
3.  **Run the script:**
    ```bash
    python instagram_bot.py
    ```
    (Assuming your main script is named `instagram_bot.py`)

### Compiling to .exe (using PyInstaller)

To create an executable like the one provided in releases:

1.  **Ensure PyInstaller is installed:**
    ```bash
    pip install pyinstaller
    ```
2.  **Navigate to your project directory** in the terminal where your `instagram_bot.py` (or whatever you named your main script) is located.
3.  **Run PyInstaller:**
    ```bash
    pyinstaller --noconsole --onefile --add-data "accounts.txt;." --add-data "settings.json;." --add-data "comments.txt;." instagram_bot.py --name "InstaAutomate_Pro_v1.01"
    ```
    * `--noconsole`: Prevents the console window from appearing when the GUI starts.
    * `--onefile`: Creates a single executable file.
    * `--add-data "source;destination"`: Crucial for including `accounts.txt`, `settings.json`, and `comments.txt` within the executable's data.
    * `--name "InstaAutomate_Pro_v1.01"`: This explicitly sets the name of the generated executable.

    The executable will be generated in the `dist` folder.

## 🤝 Support & Donation

This project is open-source and developed in my free time. If you find it useful, consider supporting its continued development:

<a href="https://ko-fi.com/zamakanino" target="_blank">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Buy Me A Coffee" height="30">
</a>

## 🌐 Connect

* **GitHub Profile:** [zamakanino](https://github.com/zamakanino)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note:** Remember to replace `your-username` and `your-repo-name` with your actual GitHub username and repository name once you create it. Also, update the placeholder screenshot with a real one!
