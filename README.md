<h1 align="center">Naliv Auto Bot</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Aiogram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Aiogram">
  <img src="https://img.shields.io/badge/Telegram%20Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/pythonanywhere-26A5E4?style=for-the-badge&logo=pythonanywhere&logoColor=white" alt="pythonanywhere.com">
</p>

<p align="center">
  <b>Naliv Auto</b> — Telegram bot for automating a logistician's tasks. <br>
 The system helps with interacting with drivers by automating the tasks of a logistics coordinator.
</p>

<p align="center">
  <!-- Telegram Bot Link -->
  <a href="https://t.me/nalivauto_bot" target="_blank">
    <img src="https://img.shields.io/badge/Open%20in-Telegram-26A5E4?style=for-the-badge&logo=telegram" alt="Open in Telegram">
  </a>
</p>

---

<h2>📸 Screenshot</h2>
<details>
<summary>Broadcast</summary>
<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px;">
  <img width="48%" src="#" />
  <img width="48%" alt="#" src="#" />
  <img width="48%" alt="#" src="#" />
  <img width="48%" alt="#" src="#" />
  <img width="48%" alt="#" src="#" />
  <img width="48%" alt="#"  src="#" />
</div>
</details>
<details>
<summary>Others</summary>
<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px;">
  <img width="48%" src="#" />
  <img width="48%" alt="#" src="#" />
  <img width="48%" alt="#" src="#" />
  <img width="48%" alt="#" src="#" />
  <img width="48%" alt="#" src="#" />
  <img width="48%" alt="#"  src="#" />
</div>
</details>


<h2>🤖 Bot Commands & Features</h2>

<ul style="display:inline-block; text-align:left;">
  <li><code>/start</code> – welcome message and main menu</li>
  <li><code>/info</code> – about the bot and the reminder</li>
  <li><code>/help</code> – logistics commands</li>
  <li><code>/ask</code> – ask the driver a question (manually)</li>
  <li><code>/who</code> – select a role within the group (so that the driver remembers the driver as a driver)
  (manually)</li>
  <li><code>/groups</code> – list of connected groups</li>
  <li><code>/driver</code> – assign a driver: VEHICLE @user (manually)</li> 
  <li><code>/broadcast</code> – mailing: HH:MM text (UTC +3)</li>
  <li><code>/delroute</code> – delete a flight by number</li>
  <li><code>/routes</code> – list of routes</li>
  <li><code>/route</code> – trip: date:time:vehicle:route:offset</li>
</ul>
<p>*By "manual," it is meant that these actions already take place automatically, without the need for commands.</p>

<h2>🚀 How to Use</h2>

<p>
  1. Open Telegram and search for <code>@nalivauto_bot</code>.<br>
  2. Start the bot with <code>/start</code>.<br>
  3. Use the menu commands.
</p>

<h2>⚙️ Installation (for developers)</h2>

<p>
  <i>Want to run your own instance?</i>
</p>

<pre style="background:#f6f8fa; padding:15px; border-radius:8px; max-width:800px; margin:0 auto;"><code># 1. Clone the repository
git clone https://github.com/yourusername/nalivauto-bot.git
cd nalivauto-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create a .env file with your bot token
echo "BOT_TOKEN=your_telegram_bot_token" > .env

# 4. Run the bot
python bot.py</code></pre>
