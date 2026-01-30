# 📖 Daily Bible Facebook Poster (Template)

Automatically posts a daily Bible verse with an image to your Facebook Page.

## ✨ Features
- Daily verse rotation
- Auto background images
- Clean text overlay
- Fully automated via GitHub Actions

---

## 🚀 Quick Start

### 1. Use this template
Click **Use this template** → Create your own repo

---

### 2. Facebook setup
You need:
- A Facebook Page
- Page Access Token with:
  - pages_manage_posts
  - pages_read_engagement

---

### 3. Add GitHub Secrets
Go to **Settings → Secrets → Actions**

Add:
- `FB_PAGE_ID`
- `FB_PAGE_ACCESS_TOKEN`
- `PEXELS_API_KEY`

---

### 4. Customize verses
Edit `verses.json`

---

### 5. Run
- Auto runs daily
- Or go to **Actions → Run workflow**

---

## 🕒 Schedule
Default: once per day (UTC)

Change in:
`.github/workflows/post_daily.yml`

---

## 📸 Image credit
Images provided via Pexels API.

---

## 🛠 Customization ideas
- Filipino verses
- Instagram cross-post
- Weekly themes
